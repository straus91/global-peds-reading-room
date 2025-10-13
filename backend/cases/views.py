# backend/cases/views.py

import re  # For parsing LLM output
import logging

from rest_framework import viewsets, permissions, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import transaction, models
from django.core.exceptions import ValidationError

# Configure logger
logger = logging.getLogger(__name__)

# Updated model imports
from .models import (
    Case,
    Report,
    Language,
    UserCaseView,
    CaseStatusChoices,
    MasterTemplate,
    MasterTemplateSection,
    CaseTemplate,
    CaseTemplateSectionContent,
    AIFeedbackRating,
    AIFeedbackDetailedRating,
    TutoringSession,
    TutoringTurn,
    TutoringSessionStatusChoices,
)

# Updated serializer imports
from .serializers import (
    CaseSerializer,
    CaseListSerializer,
    AdminCaseListSerializer,
    ReportSerializer,
    LanguageSerializer,
    MasterTemplateSerializer,
    CaseTemplateSerializer,
    AdminCaseTemplateSetupSerializer,
    BulkCaseTemplateSectionContentUpdateSerializer,
    AIFeedbackRatingSerializer,
    AIFeedbackDetailedRatingSerializer,
    TutoringSessionSerializer,
    TutoringSessionCreateSerializer,
    TutoringTurnSerializer,
    TutoringTurnCreateSerializer,
)

from .llm_feedback_service import get_feedback_from_llm, get_feedback_with_caching
from .utils import generate_report_comparison_summary

# --- ViewSets ---


class LanguageViewSet(viewsets.ModelViewSet):
    queryset = Language.objects.filter(is_active=True)
    serializer_class = LanguageSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            self.permission_classes = [permissions.IsAuthenticated]
        else:
            self.permission_classes = [permissions.IsAdminUser]
        return super().get_permissions()


class AdminMasterTemplateViewSet(viewsets.ModelViewSet):
    queryset = (
        MasterTemplate.objects.prefetch_related("sections").all().order_by("name")
    )
    serializer_class = MasterTemplateSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_serializer_context(self):
        return {"request": self.request, **super().get_serializer_context()}


class AdminCaseViewSet(viewsets.ModelViewSet):
    queryset = Case.objects.all().order_by("-created_at")
    permission_classes = [permissions.IsAdminUser]

    def get_serializer_class(self):
        if self.action == "list":
            return AdminCaseListSerializer
        return CaseSerializer

    def get_serializer_context(self):
        return {"request": self.request, **super().get_serializer_context()}

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @transaction.atomic
    def perform_update(self, serializer):
        instance = serializer.instance
        new_status = serializer.validated_data.get("status", instance.status)
        if (
            new_status == CaseStatusChoices.PUBLISHED
            and instance.status != CaseStatusChoices.PUBLISHED
            and not instance.published_at
        ):
            serializer.save(published_at=timezone.now())
        else:
            serializer.save()

    @action(
        detail=True,
        methods=["get", "post"],
        url_path="expert-templates",
        permission_classes=[permissions.IsAdminUser],
    )
    def manage_expert_templates(self, request, pk=None):
        case = self.get_object()
        if request.method == "GET":
            case_templates = CaseTemplate.objects.filter(case=case).order_by(
                "language__name"
            )
            serializer = CaseTemplateSerializer(
                case_templates, many=True, context=self.get_serializer_context()
            )
            return Response(serializer.data)

        elif request.method == "POST":
            setup_serializer = AdminCaseTemplateSetupSerializer(
                data=request.data, context={"request": request, "case": case}
            )
            if setup_serializer.is_valid(raise_exception=True):
                case_template_instance = setup_serializer.save()
                # Return the full CaseTemplate representation
                response_serializer = CaseTemplateSerializer(
                    case_template_instance, context=self.get_serializer_context()
                )
                return Response(
                    response_serializer.data, status=status.HTTP_201_CREATED
                )
            return Response(setup_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=True,
        methods=["delete"],
        url_path="expert-templates/(?P<case_template_pk>[^/.]+)",
        permission_classes=[permissions.IsAdminUser],
    )
    def delete_expert_template(self, request, pk=None, case_template_pk=None):
        case = self.get_object()
        case_template = get_object_or_404(CaseTemplate, pk=case_template_pk, case=case)
        case_template.delete()
        return Response(
            {"detail": "Expert template deleted successfully."},
            status=status.HTTP_204_NO_CONTENT,
        )


class AIReportFeedbackView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    # Use GET to retrieve previously saved AI feedback
    def get(self, request, report_id, format=None):
        try:
            user_report = Report.objects.select_related(
                "case", "case__master_template", "user"
            ).get(pk=report_id, user=request.user)
        except Report.DoesNotExist:
            return Response(
                {
                    "error": "Report not found or you do not have permission to access it."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # Check if AI feedback is already saved
        if (
            user_report.ai_feedback_content and user_report.ai_feedback_content != {}
        ):  # Check if not empty dict
            return Response(user_report.ai_feedback_content, status=status.HTTP_200_OK)
        else:
            # If no feedback content exists, return a 404 to indicate it needs to be generated
            return Response(
                {
                    "error": "AI feedback not yet generated for this report. Please generate it using a POST request."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

    # Use POST to generate and save new AI feedback
    @transaction.atomic
    def post(self, request, report_id, format=None):
        # Add transaction savepoint for rollback if needed
        sid = transaction.savepoint()

        try:
            # Validate user has access to this report
            try:
                user_report = Report.objects.select_related(
                    "case", "case__master_template", "user"
                ).get(pk=report_id, user=request.user)
            except Report.DoesNotExist:
                logger.warning(
                    f"User {request.user.id} attempted to access report {report_id} which doesn't exist or belong to them"
                )
                return Response(
                    {
                        "error": "Report not found or you do not have permission to access it."
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Log the beginning of AI feedback generation
            logger.info(
                f"Starting AI feedback generation for report {report_id} by user {request.user.id}"
            )

            # Validate case has master template
            case_instance = user_report.case
            if not case_instance.master_template:
                logger.error(
                    f"Case {case_instance.id} has no master template, cannot generate AI feedback"
                )
                return Response(
                    {
                        "error": "This case does not have an associated master template. AI feedback cannot be generated without a structure."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Get user report data
            serializer_context = {"request": request}
            user_report_data = ReportSerializer(
                user_report, context=serializer_context
            ).data
            user_report_sections_for_llm = user_report_data.get(
                "structured_content", []
            )

            if not user_report_sections_for_llm:
                logger.error(
                    f"User's report {report_id} has no content, cannot generate AI feedback"
                )
                return Response(
                    {
                        "error": "User's report content is missing or empty. Cannot generate feedback."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Get expert template (prefer English, fallback to any if English not found)
            expert_template_instance = (
                CaseTemplate.objects.select_related("language")
                .prefetch_related(
                    models.Prefetch(
                        "section_contents",
                        queryset=CaseTemplateSectionContent.objects.select_related(
                            "master_section"
                        ).order_by("master_section__order"),
                    )
                )
                .filter(case=case_instance, language__code="en")
                .first()
            )

            if not expert_template_instance:
                expert_template_instance = (
                    CaseTemplate.objects.select_related("language")
                    .prefetch_related(
                        models.Prefetch(
                            "section_contents",
                            queryset=CaseTemplateSectionContent.objects.select_related(
                                "master_section"
                            ).order_by("master_section__order"),
                        )
                    )
                    .filter(case=case_instance)
                    .first()
                )
                if not expert_template_instance:
                    logger.error(
                        f"No expert template found for case {case_instance.id}, cannot generate AI feedback"
                    )
                    return Response(
                        {
                            "error": "No expert template found for this case. AI feedback cannot be generated."
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                else:
                    logger.warning(
                        f"English expert template not found for case {case_instance.id}. Using expert template in language: {expert_template_instance.language.code}"
                    )

            expert_report_data_for_llm = CaseTemplateSerializer(
                expert_template_instance, context=serializer_context
            ).data
            expert_report_sections_for_llm = expert_report_data_for_llm.get(
                "section_contents", []
            )

            expert_section_content_objects = (
                expert_template_instance.section_contents_ordered
            )

            if not expert_report_sections_for_llm:
                logger.error(
                    f"Expert template {expert_template_instance.id} has no content, cannot generate AI feedback"
                )
                return Response(
                    {
                        "error": "Expert report content is missing or empty. Cannot generate feedback."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Generate programmatic pre-analysis
            try:
                programmatic_pre_analysis = generate_report_comparison_summary(
                    user_report_structured_content=user_report_sections_for_llm,
                    expert_section_contents=expert_section_content_objects,
                    case_diagnosis_text=case_instance.diagnosis or "",
                )
            except Exception as e:
                logger.error(f"Error generating report comparison summary: {str(e)}")
                transaction.savepoint_rollback(sid)
                return Response(
                    {
                        "error": "An error occurred during report analysis. Please try again later."
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            # Extract the identical sections for optimization
            identical_section_ids = set()
            # Also create a mapping of section IDs to names for use in parsing
            identical_section_names = set()
            section_id_to_name_map = {}

            # Build maps of section IDs and names
            for section in user_report_sections_for_llm:
                section_id = section.get("master_template_section_id")
                section_name = section.get("section_name")
                if section_id and section_name:
                    section_id_to_name_map[section_id] = section_name

            # Identify identical sections
            for section_comp in programmatic_pre_analysis.get(
                "section_comparisons", []
            ):
                if section_comp.get("text_comparison_status") == "Identical":
                    section_id = section_comp.get("master_template_section_id")
                    if section_id:
                        identical_section_ids.add(section_id)
                        # Store the section name for later use in parsing
                        if section_id in section_id_to_name_map:
                            identical_section_names.add(
                                section_id_to_name_map[section_id]
                            )

            # Store identical section names for later use (no longer trying to attach to request)
            # We'll pass this directly to the parsing method instead

            logger.info(
                f"Found {len(identical_section_ids)} sections that are identical to expert report"
            )

            # Get AI feedback from LLM (with caching and token tracking)
            try:
                ai_feedback_text = get_feedback_with_caching(
                    user_report_sections=user_report_sections_for_llm,
                    expert_report_sections=expert_report_sections_for_llm,
                    programmatic_pre_analysis_summary=programmatic_pre_analysis,
                    case=case_instance,  # ADD: Case instance for caching
                    report=user_report,  # ADD: Report instance for token logging
                    case_identifier_for_llm=case_instance.case_identifier
                    or f"Case ID {case_instance.id}",
                    case_patient_age=(
                        str(case_instance.patient_age)
                        if case_instance.patient_age
                        else ""
                    ),
                    case_patient_sex=case_instance.patient_sex or "",
                    case_clinical_history=case_instance.clinical_history or "",
                    case_expert_key_findings=case_instance.key_findings or "",
                    case_expert_diagnosis=case_instance.diagnosis or "",
                    case_expert_discussion=case_instance.discussion or "",
                    case_difficulty=case_instance.get_difficulty_display() or "",
                    identical_section_ids=identical_section_ids,  # Pass the identical sections
                )
            except Exception as e:
                logger.error(f"Error getting feedback from LLM: {str(e)}")
                transaction.savepoint_rollback(sid)
                return Response(
                    {
                        "error": "An error occurred while generating AI feedback. Please try again later."
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            # Check if feedback is dict (new parsed format) or string (error/legacy)
            if isinstance(ai_feedback_text, str):
                # Legacy format or error message
                if ai_feedback_text.startswith(
                    "Sorry, an error occurred"
                ) or ai_feedback_text.startswith("AI feedback service"):
                    logger.error(f"LLM service returned an error: {ai_feedback_text}")
                    transaction.savepoint_rollback(sid)
                    return Response(
                        {"error": ai_feedback_text},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    )

                # Legacy string response - should not happen with new get_feedback_with_caching
                logger.warning("Received legacy string feedback format")
                structured_llm_feedback = {
                    'raw_feedback': ai_feedback_text,
                    'overall_assessment': '',
                    'critical_discrepancies': [],
                    'non_critical_discrepancies': [],
                    'section_feedback': [],
                    'parse_success': False,
                    'parse_errors': ['Legacy format']
                }
            else:
                # New parsed format (dict) from get_feedback_with_caching
                structured_llm_feedback = ai_feedback_text

                # Check if parsing failed
                if not structured_llm_feedback.get('parse_success', True):
                    logger.warning(
                        f"Feedback parsing had errors: {structured_llm_feedback.get('parse_errors', [])}"
                    )

            # Save the generated AI feedback to the Report instance
            try:
                # structured_llm_feedback already contains raw_feedback, parsed fields, and metadata
                # Add generation timestamp
                feedback_to_save = {
                    **structured_llm_feedback,
                    "generated_at": timezone.now().isoformat(),
                }

                user_report.ai_feedback_content = feedback_to_save
                user_report.save()
                logger.info(
                    f"Successfully saved AI feedback for report {report_id} "
                    f"(parse_success: {structured_llm_feedback.get('parse_success', True)})"
                )

                # Commit the transaction
                transaction.savepoint_commit(sid)

                return Response(
                    user_report.ai_feedback_content, status=status.HTTP_200_OK
                )
            except Exception as e:
                logger.error(f"Error saving AI feedback to report: {str(e)}")
                transaction.savepoint_rollback(sid)
                return Response(
                    {
                        "error": "An error occurred while saving the AI feedback. Please try again later."
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        except Exception as e:
            # Catch-all for any unexpected errors
            logger.error(f"Unexpected error in AI feedback generation: {str(e)}")
            transaction.savepoint_rollback(sid)
            return Response(
                {"error": "An unexpected error occurred. Please try again later."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def _parse_llm_feedback_text(self, feedback_text, identical_section_names=None):
        """
        Parses the LLM's text output into a more structured format.
        This handles both the discrepancy list and the new section-by-section severity assessment.

        Args:
            feedback_text: The raw text output from the LLM
            identical_section_names: Set of section names that were programmatically identified as identical
        """
        if not feedback_text or not isinstance(feedback_text, str):
            logger.error(f"Invalid feedback text received: {type(feedback_text)}")
            raise ValueError("Invalid feedback text: must be a non-empty string")

        # Initialize identical_section_names to empty set if not provided
        if identical_section_names is None:
            identical_section_names = set()

        parsed_feedback = {
            "overall_impression_alignment": "",
            "section_feedback": [],
            "key_learning_points": [],
        }

        # Add debug output
        logger.debug(
            f"Parsing LLM feedback text: {feedback_text[:100]}..."
        )  # Print first 100 chars

        # Compile the regex patterns for better performance
        # These are now module-level constants to avoid recompilation
        CRITICAL_SECTION_PATTERN = re.compile(
            r"1\.\s*CRITICAL\s+DISCREPANCIES:(.*?)(?=2\.\s*NON-CRITICAL\s+DISCREPANCIES:|SECTION SEVERITY ASSESSMENT:|$)",
            re.DOTALL | re.IGNORECASE,
        )
        NON_CRITICAL_SECTION_PATTERN = re.compile(
            r"2\.\s*NON-CRITICAL\s+DISCREPANCIES:(.*?)(?=SECTION SEVERITY ASSESSMENT:|$)",
            re.DOTALL | re.IGNORECASE,
        )
        SEVERITY_ASSESSMENT_PATTERN = re.compile(
            r"SECTION SEVERITY ASSESSMENT:(.*?)(?=$)", re.DOTALL | re.IGNORECASE
        )
        SECTION_ASSESSMENT_PATTERN = re.compile(
            r"Section:\s*(.+?)\nSeverity:\s*(.+?)\nReason:\s*(.+?)(?=\n\nSection:|$)",
            re.DOTALL,
        )
        BULLET_POINT_PATTERN = re.compile(r"-\s*You\s+(.*?)(?=-\s*You|$)", re.DOTALL)
        SECTION_MENTION_PATTERN = re.compile(
            r"(?:in|for)\s+the\s+(\w+)(?:\s+section)?", re.IGNORECASE
        )

        try:
            # First, try to extract the critical discrepancies section
            critical_match = CRITICAL_SECTION_PATTERN.search(feedback_text)
            if critical_match:
                critical_section = critical_match.group(1).strip()

                # Check if there's actual content or just "None identified"
                if critical_section and "None identified" not in critical_section:
                    # Extract individual bullet points
                    bullet_matches = BULLET_POINT_PATTERN.finditer(critical_section)
                    for bullet_match in bullet_matches:
                        bullet_content = bullet_match.group(1).strip()
                        if bullet_content:
                            # Extract section name if possible (assuming format like "In the Findings section, you...")
                            section_name = "General"
                            section_match = SECTION_MENTION_PATTERN.search(
                                bullet_content
                            )
                            if section_match:
                                section_name = section_match.group(1).capitalize()

                            # Check if this is a programmatically identified identical section
                            is_identical_section = False
                            if section_name in identical_section_names:
                                is_identical_section = True
                                logger.info(
                                    f"Overriding 'Critical' severity for identical section: {section_name}"
                                )

                            # Store discrepancy for this section
                            parsed_feedback["section_feedback"].append(
                                {
                                    "section_name": section_name,
                                    "discrepancy_summary_from_llm": "You "
                                    + bullet_content,
                                    "severity_level_from_llm": (
                                        "Consistent"
                                        if is_identical_section
                                        else "Critical"
                                    ),
                                    "severity_justification_from_llm": (
                                        "This section is identical to the expert report."
                                        if is_identical_section
                                        else bullet_content
                                    ),
                                }
                            )

            # Next, extract the non-critical discrepancies section
            non_critical_match = NON_CRITICAL_SECTION_PATTERN.search(feedback_text)
            if non_critical_match:
                non_critical_section = non_critical_match.group(1).strip()

                # Check if there's actual content or just "None identified"
                if (
                    non_critical_section
                    and "None identified" not in non_critical_section
                ):
                    # Extract individual bullet points
                    bullet_matches = BULLET_POINT_PATTERN.finditer(non_critical_section)
                    for bullet_match in bullet_matches:
                        bullet_content = bullet_match.group(1).strip()
                        if bullet_content:
                            # Extract section name if possible
                            section_name = "General"
                            section_match = SECTION_MENTION_PATTERN.search(
                                bullet_content
                            )
                            if section_match:
                                section_name = section_match.group(1).capitalize()

                            # Check if this is a programmatically identified identical section
                            is_identical_section = False
                            if section_name in identical_section_names:
                                is_identical_section = True
                                logger.info(
                                    f"Overriding 'Moderate' severity for identical section: {section_name}"
                                )

                            # Store moderate discrepancy for this section
                            parsed_feedback["section_feedback"].append(
                                {
                                    "section_name": section_name,
                                    "discrepancy_summary_from_llm": "You "
                                    + bullet_content,
                                    "severity_level_from_llm": (
                                        "Consistent"
                                        if is_identical_section
                                        else "Moderate"
                                    ),
                                    "severity_justification_from_llm": (
                                        "This section is identical to the expert report."
                                        if is_identical_section
                                        else bullet_content
                                    ),
                                }
                            )
        except Exception as e:
            logger.error(f"Error parsing discrepancy sections: {str(e)}")
            # Continue processing even if this part fails

        try:
            # Extract the section-by-section severity assessment
            severity_assessment_match = SEVERITY_ASSESSMENT_PATTERN.search(
                feedback_text
            )
            if severity_assessment_match:
                severity_assessment_section = severity_assessment_match.group(1).strip()

                # Create a map to look up existing sections for merging
                section_feedback_map = {
                    item["section_name"].lower(): item
                    for item in parsed_feedback["section_feedback"]
                }

                # Extract individual section assessments
                section_assessments = SECTION_ASSESSMENT_PATTERN.finditer(
                    severity_assessment_section
                )
                section_count = 0
                for assessment in section_assessments:
                    section_count += 1
                    section_name = assessment.group(1).strip()
                    severity = assessment.group(2).strip()
                    reason = assessment.group(3).strip()

                    # Check if this is one of our programmatically identified identical sections
                    is_identical_section = False
                    if section_name in identical_section_names:
                        is_identical_section = True
                        normalized_severity = "Consistent"
                        reason = (
                            "This section is identical to the expert report."
                            if not reason
                            else reason
                        )
                        logger.info(
                            f"Programmatically enforcing 'Consistent' severity for identical section: {section_name}"
                        )
                    else:
                        # Normalize severity - ensure it's one of our three levels
                        if severity.lower() == "critical":
                            normalized_severity = "Critical"
                        elif severity.lower() == "moderate":
                            normalized_severity = "Moderate"
                        else:
                            normalized_severity = "Consistent"

                    # Check if we already have a feedback entry for this section
                    section_key = section_name.lower()
                    if section_key in section_feedback_map:
                        # Prioritize existing discrepancy feedback but update severity if needed
                        existing_entry = section_feedback_map[section_key]

                        # If this is an identical section, always force it to "Consistent"
                        if is_identical_section:
                            existing_entry["severity_level_from_llm"] = "Consistent"
                            existing_entry["severity_justification_from_llm"] = reason
                        # Otherwise only upgrade severity (e.g., from Moderate to Critical), never downgrade
                        elif (
                            existing_entry["severity_level_from_llm"] != "Critical"
                            and normalized_severity == "Critical"
                        ):
                            existing_entry["severity_level_from_llm"] = "Critical"
                            # Update justification if we're upgrading severity
                            existing_entry["severity_justification_from_llm"] = reason
                    else:
                        # Add a new entry if we don't have one yet
                        parsed_feedback["section_feedback"].append(
                            {
                                "section_name": section_name,
                                "discrepancy_summary_from_llm": reason,  # Use reason as summary for new entries
                                "severity_level_from_llm": normalized_severity,
                                "severity_justification_from_llm": reason,
                            }
                        )

                logger.info(f"Extracted {section_count} section severity assessments")
            else:
                logger.warning(
                    "No section-by-section severity assessment found in LLM response"
                )
        except Exception as e:
            logger.error(f"Error parsing severity assessments: {str(e)}")
            # Continue processing even if this part fails

        try:
            # Set a basic overall impression based on the number of issues found
            if parsed_feedback["section_feedback"]:
                critical_count = sum(
                    1
                    for item in parsed_feedback["section_feedback"]
                    if item["severity_level_from_llm"] == "Critical"
                )
                moderate_count = sum(
                    1
                    for item in parsed_feedback["section_feedback"]
                    if item["severity_level_from_llm"] == "Moderate"
                )
                consistent_count = sum(
                    1
                    for item in parsed_feedback["section_feedback"]
                    if item["severity_level_from_llm"] == "Consistent"
                )

                if critical_count > 0:
                    parsed_feedback["overall_impression_alignment"] = (
                        f"Found {critical_count} critical and {moderate_count} moderate discrepancies that need attention."
                    )
                elif moderate_count > 0:
                    parsed_feedback["overall_impression_alignment"] = (
                        f"Found {moderate_count} moderate discrepancies. Overall alignment is good with minor differences."
                    )
                else:
                    parsed_feedback["overall_impression_alignment"] = (
                        "Your report is well-aligned with the expert interpretation."
                    )
            else:
                # If we couldn't extract any structured feedback, put everything in overall_impression
                if feedback_text.strip():
                    parsed_feedback["overall_impression_alignment"] = (
                        "Could not parse detailed structure. Full AI Feedback: \n"
                        + feedback_text
                    )
        except Exception as e:
            logger.error(f"Error generating overall impression: {str(e)}")
            parsed_feedback["overall_impression_alignment"] = (
                "AI feedback was generated but summary extraction encountered an issue."
            )

        # Debug output to verify what we're returning
        logger.debug("Parsed feedback structure:")
        logger.debug(
            f"- Overall impression: {parsed_feedback['overall_impression_alignment'][:50]}..."
        )
        logger.debug(
            f"- Number of section feedback items: {len(parsed_feedback['section_feedback'])}"
        )
        for idx, sf in enumerate(
            parsed_feedback["section_feedback"][:5]
        ):  # Log just the first 5 to avoid excessive logging
            logger.debug(
                f"  Section {idx+1}: {sf['section_name']} - Severity: {sf['severity_level_from_llm']}"
            )

        # Check for pneumothorax in critical findings specifically and make sure it's critical
        for sf in parsed_feedback["section_feedback"]:
            summary = sf.get("discrepancy_summary_from_llm", "").lower()
            if (
                "pneumothorax" in summary
                and sf["severity_level_from_llm"] != "Critical"
            ):
                logger.warning(
                    f"Found pneumothorax in section {sf['section_name']} but severity is {sf['severity_level_from_llm']}. Upgrading to Critical."
                )
                sf["severity_level_from_llm"] = "Critical"
                if "pneumothorax" not in sf["severity_justification_from_llm"].lower():
                    sf[
                        "severity_justification_from_llm"
                    ] += " Critical due to potential pneumothorax which requires immediate attention."

        # Final check: Ensure all identical sections are consistently marked as "Consistent"
        if identical_section_names:
            for sf in parsed_feedback["section_feedback"]:
                section_name = sf.get("section_name")
                if (
                    section_name in identical_section_names
                    and sf["severity_level_from_llm"] != "Consistent"
                ):
                    logger.warning(
                        f"Final check: Section {section_name} was identical but severity was {sf['severity_level_from_llm']}. Correcting to Consistent."
                    )
                    sf["severity_level_from_llm"] = "Consistent"
                    sf["severity_justification_from_llm"] = (
                        "This section is identical to the expert report."
                    )

        return parsed_feedback


class CaseTemplateViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAdminUser]
    serializer_class = CaseTemplateSerializer

    def get_queryset(self):
        return CaseTemplate.objects.all()

    def get_serializer_context(self):
        return {"request": self.request}

    @action(detail=True, methods=["put"], url_path="update-sections")
    def update_sections_content(self, request, pk=None):
        case_template = get_object_or_404(
            CaseTemplate.objects.prefetch_related("section_contents__master_section"),
            pk=pk,
        )
        existing_sections_qs = case_template.section_contents.all()

        context = self.get_serializer_context()
        context["instance_map"] = {
            section.id: section for section in existing_sections_qs
        }

        print(f"--- update_sections_content for CaseTemplate PK: {pk} ---")
        print(f"Request Method: {request.method}")
        print(f"Request Content-Type: {request.content_type}")
        print(f"Type of request.data: {type(request.data)}")
        print(f"Content of request.data: {request.data}")

        serializer = BulkCaseTemplateSectionContentUpdateSerializer(
            instance=existing_sections_qs,
            data=request.data,
            partial=True,
            context=context,
        )

        if serializer.is_valid(raise_exception=True):
            updated_sections = serializer.save()
            case_template.refresh_from_db()

            full_case_template_serializer = CaseTemplateSerializer(
                case_template, context=self.get_serializer_context()
            )
            return Response(full_case_template_serializer.data)

    def retrieve(self, request, pk=None):
        case_template = get_object_or_404(CaseTemplate, pk=pk)
        serializer = CaseTemplateSerializer(
            case_template, context=self.get_serializer_context()
        )
        return Response(serializer.data)


class UserCaseViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Case.objects.filter(status=CaseStatusChoices.PUBLISHED).order_by(
        "-published_at"
    )
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "list":
            return CaseListSerializer
        return CaseSerializer

    def get_serializer_context(self):
        return {"request": self.request, **super().get_serializer_context()}

    @action(detail=True, methods=["post"])
    def viewed(self, request, pk=None):
        case = self.get_object()
        _, created = UserCaseView.objects.get_or_create(user=request.user, case=case)
        status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        message = (
            "Case marked as viewed." if created else "Case already marked as viewed."
        )
        return Response({"status": message, "created": created}, status=status_code)

    @action(
        detail=True,
        methods=["get"],
        url_path="expert-templates/(?P<language_code>[^/.]+)",
    )
    def get_expert_template_by_language(self, request, pk=None, language_code=None):
        case = self.get_object()
        try:
            language = Language.objects.get(code=language_code, is_active=True)
            case_template = get_object_or_404(
                CaseTemplate, case=case, language=language
            )
            serializer = CaseTemplateSerializer(
                case_template, context=self.get_serializer_context()
            )
            return Response(serializer.data)
        except Language.DoesNotExist:
            return Response(
                {
                    "detail": f"Language with code '{language_code}' not found or not active."
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        except CaseTemplate.DoesNotExist:
            return Response(
                {
                    "detail": f"Expert template in '{language_code}' not found for this case."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def reset(self, request, pk=None):
        """Reset a case for the current user to allow them to submit a new report."""
        sid = transaction.savepoint()
        try:
            case = self.get_object()
            user = request.user

            logger.info(f"User {user.id} requested to reset case {case.id}")

            # Find existing reports by this user for this case
            existing_reports = Report.objects.filter(user=user, case=case)

            if not existing_reports.exists():
                logger.warning(
                    f"No reports found for user {user.id} on case {case.id} to reset"
                )
                return Response(
                    {"detail": "No reports found for this case."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            try:
                # Archive existing reports by adding an 'archived' flag (we don't want to delete them)
                report_count = existing_reports.count()
                report_ids = list(existing_reports.values_list("id", flat=True))

                # Bulk update to improve performance
                Report.objects.filter(id__in=report_ids).update(
                    is_archived=True, updated_at=timezone.now()
                )

                # Remove the user's view record to reset the 'viewed' status
                view_count = UserCaseView.objects.filter(user=user, case=case).count()
                UserCaseView.objects.filter(user=user, case=case).delete()

                logger.info(
                    f"Successfully reset case {case.id} for user {user.id}. Archived {report_count} reports and removed {view_count} view records."
                )
                transaction.savepoint_commit(sid)

                return Response(
                    {
                        "status": "success",
                        "message": "Case has been reset. You can now submit a new report.",
                        "previous_reports_count": report_count,
                    },
                    status=status.HTTP_200_OK,
                )
            except Exception as e:
                logger.error(
                    f"Error resetting case {case.id} for user {user.id}: {str(e)}"
                )
                transaction.savepoint_rollback(sid)
                return Response(
                    {"detail": "Error resetting case. Please try again later."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        except Exception as e:
            logger.error(f"Unexpected error in reset case action: {str(e)}")
            transaction.savepoint_rollback(sid)
            return Response(
                {"detail": "An unexpected error occurred. Please try again later."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ReportCreateView(generics.CreateAPIView):
    serializer_class = ReportSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_context(self):
        return {"request": self.request, **super().get_serializer_context()}


class MyReportsListView(generics.ListAPIView):
    serializer_class = ReportSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Only show non-archived reports by default
        return Report.objects.filter(
            user=self.request.user, is_archived=False
        ).order_by("-submitted_at")

    def get_serializer_context(self):
        return {"request": self.request, **super().get_serializer_context()}


class AIFeedbackRatingCreateView(generics.CreateAPIView):
    queryset = AIFeedbackRating.objects.all()
    serializer_class = AIFeedbackRatingSerializer
    permission_classes = [permissions.IsAuthenticated]


class AIFeedbackDetailedRatingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for multi-dimensional AI feedback quality ratings.

    Provides CRUD operations for detailed ratings with analytics support.

    Endpoints:
    - POST /api/detailed-ratings/ - Submit a new detailed rating
    - GET /api/detailed-ratings/ - List user's own ratings
    - GET /api/detailed-ratings/{id}/ - Retrieve a specific rating
    - PUT/PATCH /api/detailed-ratings/{id}/ - Update rating
    - DELETE /api/detailed-ratings/{id}/ - Delete rating (admin only)

    Permissions:
    - Users can only view/edit their own ratings
    - Admins can view all ratings for analytics
    """
    serializer_class = AIFeedbackDetailedRatingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return only ratings by the current user, unless admin."""
        user = self.request.user

        if user.is_staff:
            # Admins can see all ratings for analytics
            return AIFeedbackDetailedRating.objects.select_related(
                'user', 'report', 'report__case'
            ).order_by('-rated_at')
        else:
            # Regular users only see their own ratings
            return AIFeedbackDetailedRating.objects.filter(
                user=user
            ).select_related(
                'report', 'report__case'
            ).order_by('-rated_at')

    def get_serializer_context(self):
        """Add request to serializer context for validation."""
        return {'request': self.request, **super().get_serializer_context()}

    def perform_destroy(self, instance):
        """Only allow admins to delete ratings."""
        if not self.request.user.is_staff:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only administrators can delete ratings.")
        instance.delete()

    @action(detail=False, methods=['get'], url_path='by-report/(?P<report_id>[^/.]+)')
    def by_report(self, request, report_id=None):
        """
        Get all ratings for a specific report.

        GET /api/detailed-ratings/by-report/{report_id}/

        Returns ratings for a report (user's own if not admin).
        """
        try:
            report = Report.objects.get(pk=report_id)
        except Report.DoesNotExist:
            return Response(
                {'error': 'Report not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check permissions
        if report.user != request.user and not request.user.is_staff:
            return Response(
                {'error': 'You do not have permission to view ratings for this report.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Get ratings for this report
        ratings = AIFeedbackDetailedRating.objects.filter(
            report=report
        ).select_related('user')

        serializer = self.get_serializer(ratings, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def analytics(self, request):
        """
        Get analytics summary for detailed ratings.

        GET /api/detailed-ratings/analytics/

        Returns aggregated statistics (admin only).
        """
        if not request.user.is_staff:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only administrators can view analytics.")

        from django.db.models import Avg, Count, Q

        # Get all ratings
        ratings = AIFeedbackDetailedRating.objects.all()

        # Calculate averages
        analytics_data = {
            'total_ratings': ratings.count(),
            'average_accuracy': ratings.aggregate(Avg('accuracy_rating'))['accuracy_rating__avg'],
            'average_helpfulness': ratings.aggregate(Avg('helpfulness_rating'))['helpfulness_rating__avg'],
            'average_actionability': ratings.aggregate(Avg('actionability_rating'))['actionability_rating__avg'],
            'average_overall': ratings.aggregate(Avg('overall_rating'))['overall_rating__avg'],
            'false_positive_count': ratings.filter(has_false_positives=True).count(),
            'false_positive_percentage': (
                (ratings.filter(has_false_positives=True).count() / ratings.count() * 100)
                if ratings.count() > 0 else 0
            ),
            'ratings_with_comments': ratings.exclude(
                Q(comment='') | Q(comment__isnull=True)
            ).count(),
        }

        # Round averages to 2 decimal places
        for key in ['average_accuracy', 'average_helpfulness', 'average_actionability', 'average_overall']:
            if analytics_data[key] is not None:
                analytics_data[key] = round(analytics_data[key], 2)

        analytics_data['false_positive_percentage'] = round(
            analytics_data['false_positive_percentage'], 1
        )

        return Response(analytics_data)

    @action(detail=False, methods=['get'], url_path='analytics/by-difficulty')
    def analytics_by_difficulty(self, request):
        """
        Get detailed rating analytics broken down by case difficulty.

        GET /api/detailed-ratings/analytics/by-difficulty/

        Returns average ratings for each difficulty level (admin only).
        Useful for identifying if AI feedback quality varies by case complexity.
        """
        if not request.user.is_staff:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only administrators can view analytics.")

        from django.db.models import Avg, Count

        # Get ratings grouped by case difficulty
        difficulty_data = AIFeedbackDetailedRating.objects.values(
            'report__case__difficulty'
        ).annotate(
            count=Count('id'),
            avg_accuracy=Avg('accuracy_rating'),
            avg_helpfulness=Avg('helpfulness_rating'),
            avg_actionability=Avg('actionability_rating'),
            avg_overall=Avg('overall_rating'),
            false_positives=Count('id', filter=models.Q(has_false_positives=True))
        ).order_by('report__case__difficulty')

        # Format results
        results = []
        for item in difficulty_data:
            results.append({
                'difficulty': item['report__case__difficulty'],
                'rating_count': item['count'],
                'average_accuracy': round(item['avg_accuracy'], 2) if item['avg_accuracy'] else None,
                'average_helpfulness': round(item['avg_helpfulness'], 2) if item['avg_helpfulness'] else None,
                'average_actionability': round(item['avg_actionability'], 2) if item['avg_actionability'] else None,
                'average_overall': round(item['avg_overall'], 2) if item['avg_overall'] else None,
                'false_positive_count': item['false_positives'],
                'false_positive_percentage': round(
                    (item['false_positives'] / item['count'] * 100) if item['count'] > 0 else 0,
                    1
                )
            })

        return Response({
            'by_difficulty': results,
            'note': 'Use this to identify if AI feedback quality varies by case complexity.'
        })

    @action(detail=False, methods=['get'], url_path='analytics/trends')
    def analytics_trends(self, request):
        """
        Get time-based trends for detailed ratings.

        GET /api/detailed-ratings/analytics/trends/?days=30

        Query parameters:
        - days (int): Number of days to look back (default: 30)

        Returns weekly aggregated ratings to track quality over time (admin only).
        """
        if not request.user.is_staff:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only administrators can view analytics.")

        from django.db.models import Avg, Count
        from django.db.models.functions import TruncWeek
        from datetime import timedelta

        # Get days parameter (default 30, max 365)
        days = int(request.GET.get('days', 30))
        if days > 365:
            days = 365

        cutoff_date = timezone.now() - timedelta(days=days)

        # Get ratings grouped by week
        weekly_data = AIFeedbackDetailedRating.objects.filter(
            rated_at__gte=cutoff_date
        ).annotate(
            week=TruncWeek('rated_at')
        ).values('week').annotate(
            count=Count('id'),
            avg_accuracy=Avg('accuracy_rating'),
            avg_helpfulness=Avg('helpfulness_rating'),
            avg_actionability=Avg('actionability_rating'),
            avg_overall=Avg('overall_rating'),
            false_positives=Count('id', filter=models.Q(has_false_positives=True))
        ).order_by('week')

        # Format results
        results = []
        for item in weekly_data:
            results.append({
                'week_start': item['week'].isoformat() if item['week'] else None,
                'rating_count': item['count'],
                'average_accuracy': round(item['avg_accuracy'], 2) if item['avg_accuracy'] else None,
                'average_helpfulness': round(item['avg_helpfulness'], 2) if item['avg_helpfulness'] else None,
                'average_actionability': round(item['avg_actionability'], 2) if item['avg_actionability'] else None,
                'average_overall': round(item['avg_overall'], 2) if item['avg_overall'] else None,
                'false_positive_count': item['false_positives']
            })

        return Response({
            'period_days': days,
            'weekly_trends': results,
            'note': 'Monitor for quality degradation after prompt changes.'
        })

    @action(detail=False, methods=['get'], url_path='analytics/false-positives')
    def analytics_false_positives(self, request):
        """
        Get detailed analysis of false positive reports.

        GET /api/detailed-ratings/analytics/false-positives/

        Returns list of ratings with false positives including details (admin only).
        Use this to identify specific AI feedback issues.
        """
        if not request.user.is_staff:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only administrators can view analytics.")

        # Get ratings with false positives
        false_positive_ratings = AIFeedbackDetailedRating.objects.filter(
            has_false_positives=True
        ).select_related(
            'report__case', 'user'
        ).order_by('-rated_at')

        # Format results
        results = []
        for rating in false_positive_ratings:
            results.append({
                'rating_id': rating.id,
                'report_id': rating.report.id,
                'case_identifier': rating.report.case.case_identifier,
                'case_difficulty': rating.report.case.difficulty,
                'user_id': rating.user.id,
                'username': rating.user.username,
                'rated_at': rating.rated_at.isoformat(),
                'false_positive_details': rating.false_positive_details,
                'overall_rating': rating.overall_rating,
                'comment': rating.comment
            })

        return Response({
            'false_positive_count': len(results),
            'false_positives': results,
            'note': 'Review these to improve AI feedback prompt accuracy.'
        })


# --- Tutoring Views ---


class TutoringSessionCreateView(generics.CreateAPIView):
    """
    Create a new tutoring session for a user's report.

    POST /api/tutoring/sessions/
    Body: {"report_id": 123}

    Returns: Full session object with empty turns array
    """
    serializer_class = TutoringSessionCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_context(self):
        return {"request": self.request, **super().get_serializer_context()}


class TutoringSessionRetrieveView(generics.RetrieveAPIView):
    """
    Retrieve a specific tutoring session with all its turns.

    GET /api/tutoring/sessions/{session_id}/

    Returns: Full session object with nested turns
    """
    serializer_class = TutoringSessionSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "id"

    def get_queryset(self):
        # Only allow users to retrieve their own sessions
        return TutoringSession.objects.filter(
            user=self.request.user
        ).select_related(
            "report",
            "report__case",
            "user"
        ).prefetch_related("turns")

    def get_serializer_context(self):
        return {"request": self.request, **super().get_serializer_context()}


class TutoringTurnCreateView(APIView):
    """
    Create a new turn in an existing tutoring session.

    POST /api/tutoring/sessions/{session_id}/turn/
    Body: {"user_message": "Why did I miss the pneumothorax?"}

    Returns: Full turn object with AI response

    Note: AI response generation will be implemented in Phase 2 (tutoring_service.py)
    For now, this creates a placeholder turn.
    """
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request, session_id, format=None):
        sid = transaction.savepoint()

        try:
            # Get the session
            try:
                session = TutoringSession.objects.select_related(
                    "report",
                    "report__case",
                    "user"
                ).get(id=session_id, user=request.user)
            except TutoringSession.DoesNotExist:
                return Response(
                    {"error": "Tutoring session not found or you do not have permission to access it."},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Check if session is still active
            if session.status != TutoringSessionStatusChoices.ACTIVE:
                return Response(
                    {"error": f"This tutoring session is {session.status}. Cannot add more turns."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Check if turn limit reached
            if session.turns_count >= session.max_turns:
                # Mark session as completed
                session.status = TutoringSessionStatusChoices.COMPLETED
                session.save(update_fields=["status"])

                return Response(
                    {"error": f"Maximum {session.max_turns} turns reached for this session. Session has been marked as completed."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Validate user message
            serializer = TutoringTurnCreateSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            user_message = serializer.validated_data["user_message"]

            # TODO: In Phase 2, call tutoring_service.py to generate AI response
            # For now, create a placeholder response
            import time
            start_time = time.time()

            ai_response = (
                "Thank you for your question. This is a placeholder response. "
                "In Phase 2, the tutoring service will analyze your question, "
                "use appropriate tools (case context, expert comparison, image analysis, etc.), "
                "and provide a helpful educational response."
            )

            response_time_ms = int((time.time() - start_time) * 1000)

            # Create the turn
            from django.db.models import F

            turn = TutoringTurn.objects.create(
                session=session,
                turn_number=session.turns_count + 1,
                user_message=user_message,
                ai_response=ai_response,
                tools_used=[],  # Will be populated by tutoring_service.py in Phase 2
                image_references=[],  # Will be detected by tutoring_service.py in Phase 2
                response_time_ms=response_time_ms
            )

            # Increment session turn count (atomic update to prevent race conditions)
            TutoringSession.objects.filter(id=session.id).update(
                turns_count=F("turns_count") + 1
            )

            # Refresh session to get updated count
            session.refresh_from_db()

            logger.info(
                f"Created turn {turn.turn_number} in session {session.id} "
                f"for user {request.user.id}"
            )

            transaction.savepoint_commit(sid)

            # Return the turn
            turn_serializer = TutoringTurnSerializer(turn)
            return Response(turn_serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Error creating tutoring turn: {str(e)}")
            transaction.savepoint_rollback(sid)
            return Response(
                {"error": "An error occurred while processing your question. Please try again."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TutoringSessionExportView(APIView):
    """
    Export a tutoring session transcript as plain text.

    GET /api/tutoring/sessions/{session_id}/export/

    Returns: Plain text transcript of the entire conversation
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, session_id, format=None):
        try:
            # Get the session
            session = TutoringSession.objects.select_related(
                "report",
                "report__case",
                "user"
            ).prefetch_related("turns").get(id=session_id, user=request.user)
        except TutoringSession.DoesNotExist:
            return Response(
                {"error": "Tutoring session not found or you do not have permission to access it."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Generate transcript
        from django.http import HttpResponse

        transcript = []
        transcript.append("=" * 80)
        transcript.append("TUTORING SESSION TRANSCRIPT")
        transcript.append("=" * 80)
        transcript.append("")
        transcript.append(f"Session ID: {session.id}")
        transcript.append(f"Case: {session.report.case.case_identifier}")
        transcript.append(f"Report ID: {session.report.id}")
        transcript.append(f"User: {session.user.username}")
        transcript.append(f"Started: {session.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        transcript.append(f"Status: {session.status}")
        transcript.append(f"Turns: {session.turns_count}/{session.max_turns}")
        transcript.append("")
        transcript.append("=" * 80)
        transcript.append("")

        # Add each turn
        for turn in session.turns.all():
            transcript.append(f"--- Turn {turn.turn_number} ---")
            transcript.append(f"Time: {turn.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            transcript.append("")
            transcript.append(f"USER: {turn.user_message}")
            transcript.append("")
            transcript.append(f"AI TUTOR: {turn.ai_response}")
            transcript.append("")
            if turn.tools_used:
                transcript.append(f"Tools used: {', '.join(turn.tools_used)}")
                transcript.append("")
            if turn.image_references:
                transcript.append(f"Images referenced: {turn.image_references}")
                transcript.append("")
            transcript.append("-" * 80)
            transcript.append("")

        transcript.append("=" * 80)
        transcript.append("END OF TRANSCRIPT")
        transcript.append("=" * 80)

        # Return as plain text file
        response = HttpResponse("\n".join(transcript), content_type="text/plain")
        response["Content-Disposition"] = f'attachment; filename="tutoring_session_{session.id}.txt"'
        return response
