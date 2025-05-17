# backend/cases/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db import models, transaction 
from .models import (
    Case, Report, UserCaseView, Language, CaseStatusChoices,
    SubspecialtyChoices, ModalityChoices, DifficultyChoices, PatientSexChoices, # <<< *** ADDED PatientSexChoices HERE ***
    MasterTemplate, MasterTemplateSection,
    CaseTemplate, CaseTemplateSectionContent,
    AIFeedbackRating # Make sure AIFeedbackRating is imported if used below
)

# Attempt to import UserSerializer, but provide a fallback if it's not there
try:
    from users.serializers import UserSerializer # Your project's UserSerializer
except ImportError:
    print("WARNING: users.serializers.UserSerializer not found. Using SimpleUserSerializer as a fallback.")
    User = get_user_model()
    class UserSerializer(serializers.ModelSerializer): # Fallback SimpleUserSerializer
        class Meta:
            model = User
            fields = ['id', 'username', 'email'] # Basic fields

# --- Serializers for Master Templates ---
class MasterTemplateSectionSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False, allow_null=True)

    class Meta:
        model = MasterTemplateSection
        fields = ['id', 'name', 'placeholder_text', 'order', 'is_required']
        extra_kwargs = {
            'name': {'help_text': "Name of the section (e.g., 'Findings')"},
            'placeholder_text': {'help_text': "Default placeholder/instructions for this section", 'required': False, 'allow_blank': True},
            'order': {'help_text': "Order of appearance"},
            'is_required': {'help_text': "Is this section mandatory?"},
        }

class MasterTemplateSerializer(serializers.ModelSerializer):
    sections = MasterTemplateSectionSerializer(many=True)
    modality_display = serializers.CharField(source='get_modality_display', read_only=True, required=False)
    body_part_display = serializers.CharField(source='get_body_part_display', read_only=True, required=False)
    created_by = UserSerializer(read_only=True, required=False)

    class Meta:
        model = MasterTemplate
        fields = [
            'id', 'name', 'modality', 'body_part', 'description',
            'is_active', 'created_by', 'sections',
            'modality_display', 'body_part_display',
        ]
        read_only_fields = ['created_by']

    def create(self, validated_data):
        sections_data = validated_data.pop('sections', [])
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            validated_data['created_by'] = request.user
        master_template = MasterTemplate.objects.create(**validated_data)
        for section_data in sections_data:
            MasterTemplateSection.objects.create(master_template=master_template, **section_data)
        return master_template

    @transaction.atomic
    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.modality = validated_data.get('modality', instance.modality)
        instance.body_part = validated_data.get('body_part', instance.body_part)
        instance.description = validated_data.get('description', instance.description)
        instance.is_active = validated_data.get('is_active', instance.is_active)
        instance.save()

        sections_data = validated_data.pop('sections', [])
        incoming_section_ids = []

        for section_data in sections_data:
            section_id = section_data.get('id', None)
            if section_id:
                try:
                    section_instance = MasterTemplateSection.objects.get(id=section_id, master_template=instance)
                    for attr, value in section_data.items():
                        if attr != 'id':
                            setattr(section_instance, attr, value)
                    section_instance.save()
                    incoming_section_ids.append(section_instance.id)
                except MasterTemplateSection.DoesNotExist:
                    if 'id' in section_data: del section_data['id']
                    new_section = MasterTemplateSection.objects.create(master_template=instance, **section_data)
                    incoming_section_ids.append(new_section.id)
            else:
                if 'id' in section_data: del section_data['id']
                new_section = MasterTemplateSection.objects.create(master_template=instance, **section_data)
                incoming_section_ids.append(new_section.id)

        for section in instance.sections.all():
            if section.id not in incoming_section_ids:
                section.delete()
        return instance

# --- Serializers for Case-Specific Template Application (Expert Filled Templates) ---

class CaseTemplateSectionContentSerializer(serializers.ModelSerializer):
    """
    Serializer for reading CaseTemplateSectionContent, including the new key_concepts_text.
    """
    master_section_id = serializers.IntegerField(source='master_section.id', read_only=True)
    master_section_name = serializers.CharField(source='master_section.name', read_only=True)
    master_section_placeholder = serializers.CharField(source='master_section.placeholder_text', read_only=True, allow_null=True)
    master_section_order = serializers.IntegerField(source='master_section.order', read_only=True)
    master_section_is_required = serializers.BooleanField(source='master_section.is_required', read_only=True)
    key_concepts_text = serializers.CharField(required=False, allow_blank=True, allow_null=True)


    class Meta:
        model = CaseTemplateSectionContent
        fields = [
            'id', 'master_section_id',
            'master_section_name', 'master_section_placeholder',
            'master_section_order', 'master_section_is_required',
            'content', 
            'key_concepts_text' 
        ]

class CaseTemplateSerializer(serializers.ModelSerializer):
    language_code = serializers.CharField(source='language.code', read_only=True)
    language_name = serializers.CharField(source='language.name', read_only=True)
    section_contents = CaseTemplateSectionContentSerializer(many=True, read_only=True, source='section_contents_ordered')

    class Meta:
        model = CaseTemplate
        fields = [
            'id', 'case', 'language', 'language_code', 'language_name',
            'section_contents', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'case', 'created_at', 'updated_at']


class AdminCaseTemplateSetupSerializer(serializers.Serializer):
    language = serializers.PrimaryKeyRelatedField(
        queryset=Language.objects.filter(is_active=True),
        help_text="ID of the language for this expert template."
    )

    def create(self, validated_data):
        case_instance = self.context.get('case')
        if not case_instance:
            if 'view' in self.context and hasattr(self.context['view'], 'get_object'):
                case_instance = self.context['view'].get_object()
            else:
                raise serializers.ValidationError("Case instance not found in serializer context.")

        language_instance = validated_data['language']

        if not case_instance.master_template:
            raise serializers.ValidationError({
                "detail": f"Case '{case_instance.title}' (ID: {case_instance.id}) does not have a MasterTemplate associated. Cannot setup an expert template."
            })

        case_template, created = CaseTemplate.objects.get_or_create(
            case=case_instance,
            language=language_instance
        )

        if created or not case_template.section_contents.exists():
            if not created:
                 case_template.section_contents.all().delete()

            master_sections = case_instance.master_template.sections.all().order_by('order')
            if not master_sections.exists():
                pass

            for ms_loop_var in master_sections:
                CaseTemplateSectionContent.objects.create(
                    case_template=case_template,
                    master_section=ms_loop_var,
                    content=ms_loop_var.placeholder_text or "",
                    key_concepts_text=None 
                )
        return case_template

    def to_representation(self, instance):
        return CaseTemplateSerializer(instance, context=self.context).data

class CaseTemplateSectionContentUpdateSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    key_concepts_text = serializers.CharField(required=False, allow_blank=True, allow_null=True, trim_whitespace=True)


    class Meta:
        model = CaseTemplateSectionContent
        fields = ['id', 'content', 'key_concepts_text'] 


class BulkCaseTemplateSectionContentUpdateSerializer(serializers.ListSerializer):
    child = CaseTemplateSectionContentUpdateSerializer()

    def update(self, instance_list_or_queryset, validated_data_list):
        instance_map = self.context.get('instance_map')
        if not instance_map:
            print("WARNING: instance_map not found in context for BulkCaseTemplateSectionContentUpdateSerializer, building from instance_list_or_queryset.")
            if instance_list_or_queryset and isinstance(instance_list_or_queryset, (models.QuerySet, list)):
                 instance_map = {instance.id: instance for instance in instance_list_or_queryset}
            else:
                raise serializers.ValidationError("Cannot perform bulk update without instances or instance_map.")

        updated_instances = []
        errors = []
        
        for data_item in validated_data_list:
            section_content_id = data_item.get('id')
            
            if section_content_id is None:
                errors.append(f"Missing 'id' in one of the data items: {data_item}")
                continue

            instance_to_update = instance_map.get(section_content_id)
            if not instance_to_update:
                errors.append(f"CaseTemplateSectionContent with ID {section_content_id} not found for this CaseTemplate.")
                continue

            current_update_fields = []
            
            if 'content' in data_item:
                new_content = data_item.get('content')
                if instance_to_update.content != new_content:
                    instance_to_update.content = new_content
                    current_update_fields.append('content')
            
            if 'key_concepts_text' in data_item:
                new_key_concepts = data_item.get('key_concepts_text')
                if instance_to_update.key_concepts_text != new_key_concepts:
                    instance_to_update.key_concepts_text = new_key_concepts
                    current_update_fields.append('key_concepts_text')

            if current_update_fields: 
                instance_to_update.save(update_fields=current_update_fields)
            
            updated_instances.append(instance_to_update)

        if errors:
            raise serializers.ValidationError(errors)
        return updated_instances

# --- Core App Serializers (Report, Language, Case) ---

class ReportSectionDetailSerializer(serializers.Serializer):
    master_template_section_id = serializers.IntegerField(
        help_text="The ID of the MasterTemplateSection this content corresponds to."
    )
    content = serializers.CharField(
        allow_blank=True, 
        trim_whitespace=False, 
        help_text="The user-entered content for this section."
    )

    def validate_master_template_section_id(self, value):
        if not MasterTemplateSection.objects.filter(id=value).exists():
            raise serializers.ValidationError(f"MasterTemplateSection with id {value} does not exist.")
        return value

class ReportSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True) 
    case_id = serializers.PrimaryKeyRelatedField(
        queryset=Case.objects.all(),
        source='case', 
        write_only=True,
        help_text="The ID of the case this report is for."
    )
    case_title = serializers.CharField(source='case.title', read_only=True) 
    case_identifier_display = serializers.CharField(source='case.case_identifier', read_only=True, allow_null=True)


    section_details = ReportSectionDetailSerializer(
        many=True,
        write_only=True, 
        help_text="Array of section contents, each with 'master_template_section_id' and 'content'."
    )
    structured_content = serializers.JSONField(read_only=True)

    class Meta:
        model = Report
        fields = [
            'id',
            'case',             
            'case_id',          
            'case_title',       
            'case_identifier_display', 
            'user',             
            'section_details',  
            'structured_content', 
            'submitted_at',
            'updated_at',
        ]
        read_only_fields = ('id', 'user', 'case', 'case_title', 'case_identifier_display', 'structured_content', 'submitted_at', 'updated_at')

    def create(self, validated_data):
        user = self.context['request'].user
        case_instance = validated_data.pop('case') 
        section_details_data = validated_data.pop('section_details', []) 

        if section_details_data and not case_instance.master_template:
            raise serializers.ValidationError(
                "Cannot submit section details for a case that has no master template associated."
            )
        
        report = Report.objects.create(
            user=user,
            case=case_instance,
            structured_content=section_details_data, 
            **validated_data 
        )
        return report

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        
        structured_content_enriched = []
        if instance.structured_content and isinstance(instance.structured_content, list):
            section_ids = [item.get('master_template_section_id') for item in instance.structured_content if item.get('master_template_section_id') is not None]
            master_sections = MasterTemplateSection.objects.filter(id__in=section_ids).in_bulk() 

            for item_data in instance.structured_content:
                section_id = item_data.get('master_template_section_id')
                master_section_obj = master_sections.get(section_id)
                enriched_item = item_data.copy() 
                if master_section_obj:
                    enriched_item['section_name'] = master_section_obj.name
                    enriched_item['section_order'] = master_section_obj.order
                else:
                    enriched_item['section_name'] = "Unknown/Orphaned Section"
                structured_content_enriched.append(enriched_item)
            
            representation['structured_content'] = sorted(structured_content_enriched, key=lambda x: x.get('section_order', float('inf')))
        else:
            representation['structured_content'] = instance.structured_content 

        return representation


class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = ['id', 'code', 'name', 'is_active']


class CaseSerializer(serializers.ModelSerializer):
    subspecialty_display = serializers.CharField(source='get_subspecialty_display', read_only=True)
    modality_display = serializers.CharField(source='get_modality_display', read_only=True)
    difficulty_display = serializers.CharField(source='get_difficulty_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    patient_sex_display = serializers.CharField(source='get_patient_sex_display', read_only=True, allow_null=True)


    subspecialty = serializers.ChoiceField(choices=SubspecialtyChoices.choices)
    modality = serializers.ChoiceField(choices=ModalityChoices.choices)
    difficulty = serializers.ChoiceField(choices=DifficultyChoices.choices, required=False)
    status = serializers.ChoiceField(choices=CaseStatusChoices.choices, required=False)
    patient_sex = serializers.ChoiceField(choices=PatientSexChoices.choices, allow_blank=True, allow_null=True, required=False)


    created_by = UserSerializer(read_only=True, required=False)
    is_viewed_by_user = serializers.SerializerMethodField()
    is_reported_by_user = serializers.SerializerMethodField()

    applied_templates = CaseTemplateSerializer(many=True, read_only=True, source='applied_expert_templates')

    master_template = serializers.PrimaryKeyRelatedField(
        queryset=MasterTemplate.objects.filter(is_active=True),
        allow_null=True,
        required=False,
        help_text="ID of the MasterTemplate to associate with this case.",
    )
    master_template_details = MasterTemplateSerializer(source='master_template', read_only=True)

    class Meta:
        model = Case
        fields = [
            'id', 'title', 'case_identifier', 
            'subspecialty', 'modality', 'difficulty', 'status',
            'patient_age', 'patient_sex', 
            'clinical_history',
            'key_findings', 'diagnosis', 'discussion', 'references',
            'created_by', 'created_at', 'updated_at', 'published_at',
            'subspecialty_display', 'modality_display', 'difficulty_display', 'status_display', 'patient_sex_display', 
            'is_viewed_by_user', 'is_reported_by_user',
            'master_template', 'master_template_details',
            'applied_templates',
            'orthanc_study_uid'  
        ]
        read_only_fields = ('id', 'created_by', 'created_at', 'updated_at', 'published_at', 'applied_templates', 'master_template_details', 'case_identifier') 

    def get_is_viewed_by_user(self, obj):
        request = self.context.get('request')
        if not request or not hasattr(request, 'user') or not request.user.is_authenticated:
            return False
        return UserCaseView.objects.filter(user=request.user, case=obj).exists()

    def get_is_reported_by_user(self, obj):
        request = self.context.get('request')
        if not request or not hasattr(request, 'user') or not request.user.is_authenticated:
            return False
        return Report.objects.filter(user=request.user, case=obj).exists()

    @transaction.atomic
    def create(self, validated_data):
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            validated_data['created_by'] = request.user
        case = super().create(validated_data)
        return case

    @transaction.atomic
    def update(self, instance, validated_data):
        validated_data.pop('case_identifier', None) 
        return super().update(instance, validated_data)
    
class CaseListSerializer(serializers.ModelSerializer):
    subspecialty = serializers.CharField(source='get_subspecialty_display', read_only=True)
    modality = serializers.CharField(source='get_modality_display', read_only=True)
    difficulty = serializers.CharField(source='get_difficulty_display', read_only=True)
    status = serializers.CharField(source='get_status_display', read_only=True)
    is_viewed_by_user = serializers.SerializerMethodField()
    is_reported_by_user = serializers.SerializerMethodField()
    has_master_template = serializers.SerializerMethodField()
    case_identifier = serializers.CharField(read_only=True) 

    class Meta:
        model = Case
        fields = [
            'id', 'title', 'case_identifier', 
            'subspecialty', 'modality', 'difficulty', 'status',
            'created_at', 'published_at',
            'is_viewed_by_user', 'is_reported_by_user', 'has_master_template',
        ]

    def get_is_viewed_by_user(self, obj):
        request = self.context.get('request')
        if not request or not hasattr(request, 'user') or not request.user.is_authenticated: return False
        return UserCaseView.objects.filter(user=request.user, case=obj).exists()

    def get_is_reported_by_user(self, obj):
        request = self.context.get('request')
        if not request or not hasattr(request, 'user') or not request.user.is_authenticated: return False
        return Report.objects.filter(user=request.user, case=obj).exists()

    def get_has_master_template(self, obj):
        return obj.master_template is not None

class AdminCaseListSerializer(CaseListSerializer):
    created_by_username = serializers.CharField(source='created_by.username', read_only=True, allow_null=True)

    class Meta(CaseListSerializer.Meta): 
        fields = CaseListSerializer.Meta.fields + ['created_by_username']


class AIFeedbackRatingSerializer(serializers.ModelSerializer): # Corrected indentation
    user = UserSerializer(read_only=True, default=serializers.CurrentUserDefault())
    report_id = serializers.IntegerField(write_only=True, help_text="ID of the report for which AI feedback is being rated.")

    class Meta:
        model = AIFeedbackRating # Corrected: This should be AIFeedbackRating
        fields = ['id', 'report', 'report_id', 'user', 'star_rating', 'comment', 'rated_at']
        read_only_fields = ('id', 'user', 'report', 'rated_at') 

    def validate_report_id(self, value):
        request = self.context.get('request')
        try:
            report = Report.objects.get(pk=value)
        except Report.DoesNotExist:
            raise serializers.ValidationError("Report not found.")
        return value

    def create(self, validated_data):
        report_id = validated_data.pop('report_id')
        report_instance = Report.objects.get(pk=report_id)
        
        if AIFeedbackRating.objects.filter(report=report_instance, user=self.context['request'].user).exists():
            raise serializers.ValidationError({"detail": "You have already rated the AI feedback for this report."})

        rating = AIFeedbackRating.objects.create(
            report=report_instance, 
            user=self.context['request'].user, 
            **validated_data
        )
        return rating
