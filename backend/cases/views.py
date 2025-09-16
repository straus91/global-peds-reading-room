# backend/cases/views.py

import re # For parsing LLM output
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
    Case, Report, Language, UserCaseView, CaseStatusChoices,
    MasterTemplate, MasterTemplateSection,
    CaseTemplate, CaseTemplateSectionContent,
    AIFeedbackRating
)
# Updated serializer imports
from .serializers import (
    CaseSerializer, CaseListSerializer, AdminCaseListSerializer, ReportSerializer, LanguageSerializer,
    MasterTemplateSerializer,
    CaseTemplateSerializer,
    AdminCaseTemplateSetupSerializer,
    BulkCaseTemplateSectionContentUpdateSerializer,
    AIFeedbackRatingSerializer
)

from .llm_feedback_service import get_feedback_from_llm
from .utils import generate_report_comparison_summary

# --- ViewSets ---

class LanguageViewSet(viewsets.ModelViewSet):
    queryset = Language.objects.filter(is_active=True)
    serializer_class = LanguageSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            self.permission_classes = [permissions.IsAuthenticated]
        else:
            self.permission_classes = [permissions.IsAdminUser]
        return super().get_permissions()

class AdminMasterTemplateViewSet(viewsets.ModelViewSet):
    queryset = MasterTemplate.objects.prefetch_related('sections').all().order_by('name')
    serializer_class = MasterTemplateSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_serializer_context(self):
        return {'request': self.request, **super().get_serializer_context()}

class AdminCaseViewSet(viewsets.ModelViewSet):
    queryset = Case.objects.all().order_by('-created_at')
    permission_classes = [permissions.IsAdminUser]

    def get_serializer_class(self):
        if self.action == 'list':
            return AdminCaseListSerializer
        return CaseSerializer

    def get_serializer_context(self):
        return {'request': self.request, **super().get_serializer_context()}

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @transaction.atomic
    def perform_update(self, serializer):
        instance = serializer.instance
        new_status = serializer.validated_data.get('status', instance.status)
        if new_status == CaseStatusChoices.PUBLISHED and instance.status != CaseStatusChoices.PUBLISHED and not instance.published_at:
            serializer.save(published_at=timezone.now())
        else:
            serializer.save()

    @action(detail=True, methods=['get', 'post'], url_path='expert-templates', permission_classes=[permissions.IsAdminUser])
    def manage_expert_templates(self, request, pk=None):
        case = self.get_object()
        if request.method == 'GET':
            case_templates = CaseTemplate.objects.filter(case=case).order_by('language__name')
            serializer = CaseTemplateSerializer(case_templates, many=True, context=self.get_serializer_context())
            return Response(serializer.data)
        
        elif request.method == 'POST':
            setup_serializer = AdminCaseTemplateSetupSerializer(
                data=request.data, 
                context={'request': request, 'case': case} 
            )
            if setup_serializer.is_valid(raise_exception=True):
                case_template_instance = setup_serializer.save() 
                # Return the full CaseTemplate representation
                response_serializer = CaseTemplateSerializer(case_template_instance, context=self.get_serializer_context())
                return Response(response_serializer.data, status=status.HTTP_201_CREATED)
            return Response(setup_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    @action(detail=True, methods=['delete'], url_path='expert-templates/(?P<case_template_pk>[^/.]+)', permission_classes=[permissions.IsAdminUser])
    def delete_expert_template(self, request, pk=None, case_template_pk=None):
        case = self.get_object()
        case_template = get_object_or_404(CaseTemplate, pk=case_template_pk, case=case)
        case_template.delete()
        return Response({"detail": "Expert template deleted successfully."}, status=status.HTTP_204_NO_CONTENT)


class AIReportFeedbackView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    # Use GET to retrieve previously saved AI feedback
    def get(self, request, report_id, format=None):
        try:
            user_report = Report.objects.select_related('case', 'case__master_template', 'user').get(pk=report_id, user=request.user)
        except Report.DoesNotExist:
            return Response(
                {"error": "Report not found or you do not have permission to access it."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check if AI feedback is already saved
        if user_report.ai_feedback_content and user_report.ai_feedback_content != {}: # Check if not empty dict
            return Response(user_report.ai_feedback_content, status=status.HTTP_200_OK)
        else:
            # If no feedback content exists, return a 404 to indicate it needs to be generated
            return Response({"error": "AI feedback not yet generated for this report. Please generate it using a POST request."}, status=status.HTTP_404_NOT_FOUND)

    # Use POST to generate and save new AI feedback
    @transaction.atomic
    def post(self, request, report_id, format=None):
        # Add transaction savepoint for rollback if needed
        sid = transaction.savepoint()
        
        try:
            # Validate user has access to this report
            try:
                user_report = Report.objects.select_related('case', 'case__master_template', 'user').get(pk=report_id, user=request.user)
            except Report.DoesNotExist:
                logger.warning(f"User {request.user.id} attempted to access report {report_id} which doesn't exist or belong to them")
                return Response(
                    {"error": "Report not found or you do not have permission to access it."},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Log the beginning of AI feedback generation
            logger.info(f"Starting AI feedback generation for report {report_id} by user {request.user.id}")
            
            # Validate case has master template
            case_instance = user_report.case
            if not case_instance.master_template:
                logger.error(f"Case {case_instance.id} has no master template, cannot generate AI feedback")
                return Response(
                    {"error": "This case does not have an associated master template. AI feedback cannot be generated without a structure."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get user report data
            serializer_context = {'request': request}
            user_report_data = ReportSerializer(user_report, context=serializer_context).data
            user_report_sections_for_llm = user_report_data.get('structured_content', [])

            if not user_report_sections_for_llm:
                logger.error(f"User's report {report_id} has no content, cannot generate AI feedback")
                return Response(
                    {"error": "User's report content is missing or empty. Cannot generate feedback."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get expert template (prefer English, fallback to any if English not found)
            expert_template_instance = CaseTemplate.objects.select_related('language') \
                                       .prefetch_related(
                                           models.Prefetch(
                                               'section_contents',
                                               queryset=CaseTemplateSectionContent.objects.select_related('master_section').order_by('master_section__order')
                                           )
                                       ).filter(case=case_instance, language__code='en').first()

            if not expert_template_instance:
                expert_template_instance = CaseTemplate.objects.select_related('language') \
                                           .prefetch_related(
                                               models.Prefetch(
                                                   'section_contents',
                                                   queryset=CaseTemplateSectionContent.objects.select_related('master_section').order_by('master_section__order')
                                               )
                                           ).filter(case=case_instance).first()
                if not expert_template_instance:
                    logger.error(f"No expert template found for case {case_instance.id}, cannot generate AI feedback")
                    return Response(
                        {"error": "No expert template found for this case. AI feedback cannot be generated."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                else:
                    logger.warning(f"English expert template not found for case {case_instance.id}. Using expert template in language: {expert_template_instance.language.code}")

            expert_report_data_for_llm = CaseTemplateSerializer(expert_template_instance, context=serializer_context).data
            expert_report_sections_for_llm = expert_report_data_for_llm.get('section_contents', [])
            
            expert_section_content_objects = expert_template_instance.section_contents_ordered

            if not expert_report_sections_for_llm:
                logger.error(f"Expert template {expert_template_instance.id} has no content, cannot generate AI feedback")
                return Response(
                    {"error": "Expert report content is missing or empty. Cannot generate feedback."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Generate programmatic pre-analysis
            try:
                programmatic_pre_analysis = generate_report_comparison_summary(
                    user_report_structured_content=user_report_sections_for_llm, 
                    expert_section_contents=expert_section_content_objects, 
                    case_diagnosis_text=case_instance.diagnosis or ""
                )
            except Exception as e:
                logger.error(f"Error generating report comparison summary: {str(e)}")
                transaction.savepoint_rollback(sid)
                return Response(
                    {"error": "An error occurred during report analysis. Please try again later."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # Extract the identical sections for optimization
            identical_section_ids = set()
            # Also create a mapping of section IDs to names for use in parsing
            identical_section_names = set()
            section_id_to_name_map = {}
            
            # Build maps of section IDs and names
            for section in user_report_sections_for_llm:
                section_id = section.get('master_template_section_id')
                section_name = section.get('section_name')
                if section_id and section_name:
                    section_id_to_name_map[section_id] = section_name
                    
            # Identify identical sections
            for section_comp in programmatic_pre_analysis.get('section_comparisons', []):
                if section_comp.get('text_comparison_status') == "Identical":
                    section_id = section_comp.get('master_template_section_id')
                    if section_id:
                        identical_section_ids.add(section_id)
                        # Store the section name for later use in parsing
                        if section_id in section_id_to_name_map:
                            identical_section_names.add(section_id_to_name_map[section_id])
            
            # Store identical section names for later use (no longer trying to attach to request)
            # We'll pass this directly to the parsing method instead
            
            logger.info(f"Found {len(identical_section_ids)} sections that are identical to expert report")
            
            # Get AI feedback from LLM
            try:
                ai_feedback_text = get_feedback_from_llm(
                    user_report_sections=user_report_sections_for_llm,
                    expert_report_sections=expert_report_sections_for_llm, 
                    programmatic_pre_analysis_summary=programmatic_pre_analysis,
                    case_identifier_for_llm=case_instance.case_identifier or f"Case ID {case_instance.id}",
                    case_patient_age=str(case_instance.patient_age) if case_instance.patient_age else "",
                    case_patient_sex=case_instance.patient_sex or "",
                    case_clinical_history=case_instance.clinical_history or "",
                    case_expert_key_findings=case_instance.key_findings or "",
                    case_expert_diagnosis=case_instance.diagnosis or "",
                    case_expert_discussion=case_instance.discussion or "",
                    case_difficulty=case_instance.get_difficulty_display() or "",
                    identical_section_ids=identical_section_ids  # Pass the identical sections
                )
            except Exception as e:
                logger.error(f"Error getting feedback from LLM: {str(e)}")
                transaction.savepoint_rollback(sid)
                return Response(
                    {"error": "An error occurred while generating AI feedback. Please try again later."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            # If the LLM response indicates an error, return the error message to the user
            if ai_feedback_text.startswith("Sorry, an error occurred") or ai_feedback_text.startswith("AI feedback service"):
                logger.error(f"LLM service returned an error: {ai_feedback_text}")
                transaction.savepoint_rollback(sid)
                return Response(
                    {"error": ai_feedback_text},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            # Parse the LLM feedback text
            try:
                structured_llm_feedback = self._parse_llm_feedback_text(ai_feedback_text, identical_section_names)
            except Exception as e:
                logger.error(f"Error parsing LLM feedback text: {str(e)}")
                transaction.savepoint_rollback(sid)
                return Response(
                    {"error": "An error occurred while processing the AI feedback. Please try again later."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            # Save the generated AI feedback to the Report instance
            try:
                user_report.ai_feedback_content = {
                    "raw_llm_feedback": ai_feedback_text,
                    "structured_feedback": structured_llm_feedback,
                    "generated_at": timezone.now().isoformat()
                }
                user_report.save()
                logger.info(f"Successfully saved AI feedback for report {report_id}")
                
                # Commit the transaction
                transaction.savepoint_commit(sid)
                
                return Response(
                    user_report.ai_feedback_content,
                    status=status.HTTP_200_OK
                )
            except Exception as e:
                logger.error(f"Error saving AI feedback to report: {str(e)}")
                transaction.savepoint_rollback(sid)
                return Response(
                    {"error": "An error occurred while saving the AI feedback. Please try again later."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
        except Exception as e:
            # Catch-all for any unexpected errors
            logger.error(f"Unexpected error in AI feedback generation: {str(e)}")
            transaction.savepoint_rollback(sid)
            return Response(
                {"error": "An unexpected error occurred. Please try again later."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
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
            "key_learning_points": []
        }

        # Add debug output
        logger.debug(f"Parsing LLM feedback text: {feedback_text[:100]}...") # Print first 100 chars
        
        # Compile the regex patterns for better performance
        # These are now module-level constants to avoid recompilation
        CRITICAL_SECTION_PATTERN = re.compile(r"1\.\s*CRITICAL\s+DISCREPANCIES:(.*?)(?=2\.\s*NON-CRITICAL\s+DISCREPANCIES:|SECTION SEVERITY ASSESSMENT:|$)", re.DOTALL | re.IGNORECASE)
        NON_CRITICAL_SECTION_PATTERN = re.compile(r"2\.\s*NON-CRITICAL\s+DISCREPANCIES:(.*?)(?=SECTION SEVERITY ASSESSMENT:|$)", re.DOTALL | re.IGNORECASE)
        SEVERITY_ASSESSMENT_PATTERN = re.compile(r"SECTION SEVERITY ASSESSMENT:(.*?)(?=$)", re.DOTALL | re.IGNORECASE)
        SECTION_ASSESSMENT_PATTERN = re.compile(r"Section:\s*(.+?)\nSeverity:\s*(.+?)\nReason:\s*(.+?)(?=\n\nSection:|$)", re.DOTALL)
        BULLET_POINT_PATTERN = re.compile(r"-\s*You\s+(.*?)(?=-\s*You|$)", re.DOTALL)
        SECTION_MENTION_PATTERN = re.compile(r"(?:in|for)\s+the\s+(\w+)(?:\s+section)?", re.IGNORECASE)

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
                            section_match = SECTION_MENTION_PATTERN.search(bullet_content)
                            if section_match:
                                section_name = section_match.group(1).capitalize()
                            
                            # Check if this is a programmatically identified identical section
                            is_identical_section = False
                            if section_name in identical_section_names:
                                is_identical_section = True
                                logger.info(f"Overriding 'Critical' severity for identical section: {section_name}")
                                
                            # Store discrepancy for this section
                            parsed_feedback["section_feedback"].append({
                                "section_name": section_name,
                                "discrepancy_summary_from_llm": "You " + bullet_content,
                                "severity_level_from_llm": "Consistent" if is_identical_section else "Critical",
                                "severity_justification_from_llm": "This section is identical to the expert report." if is_identical_section else bullet_content
                            })
            
            # Next, extract the non-critical discrepancies section
            non_critical_match = NON_CRITICAL_SECTION_PATTERN.search(feedback_text)
            if non_critical_match:
                non_critical_section = non_critical_match.group(1).strip()
                
                # Check if there's actual content or just "None identified"
                if non_critical_section and "None identified" not in non_critical_section:
                    # Extract individual bullet points
                    bullet_matches = BULLET_POINT_PATTERN.finditer(non_critical_section)
                    for bullet_match in bullet_matches:
                        bullet_content = bullet_match.group(1).strip()
                        if bullet_content:
                            # Extract section name if possible
                            section_name = "General"
                            section_match = SECTION_MENTION_PATTERN.search(bullet_content)
                            if section_match:
                                section_name = section_match.group(1).capitalize()
                            
                            # Check if this is a programmatically identified identical section
                            is_identical_section = False
                            if section_name in identical_section_names:
                                is_identical_section = True
                                logger.info(f"Overriding 'Moderate' severity for identical section: {section_name}")
                                
                            # Store moderate discrepancy for this section
                            parsed_feedback["section_feedback"].append({
                                "section_name": section_name,
                                "discrepancy_summary_from_llm": "You " + bullet_content,
                                "severity_level_from_llm": "Consistent" if is_identical_section else "Moderate",
                                "severity_justification_from_llm": "This section is identical to the expert report." if is_identical_section else bullet_content
                            })
        except Exception as e:
            logger.error(f"Error parsing discrepancy sections: {str(e)}")
            # Continue processing even if this part fails
        
        try:
            # Extract the section-by-section severity assessment
            severity_assessment_match = SEVERITY_ASSESSMENT_PATTERN.search(feedback_text)
            if severity_assessment_match:
                severity_assessment_section = severity_assessment_match.group(1).strip()
                
                # Create a map to look up existing sections for merging
                section_feedback_map = {item["section_name"].lower(): item for item in parsed_feedback["section_feedback"]}
                
                # Extract individual section assessments
                section_assessments = SECTION_ASSESSMENT_PATTERN.finditer(severity_assessment_section)
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
                        reason = "This section is identical to the expert report." if not reason else reason
                        logger.info(f"Programmatically enforcing 'Consistent' severity for identical section: {section_name}")
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
                        elif existing_entry["severity_level_from_llm"] != "Critical" and normalized_severity == "Critical":
                            existing_entry["severity_level_from_llm"] = "Critical"
                            # Update justification if we're upgrading severity
                            existing_entry["severity_justification_from_llm"] = reason
                    else:
                        # Add a new entry if we don't have one yet
                        parsed_feedback["section_feedback"].append({
                            "section_name": section_name,
                            "discrepancy_summary_from_llm": reason,  # Use reason as summary for new entries
                            "severity_level_from_llm": normalized_severity,
                            "severity_justification_from_llm": reason
                        })
                
                logger.info(f"Extracted {section_count} section severity assessments")
            else:
                logger.warning("No section-by-section severity assessment found in LLM response")
        except Exception as e:
            logger.error(f"Error parsing severity assessments: {str(e)}")
            # Continue processing even if this part fails
        
        try:
            # Set a basic overall impression based on the number of issues found
            if parsed_feedback["section_feedback"]:
                critical_count = sum(1 for item in parsed_feedback["section_feedback"] if item["severity_level_from_llm"] == "Critical")
                moderate_count = sum(1 for item in parsed_feedback["section_feedback"] if item["severity_level_from_llm"] == "Moderate")
                consistent_count = sum(1 for item in parsed_feedback["section_feedback"] if item["severity_level_from_llm"] == "Consistent")
                
                if critical_count > 0:
                    parsed_feedback["overall_impression_alignment"] = f"Found {critical_count} critical and {moderate_count} moderate discrepancies that need attention."
                elif moderate_count > 0:
                    parsed_feedback["overall_impression_alignment"] = f"Found {moderate_count} moderate discrepancies. Overall alignment is good with minor differences."
                else:
                    parsed_feedback["overall_impression_alignment"] = "Your report is well-aligned with the expert interpretation."
            else:
                # If we couldn't extract any structured feedback, put everything in overall_impression
                if feedback_text.strip(): 
                    parsed_feedback["overall_impression_alignment"] = "Could not parse detailed structure. Full AI Feedback: \n" + feedback_text
        except Exception as e:
            logger.error(f"Error generating overall impression: {str(e)}")
            parsed_feedback["overall_impression_alignment"] = "AI feedback was generated but summary extraction encountered an issue."
        
        # Debug output to verify what we're returning
        logger.debug("Parsed feedback structure:")
        logger.debug(f"- Overall impression: {parsed_feedback['overall_impression_alignment'][:50]}...")
        logger.debug(f"- Number of section feedback items: {len(parsed_feedback['section_feedback'])}")
        for idx, sf in enumerate(parsed_feedback['section_feedback'][:5]):  # Log just the first 5 to avoid excessive logging
            logger.debug(f"  Section {idx+1}: {sf['section_name']} - Severity: {sf['severity_level_from_llm']}")
        
        # Check for pneumothorax in critical findings specifically and make sure it's critical
        for sf in parsed_feedback['section_feedback']:
            summary = sf.get('discrepancy_summary_from_llm', '').lower()
            if 'pneumothorax' in summary and sf['severity_level_from_llm'] != 'Critical':
                logger.warning(f"Found pneumothorax in section {sf['section_name']} but severity is {sf['severity_level_from_llm']}. Upgrading to Critical.")
                sf['severity_level_from_llm'] = 'Critical'
                if 'pneumothorax' not in sf['severity_justification_from_llm'].lower():
                    sf['severity_justification_from_llm'] += " Critical due to potential pneumothorax which requires immediate attention."
        
        # Final check: Ensure all identical sections are consistently marked as "Consistent"
        if identical_section_names:
            for sf in parsed_feedback['section_feedback']:
                section_name = sf.get('section_name')
                if section_name in identical_section_names and sf['severity_level_from_llm'] != 'Consistent':
                    logger.warning(f"Final check: Section {section_name} was identical but severity was {sf['severity_level_from_llm']}. Correcting to Consistent.")
                    sf['severity_level_from_llm'] = 'Consistent'
                    sf['severity_justification_from_llm'] = "This section is identical to the expert report."
        
        return parsed_feedback


class CaseTemplateViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAdminUser]
    serializer_class = CaseTemplateSerializer

    def get_queryset(self):
        return CaseTemplate.objects.all()

    def get_serializer_context(self):
        return {'request': self.request}

    @action(detail=True, methods=['put'], url_path='update-sections')
    def update_sections_content(self, request, pk=None):
        case_template = get_object_or_404(CaseTemplate.objects.prefetch_related('section_contents__master_section'), pk=pk)
        existing_sections_qs = case_template.section_contents.all()
        
        context = self.get_serializer_context()
        context['instance_map'] = {section.id: section for section in existing_sections_qs}

        print(f"--- update_sections_content for CaseTemplate PK: {pk} ---")
        print(f"Request Method: {request.method}")
        print(f"Request Content-Type: {request.content_type}")
        print(f"Type of request.data: {type(request.data)}")
        print(f"Content of request.data: {request.data}")

        serializer = BulkCaseTemplateSectionContentUpdateSerializer(
            instance=existing_sections_qs, 
            data=request.data, 
            partial=True, 
            context=context 
        )
        
        if serializer.is_valid(raise_exception=True): 
            updated_sections = serializer.save() 
            case_template.refresh_from_db() 
            
            full_case_template_serializer = CaseTemplateSerializer(case_template, context=self.get_serializer_context())
            return Response(full_case_template_serializer.data)
        
    def retrieve(self, request, pk=None):
        case_template = get_object_or_404(CaseTemplate, pk=pk)
        serializer = CaseTemplateSerializer(case_template, context=self.get_serializer_context())
        return Response(serializer.data)

class UserCaseViewSet(viewsets.ReadOnlyModelViewSet): 
    queryset = Case.objects.filter(status=CaseStatusChoices.PUBLISHED).order_by('-published_at')
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'list':
            return CaseListSerializer
        return CaseSerializer 

    def get_serializer_context(self):
        return {'request': self.request, **super().get_serializer_context()}

    @action(detail=True, methods=['post'])
    def viewed(self, request, pk=None):
        case = self.get_object()
        _, created = UserCaseView.objects.get_or_create(user=request.user, case=case)
        status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        message = 'Case marked as viewed.' if created else 'Case already marked as viewed.'
        return Response({'status': message, 'created': created}, status=status_code)

    @action(detail=True, methods=['get'], url_path='expert-templates/(?P<language_code>[^/.]+)')
    def get_expert_template_by_language(self, request, pk=None, language_code=None): 
        case = self.get_object()
        try:
            language = Language.objects.get(code=language_code, is_active=True)
            case_template = get_object_or_404(CaseTemplate, case=case, language=language)
            serializer = CaseTemplateSerializer(case_template, context=self.get_serializer_context())
            return Response(serializer.data)
        except Language.DoesNotExist:
            return Response({"detail": f"Language with code '{language_code}' not found or not active."}, status=status.HTTP_404_NOT_FOUND)
        except CaseTemplate.DoesNotExist:
            return Response({"detail": f"Expert template in '{language_code}' not found for this case."}, status=status.HTTP_404_NOT_FOUND)
            
    @action(detail=True, methods=['post'])
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
                logger.warning(f"No reports found for user {user.id} on case {case.id} to reset")
                return Response({"detail": "No reports found for this case."}, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                # Archive existing reports by adding an 'archived' flag (we don't want to delete them)
                report_count = existing_reports.count()
                report_ids = list(existing_reports.values_list('id', flat=True))
                
                # Bulk update to improve performance
                Report.objects.filter(id__in=report_ids).update(
                    is_archived=True,
                    updated_at=timezone.now()
                )
                    
                # Remove the user's view record to reset the 'viewed' status
                view_count = UserCaseView.objects.filter(user=user, case=case).count()
                UserCaseView.objects.filter(user=user, case=case).delete()
                
                logger.info(f"Successfully reset case {case.id} for user {user.id}. Archived {report_count} reports and removed {view_count} view records.")
                transaction.savepoint_commit(sid)
                
                return Response({
                    "status": "success", 
                    "message": "Case has been reset. You can now submit a new report.",
                    "previous_reports_count": report_count
                }, status=status.HTTP_200_OK)
            except Exception as e:
                logger.error(f"Error resetting case {case.id} for user {user.id}: {str(e)}")
                transaction.savepoint_rollback(sid)
                return Response({"detail": "Error resetting case. Please try again later."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            logger.error(f"Unexpected error in reset case action: {str(e)}")
            transaction.savepoint_rollback(sid)
            return Response({"detail": "An unexpected error occurred. Please try again later."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ReportCreateView(generics.CreateAPIView): 
    serializer_class = ReportSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_context(self):
        return {'request': self.request, **super().get_serializer_context()}

class MyReportsListView(generics.ListAPIView): 
    serializer_class = ReportSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Only show non-archived reports by default
        return Report.objects.filter(user=self.request.user, is_archived=False).order_by('-submitted_at')
    
    def get_serializer_context(self):
        return {'request': self.request, **super().get_serializer_context()}
    
class AIFeedbackRatingCreateView(generics.CreateAPIView): 
    queryset = AIFeedbackRating.objects.all()
    serializer_class = AIFeedbackRatingSerializer
    permission_classes = [permissions.IsAuthenticated]