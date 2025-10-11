# 🔄 Common Development Workflows

## 🎯 Overview

This guide provides step-by-step workflows for common development tasks with integrated risk assessment at each critical step. Following these workflows ensures data integrity, scalability, and best practices compliance.

---

## ⚠️ Mandatory First Step: Risk Assessment

**Before starting ANY workflow that involves code changes**, complete a risk assessment:

1. Read @.claude/docs/RISK_ASSESSMENT.md
2. Use the risk assessment template
3. Identify potential impacts on data, performance, and users
4. Document mitigation strategies

**🔴 This is not optional!** Risk assessment prevents data loss, performance degradation, and user-facing bugs.

---

## 1️⃣ Adding a New Database Field

### Scenario
Adding a new optional field to an existing model.

### Step-by-Step Workflow

#### Step 1: Risk Assessment ⚠️
```markdown
## RISK ASSESSMENT: Add [field_name] to [Model]

### Direct Impact
- Model affected: [ModelName]
- Files to modify: models.py, serializers.py
- Migration required: Yes (AddField)

### Data-Driven Implications
- Historical data: Will have NULL/blank values
- Analytics queries: Existing queries unaffected (optional field)
- AI feedback: Not used in current prompts

### Scalability Impact
- Database performance: Minimal (one nullable column)
- Migration time: < 1 second for current data volume

### Risk Level: 🟢 LOW

### Mitigation
- Use null=True, blank=True for backward compatibility
- Test migration on copy of production data
- Update serializer to include field
```

#### Step 2: Update Model

```python
# backend/cases/models.py

class Case(models.Model):
    # ... existing fields ...

    # NEW FIELD
    patient_weight = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Patient weight (e.g., '25 kg', '55 lbs')"
    )
```

**💡 Best Practice**: Always use `blank=True, null=True` for new fields to ensure backward compatibility.

#### Step 3: Create Migration

```bash
cd backend
python manage.py makemigrations --name add_patient_weight_to_case
```

**Review the migration file** before applying:
```bash
cat cases/migrations/0XXX_add_patient_weight_to_case.py
```

Verify it's a simple `AddField` operation.

#### Step 4: Test Migration (Development)

```bash
# Create database backup first (production)
# pg_dump globalpeds_db > backup_before_migration.sql

# Apply migration
python manage.py migrate

# Verify field exists
python manage.py shell
>>> from cases.models import Case
>>> Case._meta.get_field('patient_weight')
<django.db.models.fields.CharField: patient_weight>

# Test creating case with new field
>>> case = Case.objects.first()
>>> case.patient_weight = '25 kg'
>>> case.save()
>>> Case.objects.get(id=case.id).patient_weight
'25 kg'

# Test existing cases (should have NULL)
>>> Case.objects.filter(patient_weight__isnull=True).count()
```

#### Step 5: Update Serializer

```python
# backend/cases/serializers.py

class CaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Case
        fields = [
            # ... existing fields ...
            'patient_weight',  # ADD NEW FIELD
        ]
```

#### Step 6: Test API

```bash
# Test GET (should include new field)
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/cases/1/

# Test POST with new field
curl -X POST -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"title": "Test", "patient_weight": "30 kg", ...}' \
  http://localhost:8000/api/cases/
```

#### Step 7: Update Tests

```python
# backend/cases/tests/test_models.py

def test_case_with_patient_weight(self):
    """Test creating case with patient_weight"""
    case = Case.objects.create(
        title='Test Case',
        patient_weight='25 kg',
        # ... other required fields ...
    )

    self.assertEqual(case.patient_weight, '25 kg')

def test_case_without_patient_weight(self):
    """Test that patient_weight is optional"""
    case = Case.objects.create(
        title='Test Case',
        # ... other required fields ...
        # patient_weight not provided
    )

    self.assertIsNone(case.patient_weight)
```

#### Step 8: Update Frontend (If Needed)

```javascript
// frontend/admin/add-case.html or admin-case-edit.js

// Add input field to form
<div class="form-group">
    <label for="patient_weight">Patient Weight (Optional)</label>
    <input type="text" id="patient_weight"
           placeholder="e.g., 25 kg" class="form-control">
</div>

// Update form submission to include new field
const caseData = {
    // ... existing fields ...
    patient_weight: document.getElementById('patient_weight').value || null
};
```

#### Step 9: Documentation

Update @.claude/docs/DATA_MODELS.md if the field is significant:

```markdown
### Case Model

**New Field (Added 2025-XX-XX)**:
- `patient_weight` (CharField, optional): Patient's weight for clinical context
```

---

## 2️⃣ Modifying AI Feedback Prompt

### Scenario
Updating the LLM prompt to improve feedback quality.

### Step-by-Step Workflow

#### Step 1: Risk Assessment ⚠️
```markdown
## RISK ASSESSMENT: Update AI feedback prompt

### Direct Impact
- File to modify: llm_feedback_service.py
- Affects: All future AI feedback generation
- Does NOT affect: Historical feedback (already generated)

### Data-Driven Implications
- AI feedback quality may improve or degrade
- Rating metrics may change (track before/after)
- Users will notice different feedback style

### Risk Level: 🟡 MEDIUM

### Mitigation
1. Save baseline rating metrics before change
2. Keep old prompt in comments for rollback
3. Monitor AIFeedbackRating for 7 days post-deployment
4. Test with sample reports before deploying
```

#### Step 2: Establish Baseline Metrics

```python
# Run in Django shell BEFORE making changes
from django.db.models import Avg
from django.utils import timezone
from datetime import timedelta

last_30_days = timezone.now() - timedelta(days=30)

baseline_rating = AIFeedbackRating.objects.filter(
    rated_at__gte=last_30_days
).aggregate(Avg('star_rating'))['star_rating__avg']

print(f"Baseline 30-day average rating: {baseline_rating:.2f}/5.00")
# Save this value for comparison!
```

#### Step 3: Comment Out Old Prompt

```python
# backend/cases/llm_feedback_service.py

def get_feedback_from_llm(...):
    # OLD PROMPT (2025-01-15 to 2025-XX-XX) - Baseline Rating: 4.2/5.0
    # prompt = f"""
    # [old prompt text...]
    # """

    # NEW PROMPT (2025-XX-XX onward) - Testing improved specificity
    prompt = f"""
    [new improved prompt...]
    """
```

**💡 Why?** Easy rollback if new prompt degrades quality.

#### Step 4: Test Locally with Sample Reports

```bash
cd backend/cases
python llm_feedback_service.py
```

Review output for:
- Format matches expected structure
- Tone is appropriate
- Feedback is specific and actionable

#### Step 5: Test with Real Reports (Staging)

```python
# In Django shell
from cases.models import Report
from cases.llm_feedback_service import get_feedback_from_llm
from cases.utils import generate_report_comparison_summary

# Get a recent report to test
test_report = Report.objects.filter(is_archived=False).first()

# Regenerate feedback with new prompt
user_sections = test_report.structured_content
expert_template = test_report.case.applied_expert_templates.first()
expert_sections = [
    {
        'master_section_id': section.master_section_id,
        'content': section.content,
        'key_concepts_text': section.key_concepts_text,
        'section_name': section.master_section.name
    }
    for section in expert_template.section_contents.all()
]

pre_analysis = generate_report_comparison_summary(
    user_sections,
    expert_sections,
    test_report.case.diagnosis
)

new_feedback = get_feedback_from_llm(
    user_sections,
    expert_sections,
    pre_analysis,
    case_identifier_for_llm=test_report.case.case_identifier,
    # ... other parameters ...
)

print(new_feedback)
# Manually review: Is this better than old feedback?
```

#### Step 6: Deploy & Monitor

After deployment, monitor for **7 days**:

```python
# Daily monitoring script
from django.db.models import Avg, Count
from datetime import timedelta

def monitor_ai_quality():
    last_7_days = timezone.now() - timedelta(days=7)

    recent_metrics = AIFeedbackRating.objects.filter(
        rated_at__gte=last_7_days
    ).aggregate(
        avg_rating=Avg('star_rating'),
        total_ratings=Count('id')
    )

    print(f"Last 7 days: {recent_metrics['avg_rating']:.2f}/5.00")
    print(f"Total ratings: {recent_metrics['total_ratings']}")

    # Alert if dropped significantly
    if recent_metrics['avg_rating'] < baseline_rating - 0.3:
        print("⚠️ ALERT: Rating dropped significantly!")
        # Consider rollback
```

#### Step 7: Document Results

```markdown
# Prompt Change Log

## 2025-XX-XX: Improved Specificity in Discrepancy Descriptions

**Changes**:
- Added instruction to use "You..." addressing
- Requested 15-word max explanations
- Clarified section severity assessment format

**Results** (7-day post-deployment):
- Baseline rating: 4.2/5.0
- New rating: 4.4/5.0 ✅ (+0.2 improvement)
- User comments: Mentioned "more specific" 8 times

**Decision**: Keep new prompt.
```

---

## 3️⃣ Creating a New Teaching Case

### Scenario
Adding a complete case with DICOM images, expert template, and metadata.

### Step-by-Step Workflow

#### Step 1: Prepare DICOM Images

1. **Upload to Orthanc**:
   - Access Orthanc web interface (usually http://localhost:8042)
   - Upload DICOM files
   - Note the `StudyInstanceUID`

2. **Verify in Orthanc**:
   - Confirm images display correctly
   - Test with OHIF Viewer

#### Step 2: Create Case via Admin Panel

1. Navigate to `/admin/cases/case/add/`
2. Fill in required fields:
   - **Title**: Internal admin title
   - **Subspecialty**: Select appropriate option
   - **Modality**: Match DICOM modality
   - **Difficulty**: Target learner level
   - **Status**: Start with `draft`
   - **Clinical History**: Patient presentation
   - **Key Findings**: Semicolon-separated (for AI)
   - **Diagnosis**: Final expert diagnosis
   - **Discussion**: Teaching points
   - **References**: URLs or citations
   - **Orthanc Study UID**: From Step 1
   - **Master Template**: Select appropriate report structure

3. **Save** - `case_identifier` auto-generates

#### Step 3: Create Expert Template

1. Navigate to `/admin/cases/casetemplate/add/`
2. Select:
   - **Case**: The case you just created
   - **Language**: Primary language (e.g., English)
3. Save

#### Step 4: Fill Expert Template Sections

1. Navigate to the CaseTemplate you created
2. Add Section Content for each section:
   - **Master Section**: Select from template (e.g., "Findings")
   - **Content**: Write expert interpretation
   - **Key Concepts**: Semicolon-separated key phrases
     - Example: `pneumothorax;right-sided;2cm at apex;no tension`
3. Repeat for all required sections

**💡 Key Concepts Tips**:
- Use specific medical terms
- Separate with semicolons (no spaces after)
- Include negatives (e.g., "no effusion")
- Used by AI for report comparison

#### Step 5: Review & Publish

1. **Preview** the case as if you're a learner:
   - Can DICOM images load?
   - Is clinical history clear?
   - Are instructions understandable?

2. **Test Report Submission**:
   - Create test user account
   - View case
   - Submit test report
   - Generate AI feedback
   - Verify feedback quality

3. **Publish**:
   - Change status to `published`
   - `published_at` timestamp auto-sets
   - Case now visible to learners

#### Step 6: Monitor Engagement

After publishing, track metrics (see @.claude/docs/MONITORING.md):
- View count
- Report submission count
- AI feedback ratings for this case
- Time to complete reports

---

## 4️⃣ Debugging AI Feedback Issues

### Scenario
Users report AI feedback is unhelpful or incorrect.

### Step-by-Step Workflow

#### Step 1: Gather Data

```python
# Get the problematic report
report = Report.objects.get(id=<report_id>)

# Check AI feedback content
print("AI Feedback:")
print(report.ai_feedback_content.get('raw_feedback', 'NO FEEDBACK'))

# Check rating (if exists)
ratings = report.ai_feedback_ratings.all()
for rating in ratings:
    print(f"Rating: {rating.star_rating}/5")
    print(f"Comment: {rating.comment}")

# Check programmatic pre-analysis
from cases.utils import generate_report_comparison_summary

user_sections = report.structured_content
expert_template = report.case.applied_expert_templates.first()

if expert_template:
    expert_sections = [...]  # Format expert sections

    pre_analysis = generate_report_comparison_summary(
        user_sections,
        expert_sections,
        report.case.diagnosis
    )

    import json
    print("Pre-Analysis:")
    print(json.dumps(pre_analysis, indent=2))
```

#### Step 2: Verify Environment

```python
# Check Gemini API key loaded
import os
print(f"GEMINI_API_KEY loaded: {'Yes' if os.environ.get('GEMINI_API_KEY') else 'No'}")

# Check LLM service configuration
from cases.llm_feedback_service import IS_GEMINI_CONFIGURED
print(f"Gemini configured: {IS_GEMINI_CONFIGURED}")

# Check rate limiting
from cases.llm_feedback_service import API_CALL_HISTORY
print(f"Recent API calls: {len(API_CALL_HISTORY)}")
```

#### Step 3: Review Input Data Quality

**Common Issues**:
1. **Missing Expert Template**: Case has no CaseTemplate
2. **Empty Key Concepts**: Expert sections missing `key_concepts_text`
3. **Malformed Report**: User report `structured_content` invalid
4. **Missing Case Context**: `key_findings` or `diagnosis` empty

```python
# Verify expert template exists
if not report.case.applied_expert_templates.exists():
    print("⚠️ NO EXPERT TEMPLATE for this case!")

# Verify key concepts
for section in expert_template.section_contents.all():
    if not section.key_concepts_text:
        print(f"⚠️ Missing key_concepts for section: {section.master_section.name}")

# Verify case has diagnosis
if not report.case.diagnosis:
    print("⚠️ Case missing diagnosis!")
```

#### Step 4: Test Manually

```python
# Manually call LLM service with debug logging enabled
# Uncomment line 320 in llm_feedback_service.py:
# logger.debug(f"Full prompt: {prompt}")

from cases.llm_feedback_service import get_feedback_from_llm

feedback = get_feedback_from_llm(
    user_sections,
    expert_sections,
    pre_analysis,
    case_identifier_for_llm=report.case.case_identifier,
    case_patient_age=report.case.patient_age,
    case_patient_sex=report.case.patient_sex,
    case_clinical_history=report.case.clinical_history,
    case_expert_key_findings=report.case.key_findings,
    case_expert_diagnosis=report.case.diagnosis,
    case_expert_discussion=report.case.discussion,
    case_difficulty=report.case.difficulty
)

print(feedback)
# Review: Does feedback make sense?
```

#### Step 5: Identify Root Cause

Common root causes:
1. **Prompt issue**: LLM not following format
2. **Input issue**: Missing/malformed data
3. **API issue**: Rate limiting, errors
4. **Parsing issue**: Feedback not parsed correctly

#### Step 6: Fix & Verify

After fixing, regenerate feedback for test cases and compare before/after.

---

## 5️⃣ Database Migration (Complex)

### Scenario
Renaming a field or changing field type (breaking change).

### Step-by-Step Workflow

#### Step 1: Risk Assessment ⚠️

**🔴 HIGH RISK** - Requires data migration and coordination with frontend.

```markdown
## RISK ASSESSMENT: Rename Case.patient_age to patient_age_text

### Breaking Changes
- API response field name changes
- Frontend must update to use new field name
- Database column renamed
- Existing code must be updated

### Risk Level: 🔴 HIGH

### Mitigation
1. Create data migration to preserve data
2. Update serializer with both fields temporarily (for rollback)
3. Update frontend before deploying backend
4. Test thoroughly in staging
5. Plan rollback procedure
```

#### Step 2: Create Migration

```bash
python manage.py makemigrations --name rename_patient_age
```

**Edit migration to preserve data**:

```python
# cases/migrations/0XXX_rename_patient_age.py

from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('cases', '0XXX_previous_migration'),
    ]

    operations = [
        # Rename field
        migrations.RenameField(
            model_name='case',
            old_name='patient_age',
            new_name='patient_age_text',
        ),
    ]
```

**⚠️ IMPORTANT**: `RenameField` preserves data automatically!

#### Step 3: Test Migration (Local)

```bash
# Backup database
pg_dump globalpeds_db > backup_before_rename.sql

# Apply migration
python manage.py migrate

# Verify data preserved
python manage.py shell
>>> from cases.models import Case
>>> Case.objects.first().patient_age_text  # Should have data
```

#### Step 4: Update All Code References

**Search for old field name**:
```bash
cd backend
grep -r "patient_age" --include="*.py" --exclude-dir=migrations
```

Update:
- Serializers
- Views
- Utils
- Tests

#### Step 5: Update Frontend

```bash
cd frontend
grep -r "patient_age" --include="*.js" --include="*.html"
```

Update all references to use `patient_age_text`.

#### Step 6: Coordinated Deployment

**Recommended Order**:
1. Deploy frontend first (tolerant of both field names)
2. Deploy backend with migration
3. Verify system works
4. Remove old field handling from frontend (cleanup)

---

## 📚 Related Documentation

- @.claude/docs/RISK_ASSESSMENT.md - Complete risk assessment framework
- @.claude/docs/DATA_MODELS.md - Understanding model relationships
- @.claude/docs/TESTING.md - Testing your changes
- @.claude/docs/MONITORING.md - Post-deployment monitoring

---

**💡 Remember**: Every workflow starts with risk assessment. Taking 10 minutes to plan prevents hours of debugging!
