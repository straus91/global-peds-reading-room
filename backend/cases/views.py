# backend/cases/views.py

from rest_framework import viewsets, permissions, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import transaction, models
import re # For parsing LLM output

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
    def post(self, request, report_id, format=None):
        try:
            user_report = Report.objects.select_related('case', 'case__master_template', 'user').get(pk=report_id, user=request.user)
        except Report.DoesNotExist:
            return Response(
                {"error": "Report not found or you do not have permission to access it."},
                status=status.HTTP_404_NOT_FOUND
            )

        case_instance = user_report.case
        if not case_instance.master_template:
            return Response(
                {"error": "This case does not have an associated master template. AI feedback cannot be generated without a structure."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer_context = {'request': request}
        # Fetch user's report content with enriched section names/orders from ReportSerializer
        user_report_data = ReportSerializer(user_report, context=serializer_context).data
        user_report_sections_for_llm = user_report_data.get('structured_content', [])

        if not user_report_sections_for_llm:
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
                return Response(
                    {"error": "No expert template found for this case. AI feedback cannot be generated."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            else:
                print(f"Warning: English expert template not found for case {case_instance.id}. Using expert template in language: {expert_template_instance.language.code}")

        expert_report_data_for_llm = CaseTemplateSerializer(expert_template_instance, context=serializer_context).data
        expert_report_sections_for_llm = expert_report_data_for_llm.get('section_contents', [])
        
        expert_section_content_objects = expert_template_instance.section_contents_ordered

        if not expert_report_sections_for_llm:
             return Response(
                {"error": "Expert report content is missing or empty. Cannot generate feedback."},
                status=status.HTTP_400_BAD_REQUEST
            )

        programmatic_pre_analysis = generate_report_comparison_summary(
            user_report_structured_content=user_report_sections_for_llm, 
            expert_section_contents=expert_section_content_objects, 
            case_diagnosis_text=case_instance.diagnosis or ""
        )
        
        # NEW: Extract the identical sections for optimization
        identical_section_ids = set()
        for section_comp in programmatic_pre_analysis.get('section_comparisons', []):
            if section_comp.get('text_comparison_status') == "Identical":
                section_id = section_comp.get('master_template_section_id')
                if section_id:
                    identical_section_ids.add(section_id)
        
        print(f"Found {len(identical_section_ids)} sections that are identical to expert report")
        
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

        structured_llm_feedback = self._parse_llm_feedback_text(ai_feedback_text)

        # Save the generated AI feedback to the Report instance
        user_report.ai_feedback_content = {
            "raw_llm_feedback": ai_feedback_text,
            "structured_feedback": structured_llm_feedback
        }
        user_report.save() # Persist the changes to the database

        return Response(
            user_report.ai_feedback_content, # Return the newly saved content
            status=status.HTTP_200_OK
        )

    def _parse_llm_feedback_text(self, feedback_text):
        """
        Parses the LLM's text output into a more structured format.
        This handles both the discrepancy list and the new section-by-section severity assessment.
        """
        parsed_feedback = {
            "overall_impression_alignment": "",
            "section_feedback": [],
            "key_learning_points": []
        }

        # Add debug output
        print("_parse_llm_feedback_text called with:", feedback_text[:100], "...") # Print first 100 chars
        
        # Pattern to match the numbered sections from Gemini's response format
        critical_section_pattern = re.compile(r"1\.\s*CRITICAL\s+DISCREPANCIES:(.*?)(?=2\.\s*NON-CRITICAL\s+DISCREPANCIES:|SECTION SEVERITY ASSESSMENT:|$)", re.DOTALL | re.IGNORECASE)
        non_critical_section_pattern = re.compile(r"2\.\s*NON-CRITICAL\s+DISCREPANCIES:(.*?)(?=SECTION SEVERITY ASSESSMENT:|$)", re.DOTALL | re.IGNORECASE)
        
        # NEW: Pattern to extract the section-by-section severity assessment
        severity_assessment_pattern = re.compile(r"SECTION SEVERITY ASSESSMENT:(.*?)(?=$)", re.DOTALL | re.IGNORECASE)
        section_assessment_pattern = re.compile(r"Section:\s*(.+?)\nSeverity:\s*(.+?)\nReason:\s*(.+?)(?=\n\nSection:|$)", re.DOTALL)
        
        # Pattern to match individual bullet points
        bullet_point_pattern = re.compile(r"-\s*You\s+(.*?)(?=-\s*You|$)", re.DOTALL)

        # First, try to extract the critical discrepancies section
        critical_match = critical_section_pattern.search(feedback_text)
        if critical_match:
            critical_section = critical_match.group(1).strip()
            
            # Check if there's actual content or just "None identified"
            if critical_section and "None identified" not in critical_section:
                # Extract individual bullet points
                bullet_matches = bullet_point_pattern.finditer(critical_section)
                for bullet_match in bullet_matches:
                    bullet_content = bullet_match.group(1).strip()
                    if bullet_content:
                        # Extract section name if possible (assuming format like "In the Findings section, you...")
                        section_name = "General"
                        section_match = re.search(r"(?:in|for)\s+the\s+(\w+)(?:\s+section)?", bullet_content, re.IGNORECASE)
                        if section_match:
                            section_name = section_match.group(1).capitalize()
                        
                        # Store critical discrepancy for this section
                        parsed_feedback["section_feedback"].append({
                            "section_name": section_name,
                            "discrepancy_summary_from_llm": "You " + bullet_content,
                            "severity_level_from_llm": "Critical",
                            "severity_justification_from_llm": bullet_content
                        })
        
        # Next, extract the non-critical discrepancies section
        non_critical_match = non_critical_section_pattern.search(feedback_text)
        if non_critical_match:
            non_critical_section = non_critical_match.group(1).strip()
            
            # Check if there's actual content or just "None identified"
            if non_critical_section and "None identified" not in non_critical_section:
                # Extract individual bullet points
                bullet_matches = bullet_point_pattern.finditer(non_critical_section)
                for bullet_match in bullet_matches:
                    bullet_content = bullet_match.group(1).strip()
                    if bullet_content:
                        # Extract section name if possible
                        section_name = "General"
                        section_match = re.search(r"(?:in|for)\s+the\s+(\w+)(?:\s+section)?", bullet_content, re.IGNORECASE)
                        if section_match:
                            section_name = section_match.group(1).capitalize()
                        
                        # Store moderate discrepancy for this section
                        parsed_feedback["section_feedback"].append({
                            "section_name": section_name,
                            "discrepancy_summary_from_llm": "You " + bullet_content,
                            "severity_level_from_llm": "Moderate",
                            "severity_justification_from_llm": bullet_content
                        })
        
        # NEW: Extract the section-by-section severity assessment
        severity_assessment_match = severity_assessment_pattern.search(feedback_text)
        if severity_assessment_match:
            severity_assessment_section = severity_assessment_match.group(1).strip()
            
            # Create a map to look up existing sections for merging
            section_feedback_map = {item["section_name"].lower(): item for item in parsed_feedback["section_feedback"]}
            
            # Extract individual section assessments
            section_assessments = section_assessment_pattern.finditer(severity_assessment_section)
            for assessment in section_assessments:
                section_name = assessment.group(1).strip()
                severity = assessment.group(2).strip()
                reason = assessment.group(3).strip()
                
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
                    
                    # Only upgrade severity (e.g., from Moderate to Critical), never downgrade
                    if existing_entry["severity_level_from_llm"] != "Critical" and normalized_severity == "Critical":
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
            
            print(f"Extracted {len(section_feedback_map)} section severity assessments")
        else:
            print("WARNING: No section-by-section severity assessment found in LLM response")
        
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
        
        # Debug output to verify what we're returning
        print("Parsed feedback structure:")
        print(f"- Overall impression: {parsed_feedback['overall_impression_alignment'][:50]}...")
        print(f"- Number of section feedback items: {len(parsed_feedback['section_feedback'])}")
        for idx, sf in enumerate(parsed_feedback['section_feedback']):
            print(f"  Section {idx+1}: {sf['section_name']} - Severity: {sf['severity_level_from_llm']}")
        print(f"- Number of learning points: {len(parsed_feedback['key_learning_points'])}")
        
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
    def reset(self, request, pk=None):
        """Reset a case for the current user to allow them to submit a new report."""
        case = self.get_object()
        user = request.user
        
        # Find existing reports by this user for this case
        existing_reports = Report.objects.filter(user=user, case=case)
        
        if not existing_reports.exists():
            return Response({"detail": "No reports found for this case."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Archive existing reports by adding an 'archived' flag (we don't want to delete them)
            for report in existing_reports:
                report.is_archived = True
                report.save()
                
            # Remove the user's view record to reset the 'viewed' status
            UserCaseView.objects.filter(user=user, case=case).delete()
            
            return Response({
                "status": "success", 
                "message": "Case has been reset. You can now submit a new report.",
                "previous_reports_count": existing_reports.count()
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": f"Error resetting case: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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