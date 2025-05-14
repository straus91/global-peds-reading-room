# cases/views.py
from rest_framework import viewsets, permissions, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import transaction

# Updated model imports
from .models import (
    Case, Report, Language, UserCaseView, CaseStatusChoices,
    MasterTemplate, MasterTemplateSection,
    CaseTemplate, CaseTemplateSectionContent
)
# Updated serializer imports
from .serializers import (
    CaseSerializer, CaseListSerializer, AdminCaseListSerializer, ReportSerializer, LanguageSerializer,
    MasterTemplateSerializer,
    CaseTemplateSerializer, 
    AdminCaseTemplateSetupSerializer, 
    BulkCaseTemplateSectionContentUpdateSerializer 
)

from .llm_feedback_service import get_feedback_from_llm 

# --- ViewSets ---

class LanguageViewSet(viewsets.ModelViewSet): # Inherits from ModelViewSet (which has get_serializer_context)
    """
    API endpoint for managing languages.
    Admins can CRUD, authenticated users can read.
    """
    queryset = Language.objects.filter(is_active=True)
    serializer_class = LanguageSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            self.permission_classes = [permissions.IsAuthenticated]
        else:
            self.permission_classes = [permissions.IsAdminUser]
        return super().get_permissions()

class AdminMasterTemplateViewSet(viewsets.ModelViewSet): # Inherits from ModelViewSet
    """
    API endpoint for Administrators to manage Master Templates globally.
    """
    queryset = MasterTemplate.objects.prefetch_related('sections').all().order_by('name')
    serializer_class = MasterTemplateSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_serializer_context(self):
        return {'request': self.request, **super().get_serializer_context()}

class AdminCaseViewSet(viewsets.ModelViewSet): # Your existing AdminCaseViewSet
    queryset = Case.objects.all().order_by('-created_at')
    permission_classes = [permissions.IsAdminUser]

    def get_serializer_class(self):
        if self.action == 'list':
            # return CaseListSerializer # As per your uploaded file
            return AdminCaseListSerializer # It's better to use the more specific one for admins
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

    # Actions for managing CaseTemplate instances (case-specific templates)
    # Assuming your frontend calls /expert-templates/ which maps to this via urls.py
    @action(detail=True, methods=['get', 'post'], url_path='expert-templates', permission_classes=[permissions.IsAdminUser])
    def manage_expert_templates(self, request, pk=None): # pk is case_pk. Changed name for clarity.
        case = self.get_object()
        if request.method == 'GET':
            case_templates = CaseTemplate.objects.filter(case=case).order_by('language__name')
            serializer = CaseTemplateSerializer(case_templates, many=True, context=self.get_serializer_context())
            return Response(serializer.data)
        
        elif request.method == 'POST':
            # ***** THIS IS THE KEY CHANGE *****
            # Use AdminCaseTemplateSetupSerializer for creation/setup.
            # It expects 'language' (ID) in request.data and 'case' in context.
            setup_serializer = AdminCaseTemplateSetupSerializer( # Changed variable name
                data=request.data, 
                context={'request': request, 'case': case} # Pass case to serializer context
            )
            if setup_serializer.is_valid(raise_exception=True): # Use raise_exception for clearer errors
                # The AdminCaseTemplateSetupSerializer's create method handles creating 
                # CaseTemplate and its CaseTemplateSectionContent.
                # Its to_representation method then uses CaseTemplateSerializer.
                case_template_instance = setup_serializer.save() 
                return Response(setup_serializer.data, status=status.HTTP_201_CREATED)
            # No need for explicit "return Response(setup_serializer.errors, status=status.HTTP_400_BAD_REQUEST)"
            # if raise_exception=True is used, as it will automatically do that.
            # However, keeping it doesn't hurt if you remove raise_exception.
            return Response(setup_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    @action(detail=True, methods=['delete'], url_path='expert-templates/(?P<case_template_pk>[^/.]+)', permission_classes=[permissions.IsAdminUser])
    def delete_expert_template(self, request, pk=None, case_template_pk=None): # pk is case_pk. Changed name for clarity.
        case = self.get_object()
        case_template = get_object_or_404(CaseTemplate, pk=case_template_pk, case=case)
        case_template.delete()
        return Response({"detail": "Expert template deleted successfully."}, status=status.HTTP_204_NO_CONTENT)




class AIReportFeedbackView(APIView):
    permission_classes = [permissions.IsAuthenticated] # Only authenticated users can request feedback

    def get(self, request, report_id, format=None):
        try:
            # Ensure the report belongs to the requesting user for security/privacy
            user_report = Report.objects.get(pk=report_id, user=request.user)
        except Report.DoesNotExist:
            return Response(
                {"error": "Report not found or you do not have permission to access it."},
                status=status.HTTP_404_NOT_FOUND
            )

        case_instance = user_report.case # Get the associated case from the report
        if not case_instance.master_template:
            return Response(
                {"error": "This case does not have an associated master template. AI feedback cannot be generated without a structure."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Fetch the user's report structured content (already enriched by ReportSerializer)
        # We need the request in the context for serializers that might use it (e.g., for user-specific fields)
        serializer_context = {'request': request}
        user_report_data = ReportSerializer(user_report, context=serializer_context).data
        user_report_sections = user_report_data.get('structured_content', [])

        if not user_report_sections:
            return Response(
                {"error": "User's report content is missing or empty. Cannot generate feedback."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Fetch the expert report. For MVP, we'll try to find an English ('en') version.
        # This logic might need to be more sophisticated later (e.g., user selects which expert version, or a default is set).
        expert_template_instance = CaseTemplate.objects.filter(case=case_instance, language__code='en').first()

        if not expert_template_instance:
            # If no English version, try to get ANY expert template for this case.
            expert_template_instance = CaseTemplate.objects.filter(case=case_instance).first()
            if not expert_template_instance:
                return Response(
                    {"error": "No expert template (e.g., English version) found for this case. AI feedback cannot be generated."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            else:
                print(f"Warning: English expert template not found for case {case_instance.id}. Using expert template in language: {expert_template_instance.language.code}")

        # CaseTemplateSerializer also provides enriched section_contents
        expert_report_data = CaseTemplateSerializer(expert_template_instance, context=serializer_context).data
        expert_report_sections = expert_report_data.get('section_contents', [])

        if not expert_report_sections:
             return Response(
                {"error": "Expert report content is missing or empty. Cannot generate feedback."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Call your LLM service function
        ai_feedback_text = get_feedback_from_llm(
            user_report_sections=user_report_sections,
            expert_report_sections=expert_report_sections,
            case_title=case_instance.title
        )

        # In a more advanced version, you might want to save this feedback to the database
        # linked to the user_report. For MVP, just returning it is fine.
        # Example: user_report.ai_feedback = ai_feedback_text; user_report.save()

        return Response(
            {"report_id": user_report.id, "feedback": ai_feedback_text},
            status=status.HTTP_200_OK
        )

class CaseTemplateViewSet(viewsets.ViewSet): 
    permission_classes = [permissions.IsAdminUser]
    serializer_class = CaseTemplateSerializer 

    def get_queryset(self): 
        return CaseTemplate.objects.all()

    def get_serializer_context(self):
        return {'request': self.request}

    @action(detail=True, methods=['put'], url_path='update-sections')
    def update_sections_content(self, request, pk=None): 
        case_template = get_object_or_404(CaseTemplate, pk=pk)
        existing_sections_qs = case_template.section_contents.all() 
        instance_map = {section.id: section for section in existing_sections_qs}
        
        context = self.get_serializer_context()
        context['instance_map'] = instance_map 

        print(f"--- update_sections_content for CaseTemplate PK: {pk} ---")
        print(f"Request Method: {request.method}")
        print(f"Request Content-Type: {request.content_type}")
        print(f"Type of request.data: {type(request.data)}")
        print(f"Content of request.data: {request.data}")

        serializer = BulkCaseTemplateSectionContentUpdateSerializer(
            instance=existing_sections_qs, 
            data=request.data, 
            # many=True, # This should be absent
            partial=True, 
            context=context 
        )
        
        if serializer.is_valid(raise_exception=True): 
            updated_sections = serializer.save() 
            
            full_case_template_serializer = CaseTemplateSerializer(case_template, context=self.get_serializer_context())
            return Response(full_case_template_serializer.data)
        
    def retrieve(self, request, pk=None):
        case_template = get_object_or_404(CaseTemplate, pk=pk)
        serializer = CaseTemplateSerializer(case_template, context=self.get_serializer_context())
        return Response(serializer.data)
class UserCaseViewSet(viewsets.ReadOnlyModelViewSet): # Inherits from ReadOnlyModelViewSet
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
    def get_expert_template_by_language(self, request, pk=None, language_code=None): # pk is case_pk
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


class ReportCreateView(generics.CreateAPIView): # Inherits from CreateAPIView
    serializer_class = ReportSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_context(self):
        return {'request': self.request, **super().get_serializer_context()} # super() is fine here

class MyReportsListView(generics.ListAPIView): # Inherits from ListAPIView
    serializer_class = ReportSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Report.objects.filter(user=self.request.user).order_by('-submitted_at')
    
    def get_serializer_context(self):
        return {'request': self.request, **super().get_serializer_context()} # super() is fine here
    
