# backend/cases/models.py

from django.db import models
from django.conf import settings # To get the User model
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
import uuid # For potentially unique parts of case_identifier

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

# NEW Patient Sex Choices
class PatientSexChoices(models.TextChoices):
    MALE = 'Male', _('Male')
    FEMALE = 'Female', _('Female')
    OTHER = 'Other', _('Other')
    UNKNOWN = 'Unknown', _('Unknown')


# --- Models ---

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
        choices=SubspecialtyChoices.choices,
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
        MasterTemplate,
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
        unique_together = ('master_template', 'name')
        verbose_name = "Master Template Section"
        verbose_name_plural = "Master Template Sections"

class Case(models.Model):
    # Admin-facing title for organization
    title = models.CharField(max_length=255, help_text="Internal title for admin organization.")
    
    # Human-readable, non-spoiling case identifier
    case_identifier = models.CharField(
        max_length=100,
        unique=True,
        blank=True, 
        null=True, # <<< *** ADDED null=True HERE ***
        help_text="Human-readable unique ID (e.g., NR-MR-2025-0001). Auto-generated if left blank."
    )
    
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
    
    patient_sex = models.CharField(
        max_length=10,
        choices=PatientSexChoices.choices,
        blank=True,
        null=True,
        help_text="Patient's biological sex if relevant and known"
    )

    clinical_history = models.TextField()
    key_findings = models.TextField(blank=True, null=True, help_text="Expert's key imaging findings summary for THIS CASE (semicolon-separated phrases recommended for AI use).")
    diagnosis = models.TextField(blank=True, null=True, help_text="Expert's final diagnosis for THIS CASE.")
    discussion = models.TextField(blank=True, null=True, help_text="Expert's discussion points for THIS CASE.")
    references = models.TextField(blank=True, null=True, help_text="References or further reading (URLs/citations, one per line).")
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='cases_created'
    )
    master_template = models.ForeignKey(
        MasterTemplate,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='cases',
        help_text="The master report template structure associated with this case."
    )
    viewed_by = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='UserCaseView',
        related_name='viewed_cases',
        blank=True
    )
    orthanc_study_uid = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        unique=False, 
        help_text="The DICOM StudyInstanceUID for the primary study in Orthanc associated with this case."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True, help_text="Date when the case becomes publicly visible.")

    def __str__(self):
        return self.case_identifier if self.case_identifier else f"Case {self.id} (No Identifier) - {self.title}"

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if self.status == CaseStatusChoices.PUBLISHED and not self.published_at:
            self.published_at = timezone.now()
        
        if not self.case_identifier:
            # Determine abbreviations safely
            sub_abbr = "GEN" # Default
            if self.subspecialty:
                try:
                    sub_abbr = self.get_subspecialty_display().split(' - ')[0]
                except: # Catch any error if display format is unexpected
                    sub_abbr = self.subspecialty[:3].upper() if self.subspecialty else "GEN"

            mod_abbr = "MOD" # Default
            if self.modality:
                try:
                    mod_abbr = self.get_modality_display().split(' - ')[0]
                except:
                    mod_abbr = self.modality[:3].upper() if self.modality else "MOD"
            
            year_str = timezone.now().strftime("%Y")
            
            # Simplified sequence for this attempt, focusing on uniqueness rather than strict daily sequence
            # For a truly robust sequential ID under high concurrency, a database sequence or more complex locking might be needed.
            # This approach relies on the unique constraint and retries with a UUID component if a simple counter collides.
            
            # Get a base for counting. This is not perfectly atomic for high concurrency daily sequences.
            # A simpler approach for now: use total count or a timestamp component.
            # Let's use a simpler year-based sequence for now.
            base_id_prefix = f"{sub_abbr}-{mod_abbr}-{year_str}-"
            
            # Find the highest sequence number for this prefix this year
            last_case_with_prefix = Case.objects.filter(case_identifier__startswith=base_id_prefix).order_by('case_identifier').last()
            next_seq = 1
            if last_case_with_prefix and last_case_with_prefix.case_identifier:
                try:
                    last_seq_str = last_case_with_prefix.case_identifier.split('-')[-1]
                    # Check if it's purely numeric before trying to convert
                    if last_seq_str.isdigit():
                        next_seq = int(last_seq_str) + 1
                    # If it has an underscore (from previous collision handling), parse that
                    elif '_' in last_seq_str and last_seq_str.split('_')[0].isdigit():
                         next_seq = int(last_seq_str.split('_')[0]) + 1
                except (ValueError, IndexError):
                    # If parsing fails, fallback to a simple counter or UUID based approach
                    pass # next_seq remains 1 or consider another strategy

            temp_id = f"{base_id_prefix}{next_seq:04d}"
            counter = 0
            # Check for uniqueness, excluding self if updating
            while Case.objects.filter(case_identifier=temp_id).exclude(pk=self.pk).exists():
                counter += 1
                # If simple sequence collides, try adding a small counter, then fallback to UUID
                if counter <= 5: # Try a few simple increments
                     temp_id = f"{base_id_prefix}{next_seq+counter:04d}"
                else: # Fallback to ensure uniqueness if many collisions
                    temp_id = f"{base_id_prefix}{next_seq:04d}_{uuid.uuid4().hex[:4]}"
                    break 
            self.case_identifier = temp_id
            
        super().save(*args, **kwargs)

class CaseTemplate(models.Model):
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='applied_expert_templates')
    language = models.ForeignKey(Language, on_delete=models.PROTECT, help_text="Language of this expert-filled template.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def section_contents_ordered(self):
        return self.section_contents.all().order_by('master_section__order')

    def __str__(self):
        return f"Expert Template for '{self.case.case_identifier if self.case.case_identifier else self.case.title}' in {self.language.name}"

    class Meta:
        unique_together = ('case', 'language')
        ordering = ['case', 'language']
        verbose_name = "Expert-Filled Case Template"
        verbose_name_plural = "Expert-Filled Case Templates"

class CaseTemplateSectionContent(models.Model):
    case_template = models.ForeignKey(CaseTemplate, on_delete=models.CASCADE, related_name='section_contents')
    master_section = models.ForeignKey(
        MasterTemplateSection,
        on_delete=models.CASCADE,
        help_text="The corresponding section from the MasterTemplate."
    )
    content = models.TextField(blank=True, help_text="The expert-filled content for this section.")
    
    key_concepts_text = models.TextField(
        blank=True, 
        null=True, 
        help_text="Admin-defined, case-specific key concepts for this section of this expert template (semicolon-separated phrases)."
    )

    def __str__(self):
        return f"Content for '{self.master_section.name}' in {self.case_template}"

    class Meta:
        ordering = ['case_template', 'master_section__order']
        unique_together = ('case_template', 'master_section')
        verbose_name = "Expert Template Section Content"
        verbose_name_plural = "Expert Template Section Contents"

class Report(models.Model):
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='reports')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reports')
    structured_content = models.JSONField(
        default=list,
        blank=True,
        help_text="Stores the user's report content, structured by master template sections."
    )
    ai_feedback_content = models.JSONField( # <<< ADD THIS LINE
        default=dict,
        blank=True,
        help_text="Stores the AI-generated feedback content for this report."
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Report by {self.user.username} for {self.case.case_identifier if self.case.case_identifier else self.case.title}"

    class Meta:
        ordering = ['-submitted_at']
        unique_together = ('case', 'user')

class UserCaseView(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    case = models.ForeignKey(Case, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} viewed {self.case.case_identifier if self.case.case_identifier else self.case.title} at {self.timestamp}"

    class Meta:
        unique_together = ('user', 'case')
        ordering = ['-timestamp']

class AIFeedbackRating(models.Model):
    report = models.ForeignKey(
        Report, 
        on_delete=models.CASCADE, 
        related_name='ai_feedback_ratings',
        help_text="The user report for which AI feedback was provided and is being rated."
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='ai_feedback_ratings_given',
        help_text="The user who is providing the rating for the AI feedback."
    )
    star_rating = models.IntegerField(
        choices=[(i, str(i)) for i in range(1, 6)], # 1 to 5 stars
        help_text="User's star rating for the AI feedback (1-5)."
    )
    comment = models.TextField(
        blank=True, 
        null=True,
        help_text="Optional textual comment from the user about the AI feedback."
    )
    rated_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when the rating was submitted."
    )

    def __str__(self):
        return f"Rating for AI feedback on Report ID {self.report.id} by {self.user.username}: {self.star_rating} stars"

    class Meta:
        ordering = ['-rated_at']
        unique_together = ('report', 'user') 
        verbose_name = "AI Feedback Rating"
        verbose_name_plural = "AI Feedback Ratings"