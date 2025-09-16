# backend/cases/admin.py
from django.contrib import admin
from django.conf import settings 
from django.urls import reverse 
from django.utils.html import format_html 
from django.db import models 

from .models import (
    Case, Report, UserCaseView,
    Language, MasterTemplate, MasterTemplateSection,
    CaseTemplate, CaseTemplateSectionContent,
    AIFeedbackRating # NEW: Import AIFeedbackRating
)

@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'code')

class MasterTemplateSectionInline(admin.TabularInline): 
    model = MasterTemplateSection
    extra = 1 
    ordering = ('order',) 

@admin.register(MasterTemplate)
class MasterTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'modality', 'body_part', 'is_active', 'created_by', 'sections_count')
    list_filter = ('is_active', 'modality', 'body_part', 'created_by')
    search_fields = ('name', 'description', 'sections__name')
    inlines = [MasterTemplateSectionInline] 
    readonly_fields = ('created_at', 'updated_at') 

    def sections_count(self, obj):
        return obj.sections.count()
    sections_count.short_description = 'Sections'

    def save_model(self, request, obj, form, change): 
        if not obj.pk: 
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(MasterTemplateSection)
class MasterTemplateSectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'master_template_link', 'order', 'is_required')
    list_filter = ('master_template__name', 'is_required') 
    search_fields = ('name', 'master_template__name')
    list_select_related = ('master_template',)

    def master_template_link(self, obj):
        if obj.master_template:
            link = reverse("admin:cases_mastertemplate_change", args=[obj.master_template.id])
            return format_html('<a href="{}">{}</a>', link, obj.master_template.name)
        return "-"
    master_template_link.short_description = 'Master Template'

class CaseTemplateSectionContentInline(admin.TabularInline): 
    model = CaseTemplateSectionContent
    extra = 0 
    ordering = ('master_section__order',)
    # UPDATED: Add key_concepts_text to the inline form
    fields = ('master_section', 'content', 'key_concepts_text') 
    # readonly_fields = ('master_section',) 
    # autocomplete_fields = ['master_section']
    # Add a simple textarea widget for key_concepts_text if needed, or rely on default
    formfield_overrides = {
        models.TextField: {'widget': admin.widgets.AdminTextareaWidget(attrs={'rows': 2, 'cols': 40})},
    }


@admin.register(CaseTemplate)
class CaseTemplateAdmin(admin.ModelAdmin):
    list_display = ('id', 'case_link', 'language', 'created_at', 'updated_at')
    list_filter = ('language__name', 'case__title', 'case__case_identifier') 
    search_fields = ('case__title', 'case__case_identifier', 'language__name')
    list_select_related = ('case', 'language')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [CaseTemplateSectionContentInline] 

    def case_link(self, obj):
        if obj.case:
            link = reverse("admin:cases_case_change", args=[obj.case.id])
            # Display case_identifier if available, otherwise title
            display_name = obj.case.case_identifier if obj.case.case_identifier else obj.case.title
            return format_html('<a href="{}">{}</a>', link, display_name)
        return "-"
    case_link.short_description = 'Case'

@admin.register(CaseTemplateSectionContent)
class CaseTemplateSectionContentAdmin(admin.ModelAdmin):
    # UPDATED: Add key_concepts_text to list_display and search_fields
    list_display = ('id', 'case_template_link', 'master_section_name_admin', 'content_preview', 'key_concepts_text_preview')
    list_filter = ('case_template__case__title', 'case_template__case__case_identifier', 'master_section__name')
    search_fields = ('content', 'master_section__name', 'case_template__case__title', 'case_template__case__case_identifier', 'key_concepts_text')
    list_select_related = ('case_template__case', 'case_template__language', 'master_section')
    
    def key_concepts_text_preview(self, obj):
        if obj.key_concepts_text:
            return (obj.key_concepts_text[:75] + '...') if len(obj.key_concepts_text) > 75 else obj.key_concepts_text
        return "-"
    key_concepts_text_preview.short_description = 'Key Concepts'


    def case_template_link(self, obj):
        if obj.case_template:
            link = reverse("admin:cases_casetemplate_change", args=[obj.case_template.id])
            return format_html('<a href="{}">{}</a>', link, str(obj.case_template))
        return "-"
    case_template_link.short_description = 'Case Template'

    def master_section_name_admin(self, obj):
        if obj.master_section:
            return obj.master_section.name
        return "-"
    master_section_name_admin.short_description = 'Master Section'

    def content_preview(self, obj):
        return (obj.content[:75] + '...') if len(obj.content) > 75 else obj.content
    content_preview.short_description = 'Content Preview'


@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    # UPDATED: Added case_identifier and patient_sex to list_display and relevant filters/search
    list_display = (
        'id', 'case_identifier', 'title', 'patient_sex', 'subspecialty', 
        'modality', 'difficulty', 'status', 'created_by', 
        'created_at', 'published_at', 'master_template'
    )
    list_filter = (
        'status', 'subspecialty', 'modality', 'difficulty', 
        'created_by', 'master_template__name', 'patient_sex' # Added patient_sex
    )
    search_fields = (
        'title', 'case_identifier', 'clinical_history', 'key_findings', # Added case_identifier
        'diagnosis', 'discussion', 'created_by__username', 'created_by__email'
    )
    # UPDATED: Made case_identifier read-only as it's auto-generated
    readonly_fields = ('created_at', 'updated_at', 'case_identifier') 
    list_per_page = 25
    autocomplete_fields = ['master_template', 'created_by'] 

    # To control field order in the admin detail form, you might use fieldsets
    fieldsets = (
        (None, {
            'fields': ('case_identifier', 'title', 'status', 'published_at')
        }),
        ('Patient & Clinical Info', {
            'fields': ('patient_age', 'patient_sex', 'clinical_history')
        }),
        ('Case Classification', {
            'fields': ('subspecialty', 'modality', 'difficulty', 'master_template')
        }),
        ('Expert Content (for this specific case)', {
            'fields': ('key_findings', 'diagnosis', 'discussion', 'references')
        }),
        ('DICOM & Tracking', {
            'fields': ('orthanc_study_uid', 'created_by', 'created_at', 'updated_at')
        }),
    )


    def get_readonly_fields(self, request, obj=None):
        # Make 'published_at' readonly after it's set
        # Keep case_identifier always readonly
        ro_fields = list(super().get_readonly_fields(request, obj))
        if 'case_identifier' not in ro_fields:
            ro_fields.append('case_identifier')
        if obj and obj.published_at:
            if 'published_at' not in ro_fields:
                 ro_fields.append('published_at')
        return tuple(ro_fields)

    def save_model(self, request, obj, form, change): 
        if not obj.pk and not obj.created_by: 
            obj.created_by = request.user
        # case_identifier is auto-generated by the model's save() method
        super().save_model(request, obj, form, change)

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'case_link', 'user_link', 'submitted_at')
    list_filter = ('case__subspecialty', 'case__modality', 'user__username', 'case__case_identifier') 
    search_fields = ('user__username', 'user__email', 'case__title', 'case__case_identifier', 'structured_content') # was findings, impression
    readonly_fields = ('submitted_at', 'updated_at')
    list_per_page = 25
    list_select_related = ('case', 'user') 

    def case_link(self, obj):
        if obj.case:
            link = reverse("admin:cases_case_change", args=[obj.case.id])
            display_name = obj.case.case_identifier if obj.case.case_identifier else obj.case.title
            return format_html('<a href="{}">{}</a>', link, display_name)
        return "-"
    case_link.short_description = 'Case'

    def user_link(self, obj):
        if obj.user:
            user_model_meta = obj.user._meta
            try:
                link = reverse(f"admin:{user_model_meta.app_label}_{user_model_meta.model_name}_change", args=[obj.user.id])
            except: 
                link = reverse("admin:auth_user_change", args=[obj.user.id]) 
            return format_html('<a href="{}">{}</a>', link, obj.user.username)
        return "-"
    user_link.short_description = 'User'

@admin.register(UserCaseView)
class UserCaseViewAdmin(admin.ModelAdmin):
    list_display = ('user', 'case_link_ucv', 'timestamp') # Renamed case to case_link_ucv
    list_filter = ('user__username', 'case__title', 'case__case_identifier')
    search_fields = ('user__username', 'case__title', 'case__case_identifier')
    readonly_fields = ('user', 'case', 'timestamp') 
    list_per_page = 50
    list_select_related = ('user', 'case')

    def case_link_ucv(self, obj): # New method to avoid conflict
        if obj.case:
            link = reverse("admin:cases_case_change", args=[obj.case.id])
            display_name = obj.case.case_identifier if obj.case.case_identifier else obj.case.title
            return format_html('<a href="{}">{}</a>', link, display_name)
        return "-"
    case_link_ucv.short_description = 'Case'
    case_link_ucv.admin_order_field = 'case' # Allows sorting by case

# NEW: Register AIFeedbackRating model
@admin.register(AIFeedbackRating)
class AIFeedbackRatingAdmin(admin.ModelAdmin):
    list_display = ('report_link', 'user', 'star_rating', 'comment_preview', 'rated_at')
    list_filter = ('star_rating', 'user__username', 'report__case__case_identifier')
    search_fields = ('user__username', 'report__case__case_identifier', 'comment')
    readonly_fields = ('report', 'user', 'star_rating', 'comment', 'rated_at') # Usually all read-only
    list_select_related = ('report__case', 'user')

    def report_link(self, obj):
        if obj.report and obj.report.case:
            # Link to the Report admin page, or directly to the Case if more useful
            link = reverse("admin:cases_report_change", args=[obj.report.id])
            display_name = f"Report ID {obj.report.id} (Case: {obj.report.case.case_identifier if obj.report.case.case_identifier else obj.report.case.id})"
            return format_html('<a href="{}">{}</a>', link, display_name)
        return "N/A"
    report_link.short_description = 'Rated Report'

    def comment_preview(self, obj):
        if obj.comment:
            return (obj.comment[:75] + '...') if len(obj.comment) > 75 else obj.comment
        return "-"
    comment_preview.short_description = 'Comment'

    def has_add_permission(self, request): # Users add ratings via API, not admin
        return False

    def has_change_permission(self, request, obj=None): # Ratings are immutable via admin
        return False

    # has_delete_permission can be True if admins should be able to delete ratings
