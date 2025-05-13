# backend/cases/models.py
from django.db import models
from django.conf import settings # To get the User model
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

# --- Choices (can be at the top) ---

class ModalityChoices(models.TextChoices):
    CT = 'CT', _('Computer Tomography')
    MR = 'MR', _('Magnetic Resonance')
    US = 'US', _('Ultrasound')
    XR = 'XR', _('X-ray')
    FL = 'FL', _('Fluoroscopy')
    NM = 'NM', _('Nuclear Medicine')
    OT = 'OT', _('Other')

class SubspecialtyChoices(models.TextChoices):
    BR = 'BR', _('Breast (Imaging and Interventional)')
    CA = 'CA', _('Cardiac Radiology')
    CH = 'CH', _('Chest Radiology')
    ER = 'ER', _('Emergency Radiology')
    GI = 'GI', _('Gastrointestinal Radiology')
    GU = 'GU', _('Genitourinary Radiology')
    HN = 'HN', _('Head and Neck')
    IR = 'IR', _('Interventional Radiology')
    MK = 'MK', _('Musculoskeletal Radiology')
    NM = 'NM', _('Nuclear Medicine') # As a subspecialty
    NR = 'NR', _('Neuroradiology')
    OB = 'OB', _('Obstetric/Gynecologic Radiology')
    OI = 'OI', _('Oncologic Imaging')
    VA = 'VA', _('Vascular Radiology')
    PD = 'PD', _('Pediatric Radiology')
    OT = 'OT', _('Other')

class DifficultyChoices(models.TextChoices):
    BEGINNER = 'beginner', _('Beginner')
    INTERMEDIATE = 'intermediate', _('Intermediate')
    ADVANCED = 'advanced', _('Advanced')
    EXPERT = 'expert', _('Expert')

class CaseStatusChoices(models.TextChoices):
    DRAFT = 'draft', _('Draft')
    PUBLISHED = 'published', _('Active (Published)')
    ARCHIVED = 'archived', _('Archived')

# --- Models (Reordered for correct ForeignKey references) ---

class Language(models.Model):
    code = models.CharField(max_length=5, unique=True, help_text="Language code (e.g., 'en', 'es')")
    name = models.CharField(max_length=100, help_text="Full language name (e.g., 'English')")
    is_active = models.BooleanField(default=True, help_text="Is this language available for templates?")

    def __str__(self):
        return f"{self.name} ({self.code})"

    class Meta:
        ordering = ['name']

class MasterTemplate(models.Model):
    name = models.CharField(max_length=255, help_text="Name of the master template (e.g., 'CT Brain Basic')")
    modality = models.CharField(
        max_length=5,
        choices=ModalityChoices.choices,
        default=ModalityChoices.OT,
        help_text="Primary imaging modality this template is for."
    )
    body_part = models.CharField(
        max_length=5,
        choices=SubspecialtyChoices.choices, # Using SubspecialtyChoices for body_part as per original file
        default=SubspecialtyChoices.OT,
        help_text="Primary body part or region this template is for."
    )
    description = models.TextField(blank=True, null=True, help_text="Optional description of the template.")
    is_active = models.BooleanField(default=True, help_text="Is this master template currently active and usable?")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='master_templates_created',
        help_text="Admin user who created this master template."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.get_modality_display()} - {self.get_body_part_display()})"

    class Meta:
        ordering = ['name']
        verbose_name = "Master Report Template"
        verbose_name_plural = "Master Report Templates"

class MasterTemplateSection(models.Model):
    master_template = models.ForeignKey(
        MasterTemplate, # MasterTemplate is now defined above
        on_delete=models.CASCADE,
        related_name='sections',
        help_text="The master template this section belongs to."
    )
    name = models.CharField(max_length=255, help_text="Name of the section (e.g., 'Findings', 'Impression').")
    placeholder_text = models.TextField(
        blank=True, null=True,
        help_text="Placeholder text or instructions for this section in the report form."
    )
    order = models.PositiveIntegerField(default=0, help_text="Order in which this section appears in the template.")
    is_required = models.BooleanField(default=True, help_text="Is this section mandatory for reports using this template?")

    def __str__(self):
        return f"{self.name} (Order: {self.order}) - Template: {self.master_template.name}"

    class Meta:
        ordering = ['master_template', 'order', 'name']
        unique_together = ('master_template', 'name') # A section name should be unique within a given master template
        verbose_name = "Master Template Section"
        verbose_name_plural = "Master Template Sections"

class Case(models.Model):
    title = models.CharField(max_length=255)
    subspecialty = models.CharField(
        max_length=5,
        choices=SubspecialtyChoices.choices,
        default=SubspecialtyChoices.OT
    )
    modality = models.CharField(
        max_length=5,
        choices=ModalityChoices.choices,
        default=ModalityChoices.OT
    )
    difficulty = models.CharField(
        max_length=20,
        choices=DifficultyChoices.choices,
        default=DifficultyChoices.BEGINNER
    )
    status = models.CharField(
        max_length=20,
        choices=CaseStatusChoices.choices,
        default=CaseStatusChoices.DRAFT
    )
    patient_age = models.CharField(max_length=50, blank=True, null=True, help_text="e.g., '5 years', '3 months', 'Neonate'")
    clinical_history = models.TextField()
    key_findings = models.TextField(blank=True, null=True, help_text="Expert's key imaging findings.")
    diagnosis = models.TextField(blank=True, null=True, help_text="Expert's final diagnosis.")
    discussion = models.TextField(blank=True, null=True, help_text="Expert's discussion points.")
    references = models.TextField(blank=True, null=True, help_text="References or further reading.")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='cases_created'
    )
    master_template = models.ForeignKey(
        MasterTemplate, # MasterTemplate is now defined above
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='cases',
        help_text="The master report template structure associated with this case."
    )
    viewed_by = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='UserCaseView', # Will define UserCaseView below
        related_name='viewed_cases',
        blank=True
    )
    # ***** YOUR NEW FIELD - Correctly placed within Case model *****
    orthanc_study_uid = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        unique=False,
        help_text="The DICOM StudyInstanceUID for the primary study in Orthanc associated with this case."
    )
    # ***** END NEW FIELD *****
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True, help_text="Date when the case becomes publicly visible.")

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if self.status == CaseStatusChoices.PUBLISHED and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

class CaseTemplate(models.Model):
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='applied_expert_templates') # Case is defined above
    language = models.ForeignKey(Language, on_delete=models.PROTECT, help_text="Language of this expert-filled template.") # Language is defined above
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def section_contents_ordered(self):
        return self.section_contents.all().order_by('master_section__order')

    def __str__(self):
        return f"Expert Template for '{self.case.title}' in {self.language.name}"

    class Meta:
        unique_together = ('case', 'language')
        ordering = ['case', 'language']
        verbose_name = "Expert-Filled Case Template"
        verbose_name_plural = "Expert-Filled Case Templates"

class CaseTemplateSectionContent(models.Model):
    case_template = models.ForeignKey(CaseTemplate, on_delete=models.CASCADE, related_name='section_contents') # CaseTemplate defined above
    master_section = models.ForeignKey(
        MasterTemplateSection, # MasterTemplateSection defined above
        on_delete=models.CASCADE,
        help_text="The corresponding section from the MasterTemplate."
    )
    content = models.TextField(blank=True, help_text="The expert-filled content for this section.")

    def __str__(self):
        return f"Content for '{self.master_section.name}' in {self.case_template}"

    class Meta:
        ordering = ['case_template', 'master_section__order']
        unique_together = ('case_template', 'master_section')
        verbose_name = "Expert Template Section Content"
        verbose_name_plural = "Expert Template Section Contents"

class Report(models.Model):
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='reports') # Case defined above
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reports')
    structured_content = models.JSONField(
        default=list,
        blank=True,
        help_text="Stores the user's report content, structured by master template sections."
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Report by {self.user.username} for {self.case.title}"

    class Meta:
        ordering = ['-submitted_at']
        unique_together = ('case', 'user')

class UserCaseView(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    case = models.ForeignKey(Case, on_delete=models.CASCADE) # Case defined above
    timestamp = models.DateTimeField(auto_now_add=True) # Renamed from viewed_at to match migration 0002

    def __str__(self):
        return f"{self.user.username} viewed {self.case.title} at {self.timestamp}"

    class Meta:
        unique_together = ('user', 'case')
        ordering = ['-timestamp']