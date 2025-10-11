# 🗄️ Data Models Documentation

## 🎯 Overview

Global Peds Reading Room uses a sophisticated multi-tier data model designed to support:
- 🌐 **Multi-language** expert content
- 📋 **Structured reporting** with reusable templates
- 🤖 **AI-powered feedback** on user submissions
- 📊 **Analytics & metrics** for continuous improvement
- 🔄 **Report versioning** to track user progress

---

## 📊 Entity Relationship Overview

```
┌──────────────┐         ┌──────────────────┐
│   Language   │         │  MasterTemplate  │
└──────┬───────┘         └────────┬─────────┘
       │                          │
       │                          │ defines structure
       │                          ▼
       │                  ┌───────────────┐
       │                  │     Case      │◄──────┐
       │                  └───────┬───────┘       │
       │                          │               │
       │         ┌────────────────┼───────────────┤
       │         │                │               │
       │         ▼                ▼               │
       │  ┌─────────────┐  ┌──────────────┐     │
       └─►│CaseTemplate │  │    Report    │─────┘
          └──────┬──────┘  └──────┬───────┘
                 │                 │
                 ▼                 ▼
    ┌────────────────────┐  ┌──────────────────┐
    │CaseTemplateSection │  │ AIFeedbackRating │
    │     Content        │  └──────────────────┘
    └────────────────────┘
```

---

## 📚 Core Models

### 1️⃣ Language

**Purpose**: Supports multi-language expert templates and internationalization.

**Location**: `backend/cases/models.py:59-68`

**Fields**:
- `code` (CharField, unique): Language code (e.g., 'en', 'es', 'fr')
- `name` (CharField): Full language name (e.g., 'English', 'Spanish')
- `is_active` (BooleanField): Controls availability for new templates

**Relationships**:
- `CaseTemplate` (One Language → Many CaseTemplates)

**Key Behaviors**:
- Ordered alphabetically by name
- Deactivating a language doesn't delete existing templates

**Data-Driven Considerations**:
- Track which languages are most used for analytics
- Monitor feedback quality by language
- Consider adding language usage statistics

**Example Usage**:
```python
# Get all active languages for template creation
active_languages = Language.objects.filter(is_active=True)

# Find templates in Spanish
spanish = Language.objects.get(code='es')
spanish_templates = spanish.casetemplates.all()
```

---

### 2️⃣ MasterTemplate

**Purpose**: Defines reusable report structures (sections) for different imaging modalities and body parts.

**Location**: `backend/cases/models.py:70-102`

**Fields**:
- `name` (CharField): Template name (e.g., 'CT Brain Basic', 'X-Ray Chest')
- `modality` (CharField, choices): Imaging type (CT, MR, US, XR, FL, NM, OT)
- `body_part` (CharField, choices): Subspecialty/region (BR, CA, CH, ER, GI, etc.)
- `description` (TextField, optional): Detailed template explanation
- `is_active` (BooleanField): Controls template availability
- `created_by` (ForeignKey → User, nullable)
- `created_at`, `updated_at` (DateTimeField, auto)

**Relationships**:
- `sections` (One MasterTemplate → Many MasterTemplateSection)
- `cases` (One MasterTemplate → Many Case)

**Key Behaviors**:
- Defines STRUCTURE only, not content
- Can be reused across many cases
- Ordered by name

**Scalability Considerations**:
- ⚠️ Deleting a MasterTemplate: Use `SET_NULL` for Cases (they retain reference)
- Use `select_related('created_by')` when querying with user info
- Consider caching frequently used templates

**Example Usage**:
```python
# Create a new template
template = MasterTemplate.objects.create(
    name="CT Brain Basic",
    modality="CT",
    body_part="NR",  # Neuroradiology
    created_by=admin_user
)

# Get all active chest x-ray templates
xr_chest = MasterTemplate.objects.filter(
    modality="XR",
    body_part="CH",
    is_active=True
)
```

---

### 3️⃣ MasterTemplateSection

**Purpose**: Defines individual sections (e.g., "Findings", "Impression") within a MasterTemplate.

**Location**: `backend/cases/models.py:104-126`

**Fields**:
- `master_template` (ForeignKey → MasterTemplate, CASCADE)
- `name` (CharField): Section name
- `placeholder_text` (TextField, optional): Instructions for report form
- `order` (PositiveIntegerField): Display order
- `is_required` (BooleanField): Whether users must complete this section

**Relationships**:
- `master_template` (Many Sections → One MasterTemplate)

**Constraints**:
- `unique_together`: (master_template, name) - no duplicate section names per template

**Key Behaviors**:
- Ordered by order field, then name
- Deleting a MasterTemplate cascades to delete all sections

**Data-Driven Considerations**:
- Track which sections have most feedback discrepancies
- Analyze section completion rates (required vs optional)

**Example Usage**:
```python
# Add sections to a template
MasterTemplateSection.objects.create(
    master_template=template,
    name="Findings",
    placeholder_text="Describe all imaging findings systematically",
    order=1,
    is_required=True
)
```

---

### 4️⃣ Case

**Purpose**: Represents a teaching radiology case with patient info, clinical context, and expert interpretation.

**Location**: `backend/cases/models.py:128-273`

**Fields**:
- `title` (CharField): Admin-facing title
- `case_identifier` (CharField, unique, **auto-generated**): Human-readable ID
- `subspecialty` (CharField, choices): Medical subspecialty
- `modality` (CharField, choices): Imaging modality
- `difficulty` (CharField, choices): beginner, intermediate, advanced, expert
- `status` (CharField, choices): draft, published, archived
- `patient_age` (CharField, nullable): e.g., '5 years', '3 months'
- `patient_sex` (CharField, choices, nullable): Male, Female, Other, Unknown
- `clinical_history` (TextField): Patient background
- `key_findings` (TextField, nullable): Expert's key findings (semicolon-separated)
- `diagnosis` (TextField, nullable): Expert's final diagnosis
- `discussion` (TextField, nullable): Expert's teaching points
- `references` (TextField, nullable): URLs/citations
- `master_template` (ForeignKey → MasterTemplate, SET_NULL)
- `created_by` (ForeignKey → User, SET_NULL)
- `orthanc_study_uid` (CharField, nullable): DICOM StudyInstanceUID
- `published_at` (DateTimeField, nullable): Auto-set when published
- `created_at`, `updated_at` (DateTimeField, auto)

**Relationships**:
- `applied_expert_templates` (One Case → Many CaseTemplate, CASCADE)
- `reports` (One Case → Many Report, CASCADE)
- `viewed_by` (Many-to-Many with User through UserCaseView)

**Key Behaviors**:
- **Auto-generates case_identifier** on save using format: `{SUBSPECIALTY}-{MODALITY}-{YEAR}-{SEQUENCE}`
  - Example: `NR-MR-2025-0001`
  - Handles collisions with retry logic (models.py:260-271)
  - Falls back to UUID suffix if needed
- **Auto-sets published_at** when status changes to 'published'
- Ordered by most recent first

**Scalability Considerations**:
- ⚠️ **Case identifier generation** uses `.last()` which can be slow with many cases
  - Consider database sequence for production
  - Test under concurrent case creation
- Use `select_related('master_template', 'created_by')` for queries
- Use `prefetch_related('reports', 'applied_expert_templates')` when needed

**Data-Driven Considerations**:
- `key_findings` used for AI feedback context
- `diagnosis` compared against user reports
- Track view counts via `viewed_by` relationship
- Analyze case difficulty vs report accuracy

**Example Usage**:
```python
# Create a new case (identifier auto-generated)
case = Case.objects.create(
    title="Pneumothorax in 5yo",
    subspecialty="CH",  # Chest
    modality="XR",
    difficulty="intermediate",
    status="draft",
    patient_age="5 years",
    patient_sex="Male",
    clinical_history="Shortness of breath after fall",
    key_findings="right-sided pneumothorax;no rib fracture",
    diagnosis="Right pneumothorax",
    master_template=chest_xr_template,
    created_by=admin
)
# case_identifier will be auto-generated like: CH-XR-2025-0001

# Query with optimization
cases = Case.objects.filter(status='published') \
    .select_related('master_template', 'created_by') \
    .prefetch_related('reports')
```

---

### 5️⃣ CaseTemplate

**Purpose**: Expert-filled report content for a specific Case in a specific Language.

**Location**: `backend/cases/models.py:275-292`

**Fields**:
- `case` (ForeignKey → Case, CASCADE)
- `language` (ForeignKey → Language, PROTECT)
- `created_at`, `updated_at` (DateTimeField, auto)

**Relationships**:
- `section_contents` (One CaseTemplate → Many CaseTemplateSectionContent, CASCADE)

**Constraints**:
- `unique_together`: (case, language) - one expert template per case per language

**Key Behaviors**:
- Uses PROTECT for Language (can't delete language if templates exist)
- Deleting a Case cascades to delete associated CaseTemplates
- Property `section_contents_ordered` returns sections ordered by master_section__order

**Data-Driven Considerations**:
- Compare user reports against these expert templates
- Track which languages have most complete templates
- Analyze feedback quality by language availability

**Example Usage**:
```python
# Create expert template for a case
expert_template = CaseTemplate.objects.create(
    case=case,
    language=english
)

# Get ordered expert sections for comparison
expert_sections = expert_template.section_contents_ordered
```

---

### 6️⃣ CaseTemplateSectionContent

**Purpose**: The actual expert-written content for each section of a CaseTemplate.

**Location**: `backend/cases/models.py:294-316`

**Fields**:
- `case_template` (ForeignKey → CaseTemplate, CASCADE)
- `master_section` (ForeignKey → MasterTemplateSection, CASCADE)
- `content` (TextField): Expert's report text for this section
- `key_concepts_text` (TextField, nullable): Semicolon-separated key phrases for AI comparison

**Constraints**:
- `unique_together`: (case_template, master_section) - one content per section per template

**Key Behaviors**:
- Ordered by master_section__order
- Cascade deletes with CaseTemplate

**Data-Driven Considerations**:
- 🤖 **Critical for AI feedback**: `key_concepts_text` used in programmatic pre-analysis
- Content compared against user reports to identify discrepancies
- Track which key concepts users most commonly miss

**Example Usage**:
```python
# Add expert content to template
CaseTemplateSectionContent.objects.create(
    case_template=expert_template,
    master_section=findings_section,
    content="Right-sided pneumothorax measuring 2cm at apex...",
    key_concepts_text="pneumothorax;right-sided;apex measurement;no tension"
)

# Compare user content against expert
expert_content = CaseTemplateSectionContent.objects.get(
    case_template__case=case,
    case_template__language=english,
    master_section=findings_section
)
```

---

### 7️⃣ Report

**Purpose**: User-submitted diagnostic report with AI feedback and versioning support.

**Location**: `backend/cases/models.py:318-344`

**Fields**:
- `case` (ForeignKey → Case, CASCADE)
- `user` (ForeignKey → User, CASCADE)
- `structured_content` (JSONField, default=list): List of section dictionaries
- `ai_feedback_content` (JSONField, default=dict): AI-generated feedback
- `is_archived` (BooleanField, default=False): For report versioning
- `submitted_at`, `updated_at` (DateTimeField, auto)

**Relationships**:
- `ai_feedback_ratings` (One Report → Many AIFeedbackRating, CASCADE)

**Key Behaviors**:
- **Multiple reports per user/case allowed** (unique_together removed)
- Most recent non-archived report is considered "active"
- Ordered by most recent first
- Deleting a Case or User cascades to delete reports

**JSONField Structures**:

`structured_content` format:
```python
[
    {
        "master_template_section_id": 1,
        "section_name": "Findings",
        "section_order": 1,
        "content": "User's findings text..."
    },
    {
        "master_template_section_id": 2,
        "section_name": "Impression",
        "section_order": 2,
        "content": "User's impression..."
    }
]
```

`ai_feedback_content` format:
```python
{
    "raw_feedback": "Full LLM response text...",
    "section_feedback": [
        {
            "section_name": "Findings",
            "severity": "Critical",  # or "Moderate", "Consistent"
            "reason": "You missed the pneumothorax..."
        }
    ],
    "critical_discrepancies": ["Missed right pneumothorax"],
    "non_critical_discrepancies": ["Did not mention rib counting"],
    "overall_assessment": "You missed the primary diagnosis."
}
```

**Scalability Considerations**:
- ⚠️ JSONField queries can be slow - avoid complex filtering on JSON content
- Consider denormalizing frequently queried fields
- Archive old reports to maintain query performance

**Data-Driven Considerations**:
- 📊 **Core analytics entity**: Track user progress over time
- Compare archived vs current reports to measure improvement
- Analyze ai_feedback_content for common discrepancy patterns
- Monitor report submission trends

**Example Usage**:
```python
# Create user report
report = Report.objects.create(
    case=case,
    user=user,
    structured_content=[
        {
            "master_template_section_id": 1,
            "section_name": "Findings",
            "section_order": 1,
            "content": "Lungs are clear. Heart size normal."
        }
    ]
)

# Get user's current (non-archived) report for a case
current_report = Report.objects.filter(
    case=case,
    user=user,
    is_archived=False
).first()

# Archive old report when user submits new one
old_report.is_archived = True
old_report.save()
```

---

### 8️⃣ UserCaseView

**Purpose**: Tracks which users have viewed which cases for analytics and "viewed" status.

**Location**: `backend/cases/models.py:346-356`

**Fields**:
- `user` (ForeignKey → User, CASCADE)
- `case` (ForeignKey → Case, CASCADE)
- `timestamp` (DateTimeField, auto)

**Constraints**:
- `unique_together`: (user, case) - prevents duplicate view records

**Key Behaviors**:
- Ordered by most recent first
- CASCADE deletes with User or Case
- Automatically populated through `viewed_by` ManyToMany on Case

**Data-Driven Considerations**:
- 📊 Track case engagement and popularity
- Calculate view-to-report conversion rates
- Identify cases users view but don't complete
- Time-based analytics (views over time)

**Example Usage**:
```python
# Mark case as viewed
case.viewed_by.add(user)

# Get all cases viewed by user
viewed_cases = user.viewed_cases.all()

# Analytics: Cases with most views
popular_cases = Case.objects.annotate(
    view_count=Count('viewed_by')
).order_by('-view_count')
```

---

### 9️⃣ AIFeedbackRating

**Purpose**: Collects user ratings on AI feedback quality for continuous improvement.

**Location**: `backend/cases/models.py:358-392`

**Fields**:
- `report` (ForeignKey → Report, CASCADE)
- `user` (ForeignKey → User, CASCADE)
- `star_rating` (IntegerField, choices=1-5): User's quality rating
- `comment` (TextField, nullable): Optional feedback explanation
- `rated_at` (DateTimeField, auto)

**Constraints**:
- `unique_together`: (report, user) - one rating per user per report

**Key Behaviors**:
- Ordered by most recent first
- CASCADE deletes with Report or User
- Ratings range 1-5 stars

**Data-Driven Considerations**:
- 📊 **Critical for AI quality monitoring**
- Calculate average rating by case difficulty
- Identify low-rated feedback for prompt improvement
- Track rating trends over time (after prompt changes)
- Analyze comments for common themes

**Example Usage**:
```python
# User rates AI feedback
AIFeedbackRating.objects.create(
    report=report,
    user=user,
    star_rating=4,
    comment="Very helpful but could be more specific about findings"
)

# Analytics: Average AI feedback quality
from django.db.models import Avg
avg_rating = AIFeedbackRating.objects.aggregate(
    Avg('star_rating')
)['star_rating__avg']

# Find low-rated feedback for review
low_rated = AIFeedbackRating.objects.filter(
    star_rating__lte=2
).select_related('report__case')
```

---

## 🔄 Data Flow Examples

### 1️⃣ Creating a Complete Teaching Case

```python
# Step 1: Create or select template structure
template = MasterTemplate.objects.get(name="CT Brain Basic")

# Step 2: Create case
case = Case.objects.create(
    title="Epidural Hematoma",
    subspecialty="NR",
    modality="CT",
    difficulty="intermediate",
    clinical_history="Head trauma after fall",
    key_findings="lens-shaped hyperdensity;right temporal;mass effect",
    diagnosis="Right temporal epidural hematoma",
    master_template=template,
    orthanc_study_uid="1.2.840.113619.2.134.1"
)

# Step 3: Add expert template content
expert_template = CaseTemplate.objects.create(
    case=case,
    language=Language.objects.get(code='en')
)

for section in template.sections.all():
    CaseTemplateSectionContent.objects.create(
        case_template=expert_template,
        master_section=section,
        content="[Expert's detailed content for this section]",
        key_concepts_text="key1;key2;key3"
    )

# Step 4: Publish case
case.status = 'published'
case.save()  # Auto-sets published_at
```

### 2️⃣ User Submitting Report & Receiving AI Feedback

```python
# Step 1: User submits report
report = Report.objects.create(
    case=case,
    user=user,
    structured_content=[
        {"master_template_section_id": 1, "section_name": "Findings",
         "content": "User's findings..."},
        {"master_template_section_id": 2, "section_name": "Impression",
         "content": "User's impression..."}
    ]
)

# Step 2: Generate AI feedback (via API endpoint)
# - Retrieves expert template
# - Performs programmatic pre-analysis (utils.generate_report_comparison_summary)
# - Calls Gemini API (llm_feedback_service.get_feedback_from_llm)
# - Parses and structures feedback

report.ai_feedback_content = {
    "raw_feedback": "LLM response...",
    "section_feedback": [...],
    "critical_discrepancies": [...],
    "non_critical_discrepancies": [...]
}
report.save()

# Step 3: User rates feedback
AIFeedbackRating.objects.create(
    report=report,
    user=user,
    star_rating=5,
    comment="Very helpful!"
)
```

### 3️⃣ Analytics Query Examples

```python
# User progress: Compare first vs recent reports
user_reports = Report.objects.filter(user=user).order_by('submitted_at')
first_report = user_reports.first()
recent_report = user_reports.last()

# Case popularity
popular_cases = Case.objects.annotate(
    view_count=Count('viewed_by'),
    report_count=Count('reports')
).order_by('-view_count')[:10]

# AI feedback quality by difficulty
from django.db.models import Avg
quality_by_difficulty = AIFeedbackRating.objects.values(
    'report__case__difficulty'
).annotate(
    avg_rating=Avg('star_rating'),
    rating_count=Count('id')
)

# Cases with low completion rate
cases_with_metrics = Case.objects.annotate(
    views=Count('viewed_by', distinct=True),
    reports=Count('reports', distinct=True)
).filter(views__gt=0).annotate(
    completion_rate=F('reports') * 100.0 / F('views')
).filter(completion_rate__lt=50)
```

---

## 🔍 Query Optimization Patterns

### Always Use select_related For:
```python
# Case with template and creator
Case.objects.select_related('master_template', 'created_by')

# Report with case and user
Report.objects.select_related('case', 'user')

# CaseTemplate with language and case
CaseTemplate.objects.select_related('language', 'case')
```

### Always Use prefetch_related For:
```python
# Case with all expert templates and their sections
Case.objects.prefetch_related(
    'applied_expert_templates',
    'applied_expert_templates__section_contents',
    'applied_expert_templates__section_contents__master_section'
)

# Case with all reports and their ratings
Case.objects.prefetch_related(
    'reports',
    'reports__ai_feedback_ratings'
)
```

### Complex Optimization Example:
```python
# Get published cases with full template, expert content, and metrics
cases = Case.objects.filter(status='published') \
    .select_related('master_template', 'created_by') \
    .prefetch_related(
        'master_template__sections',
        'applied_expert_templates__language',
        'applied_expert_templates__section_contents__master_section'
    ) \
    .annotate(
        view_count=Count('viewed_by', distinct=True),
        report_count=Count('reports', distinct=True)
    )
```

---

## ⚠️ Common Pitfalls & Solutions

### Pitfall 1: Case Identifier Collisions
**Problem**: Concurrent case creation can cause identifier collisions.
**Solution**: Use database-level sequence or locking for production (models.py:213-273 handles this with retry logic).

### Pitfall 2: Orphaned Reports After Template Changes
**Problem**: Changing MasterTemplate sections can make existing reports reference non-existent sections.
**Solution**: Use migrations carefully; consider data migration to update report structured_content.

### Pitfall 3: N+1 Queries on Nested Relationships
**Problem**: Accessing case.applied_expert_templates.all()[0].section_contents.all() in loop.
**Solution**: Use prefetch_related as shown above.

### Pitfall 4: Large JSON Fields Slow Queries
**Problem**: Filtering or searching within ai_feedback_content JSONField.
**Solution**: Denormalize frequently queried fields or use PostgreSQL JSON indexing.

### Pitfall 5: Cascading Deletes Unintended
**Problem**: Deleting a Case removes all Reports and AIFeedbackRatings.
**Solution**: Consider soft deletes (is_deleted flag) for Cases with user data.

---

## 📊 Scalability Recommendations

### Short-term (Current Scale):
- ✅ Use select_related/prefetch_related consistently
- ✅ Add database indexes on frequently filtered fields:
  - `Case.status`
  - `Case.case_identifier`
  - `Report.is_archived`
  - `Report.submitted_at`

### Medium-term (Growing Data):
- 🔄 Implement database sequence for case_identifier generation
- 🔄 Archive old reports (soft delete or separate table)
- 🔄 Add caching for published cases and templates
- 🔄 Consider read replicas for analytics queries

### Long-term (High Scale):
- ⚡ Partition reports table by date
- ⚡ Move ai_feedback_content to separate table/storage
- ⚡ Implement materialized views for analytics
- ⚡ Consider NoSQL for high-volume analytics data

---

## 📚 Related Documentation

- @.claude/docs/RISK_ASSESSMENT.md - Assess impact before model changes
- @.claude/docs/WORKFLOWS.md - Safe database migration workflows
- @.claude/docs/TESTING.md - How to test model changes
- @.claude/docs/MONITORING.md - Track model-related metrics

---

**💡 Best Practice**: Before modifying any model, complete a risk assessment from @.claude/docs/RISK_ASSESSMENT.md to understand cascading effects and data implications.
