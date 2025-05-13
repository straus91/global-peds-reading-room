# cases/admin.py
from django.contrib import admin
from django.conf import settings # For AUTH_USER_MODEL if needed in user_link
from django.urls import reverse # Import reverse
from django.utils.html import format_html # Import format_html

from .models import (
    Case, Report, UserCaseView,
    Language, MasterTemplate, MasterTemplateSection,
    CaseTemplate, CaseTemplateSectionContent
)

@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'code')

# Inline admin for MasterTemplateSection to be used in MasterTemplateAdmin
class MasterTemplateSectionInline(admin.TabularInline): # or admin.StackedInline
    model = MasterTemplateSection
    extra = 1 # Number of empty forms to display
    ordering = ('order',) # Optional: if you want to enforce an order in the admin

@admin.register(MasterTemplate)
class MasterTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'modality', 'body_part', 'is_active', 'created_by', 'sections_count')
    list_filter = ('is_active', 'modality', 'body_part', 'created_by')
    search_fields = ('name', 'description', 'sections__name')
    inlines = [MasterTemplateSectionInline] # Add the inline here
    readonly_fields = ('created_at', 'updated_at') # Add these if not already present and desired

    def sections_count(self, obj):
        return obj.sections.count()
    sections_count.short_description = 'Sections'

    def save_model(self, request, obj, form, change): # Ensure created_by is set
        if not obj.pk: # if creating a new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(MasterTemplateSection)
class MasterTemplateSectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'master_template_link', 'order', 'is_required')
    list_filter = ('master_template__name', 'is_required') # Filter by master_template name
    search_fields = ('name', 'master_template__name')
    list_select_related = ('master_template',)

    def master_template_link(self, obj):
        # from django.urls import reverse # Moved to top-level imports
        # from django.utils.html import format_html # Moved to top-level imports
        if obj.master_template:
            link = reverse("admin:cases_mastertemplate_change", args=[obj.master_template.id])
            return format_html('<a href="{}">{}</a>', link, obj.master_template.name)
        return "-"
    master_template_link.short_description = 'Master Template'

# Inline admin for CaseTemplateSectionContent to be used in CaseTemplateAdmin
class CaseTemplateSectionContentInline(admin.TabularInline): # Or StackedInline
    model = CaseTemplateSectionContent
    extra = 0 # Don't add new ones by default if they are auto-created
    ordering = ('master_section__order',)
    fields = ('master_section', 'content')
    # readonly_fields = ('master_section',) # If master_section should not be changed here
    # Autocomplete fields can be useful if master_section list is long
    # autocomplete_fields = ['master_section']


@admin.register(CaseTemplate)
class CaseTemplateAdmin(admin.ModelAdmin):
    list_display = ('id', 'case_link', 'language', 'created_at', 'updated_at')
    list_filter = ('language__name', 'case__title') # Filter by language name and case title
    search_fields = ('case__title', 'language__name')
    list_select_related = ('case', 'language')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [CaseTemplateSectionContentInline] # Add the inline here

    def case_link(self, obj):
        # from django.urls import reverse # Moved to top-level imports
        # from django.utils.html import format_html # Moved to top-level imports
        if obj.case:
            link = reverse("admin:cases_case_change", args=[obj.case.id])
            return format_html('<a href="{}">{}</a>', link, obj.case.title)
        return "-"
    case_link.short_description = 'Case'

@admin.register(CaseTemplateSectionContent)
class CaseTemplateSectionContentAdmin(admin.ModelAdmin):
    list_display = ('id', 'case_template_link', 'master_section_name_admin', 'content_preview')
    list_filter = ('case_template__case__title', 'master_section__name')
    search_fields = ('content', 'master_section__name', 'case_template__case__title')
    list_select_related = ('case_template__case', 'case_template__language', 'master_section')
    readonly_fields = [] # Typically content is editable here

    def case_template_link(self, obj):
        # from django.urls import reverse # Moved to top-level imports
        # from django.utils.html import format_html # Moved to top-level imports
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
    list_display = ('id', 'title', 'subspecialty', 'modality', 'difficulty', 'status', 'created_by', 'created_at', 'published_at', 'master_template')
    list_filter = ('status', 'subspecialty', 'modality', 'difficulty', 'created_by', 'master_template__name') # Filter by master_template name
    search_fields = ('title', 'clinical_history', 'key_findings', 'diagnosis', 'discussion', 'created_by__username', 'created_by__email')
    readonly_fields = ('created_at', 'updated_at')
    list_per_page = 25
    autocomplete_fields = ['master_template', 'created_by'] # Makes selecting these easier if many exist

    def get_readonly_fields(self, request, obj=None):
        # Make 'published_at' readonly after it's set
        ro_fields = list(self.readonly_fields) # Make a mutable copy
        if obj and obj.published_at:
            if 'published_at' not in ro_fields:
                 ro_fields.append('published_at')
        return tuple(ro_fields)

    def save_model(self, request, obj, form, change): # Ensure created_by is set
        if not obj.pk and not obj.created_by: # if creating a new object and created_by is not set
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'case_link', 'user_link', 'submitted_at')
    list_filter = ('case__subspecialty', 'case__modality', 'user__username') # Filter by user username
    search_fields = ('user__username', 'user__email', 'case__title', 'findings', 'impression')
    readonly_fields = ('submitted_at', 'updated_at')
    list_per_page = 25
    list_select_related = ('case', 'user') # Optimize queries

    def case_link(self, obj):
        # from django.urls import reverse # Moved to top-level imports
        # from django.utils.html import format_html # Moved to top-level imports
        if obj.case:
            link = reverse("admin:cases_case_change", args=[obj.case.id])
            return format_html('<a href="{}">{}</a>', link, obj.case.title) # Use obj.case.title
        return "-"
    case_link.short_description = 'Case'

    def user_link(self, obj):
        # from django.urls import reverse # Moved to top-level imports
        # from django.utils.html import format_html # Moved to top-level imports
        if obj.user:
            # Construct admin URL for the user model dynamically
            user_model_meta = obj.user._meta
            try:
                link = reverse(f"admin:{user_model_meta.app_label}_{user_model_meta.model_name}_change", args=[obj.user.id])
            except: # Fallback for simpler user models or different registration
                link = reverse("admin:auth_user_change", args=[obj.user.id]) # Standard Django user
            return format_html('<a href="{}">{}</a>', link, obj.user.username)
        return "-"
    user_link.short_description = 'User'

@admin.register(UserCaseView)
class UserCaseViewAdmin(admin.ModelAdmin):
    # ***** CORRECTED HERE *****
    list_display = ('user', 'case', 'timestamp') # Changed 'viewed_at' to 'timestamp'
    # ***** END OF CORRECTION *****
    list_filter = ('user__username', 'case__title')
    search_fields = ('user__username', 'case__title')
    # ***** CORRECTED HERE *****
    readonly_fields = ('user', 'case', 'timestamp') # Changed 'viewed_at' to 'timestamp' and made all fields readonly as they are set on creation
    # ***** END OF CORRECTION *****
    list_per_page = 50
    list_select_related = ('user', 'case') # Optimize queries
