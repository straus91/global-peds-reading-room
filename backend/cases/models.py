# backend/cases/models.py

from django.db import models
from django.conf import settings  # To get the User model
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
import uuid  # For potentially unique parts of case_identifier

# --- Choices (can be at the top) ---


class ModalityChoices(models.TextChoices):
    CT = "CT", _("Computer Tomography")
    MR = "MR", _("Magnetic Resonance")
    US = "US", _("Ultrasound")
    XR = "XR", _("X-ray")
    FL = "FL", _("Fluoroscopy")
    NM = "NM", _("Nuclear Medicine")
    OT = "OT", _("Other")


class SubspecialtyChoices(models.TextChoices):
    BR = "BR", _("Breast (Imaging and Interventional)")
    CA = "CA", _("Cardiac Radiology")
    CH = "CH", _("Chest Radiology")
    ER = "ER", _("Emergency Radiology")
    GI = "GI", _("Gastrointestinal Radiology")
    GU = "GU", _("Genitourinary Radiology")
    HN = "HN", _("Head and Neck")
    IR = "IR", _("Interventional Radiology")
    MK = "MK", _("Musculoskeletal Radiology")
    NM = "NM", _("Nuclear Medicine")  # As a subspecialty
    NR = "NR", _("Neuroradiology")
    OB = "OB", _("Obstetric/Gynecologic Radiology")
    OI = "OI", _("Oncologic Imaging")
    VA = "VA", _("Vascular Radiology")
    PD = "PD", _("Pediatric Radiology")
    OT = "OT", _("Other")


class DifficultyChoices(models.TextChoices):
    BEGINNER = "beginner", _("Beginner")
    INTERMEDIATE = "intermediate", _("Intermediate")
    ADVANCED = "advanced", _("Advanced")
    EXPERT = "expert", _("Expert")


class CaseStatusChoices(models.TextChoices):
    DRAFT = "draft", _("Draft")
    PUBLISHED = "published", _("Active (Published)")
    ARCHIVED = "archived", _("Archived")


# NEW Patient Sex Choices
class PatientSexChoices(models.TextChoices):
    MALE = "Male", _("Male")
    FEMALE = "Female", _("Female")
    OTHER = "Other", _("Other")
    UNKNOWN = "Unknown", _("Unknown")


# --- Models ---


class Language(models.Model):
    code = models.CharField(
        max_length=5, unique=True, help_text="Language code (e.g., 'en', 'es')"
    )
    name = models.CharField(
        max_length=100, help_text="Full language name (e.g., 'English')"
    )
    is_active = models.BooleanField(
        default=True, help_text="Is this language available for templates?"
    )

    def __str__(self):
        return f"{self.name} ({self.code})"

    class Meta:
        ordering = ["name"]


class MasterTemplate(models.Model):
    name = models.CharField(
        max_length=255, help_text="Name of the master template (e.g., 'CT Brain Basic')"
    )
    modality = models.CharField(
        max_length=5,
        choices=ModalityChoices.choices,
        default=ModalityChoices.OT,
        help_text="Primary imaging modality this template is for.",
    )
    body_part = models.CharField(
        max_length=5,
        choices=SubspecialtyChoices.choices,
        default=SubspecialtyChoices.OT,
        help_text="Primary body part or region this template is for.",
    )
    description = models.TextField(
        blank=True, null=True, help_text="Optional description of the template."
    )
    is_active = models.BooleanField(
        default=True, help_text="Is this master template currently active and usable?"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="master_templates_created",
        help_text="Admin user who created this master template.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.get_modality_display()} - {self.get_body_part_display()})"

    class Meta:
        ordering = ["name"]
        verbose_name = "Master Report Template"
        verbose_name_plural = "Master Report Templates"


class MasterTemplateSection(models.Model):
    master_template = models.ForeignKey(
        MasterTemplate,
        on_delete=models.CASCADE,
        related_name="sections",
        help_text="The master template this section belongs to.",
    )
    name = models.CharField(
        max_length=255,
        help_text="Name of the section (e.g., 'Findings', 'Impression').",
    )
    placeholder_text = models.TextField(
        blank=True,
        null=True,
        help_text="Placeholder text or instructions for this section in the report form.",
    )
    order = models.PositiveIntegerField(
        default=0, help_text="Order in which this section appears in the template."
    )
    is_required = models.BooleanField(
        default=True,
        help_text="Is this section mandatory for reports using this template?",
    )

    def __str__(self):
        return (
            f"{self.name} (Order: {self.order}) - Template: {self.master_template.name}"
        )

    class Meta:
        ordering = ["master_template", "order", "name"]
        unique_together = ("master_template", "name")
        verbose_name = "Master Template Section"
        verbose_name_plural = "Master Template Sections"


class Case(models.Model):
    # Admin-facing title for organization
    title = models.CharField(
        max_length=255, help_text="Internal title for admin organization."
    )

    # Human-readable, non-spoiling case identifier
    case_identifier = models.CharField(
        max_length=100,
        unique=True,
        blank=True,
        null=True,  # <<< *** ADDED null=True HERE ***
        help_text="Human-readable unique ID (e.g., NR-MR-2025-0001). Auto-generated if left blank.",
    )

    subspecialty = models.CharField(
        max_length=5,
        choices=SubspecialtyChoices.choices,
        default=SubspecialtyChoices.OT,
    )
    modality = models.CharField(
        max_length=5, choices=ModalityChoices.choices, default=ModalityChoices.OT
    )
    difficulty = models.CharField(
        max_length=20,
        choices=DifficultyChoices.choices,
        default=DifficultyChoices.BEGINNER,
    )
    status = models.CharField(
        max_length=20,
        choices=CaseStatusChoices.choices,
        default=CaseStatusChoices.DRAFT,
    )
    patient_age = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="e.g., '5 years', '3 months', 'Neonate'",
    )

    patient_sex = models.CharField(
        max_length=10,
        choices=PatientSexChoices.choices,
        blank=True,
        null=True,
        help_text="Patient's biological sex if relevant and known",
    )

    clinical_history = models.TextField()
    key_findings = models.TextField(
        blank=True,
        null=True,
        help_text="Expert's key imaging findings summary for THIS CASE (semicolon-separated phrases recommended for AI use).",
    )
    diagnosis = models.TextField(
        blank=True, null=True, help_text="Expert's final diagnosis for THIS CASE."
    )
    discussion = models.TextField(
        blank=True, null=True, help_text="Expert's discussion points for THIS CASE."
    )
    references = models.TextField(
        blank=True,
        null=True,
        help_text="References or further reading (URLs/citations, one per line).",
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cases_created",
    )
    master_template = models.ForeignKey(
        MasterTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cases",
        help_text="The master report template structure associated with this case.",
    )
    viewed_by = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through="UserCaseView",
        related_name="viewed_cases",
        blank=True,
    )
    orthanc_study_uid = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        unique=False,
        help_text="The DICOM StudyInstanceUID for the primary study in Orthanc associated with this case.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(
        null=True, blank=True, help_text="Date when the case becomes publicly visible."
    )

    def __str__(self):
        return (
            self.case_identifier
            if self.case_identifier
            else f"Case {self.id} (No Identifier) - {self.title}"
        )

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if self.status == CaseStatusChoices.PUBLISHED and not self.published_at:
            self.published_at = timezone.now()

        if not self.case_identifier:
            # Determine abbreviations safely
            sub_abbr = "GEN"  # Default
            if self.subspecialty:
                try:
                    sub_abbr = self.get_subspecialty_display().split(" - ")[0]
                except (ValueError, IndexError, AttributeError):  # Catch parsing errors
                    sub_abbr = (
                        self.subspecialty[:3].upper() if self.subspecialty else "GEN"
                    )

            mod_abbr = "MOD"  # Default
            if self.modality:
                try:
                    mod_abbr = self.get_modality_display().split(" - ")[0]
                except (ValueError, IndexError, AttributeError):  # Catch parsing errors
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
            last_case_with_prefix = (
                Case.objects.filter(case_identifier__startswith=base_id_prefix)
                .order_by("case_identifier")
                .last()
            )
            next_seq = 1
            if last_case_with_prefix and last_case_with_prefix.case_identifier:
                try:
                    last_seq_str = last_case_with_prefix.case_identifier.split("-")[-1]
                    # Check if it's purely numeric before trying to convert
                    if last_seq_str.isdigit():
                        next_seq = int(last_seq_str) + 1
                    # If it has an underscore (from previous collision handling), parse that
                    elif "_" in last_seq_str and last_seq_str.split("_")[0].isdigit():
                        next_seq = int(last_seq_str.split("_")[0]) + 1
                except (ValueError, IndexError):
                    # If parsing fails, fallback to a simple counter or UUID based approach
                    pass  # next_seq remains 1 or consider another strategy

            temp_id = f"{base_id_prefix}{next_seq:04d}"
            counter = 0
            # Check for uniqueness, excluding self if updating
            while (
                Case.objects.filter(case_identifier=temp_id)
                .exclude(pk=self.pk)
                .exists()
            ):
                counter += 1
                # If simple sequence collides, try adding a small counter, then fallback to UUID
                if counter <= 5:  # Try a few simple increments
                    temp_id = f"{base_id_prefix}{next_seq+counter:04d}"
                else:  # Fallback to ensure uniqueness if many collisions
                    temp_id = f"{base_id_prefix}{next_seq:04d}_{uuid.uuid4().hex[:4]}"
                    break
            self.case_identifier = temp_id

        super().save(*args, **kwargs)


class CaseTemplate(models.Model):
    case = models.ForeignKey(
        Case, on_delete=models.CASCADE, related_name="applied_expert_templates"
    )
    language = models.ForeignKey(
        Language,
        on_delete=models.PROTECT,
        help_text="Language of this expert-filled template.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def section_contents_ordered(self):
        return self.section_contents.all().order_by("master_section__order")

    def __str__(self):
        return f"Expert Template for '{self.case.case_identifier if self.case.case_identifier else self.case.title}' in {self.language.name}"

    class Meta:
        unique_together = ("case", "language")
        ordering = ["case", "language"]
        verbose_name = "Expert-Filled Case Template"
        verbose_name_plural = "Expert-Filled Case Templates"


class CaseTemplateSectionContent(models.Model):
    case_template = models.ForeignKey(
        CaseTemplate, on_delete=models.CASCADE, related_name="section_contents"
    )
    master_section = models.ForeignKey(
        MasterTemplateSection,
        on_delete=models.CASCADE,
        help_text="The corresponding section from the MasterTemplate.",
    )
    content = models.TextField(
        blank=True, help_text="The expert-filled content for this section."
    )

    key_concepts_text = models.TextField(
        blank=True,
        null=True,
        help_text="Admin-defined, case-specific key concepts for this section of this expert template (semicolon-separated phrases).",
    )

    def __str__(self):
        return f"Content for '{self.master_section.name}' in {self.case_template}"

    class Meta:
        ordering = ["case_template", "master_section__order"]
        unique_together = ("case_template", "master_section")
        verbose_name = "Expert Template Section Content"
        verbose_name_plural = "Expert Template Section Contents"


class Report(models.Model):
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name="reports")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reports"
    )
    structured_content = models.JSONField(
        default=list,
        blank=True,
        help_text="Stores the user's report content, structured by master template sections.",
    )
    ai_feedback_content = models.JSONField(
        default=dict,
        blank=True,
        help_text="Stores the AI-generated feedback content for this report.",
    )
    is_archived = models.BooleanField(
        default=False,
        help_text="Flag to mark this report as archived. Archived reports are kept for history but not shown as the current report.",
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Report by {self.user.username} for {self.case.case_identifier if self.case.case_identifier else self.case.title}"

    class Meta:
        ordering = ["-submitted_at"]
        # Removed the unique_together constraint to allow multiple reports per user/case
        # With the is_archived flag we can track which one is the current active report


class UserCaseView(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    case = models.ForeignKey(Case, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} viewed {self.case.case_identifier if self.case.case_identifier else self.case.title} at {self.timestamp}"

    class Meta:
        unique_together = ("user", "case")
        ordering = ["-timestamp"]


class AIFeedbackRating(models.Model):
    report = models.ForeignKey(
        Report,
        on_delete=models.CASCADE,
        related_name="ai_feedback_ratings",
        help_text="The user report for which AI feedback was provided and is being rated.",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ai_feedback_ratings_given",
        help_text="The user who is providing the rating for the AI feedback.",
    )
    star_rating = models.IntegerField(
        choices=[(i, str(i)) for i in range(1, 6)],  # 1 to 5 stars
        help_text="User's star rating for the AI feedback (1-5).",
    )
    comment = models.TextField(
        blank=True,
        null=True,
        help_text="Optional textual comment from the user about the AI feedback.",
    )
    rated_at = models.DateTimeField(
        auto_now_add=True, help_text="Timestamp when the rating was submitted."
    )

    def __str__(self):
        return f"Rating for AI feedback on Report ID {self.report.id} by {self.user.username}: {self.star_rating} stars"

    class Meta:
        ordering = ["-rated_at"]
        unique_together = ("report", "user")
        verbose_name = "AI Feedback Rating"
        verbose_name_plural = "AI Feedback Ratings"


# --- Phase 1: Foundation Improvements Models ---


class AIFeedbackDetailedRating(models.Model):
    """
    Multi-dimensional rating for AI feedback quality.

    Replaces simple star rating with category-specific scoring to enable
    data-driven prompt optimization.

    Business Rules:
    - One rating per user per report (enforced by unique constraint)
    - All ratings on 1-5 scale
    - False positive tracking for quality monitoring
    - Indexed for analytics query performance
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique rating identifier (UUID)."
    )

    # Relationships
    report = models.ForeignKey(
        Report,
        on_delete=models.CASCADE,
        related_name="detailed_feedback_ratings",
        help_text="The user report being rated."
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="detailed_feedback_ratings_given",
        help_text="The user providing the rating."
    )

    # Multi-dimensional ratings (1-5 scale)
    accuracy_rating = models.IntegerField(
        choices=[(i, str(i)) for i in range(1, 6)],
        help_text="How accurate was the AI feedback? (1=Very Inaccurate, 5=Very Accurate)"
    )
    helpfulness_rating = models.IntegerField(
        choices=[(i, str(i)) for i in range(1, 6)],
        help_text="How helpful was the feedback for learning? (1=Not Helpful, 5=Very Helpful)"
    )
    actionability_rating = models.IntegerField(
        choices=[(i, str(i)) for i in range(1, 6)],
        help_text="How actionable/specific were the suggestions? (1=Too Vague, 5=Very Specific)"
    )
    overall_rating = models.IntegerField(
        choices=[(i, str(i)) for i in range(1, 6)],
        help_text="Overall satisfaction with AI feedback (1=Very Dissatisfied, 5=Very Satisfied)"
    )

    # False positive tracking
    has_false_positives = models.BooleanField(
        default=False,
        help_text="Did AI incorrectly flag issues that were actually correct?"
    )
    false_positive_details = models.TextField(
        blank=True,
        null=True,
        help_text="Details about false positives if any (what was incorrectly flagged?)"
    )

    # Optional comment
    comment = models.TextField(
        blank=True,
        null=True,
        help_text="Optional textual comment about the AI feedback quality."
    )

    # Timestamp
    rated_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this rating was submitted."
    )

    def __str__(self):
        return f"Detailed Rating for Report {self.report.id} by {self.user.username}: Overall {self.overall_rating}/5"

    class Meta:
        ordering = ["-rated_at"]
        unique_together = [["report", "user"]]
        verbose_name = "AI Feedback Detailed Rating"
        verbose_name_plural = "AI Feedback Detailed Ratings"
        indexes = [
            models.Index(fields=["rated_at"], name="detailed_rating_date_idx"),
            models.Index(fields=["accuracy_rating"], name="detailed_rating_accuracy_idx"),
            models.Index(fields=["helpfulness_rating"], name="detailed_rating_helpful_idx"),
            models.Index(fields=["actionability_rating"], name="detailed_rating_action_idx"),
            models.Index(fields=["has_false_positives"], name="detailed_rating_fp_idx"),
        ]


class FeedbackCache(models.Model):
    """
    Cache for AI-generated feedback based on report content hash.

    Reduces API costs by serving cached feedback for identical reports.
    Cache key is SHA256 hash of (user_sections + expert_sections + case_context).

    Business Rules:
    - Cache expires after 30 days or when prompt version changes
    - Hit count tracks cache effectiveness
    - Indexed for O(1) cache lookup performance
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique cache entry identifier (UUID)."
    )

    # Cache key (hash of report content)
    content_hash = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        help_text="SHA256 hash of normalized report content (user + expert + case context)."
    )

    # Cached data
    feedback_content = models.JSONField(
        help_text="Cached AI feedback response (structured JSON format)."
    )

    # Metadata
    case = models.ForeignKey(
        Case,
        on_delete=models.CASCADE,
        related_name="feedback_caches",
        help_text="Case for which feedback was generated (for analytics)."
    )
    prompt_version = models.ForeignKey(
        "PromptVersion",  # Forward reference since defined below
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cached_feedbacks",
        help_text="Prompt version used to generate this cached feedback."
    )

    # Usage tracking
    hit_count = models.IntegerField(
        default=0,
        help_text="Number of times this cache entry was served."
    )
    last_hit_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last time this cache was hit."
    )

    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this cache entry was created."
    )
    expires_at = models.DateTimeField(
        help_text="Cache expiration timestamp (invalidate after prompt changes)."
    )

    def __str__(self):
        return f"Cache {self.content_hash[:8]}... (hits: {self.hit_count}, case: {self.case.case_identifier})"

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Feedback Cache Entry"
        verbose_name_plural = "Feedback Cache Entries"
        indexes = [
            models.Index(fields=["content_hash"], name="cache_hash_idx"),
            models.Index(fields=["case", "created_at"], name="cache_case_date_idx"),
            models.Index(fields=["expires_at"], name="cache_expires_idx"),
            models.Index(fields=["hit_count"], name="cache_hits_idx"),
        ]


class PromptVersion(models.Model):
    """
    Version control for AI feedback prompts.

    Enables A/B testing, performance tracking, and easy rollback.
    Tracks quality metrics and costs per version for data-driven optimization.

    Business Rules:
    - Only one version can be active at a time (enforced in code)
    - A/B testing uses weighted random selection
    - Metrics updated when ratings received
    - Indexed for prompt selection performance
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique version identifier (UUID)."
    )

    # Version metadata
    version_number = models.CharField(
        max_length=20,
        unique=True,
        help_text="Semantic version (e.g., 'v1.2.3', 'v2.0.0')."
    )
    name = models.CharField(
        max_length=200,
        help_text="Human-readable name (e.g., 'Improved Specificity v2')."
    )
    description = models.TextField(
        help_text="What changed in this version and why (changelog entry)."
    )

    # Prompt content
    prompt_template = models.TextField(
        help_text="Full prompt template with placeholders for context variables."
    )

    # Status
    is_active = models.BooleanField(
        default=False,
        help_text="Is this version currently in use? (only one can be true)"
    )
    is_ab_test = models.BooleanField(
        default=False,
        help_text="Is this version part of an A/B test?"
    )
    ab_test_weight = models.IntegerField(
        default=0,
        help_text="Weight for A/B testing (0-100, higher = more traffic). Total weights should sum to 100."
    )

    # Performance tracking (calculated fields)
    total_uses = models.IntegerField(
        default=0,
        help_text="Number of times this prompt was used to generate feedback."
    )
    average_rating = models.FloatField(
        null=True,
        blank=True,
        help_text="Average overall rating for feedback from this prompt (calculated from ratings)."
    )
    average_accuracy = models.FloatField(
        null=True,
        blank=True,
        help_text="Average accuracy rating for this prompt version."
    )
    average_helpfulness = models.FloatField(
        null=True,
        blank=True,
        help_text="Average helpfulness rating for this prompt version."
    )
    average_actionability = models.FloatField(
        null=True,
        blank=True,
        help_text="Average actionability rating for this prompt version."
    )

    # Cost tracking
    total_tokens_used = models.BigIntegerField(
        default=0,
        help_text="Total tokens consumed by this prompt version."
    )
    average_tokens_per_use = models.FloatField(
        null=True,
        blank=True,
        help_text="Average tokens per feedback generation (for cost estimation)."
    )

    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this version was created."
    )
    activated_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this version was first activated."
    )
    deactivated_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this version was deactivated."
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="prompt_versions_created",
        help_text="Admin user who created this prompt version."
    )

    def __str__(self):
        status = "ACTIVE" if self.is_active else ("A/B TEST" if self.is_ab_test else "INACTIVE")
        return f"{self.version_number} - {self.name} ({status})"

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Prompt Version"
        verbose_name_plural = "Prompt Versions"
        indexes = [
            models.Index(fields=["version_number"], name="prompt_version_num_idx"),
            models.Index(fields=["is_active"], name="prompt_is_active_idx"),
            models.Index(fields=["is_ab_test", "ab_test_weight"], name="prompt_ab_test_idx"),
            models.Index(fields=["average_rating"], name="prompt_avg_rating_idx"),
            models.Index(fields=["created_at"], name="prompt_created_idx"),
        ]


class TokenUsageLog(models.Model):
    """
    Log of token usage for each AI feedback generation.

    Enables cost tracking, budget monitoring, and optimization.
    Tracks both cached and uncached requests for ROI analysis.

    Business Rules:
    - Created for every feedback generation (cached or not)
    - Cost calculated based on current Gemini pricing
    - Indexed for time-series and cost analytics
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique log entry identifier (UUID)."
    )

    # Request context
    report = models.ForeignKey(
        Report,
        on_delete=models.CASCADE,
        related_name="token_usage_logs",
        help_text="Report for which feedback was generated."
    )
    case = models.ForeignKey(
        Case,
        on_delete=models.CASCADE,
        related_name="token_usage_logs",
        help_text="Case associated with this request (for cost per case analytics)."
    )
    prompt_version = models.ForeignKey(
        PromptVersion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="token_usage_logs",
        help_text="Prompt version used for this request."
    )

    # Token metrics
    input_tokens = models.IntegerField(
        help_text="Tokens in prompt (input to LLM)."
    )
    output_tokens = models.IntegerField(
        help_text="Tokens in response (output from LLM)."
    )
    total_tokens = models.IntegerField(
        help_text="input_tokens + output_tokens."
    )

    # Cost calculation (USD, 6 decimal places for precision)
    input_cost = models.DecimalField(
        max_digits=10,
        decimal_places=6,
        help_text="Cost for input tokens in USD (based on model pricing)."
    )
    output_cost = models.DecimalField(
        max_digits=10,
        decimal_places=6,
        help_text="Cost for output tokens in USD (based on model pricing)."
    )
    total_cost = models.DecimalField(
        max_digits=10,
        decimal_places=6,
        help_text="Total cost for this request in USD."
    )

    # Performance metrics
    response_time_ms = models.IntegerField(
        help_text="Time to receive response in milliseconds (for monitoring)."
    )

    # Cache status
    was_cached = models.BooleanField(
        default=False,
        help_text="Was this served from cache? (if true, tokens/costs are 0)"
    )

    # Model details
    model_name = models.CharField(
        max_length=100,
        help_text="AI model used (e.g., 'gemini-2.5-flash', 'gemini-1.5-flash')."
    )

    # Timestamp
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this request was made."
    )

    def __str__(self):
        cached_str = " (CACHED)" if self.was_cached else ""
        return f"Token Log {self.created_at.strftime('%Y-%m-%d %H:%M')} - ${self.total_cost:.4f}{cached_str}"

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Token Usage Log"
        verbose_name_plural = "Token Usage Logs"
        indexes = [
            models.Index(fields=["created_at"], name="token_log_date_idx"),
            models.Index(fields=["case", "created_at"], name="token_log_case_date_idx"),
            models.Index(fields=["was_cached"], name="token_log_cached_idx"),
            models.Index(fields=["total_cost"], name="token_log_cost_idx"),
            models.Index(fields=["prompt_version", "created_at"], name="token_log_version_idx"),
        ]


# --- Tutoring Session Models ---


class TutoringSessionStatusChoices(models.TextChoices):
    ACTIVE = "active", _("Active")
    COMPLETED = "completed", _("Completed")
    ABANDONED = "abandoned", _("Abandoned")


class TutoringSession(models.Model):
    """
    Interactive tutoring conversation session for a user's report.

    A session allows multi-turn Q&A between user and AI tutor about their report,
    with access to case context, expert comparison, terminology, literature, and
    visual analysis via VLM.

    Business Rules:
    - One active session per (report, user) - enforced by unique constraint
    - Maximum 10 turns per session by default
    - User can have up to 3 sessions per day (enforced in API)
    - Sessions cascade delete when Report is deleted
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique session identifier (UUID)."
    )
    report = models.ForeignKey(
        Report,
        on_delete=models.CASCADE,
        related_name="tutoring_sessions",
        help_text="The user report this tutoring session is about."
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tutoring_sessions",
        help_text="The user engaging in this tutoring session."
    )
    turns_count = models.IntegerField(
        default=0,
        help_text="Current number of conversation turns in this session."
    )
    max_turns = models.IntegerField(
        default=10,
        help_text="Maximum allowed turns for this session."
    )
    status = models.CharField(
        max_length=20,
        choices=TutoringSessionStatusChoices.choices,
        default=TutoringSessionStatusChoices.ACTIVE,
        help_text="Current status of the tutoring session."
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this session was created."
    )
    last_turn_at = models.DateTimeField(
        auto_now=True,
        help_text="When the last turn was created in this session."
    )

    def __str__(self):
        return f"Tutoring Session {self.id} for {self.user.username} (Report: {self.report.id})"

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Tutoring Session"
        verbose_name_plural = "Tutoring Sessions"
        indexes = [
            models.Index(fields=["report"], name="tutoring_report_idx"),
            models.Index(fields=["user", "created_at"], name="tutoring_user_created_idx"),
            models.Index(fields=["status"], name="tutoring_status_idx"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["report", "user"],
                condition=models.Q(status=TutoringSessionStatusChoices.ACTIVE),
                name="unique_active_session_per_report_user"
            )
        ]


class TutoringTurn(models.Model):
    """
    A single conversation turn in a tutoring session.

    Each turn contains:
    - User's question/message
    - AI tutor's response
    - Tools used (e.g., fetch_image, vlm_analysis, literature_search)
    - Image references (if user mentioned specific images)
    - Response time for monitoring

    Ordering: By turn_number within session (chronological)
    """
    session = models.ForeignKey(
        TutoringSession,
        on_delete=models.CASCADE,
        related_name="turns",
        help_text="The tutoring session this turn belongs to."
    )
    turn_number = models.IntegerField(
        help_text="Sequential turn number within this session (1, 2, 3, ...)."
    )
    user_message = models.TextField(
        help_text="The user's question or message in this turn."
    )
    ai_response = models.TextField(
        help_text="The AI tutor's response to the user's message."
    )
    tools_used = models.JSONField(
        default=list,
        blank=True,
        help_text="List of tool names used to generate this response (e.g., ['fetch_image', 'vlm_analysis'])."
    )
    image_references = models.JSONField(
        default=list,
        blank=True,
        help_text="List of image references detected in user message (e.g., [{'series': 5, 'image': 35}])."
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this turn was created."
    )
    response_time_ms = models.IntegerField(
        help_text="Time taken to generate AI response in milliseconds."
    )

    def __str__(self):
        return f"Turn {self.turn_number} in Session {self.session.id}"

    class Meta:
        ordering = ["turn_number"]
        unique_together = [["session", "turn_number"]]
        verbose_name = "Tutoring Turn"
        verbose_name_plural = "Tutoring Turns"
        indexes = [
            models.Index(fields=["session", "turn_number"], name="tutoring_turn_session_num_idx"),
            models.Index(fields=["created_at"], name="tutoring_turn_created_idx"),
        ]
