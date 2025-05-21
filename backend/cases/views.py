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
            case_difficulty=case_instance.get_difficulty_display() or ""
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
        This is a best-effort parsing and might need refinement based on actual LLM output patterns.
        """
        parsed_feedback = {
            "overall_impression_alignment": "",
            "section_feedback": [],
            "key_learning_points": []
        }

        # Regex to find sections like "II. Section-by-Section Discrepancy Analysis:"
        # and "Severity: Critical - " or "Severity: Moderate - "
        section_header_pattern = re.compile(r"^\s*([A-Z]+(?: [A-Z]+)*):\s*(.*)", re.MULTILINE)
        severity_pattern = re.compile(r"Severity: (Critical|Moderate) - (.+)")
        learning_point_pattern = re.compile(r"Learning Point:\s*(.+?)\s*Advice:\s*(.+?)(?:\s*Topics for Further Study:\s*(.+))?(?=\nLearning Point:|\Z)", re.DOTALL)


        current_major_section = None
        current_section_name_for_feedback = None
        buffer = []

        # Split by major headers (I, II, III)
        raw_major_sections = re.split(r"\n\s*(?=I\.|II\.|III\.)", feedback_text)

        for part in raw_major_sections:
            part = part.strip()
            if not part:
                continue

            if part.startswith("I. Overall Impression Alignment:"):
                parsed_feedback["overall_impression_alignment"] = part.replace("I. Overall Impression Alignment:", "").strip()
            elif part.startswith("II. Section-by-Section Discrepancy Analysis:"):
                content = part.replace("II. Section-by-Section Discrepancy Analysis:", "").strip()
                # Split by individual section mentions (e.g., "Findings:", "Impression:")
                # This assumes LLM uses "Section Name:" format
                individual_section_parts = re.split(r"\n\s*(?=[A-Za-z ]+:\s*Severity:)", "\n" + content) # Add newline to catch first
                for section_part in individual_section_parts:
                    section_part = section_part.strip()
                    if not section_part:
                        continue
                    
                    section_name_match = re.match(r"(.+?):\s*(Severity:.*)", section_part, re.DOTALL)
                    if section_name_match:
                        section_name = section_name_match.group(1).strip()
                        severity_and_justification_text = section_name_match.group(2).strip()
                        
                        severity_match = severity_pattern.search(severity_and_justification_text)
                        if severity_match:
                            severity = severity_match.group(1)
                            justification = severity_match.group(2).strip()
                            parsed_feedback["section_feedback"].append({
                                "section_name": section_name,
                                "discrepancy_summary_from_llm": justification, 
                                "severity_level_from_llm": severity,
                                "severity_justification_from_llm": justification 
                            })
                        else: 
                             parsed_feedback["section_feedback"].append({
                                "section_name": section_name,
                                "discrepancy_summary_from_llm": severity_and_justification_text,
                                "severity_level_from_llm": "Unknown",
                                "severity_justification_from_llm": "Severity not explicitly stated by AI."
                            })
                    elif "Generally consistent" in section_part: 
                        section_name_match_consistent = re.match(r"(.+?):\s*Generally consistent.*", section_part)
                        if section_name_match_consistent:
                            section_name = section_name_match_consistent.group(1).strip()
                            parsed_feedback["section_feedback"].append({
                                "section_name": section_name,
                                "discrepancy_summary_from_llm": section_part.replace(f"{section_name}:", "").strip(),
                                "severity_level_from_llm": "Consistent",
                                "severity_justification_from_llm": ""
                            })


            elif part.startswith("III. Key Learning Points & Actionable Advice:"):
                content = part.replace("III. Key Learning Points & Actionable Advice:", "").strip()
                for match in learning_point_pattern.finditer(content):
                    parsed_feedback["key_learning_points"].append({
                        "point": match.group(1).strip() if match.group(1) else "",
                        "advice": match.group(2).strip() if match.group(2) else "",
                        "topics_for_study": match.group(3).strip() if match.group(3) else ""
                    })
        
        if not parsed_feedback["overall_impression_alignment"] and not parsed_feedback["section_feedback"] and not parsed_feedback["key_learning_points"]:
            if feedback_text.strip(): 
                parsed_feedback["overall_impression_alignment"] = "Could not parse detailed structure. Full AI Feedback: \n" + feedback_text

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


class ReportCreateView(generics.CreateAPIView): 
    serializer_class = ReportSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_context(self):
        return {'request': self.request, **super().get_serializer_context()}

class MyReportsListView(generics.ListAPIView): 
    serializer_class = ReportSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Report.objects.filter(user=self.request.user).order_by('-submitted_at')
    
    def get_serializer_context(self):
        return {'request': self.request, **super().get_serializer_context()}
    
class AIFeedbackRatingCreateView(generics.CreateAPIView): 
    queryset = AIFeedbackRating.objects.all()
    serializer_class = AIFeedbackRatingSerializer
    permission_classes = [permissions.IsAuthenticated]