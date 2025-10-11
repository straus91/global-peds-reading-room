# 🤖 AI Features Roadmap

**Project**: Global Peds Reading Room
**Current AI Quality**: 7.5/10
**Target**: 9-10/10
**Last Updated**: 2025-10-11

> Phased roadmap to transform AI feedback from good to exceptional through data-driven improvements and selective agentic features.

**Source**: Distilled from `further-ai.txt` with actionable implementation steps.

---

## 📊 Current State Assessment

### ✅ What's Working Well (Keep These!)

- **Hybrid Approach**: Programmatic pre-analysis + LLM (cost-effective)
- **Rich Context**: Demographics, clinical history, expert findings, key concepts
- **Security**: Input sanitization, rate limiting, atomic transactions
- **Structured Output**: Color-coded severity (Critical/Moderate/Consistent)
- **Educational Focus**: Section-level feedback, non-spoiling case IDs

**Current Annual Cost**: ~$200/year (10k feedbacks)

### 🔧 Key Missing Elements

| Missing Element | Current Problem | Impact |
|----------------|----------------|--------|
| **Feedback Quality Metrics** | Collect ratings but don't act on them | Can't improve systematically |
| **Prompt Versioning** | Hardcoded prompts, risky to change | No A/B testing, difficult rollback |
| **Learning Analytics** | No user progression tracking | Can't personalize or prove effectiveness |
| **Scalability** | Synchronous, no caching | Will struggle at 10× growth |
| **Outcome Measurement** | No learning improvement metrics | Can't prove platform works |

---

## 🗺️ Phased Roadmap Overview

```
┌─────────────────────────────────────────────────────────┐
│ Phase 1: Foundation (2 months) - Data-driven iteration │
├─────────────────────────────────────────────────────────┤
│ Phase 2: Interactive Tutoring (2 months) - Agentic AI  │
├─────────────────────────────────────────────────────────┤
│ Phase 3A: Visual Verification (2 months) - VLM         │
│ Phase 3B: Literature (Optional, 2 months)              │
├─────────────────────────────────────────────────────────┤
│ Phase 4: Learning Analytics (3 months) - Outcomes      │
├─────────────────────────────────────────────────────────┤
│ Phase 5: Scale & Optimize (3 months) - Production      │
└─────────────────────────────────────────────────────────┘

Total Timeline: 12 months (10 months if skipping Phase 3B)
```

---

## 📋 PHASE 1: Foundation Improvements

**Timeline**: Months 1-2
**Cost**: $0 (dev time only)
**Risk**: Low
**Priority**: ✅✅✅ **MUST DO** - Foundation for all future improvements

### 🎯 Goals

1. Enable data-driven prompt iteration
2. Track AI system costs and quality
3. Improve efficiency through caching
4. Establish baseline metrics

### ✅ Feature 1.1: Structured Feedback Categories

**Problem**: Currently only collect star ratings (1-5), no detailed quality metrics.

**Solution**: Add structured feedback tracking.

**Implementation**:

```python
# New model: backend/cases/models.py
class AIFeedbackRating(models.Model):
    # Existing fields
    star_rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField(blank=True, null=True)

    # NEW: Add structured categories
    accuracy_rating = models.IntegerField(
        choices=[(i, i) for i in range(1, 6)],
        null=True,
        blank=True,
        help_text="How accurate was the AI feedback?"
    )
    helpfulness_rating = models.IntegerField(
        choices=[(i, i) for i in range(1, 6)],
        null=True,
        blank=True,
        help_text="How helpful for learning?"
    )
    actionability_rating = models.IntegerField(
        choices=[(i, i) for i in range(1, 6)],
        null=True,
        blank=True,
        help_text="How actionable were suggestions?"
    )

    # Track false positives
    flagged_false_positive = models.BooleanField(
        default=False,
        help_text="Did AI incorrectly flag a discrepancy?"
    )
    false_positive_description = models.TextField(
        blank=True,
        null=True
    )
```

**Migration**: `python manage.py makemigrations --name add_structured_feedback`

**Analytics Query**:

```python
# Get detailed quality metrics
from django.db.models import Avg
from cases.models import AIFeedbackRating

metrics = AIFeedbackRating.objects.aggregate(
    avg_overall=Avg('star_rating'),
    avg_accuracy=Avg('accuracy_rating'),
    avg_helpfulness=Avg('helpfulness_rating'),
    avg_actionability=Avg('actionability_rating')
)

false_positive_rate = AIFeedbackRating.objects.filter(
    flagged_false_positive=True
).count() / AIFeedbackRating.objects.count()
```

**Testing**: Use `AI_ITERATION_WORKFLOW.md` methodology

---

### ✅ Feature 1.2: Prompt Version Management

**Problem**: Prompts hardcoded, risky to iterate, can't A/B test or rollback.

**Solution**: Database-backed prompt versioning with performance tracking.

**Implementation**:

```python
# New model: backend/cases/models.py
class AIPromptVersion(models.Model):
    version = models.CharField(max_length=50, unique=True)
    description = models.TextField()
    prompt_template = models.TextField(
        help_text="Prompt template with placeholders"
    )
    model_name = models.CharField(
        max_length=100,
        default="gemini-2.5-flash"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=False)

    # Performance metrics
    avg_rating = models.FloatField(null=True, blank=True)
    total_feedbacks = models.IntegerField(default=0)
    total_ratings = models.IntegerField(default=0)
    avg_tokens = models.IntegerField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

# Update Report model to track which prompt version was used
class Report(models.Model):
    # Existing fields...

    # NEW: Track prompt version
    ai_prompt_version = models.CharField(
        max_length=50,
        null=True,
        blank=True
    )
```

**Usage**:

```python
# In llm_feedback_service.py
def get_active_prompt_version():
    """Get currently active prompt version"""
    return AIPromptVersion.objects.filter(is_active=True).first()

def get_feedback_from_llm(...):
    prompt_version = get_active_prompt_version()

    if prompt_version:
        prompt = prompt_version.prompt_template.format(
            # ... all the context variables
        )
    else:
        # Fallback to hardcoded prompt
        prompt = """..."""

    # ... generate feedback ...

    # Save prompt version used
    report.ai_prompt_version = prompt_version.version
    report.save()
```

**A/B Testing**:

```python
# Activate new prompt version for 50% of users
import random

def get_prompt_version_for_user(user):
    if random.random() < 0.5:
        return AIPromptVersion.objects.get(version="v2.0")
    else:
        return AIPromptVersion.objects.get(version="v1.0")
```

**Performance Comparison**:

```python
# Compare prompt versions
from cases.models import Report, AIFeedbackRating

v1_reports = Report.objects.filter(ai_prompt_version="v1.0")
v2_reports = Report.objects.filter(ai_prompt_version="v2.0")

v1_avg = AIFeedbackRating.objects.filter(
    report__in=v1_reports
).aggregate(Avg('star_rating'))['star_rating__avg']

v2_avg = AIFeedbackRating.objects.filter(
    report__in=v2_reports
).aggregate(Avg('star_rating'))['star_rating__avg']

print(f"v1.0: {v1_avg:.2f}/5.00")
print(f"v2.0: {v2_avg:.2f}/5.00")
print(f"Improvement: {v2_avg - v1_avg:+.2f} points")
```

---

### ✅ Feature 1.3: Report Caching

**Problem**: Identical reports regenerate feedback, wasting API costs.

**Solution**: Hash reports and cache feedback.

**Implementation**:

```python
import hashlib
import json

def hash_report(structured_content, case_id):
    """Generate unique hash for report content"""
    content_str = json.dumps(structured_content, sort_keys=True)
    combined = f"{case_id}:{content_str}"
    return hashlib.md5(combined.encode()).hexdigest()

# Add to Report model
class Report(models.Model):
    # Existing fields...

    # NEW: Content hash for caching
    content_hash = models.CharField(
        max_length=32,
        db_index=True,
        null=True,
        blank=True
    )

# In views.py (AIReportFeedbackView)
def generate_feedback(report):
    # Compute hash
    content_hash = hash_report(
        report.structured_content,
        report.case_id
    )
    report.content_hash = content_hash
    report.save()

    # Check for cached feedback
    cached_report = Report.objects.filter(
        content_hash=content_hash,
        case=report.case
    ).exclude(
        id=report.id
    ).exclude(
        ai_feedback_content={}
    ).first()

    if cached_report:
        # Use cached feedback
        report.ai_feedback_content = cached_report.ai_feedback_content
        report.save()
        logger.info(f"Used cached feedback for report {report.id}")
        return report.ai_feedback_content

    # Generate new feedback...
    # (existing logic)
```

**Metrics**:

```python
# Track cache hit rate
total_feedbacks = Report.objects.exclude(ai_feedback_content={}).count()
cached_feedbacks = Report.objects.filter(
    content_hash__in=Report.objects.values('content_hash').annotate(
        count=Count('id')
    ).filter(count__gt=1).values_list('content_hash', flat=True)
).count()

cache_hit_rate = cached_feedbacks / total_feedbacks if total_feedbacks > 0 else 0
print(f"Cache hit rate: {cache_hit_rate:.1%}")
```

---

### ✅ Feature 1.4: Token Usage Logging

**Problem**: No visibility into AI costs per case/subspecialty.

**Solution**: Track token usage and costs.

**Implementation**:

```python
# Update Report model
class Report(models.Model):
    # Existing fields...

    # NEW: Token tracking
    ai_tokens_used = models.IntegerField(null=True, blank=True)
    ai_cost_estimate = models.DecimalField(
        max_digits=6,
        decimal_places=4,
        null=True,
        blank=True
    )

# In llm_feedback_service.py
def get_feedback_from_llm(...):
    # ... existing code ...

    response = model.generate_content(prompt)

    # Estimate tokens (rough approximation)
    tokens_used = len(response.text) // 4  # ~4 chars per token
    cost_per_1k_tokens = 0.00025  # Gemini 2.5 Flash pricing
    cost_estimate = (tokens_used / 1000) * cost_per_1k_tokens

    # Log
    logger.info(
        f"AI feedback - Case: {case_identifier_for_llm}, "
        f"Tokens: ~{tokens_used}, Cost: ${cost_estimate:.4f}"
    )

    return response.text, tokens_used, cost_estimate
```

**Cost Dashboard**:

```python
# Monthly cost analysis
from django.db.models import Sum
from datetime import timedelta

last_30_days = timezone.now() - timedelta(days=30)

total_cost = Report.objects.filter(
    submitted_at__gte=last_30_days,
    ai_cost_estimate__isnull=False
).aggregate(Sum('ai_cost_estimate'))['ai_cost_estimate__sum']

print(f"Last 30 days AI cost: ${total_cost:.2f}")

# By subspecialty
costs_by_subspecialty = Report.objects.filter(
    submitted_at__gte=last_30_days
).values('case__subspecialty').annotate(
    total_cost=Sum('ai_cost_estimate'),
    count=Count('id')
).order_by('-total_cost')
```

---

### 📋 Phase 1 Checklist

- [ ] Create migrations for new models (AIPromptVersion, feedback categories)
- [ ] Update AIFeedbackRating model with structured categories
- [ ] Update Report model with prompt versioning and caching fields
- [ ] Implement prompt versioning system
- [ ] Implement report caching
- [ ] Implement token usage logging
- [ ] Create admin interface for prompt versions
- [ ] Update frontend to collect structured feedback
- [ ] Create analytics dashboard for metrics
- [ ] Document baseline metrics using MONITORING_SETUP.md
- [ ] Test with AI_ITERATION_WORKFLOW.md methodology

**Success Criteria**:
- [ ] Can create and activate new prompt versions
- [ ] Can A/B test prompts
- [ ] Cache hit rate > 10%
- [ ] Token usage tracked for all feedbacks
- [ ] Structured feedback categories collected

---

## 🎓 PHASE 2: Interactive Tutoring

**Timeline**: Months 3-4
**Cost**: ~$500/year (10k feedbacks, 5k tutoring sessions @ 2 turns each)
**Risk**: Medium
**Priority**: ✅✅✅ **MUST DO** - Highest pedagogical value

### 🎯 Goals

Transform passive feedback into active learning through conversational AI.

### 💡 The Problem This Solves

**Current**: User reads AI feedback → Doesn't understand point → Frustrated → Moves on
**With Tutoring**: User reads feedback → Asks clarifying question → Gets personalized explanation → Understands

**Example**:
```
Initial Feedback: "You missed a pneumothorax"

User: "Why is this critical?"
AI Tutor: "A pneumothorax is air in the pleural space that can compress the lung.
In this case, it measures 2cm, which requires intervention..."

User: "How do I avoid missing these?"
AI Tutor: "For chest X-rays, systematically check the lung edges. Look for:
1. Lack of lung markings peripherally
2. Visible pleural line
3. Increased lucency..."
```

### ✅ Feature 2.1: Conversational Agent Backend

**Implementation**:

```python
# New model: backend/cases/models.py
class TutoringConversation(models.Model):
    report = models.ForeignKey(Report, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    total_turns = models.IntegerField(default=0)

    class Meta:
        ordering = ['-started_at']

class TutoringMessage(models.Model):
    conversation = models.ForeignKey(
        TutoringConversation,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    turn_number = models.IntegerField()
    role = models.CharField(
        max_length=10,
        choices=[('user', 'User'), ('assistant', 'Assistant')]
    )
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    tokens_used = models.IntegerField(null=True, blank=True)

    class Meta:
        ordering = ['turn_number']
```

**Agentic System Prompt**:

```python
# backend/cases/tutoring_service.py
def get_tutoring_system_prompt(report, case):
    return f"""You are an expert pediatric radiology tutor helping a trainee understand their performance on a case.

CASE CONTEXT:
- Case ID: {case.case_identifier} (don't reveal clinical details unless asked)
- Patient: {case.patient_age}, {case.patient_sex}
- Clinical History: {case.clinical_history}
- Expert Diagnosis: {case.diagnosis}

STUDENT'S REPORT:
{report.structured_content}

AI FEEDBACK GIVEN:
{report.ai_feedback_content.get('raw_feedback', '')}

YOUR ROLE:
1. Answer follow-up questions about the feedback
2. Explain WHY findings are important
3. Teach HOW to avoid missing similar findings
4. Adapt explanation depth to student's understanding
5. Use Socratic method when appropriate

CONSTRAINTS:
- Keep responses concise (2-3 paragraphs max)
- Use analogies and examples
- Don't just repeat the feedback - add teaching value
- Encourage critical thinking
- Stay professional and constructive

TOOLS AVAILABLE:
- [SEARCH_LITERATURE]: Search medical literature
- [GET_CASE_DETAILS]: Retrieve additional case information
- [COMPARE_CASES]: Find similar teaching cases

Remember: You're teaching, not just answering. Guide them to deeper understanding."""

def generate_tutoring_response(conversation, user_message):
    """Generate tutoring response using agentic AI"""

    # Build conversation history
    messages = [
        {"role": "system", "content": get_tutoring_system_prompt(
            conversation.report,
            conversation.report.case
        )}
    ]

    for msg in conversation.messages.all():
        messages.append({
            "role": msg.role,
            "content": msg.content
        })

    # Add current user message
    messages.append({
        "role": "user",
        "content": user_message
    })

    # Call Gemini with conversation history
    # (Use gemini-2.5-flash or upgrade to gemini-2.5-pro for complex reasoning)

    response = model.generate_content(messages)

    return response.text
```

---

### ✅ Feature 2.2: Frontend UI

**Add to frontend/main.js**:

```javascript
// After AI feedback displays
function displayTutoringButton(reportId) {
    const tutoringButton = `
        <button id="ask-question-btn" class="btn btn-primary">
            💬 Ask a Question
        </button>
        <div id="tutoring-chat" style="display: none;">
            <div id="chat-history"></div>
            <textarea id="tutoring-question"
                      placeholder="Ask a follow-up question..."></textarea>
            <button id="send-question">Send</button>
            <button id="end-session">End Tutoring</button>
        </div>
    `;

    document.getElementById('ai-feedback').insertAdjacentHTML(
        'beforeend',
        tutoringButton
    );

    // Event listeners
    document.getElementById('ask-question-btn').addEventListener('click', () => {
        document.getElementById('tutoring-chat').style.display = 'block';
        startTutoringSession(reportId);
    });
}

async function startTutoringSession(reportId) {
    const response = await fetch(`/api/tutoring/start/`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ report_id: reportId })
    });

    const data = await response.json();
    window.currentConversationId = data.conversation_id;
}

async function sendTutoringMessage(message) {
    const response = await fetch(`/api/tutoring/${window.currentConversationId}/message/`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ message: message })
    });

    const data = await response.json();

    // Display in chat
    displayMessage('user', message);
    displayMessage('assistant', data.response);
}
```

---

### 📋 Phase 2 Checklist

- [ ] Create TutoringConversation and TutoringMessage models
- [ ] Implement tutoring_service.py with agentic system
- [ ] Create API endpoints (start session, send message, end session)
- [ ] Implement conversation history management
- [ ] Add "Ask a Question" button to frontend
- [ ] Build chat interface UI
- [ ] Implement session management (max 10 turns, timeout after 30 min)
- [ ] Add token usage tracking for tutoring
- [ ] Test with diverse questions
- [ ] Monitor quality and costs

**Success Criteria**:
- [ ] Users can ask follow-up questions
- [ ] Responses add teaching value (not just repeat feedback)
- [ ] Average 2-3 turns per session
- [ ] Positive user feedback on tutoring quality

---

## 👁️ PHASE 3A: Visual False Positive Verification

**Timeline**: Months 4-6 (parallel with Phase 3B)
**Cost**: ~$1,500/year (occurs in ~30-40% of reports)
**Risk**: Medium
**Priority**: ✅✅ **SHOULD DO** - Addresses #1 user frustration

### 🎯 The Problem This Solves

**#1 Frustration in Radiology Education**:
> "The attending says I'm wrong, but I don't understand WHY. I SAW something!"

**Your Solution**: Use visual AI to explain WHAT the user saw and WHY it's not pathology.

### 💡 Why This is Better Than Full Image Analysis

| Approach | Scope | Cost | Teaching Value |
|----------|-------|------|---------------|
| **Full analysis** (initial thought) | All 250 images | $1+ per case | Shows missed findings |
| **Your approach** | Only claimed findings | $0.15 per feedback | Explains confusion ⭐⭐⭐⭐⭐ |

**Example**:
```
User reports: "ACL tear visible"
Expert says: "ACL intact"

Visual verification:
1. Fetch knee MRI sagittal series
2. Check for ACL tear evidence → Not present
3. Identify what user likely saw → Normal fiber orientation
4. Explain: "You may have seen the normal striations of the ACL.
   A tear would show disruption and fluid signal. Compare with
   this tear example [annotated image]..."
```

---

### ✅ Feature 3A.1: False Positive Detection

**Implementation**:

```python
# In utils.py - enhance generate_report_comparison_summary
def identify_false_positives(user_sections, expert_sections, case_key_findings):
    """Identify findings user reported that expert didn't"""

    false_positives = []

    for user_section in user_sections:
        section_name = user_section['section_name']
        user_content = user_section['content'].lower()

        # Find corresponding expert section
        expert_section = next(
            (s for s in expert_sections if s['section_name'] == section_name),
            None
        )

        if not expert_section:
            continue

        expert_content = expert_section['content'].lower()
        expert_concepts = expert_section.get('key_concepts_text', '').lower().split(';')

        # Look for positive findings in user report not in expert
        # (Simple NLP - can enhance with spaCy for medical NER)
        positive_patterns = [
            r'(?:shows?|demonstrates?|reveals?|consistent with)\s+(\w+(?:\s+\w+){0,3})',
            r'(\w+(?:\s+\w+){0,2})\s+(?:is|are)\s+(?:present|visible|seen)'
        ]

        import re
        user_findings = []
        for pattern in positive_patterns:
            matches = re.findall(pattern, user_content)
            user_findings.extend(matches)

        # Check if user findings are in expert content
        for finding in user_findings:
            if finding not in expert_content and finding not in ' '.join(expert_concepts):
                false_positives.append({
                    'section': section_name,
                    'claimed_finding': finding,
                    'user_description': user_section['content']
                })

    return false_positives
```

---

### ✅ Feature 3A.2: Visual Verification Agent

**Implementation**:

```python
# backend/cases/visual_verification_service.py
import google.generativeai as genai
from PIL import Image
import io

def fetch_dicom_images_for_finding(orthanc_study_uid, finding_type):
    """Fetch relevant DICOM series from Orthanc"""
    # Query Orthanc API for study
    study = requests.get(
        f"http://orthanc:8042/studies/{orthanc_study_uid}"
    ).json()

    # Determine relevant series based on finding type
    # (e.g., "ACL tear" → sagittal knee MRI series)

    # Fetch images
    # Convert DICOM to PIL Images

    return images

def verify_finding_visually(images, claimed_finding, case_context):
    """Use Gemini Vision to verify if finding is present"""

    prompt = f"""You are analyzing medical images to verify a learner's claim.

CLAIMED FINDING: {claimed_finding}

CASE CONTEXT:
- Patient Age: {case_context['patient_age']}
- Clinical History: {case_context['clinical_history']}

TASK:
1. Is there evidence of "{claimed_finding}" in these images? (Yes/No/Uncertain)
2. If No: What might the learner have mistaken for this finding?
3. Why might this normal variant/artifact look like "{claimed_finding}"?
4. How can the learner differentiate between this and actual pathology?

Be specific about image locations (e.g., "slice 12, upper right quadrant").
Focus on teaching, not diagnosis."""

    # Use Gemini Vision (gemini-2.5-flash supports vision)
    model = genai.GenerativeModel('gemini-2.5-flash')

    # Prepare content with images
    content = [prompt]
    for img in images[:10]:  # Limit to 10 images to control cost
        content.append(img)

    response = model.generate_content(content)

    return response.text

def generate_visual_explanation(
    false_positive,
    verification_result,
    case
):
    """Generate teaching explanation with visual context"""

    explanation_prompt = f"""Create a teaching explanation for why a learner made this error:

LEARNER'S CLAIM: {false_positive['claimed_finding']}
ACTUAL STATE: Not present (verified visually)

VISUAL ANALYSIS:
{verification_result}

CASE: {case.patient_age}, {case.clinical_history}

Generate a concise (2-3 paragraph) teaching explanation that:
1. Validates what they saw ("You likely saw...")
2. Explains why it's not pathology ("This is actually...")
3. Teaches differentiation ("To tell the difference, look for...")
4. Provides systematic approach ("When evaluating X, always check...")

Keep it constructive and educational."""

    model = genai.GenerativeModel('gemini-2.5-flash')
    response = model.generate_content(explanation_prompt)

    return response.text
```

---

### ✅ Feature 3A.3: Integration with Feedback Flow

**Update AIReportFeedbackView**:

```python
# In views.py
def generate_ai_feedback(report):
    # ... existing text-only feedback generation ...

    # Check for false positives
    false_positives = identify_false_positives(
        user_sections,
        expert_sections,
        case.key_findings
    )

    if false_positives and case.orthanc_study_uid:
        # Visual verification for up to 2 false positives
        visual_explanations = []

        for fp in false_positives[:2]:  # Limit cost
            try:
                # Fetch images
                images = fetch_dicom_images_for_finding(
                    case.orthanc_study_uid,
                    fp['claimed_finding']
                )

                # Verify
                verification = verify_finding_visually(
                    images,
                    fp['claimed_finding'],
                    {
                        'patient_age': case.patient_age,
                        'clinical_history': case.clinical_history
                    }
                )

                # Generate explanation
                explanation = generate_visual_explanation(
                    fp,
                    verification,
                    case
                )

                visual_explanations.append({
                    'finding': fp['claimed_finding'],
                    'section': fp['section'],
                    'explanation': explanation
                })

            except Exception as e:
                logger.error(f"Visual verification failed: {e}")
                # Continue with text-only feedback

        # Add visual explanations to feedback
        if visual_explanations:
            report.ai_feedback_content['visual_explanations'] = visual_explanations
            report.save()

    return report.ai_feedback_content
```

---

### 📋 Phase 3A Checklist

- [ ] Implement false positive detection in utils.py
- [ ] Set up Orthanc API integration
- [ ] Implement DICOM to PIL image conversion
- [ ] Create visual_verification_service.py
- [ ] Implement Gemini Vision API calls
- [ ] Add visual explanations to Report model JSON field
- [ ] Update frontend to display visual explanations
- [ ] Add image annotation capability (optional)
- [ ] Test with diverse false positive scenarios
- [ ] Monitor costs and accuracy

**Success Criteria**:
- [ ] False positives detected accurately
- [ ] Visual verification works for common scenarios
- [ ] Explanations are educational and specific
- [ ] Cost stays within $0.15-0.40 per feedback average

---

## 📚 PHASE 3B: Literature Augmentation (Optional)

**Timeline**: Months 5-7 (parallel with 3A)
**Cost**: ~$300/year
**Risk**: Low
**Priority**: ⚠️ **OPTIONAL** - Do if budget allows

### 🎯 Goals

Provide evidence-based learning for uncommon/controversial findings.

**When to Use**: Automatically cite literature for:
- Rare pathology
- Controversial interpretations
- Latest guideline changes
- Uncommon normal variants

**Implementation**: See further-ai.txt for details. Skip if budget/time limited.

---

## 📊 PHASE 4: Learning Analytics

**Timeline**: Months 7-9
**Cost**: $0 (dev time)
**Risk**: Low
**Priority**: ✅ **SHOULD DO** - Proves platform effectiveness

### 🎯 Goals

1. Track individual learner progression
2. Prove educational effectiveness
3. Enable personalized learning
4. Support research and publications

### ✅ Feature 4.1: User Learning Profiles

**Implementation**:

```python
# New model
class UserLearningProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Competency tracking by subspecialty
    neuroradiology_level = models.IntegerField(default=1)  # 1-5
    chest_level = models.IntegerField(default=1)
    abdomen_level = models.IntegerField(default=1)
    musculoskeletal_level = models.IntegerField(default=1)
    # ... etc

    # Learning metrics
    total_cases_attempted = models.IntegerField(default=0)
    total_reports_submitted = models.IntegerField(default=0)
    avg_accuracy_score = models.FloatField(default=0.0)
    avg_completeness_score = models.FloatField(default=0.0)

class CompetencyMilestone(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    subspecialty = models.CharField(max_length=10)
    level_achieved = models.IntegerField()
    achieved_at = models.DateTimeField(auto_now_add=True)
    criteria_met = models.JSONField()  # Track what criteria triggered milestone
```

**Analytics**:

```python
def calculate_user_progression(user):
    """Calculate learning progression over time"""

    reports = Report.objects.filter(user=user).order_by('submitted_at')

    progression = {
        'first_report': reports.first().submitted_at if reports.exists() else None,
        'total_reports': reports.count(),
        'subspecialties_attempted': reports.values('case__subspecialty').distinct().count(),
        'accuracy_trend': [],
        'completeness_trend': []
    }

    # Calculate metrics over time (monthly)
    # ... implementation details ...

    return progression
```

---

### 📋 Phase 4 Checklist

- [ ] Create UserLearningProfile model
- [ ] Implement competency calculation algorithms
- [ ] Create progression tracking system
- [ ] Build analytics dashboard (admin view)
- [ ] Implement adaptive feedback (adjust to user level)
- [ ] Add user progress page (learner view)
- [ ] Test competency calculations
- [ ] Validate against manual assessments

**Success Criteria**:
- [ ] Can track user progression over time
- [ ] Competency levels reflect actual performance
- [ ] Adaptive feedback shows measurable improvement
- [ ] Can generate learning outcome reports

---

## ⚡ PHASE 5: Scale & Optimize

**Timeline**: Months 10-12
**Cost**: $0 (infrastructure)
**Risk**: Medium
**Priority**: ⚠️ **WHEN NEEDED** - Do when approaching scale limits

### 🎯 Goals

Support 10× user growth without cost explosion.

### ✅ Feature 5.1: Async Task Processing

**Implementation**: Use Celery or Django-Q

```python
# Install: pip install celery redis

# celery.py
from celery import Celery

app = Celery('globalpeds')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# tasks.py
from celery import shared_task

@shared_task
def generate_ai_feedback_async(report_id):
    """Generate AI feedback in background"""
    report = Report.objects.get(id=report_id)

    # ... generate feedback ...

    report.ai_feedback_content = feedback
    report.save()

    # Notify user (websocket or email)
    notify_user_feedback_ready(report.user, report)
```

---

### 📋 Phase 5 Checklist

- [ ] Set up Redis for Celery
- [ ] Configure Celery
- [ ] Convert feedback generation to async tasks
- [ ] Implement user notifications
- [ ] Add advanced caching (semantic similarity)
- [ ] Implement intelligent model routing
- [ ] Batch processing for off-peak generation
- [ ] Load testing and optimization

**Success Criteria**:
- [ ] Can handle 10× current load
- [ ] Cost per feedback reduced by 20%+
- [ ] Response times acceptable (users notified when ready)

---

## 💰 Cost Summary

| Phase | Annual Cost | Cumulative Cost | Value Add |
|-------|-------------|-----------------|-----------|
| Phase 1 | $0 | $200 (baseline) | Foundation ⭐⭐⭐⭐⭐ |
| Phase 2 | +$500 | $700 | Interactive learning ⭐⭐⭐⭐⭐ |
| Phase 3A | +$1,500 | $2,200 | Visual explanations ⭐⭐⭐⭐ |
| Phase 3B | +$300 | $2,500 | Literature (optional) ⭐⭐⭐ |
| Phase 4 | $0 | $2,500 | Learning analytics ⭐⭐⭐⭐ |
| Phase 5 | $0 | $2,500 | Scale readiness ⭐⭐⭐ |

**Total**: $2,200-2,500/year (11-12.5× baseline, but 5-6× value)

---

## 📋 Implementation Priorities

### ✅✅✅ MUST DO (Phases 1-2)
1. Structured feedback tracking
2. Prompt versioning
3. Report caching
4. Interactive tutoring agent

**Timeline**: 4 months
**Cost**: $700/year
**Impact**: Foundation + transformative learning

### ✅✅ SHOULD DO (Phase 3A, 4)
5. False positive visual verification
6. Learning analytics

**Timeline**: +5 months (9 total)
**Cost**: $2,200/year
**Impact**: Addresses top frustration + proves effectiveness

### ⚠️ OPTIONAL (Phase 3B, 5)
7. Literature augmentation
8. Async processing

**Timeline**: +3 months (12 total)
**Cost**: $2,500/year
**Impact**: Polish and scale readiness

---

## 🎯 Getting Started

### Month 1 Action Plan

**Week 1-2: Foundation Setup**
1. Create new database models (migrations)
2. Set up prompt versioning system
3. Implement structured feedback categories

**Week 3-4: Caching & Logging**
4. Implement report caching
5. Add token usage tracking
6. Create baseline metrics dashboard

**Success Metrics to Track**:
- [ ] Baseline AI quality (use `scripts/track_ai_baseline.py`)
- [ ] Current false positive rate
- [ ] Average tokens per feedback
- [ ] Cache hit rate (should start at 0%)

---

## 📚 Related Documentation

- **AI_ITERATION_WORKFLOW.md** - How to test and iterate on AI improvements
- **MONITORING_SETUP.md** - Track metrics for each phase
- **BETA_TESTING_WORKFLOW.md** - Test new features systematically
- **further-ai.txt** - Complete technical discussion and rationale

---

## ❓ Decision Points

Before starting, decide:

1. **Budget**: $700 (conservative) or $2,200 (recommended) or $2,500 (maximum)?
2. **Timeline**: 4 months (Phases 1-2) or 9 months (through Phase 4) or 12 months (all)?
3. **Priority**: Interactive tutoring first or visual verification first?
4. **Scope**: Start with one subspecialty or all cases?
5. **Resources**: Can you set up Celery/Redis (Phase 5) or keep it simple?

---

**Remember**: Each phase builds on the previous. Start with Phase 1 foundation - it enables everything else!

**Last Updated**: 2025-10-11
