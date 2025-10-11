# 🔄 AI Iteration Workflow - Data-Driven Improvement

**Purpose**: Systematic framework for improving AI feedback quality using data-driven decision making

**Last Updated**: 2025-10-11

**Related Docs**:
- [further-ai.txt](../further-ai.txt) - Strategic AI vision
- [AI_GUIDE.md](AI_GUIDE.md) - Current AI implementation
- [AI_FEATURES_ROADMAP.md](AI_FEATURES_ROADMAP.md) - Phased feature rollout
- [MONITORING_SETUP.md](MONITORING_SETUP.md) - Metrics infrastructure

---

## 🎯 Philosophy

> "In God we trust, all others must bring data." - W. Edwards Deming

**Core Principles**:
1. **Measure Before Changing** - Establish baseline metrics
2. **One Variable at a Time** - Isolate what's being tested
3. **Statistical Significance** - Collect enough data to be confident
4. **User-Centric** - Quality is defined by user ratings and outcomes
5. **Reversible** - Always have a rollback plan

---

## 📊 Key Metrics to Track

### 1️⃣ AI Feedback Quality (Primary)

**User Ratings** (`AIFeedbackRating` model):
- Average star rating (1-5)
- Distribution of ratings
- Ratings by case difficulty
- Ratings over time
- Rating trends after prompt changes

**Target**: Average rating ≥ 4.0/5.0

```sql
-- Query average rating
SELECT
    AVG(star_rating) as avg_rating,
    COUNT(*) as total_ratings,
    COUNT(DISTINCT user_id) as unique_users,
    COUNT(DISTINCT report_id) as unique_reports
FROM cases_aifeedbackrating
WHERE rated_at >= NOW() - INTERVAL '30 days';

-- Rating distribution
SELECT
    star_rating,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage
FROM cases_aifeedbackrating
WHERE rated_at >= NOW() - INTERVAL '30 days'
GROUP BY star_rating
ORDER BY star_rating DESC;
```

### 2️⃣ AI Feedback Accuracy

**False Positives**:
- How often AI flags discrepancies that don't exist
- Track via user feedback comments mentioning "incorrect", "wrong", "not a problem"

**Missed Discrepancies**:
- Critical findings AI didn't catch
- Compare against expert feedback on same reports

**Target**: False positive rate < 10%, Missed critical findings < 5%

### 3️⃣ AI System Performance

**Response Time**:
- Time from request to feedback delivery
- Target: < 5 seconds (95th percentile)

**Token Usage**:
- Prompt length (tokens)
- Response length (tokens)
- Cost per feedback

**Error Rate**:
- API failures
- Parsing failures
- Timeout rate

**Target**: Error rate < 1%, Cost < $0.05 per feedback

```python
# Track in llm_feedback_service.py
import time
start_time = time.time()
# ... generate feedback ...
elapsed = time.time() - start_time
logger.info(f"AI feedback generated in {elapsed:.2f}s for report {report_id}")
```

### 4️⃣ User Engagement

**Usage Metrics**:
- % of reports requesting AI feedback
- Average time between report submission and feedback request
- Repeat usage rate

**Target**: > 80% of reports request feedback, > 70% of users return

### 5️⃣ Learning Outcomes

**Improvement Over Time**:
- User report quality metrics (completeness, accuracy)
- Reduction in critical errors over time
- Progression through difficulty levels

---

## 🔬 The Iteration Cycle

### Phase 1: Baseline Establishment

**Before making ANY AI changes**, establish your baseline:

#### Step 1.1: Collect Current Metrics

```bash
# SSH into beta droplet
ssh root@YOUR_DROPLET_IP

# Activate Django environment
cd /var/www/gr4-gemini/backend
source /path/to/venv/bin/activate

# Django shell
python manage.py shell
```

```python
# Run these queries
from django.db.models import Avg, Count
from cases.models import AIFeedbackRating, Report
from datetime import datetime, timedelta

# Baseline period (last 30 days or since launch)
baseline_start = datetime.now() - timedelta(days=30)

# Average rating
baseline_rating = AIFeedbackRating.objects.filter(
    rated_at__gte=baseline_start
).aggregate(
    avg=Avg('star_rating'),
    count=Count('id')
)
print(f"Baseline Rating: {baseline_rating['avg']:.2f} ({baseline_rating['count']} ratings)")

# Rating distribution
from collections import Counter
ratings = AIFeedbackRating.objects.filter(
    rated_at__gte=baseline_start
).values_list('star_rating', flat=True)
distribution = Counter(ratings)
print(f"Distribution: {dict(distribution)}")

# Reports with feedback
reports_with_feedback = Report.objects.filter(
    submitted_at__gte=baseline_start
).exclude(ai_feedback_content={}).count()

total_reports = Report.objects.filter(
    submitted_at__gte=baseline_start
).count()

feedback_rate = (reports_with_feedback / total_reports * 100) if total_reports > 0 else 0
print(f"Feedback Request Rate: {feedback_rate:.1f}%")
```

#### Step 1.2: Document Baseline

Create a baseline record:

```markdown
## Baseline - [Date]

### Context
- Prompt Version: [e.g., "Initial prompt with pedagogical enhancements"]
- Model: Gemini 2.5 Flash
- Data Period: [Start Date] to [End Date]
- Sample Size: [N] ratings, [M] feedbacks

### Metrics
- **Average Rating**: X.XX / 5.0
- **Rating Distribution**: 5★: X%, 4★: X%, 3★: X%, 2★: X%, 1★: X%
- **Feedback Request Rate**: XX%
- **Average Response Time**: X.Xs
- **Cost per Feedback**: $X.XX

### Common User Feedback Themes
(From rating comments):
- Theme 1: Description
- Theme 2: Description
```

Save this in: `docs/ai_baselines/baseline_YYYYMMDD.md`

---

### Phase 2: Hypothesis Formation

**What are you trying to improve?**

#### Example Hypotheses:

**Hypothesis 1: Context Improvement**
- **Problem**: Users report AI feedback is "too generic"
- **Hypothesis**: Adding patient age context to prompt will make feedback more specific
- **Expected Outcome**: Average rating increases by 0.3 points
- **Risk**: Minimal - age is already collected, low implementation risk

**Hypothesis 2: Severity Calibration**
- **Problem**: Users rate feedback poorly when minor issues are marked "Critical"
- **Hypothesis**: Refining severity criteria will reduce false critical ratings
- **Expected Outcome**: Reduce 1-2 star ratings by 50%
- **Risk**: Medium - need to ensure real critical issues still flagged

**Hypothesis 3: Response Length**
- **Problem**: Feedback is too verbose, users skim it
- **Hypothesis**: Limiting feedback to 3 key points improves readability and ratings
- **Expected Outcome**: Increase 5-star ratings by 20%
- **Risk**: Low-medium - might lose detail

#### Documentation Template:

```markdown
## Hypothesis - [Name] - [Date]

### Problem Statement
What issue are we trying to solve? What user pain point?

### Hypothesis
We believe that [change] will result in [outcome] because [reasoning].

### Success Metrics
- Primary: [e.g., Average rating increases from 3.8 to 4.1]
- Secondary: [e.g., % of 1-2 star ratings decreases by 30%]

### Minimum Sample Size
- [N] feedback ratings (recommend 30-50 minimum)
- [M] days of data collection

### Implementation
- Files to change:
- Code changes:
- Deployment plan:

### Rollback Plan
If metrics don't improve or degrade:
1. Revert to commit [hash]
2. Restart services
3. Monitor for 24h
```

Save in: `docs/ai_hypotheses/hypothesis_NAME_YYYYMMDD.md`

---

### Phase 3: Implementation

#### Step 3.1: Make the Change

**Example**: Adding patient weight to AI prompt

```python
# backend/cases/llm_feedback_service.py

def get_feedback_from_llm(
    user_sections,
    expert_sections,
    pre_analysis,
    case_identifier_for_llm,
    # ... existing params ...
    case_patient_weight=None,  # NEW PARAM
    # ... other params ...
):
    # Sanitize new input
    patient_weight_str = sanitize_text(case_patient_weight) if case_patient_weight else "Not specified"

    # Update prompt
    prompt = f"""
    ... existing prompt ...

    **Patient Weight**: {patient_weight_str}

    ... rest of prompt ...
    """
```

#### Step 3.2: Add Prompt Version Tracking

**Create a new model** (one-time setup):

```python
# backend/cases/models.py

class AIPromptVersion(models.Model):
    version = models.CharField(max_length=50, unique=True)
    description = models.TextField()
    prompt_template = models.TextField()
    model_name = models.CharField(max_length=100, default="gemini-2.5-flash")
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=False)

    # Metrics
    avg_rating = models.FloatField(null=True, blank=True)
    total_feedbacks = models.IntegerField(default=0)
    total_ratings = models.IntegerField(default=0)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.version} - {'Active' if self.is_active else 'Inactive'}"
```

Run migrations:
```bash
python manage.py makemigrations
python manage.py migrate
```

**Track which version generated each feedback**:

```python
# backend/cases/models.py - Update Report model

class Report(models.Model):
    # ... existing fields ...
    ai_prompt_version = models.CharField(max_length=50, null=True, blank=True)
```

**Update AIReportFeedbackView**:

```python
# backend/cases/views.py

class AIReportFeedbackView(APIView):
    def post(self, request, report_id):
        # ... existing code ...

        # Get current active prompt version
        from cases.models import AIPromptVersion
        active_version = AIPromptVersion.objects.filter(is_active=True).first()

        # Generate feedback
        llm_feedback = get_feedback_from_llm(...)

        # Save with version
        report.ai_prompt_version = active_version.version if active_version else "v1.0"
        report.save()
```

#### Step 3.3: Deploy to Beta

Follow [BETA_DEPLOYMENT.md](BETA_DEPLOYMENT.md):

```bash
# Local
git add -A
git commit -m "Add patient weight to AI prompt - Hypothesis: Context Improvement"
git push origin online_beta

# Droplet
ssh root@YOUR_DROPLET_IP
cd /var/www/gr4-gemini
git pull origin online_beta
source /path/to/venv/bin/activate
cd backend
python manage.py migrate  # If model changes
sudo systemctl restart gunicorn

# Verify
tail -f /var/log/globalpeds/gunicorn.log
```

---

### Phase 4: Data Collection

**Duration**: Depends on traffic

- **High Traffic** (10+ feedbacks/day): 3-7 days minimum
- **Medium Traffic** (5-10 feedbacks/day): 7-14 days
- **Low Traffic** (<5 feedbacks/day): 14-30 days

**Minimum Sample Size**: 30-50 ratings for statistical confidence

**During Collection**:
- ✅ Monitor error rates daily
- ✅ Read user comments on ratings
- ✅ Check for unexpected behaviors
- ❌ Don't make other AI changes
- ❌ Don't interpret results prematurely

**Early Warning Signs** (stop experiment early):
- Error rate > 5%
- Average rating drops > 0.5 points
- Multiple user complaints about same issue
- System performance degrades

---

### Phase 5: Analysis

#### Step 5.1: Query Results

```python
# Django shell
from cases.models import AIFeedbackRating, Report
from django.db.models import Avg, Count
from datetime import datetime, timedelta

# Define experiment period
experiment_start = datetime(2025, 10, 15)  # UPDATE
experiment_end = datetime.now()

# Get ratings for this experiment
experiment_ratings = AIFeedbackRating.objects.filter(
    report__ai_prompt_version='v1.1',  # UPDATE version
    rated_at__gte=experiment_start,
    rated_at__lte=experiment_end
)

# Calculate metrics
results = experiment_ratings.aggregate(
    avg_rating=Avg('star_rating'),
    total_ratings=Count('id')
)

print(f"Experiment Results:")
print(f"Average Rating: {results['avg_rating']:.2f}")
print(f"Total Ratings: {results['total_ratings']}")

# Distribution
from collections import Counter
ratings_list = experiment_ratings.values_list('star_rating', flat=True)
distribution = Counter(ratings_list)
print(f"Distribution: {dict(sorted(distribution.items(), reverse=True))}")

# Compare to baseline
baseline_avg = 3.80  # From Phase 1
improvement = results['avg_rating'] - baseline_avg
print(f"Improvement: {improvement:+.2f} points ({improvement/baseline_avg*100:+.1f}%)")
```

#### Step 5.2: Statistical Significance

**Simple T-Test** (requires scipy):

```python
from scipy import stats

# Get baseline ratings
baseline_ratings = list(AIFeedbackRating.objects.filter(
    report__ai_prompt_version='v1.0',  # Baseline
    rated_at__gte=baseline_start,
    rated_at__lt=experiment_start
).values_list('star_rating', flat=True))

# Get experiment ratings
experiment_ratings_list = list(ratings_list)

# T-test
t_stat, p_value = stats.ttest_ind(experiment_ratings_list, baseline_ratings)
print(f"T-statistic: {t_stat:.3f}")
print(f"P-value: {p_value:.4f}")
print(f"Statistically significant: {'Yes' if p_value < 0.05 else 'No'}")
```

#### Step 5.3: Qualitative Analysis

```python
# Read user comments
comments = AIFeedbackRating.objects.filter(
    report__ai_prompt_version='v1.1',
    rated_at__gte=experiment_start
).exclude(comment='').values_list('star_rating', 'comment')

for rating, comment in comments:
    print(f"{rating}★: {comment}")
    print("-" * 80)
```

**Look for patterns**:
- Common positive themes
- Common complaints
- Unexpected feedback
- Edge cases

---

### Phase 6: Decision Making

#### Decision Matrix:

| Outcome | Average Rating Change | P-value | Decision |
|---------|----------------------|---------|----------|
| **Clear Win** | +0.3 or more | < 0.05 | ✅ Promote to production immediately |
| **Modest Win** | +0.1 to +0.3 | < 0.05 | ✅ Promote, monitor closely |
| **Marginal** | +0.05 to +0.1 | < 0.05 | ⚠️ Keep testing or iterate |
| **No Change** | -0.05 to +0.05 | > 0.05 | ❌ Rollback, new hypothesis |
| **Degradation** | < -0.05 | Any | ❌ Immediate rollback |

#### Document Decision:

```markdown
## Experiment Results - [Name] - [Date]

### Hypothesis
[Repeat hypothesis]

### Results
- **Baseline**: 3.80 / 5.0 (50 ratings)
- **Experiment**: 4.10 / 5.0 (45 ratings)
- **Change**: +0.30 points (+7.9%)
- **P-value**: 0.023 (statistically significant)
- **Sample Period**: 14 days
- **Error Rate**: 0.8% (acceptable)

### Qualitative Findings
- Positive: 15 comments mentioned "more relevant"
- Positive: 8 comments praised specificity
- Negative: 3 comments said "too much detail"

### Decision
✅ **PROMOTE** - Clear win, statistically significant

### Actions
1. Merge to main branch
2. Deploy to production
3. Monitor for 7 days
4. Update baseline metrics
5. Archive this experiment

### Lessons Learned
- Patient age context significantly improved relevance
- Optimal context: age, weight, history, key findings
- Users value specificity over brevity

### Next Steps
- Hypothesis: Adding clinical significance explanations
- Hypothesis: Adaptive detail based on user level
```

Save in: `docs/ai_experiments/experiment_NAME_YYYYMMDD_results.md`

---

### Phase 7: Promotion or Rollback

#### If Promoting:

```bash
# 1. Merge to main (if using branches)
git checkout main
git merge online_beta
git push origin main

# 2. Update AIPromptVersion model
python manage.py shell
```

```python
from cases.models import AIPromptVersion

# Deactivate old version
AIPromptVersion.objects.filter(is_active=True).update(is_active=False)

# Activate new version
new_version = AIPromptVersion.objects.get(version='v1.1')
new_version.is_active = True
new_version.save()

print(f"Activated version: {new_version.version}")
```

```bash
# 3. Deploy to production (when ready)
# Follow production deployment procedures

# 4. Update baseline for future experiments
# New baseline is this experiment's results
```

#### If Rolling Back:

```bash
# 1. Revert code
git revert HEAD~1  # Or specific commit
git push origin online_beta

# 2. Deploy
ssh root@YOUR_DROPLET_IP
cd /var/www/gr4-gemini
git pull origin online_beta
sudo systemctl restart gunicorn

# 3. Deactivate failed version
python manage.py shell
```

```python
from cases.models import AIPromptVersion
AIPromptVersion.objects.filter(version='v1.1').update(is_active=False)
AIPromptVersion.objects.filter(version='v1.0').update(is_active=True)
```

```bash
# 4. Document why rollback
# See docs/ai_experiments/experiment_NAME_YYYYMMDD_results.md
```

---

## 🎯 A/B Testing (Advanced)

For higher traffic, run parallel experiments:

### Setup

1. **Randomize users** into groups:
   - Group A (control): Old prompt (50%)
   - Group B (test): New prompt (50%)

2. **Update view to route by group**:

```python
# backend/cases/views.py

def get_user_ab_group(user_id):
    """Consistent hash-based assignment"""
    return 'A' if hash(f"{user_id}_experiment_1") % 2 == 0 else 'B'

class AIReportFeedbackView(APIView):
    def post(self, request, report_id):
        # ... existing code ...

        # Get user's A/B group
        group = get_user_ab_group(request.user.id)

        if group == 'A':
            # Use old prompt
            prompt_version = 'v1.0'
            # Old parameters
        else:
            # Use new prompt
            prompt_version = 'v1.1'
            # New parameters

        # Generate feedback with appropriate version
        llm_feedback = get_feedback_from_llm(..., prompt_version=prompt_version)

        report.ai_prompt_version = prompt_version
        report.save()
```

3. **Analyze by group**:

```python
# Compare Group A vs Group B
from cases.models import AIFeedbackRating

group_a_avg = AIFeedbackRating.objects.filter(
    report__ai_prompt_version='v1.0',
    rated_at__gte=experiment_start
).aggregate(Avg('star_rating'))['star_rating__avg']

group_b_avg = AIFeedbackRating.objects.filter(
    report__ai_prompt_version='v1.1',
    rated_at__gte=experiment_start
).aggregate(Avg('star_rating'))['star_rating__avg']

print(f"Group A (control): {group_a_avg:.2f}")
print(f"Group B (test): {group_b_avg:.2f}")
print(f"Lift: {(group_b_avg - group_a_avg):.2f} ({(group_b_avg - group_a_avg)/group_a_avg*100:.1f}%)")
```

---

## 📝 Experiment Log

Keep a running log of all experiments:

**File**: `docs/ai_experiments/EXPERIMENT_LOG.md`

```markdown
# AI Experiment Log

| Date | Hypothesis | Version | Result | Rating Δ | Decision | Notes |
|------|-----------|---------|--------|----------|----------|-------|
| 2025-10-15 | Patient weight context | v1.1 | Win | +0.30 | ✅ Promote | Significantly improved relevance |
| 2025-10-22 | Reduce verbosity | v1.2 | Marginal | +0.08 | ⚠️ Monitor | Mixed feedback, continue testing |
| 2025-10-30 | Age-appropriate language | v1.3 | No change | -0.02 | ❌ Rollback | Users found it condescending |
```

---

## 🎓 Best Practices

### DO:
✅ Establish baseline before every change
✅ Change one thing at a time
✅ Collect enough data for statistical confidence
✅ Read user comments, not just ratings
✅ Document everything (hypotheses, results, decisions)
✅ Monitor for unexpected side effects
✅ Have a rollback plan ready

### DON'T:
❌ Make changes based on anecdotes
❌ Skip baseline measurement
❌ Stop experiment early (unless clear degradation)
❌ Interpret results with insufficient data
❌ Ignore qualitative feedback
❌ Make multiple AI changes simultaneously
❌ Deploy to production without beta testing

---

## 🚀 Quick Start Checklist

Starting your first AI improvement:

- [ ] Read [further-ai.txt](../further-ai.txt) for strategic vision
- [ ] Establish baseline metrics (Phase 1)
- [ ] Formulate hypothesis (Phase 2)
- [ ] Set up prompt version tracking
- [ ] Implement change locally
- [ ] Test locally
- [ ] Deploy to beta
- [ ] Collect data (minimum 30 ratings)
- [ ] Analyze results
- [ ] Make data-driven decision
- [ ] Document findings
- [ ] Promote or rollback

---

## 📚 Related Documentation

- [AI_GUIDE.md](AI_GUIDE.md) - Current AI implementation details
- [AI_FEATURES_ROADMAP.md](AI_FEATURES_ROADMAP.md) - Planned features from further-ai.txt
- [MONITORING_SETUP.md](MONITORING_SETUP.md) - Setting up metrics infrastructure
- [BETA_DEPLOYMENT.md](BETA_DEPLOYMENT.md) - Deployment procedures
- [.claude/docs/TESTING.md](../.claude/docs/TESTING.md) - Testing strategies

---

## 💡 Example: Complete Iteration

See `docs/ai_experiments/example_iteration.md` for a complete walkthrough of a real experiment from hypothesis to decision.

---

**Remember**: Good data beats opinions. Measure, experiment, learn, iterate. Every improvement should be driven by user feedback and measurable outcomes.

**Last Updated**: 2025-10-11
**Maintained By**: Project Team
**Questions?**: Review examples in `docs/ai_experiments/` directory
