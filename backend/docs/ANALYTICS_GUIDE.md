# 📊 AI Feedback Analytics Guide for Administrators

Comprehensive guide for administrators to monitor, analyze, and improve AI feedback quality using the analytics dashboard.

---

## 🎯 Overview

The AI Feedback Quality Analytics system helps administrators:

1. **📈 Track Costs**: Monitor AI API token usage and expenses
2. **⭐ Measure Quality**: Analyze user ratings of AI feedback
3. **🔄 A/B Testing**: Compare prompt versions for quality improvements
4. **💾 Optimize Caching**: Monitor cache effectiveness for cost savings
5. **🐛 Identify Issues**: Find false positives and problem areas

---

## 🚀 Quick Start

### Prerequisites

1. Admin account with `is_staff=True` permission
2. Valid JWT access token
3. Access to analytics endpoints

### Getting Started

```bash
# 1. Login as admin
curl -X POST https://api.example.com/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "your_password"}'

# Response: {"access": "YOUR_TOKEN", "refresh": "..."}

# 2. Test analytics access
curl https://api.example.com/api/cases/detailed-ratings/analytics/cost-trends/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 📈 Analytics Endpoints

### 1. Cost Trends Dashboard

**Endpoint:** `GET /api/cases/detailed-ratings/analytics/cost-trends/`

**Purpose:** Track AI API spending and token usage over time.

**Query Parameters:**
- `days` (optional, default=30, max=365): Analysis period

**Key Metrics:**

| Metric | Description | Action Threshold |
|--------|-------------|------------------|
| `total_cost_usd` | Total AI API costs | Alert if >$500/month |
| `total_requests` | API calls made | Monitor growth trends |
| `cached_requests` | Cache hits | Low (<15%)? Improve caching |
| `cache_savings_usd` | Money saved by cache | Celebrate wins! |
| `daily_breakdown` | Day-by-day trends | Identify usage spikes |

**Example Response:**
```json
{
  "total_requests": 450,
  "total_prompt_tokens": 675000,
  "total_completion_tokens": 135000,
  "total_cost_usd": "20.25",
  "cached_requests": 85,
  "cache_savings_usd": "3.825",
  "daily_breakdown": [
    {
      "date": "2025-01-12",
      "requests": 25,
      "prompt_tokens": 37500,
      "completion_tokens": 7500,
      "cost_usd": "1.125",
      "cached_count": 5
    }
  ]
}
```

**📊 Dashboard Visualizations:**

1. **Line Chart**: `daily_breakdown.cost_usd` over time
2. **Bar Chart**: `daily_breakdown.requests` vs `cached_count`
3. **Pie Chart**: `cached_requests` vs `(total_requests - cached_requests)`
4. **KPI Cards**: `total_cost_usd`, `cache_savings_usd`, `total_requests`

**⚠️ Warning Signs:**
- Daily costs spike unexpectedly → Investigate unusual usage
- Cache hit rate drops below 10% → Check cache TTL settings
- Token counts growing faster than user base → Optimize prompts

---

### 2. Prompt Version Comparison (A/B Testing)

**Endpoint:** `GET /api/cases/detailed-ratings/analytics/prompt-comparison/`

**Purpose:** Compare quality metrics across different prompt versions to identify best performer.

**Key Metrics:**

| Metric | Description | Target Value |
|--------|-------------|--------------|
| `avg_overall` | Overall quality rating | ≥4.0/5.0 |
| `avg_accuracy` | How accurate was feedback? | ≥4.2/5.0 |
| `avg_helpfulness` | How helpful was feedback? | ≥4.0/5.0 |
| `avg_actionability` | How actionable was feedback? | ≥3.8/5.0 |
| `false_positive_rate` | % reports with false positives | <10% |
| `rating_count` | Sample size | ≥50 for confidence |

**Example Response:**
```json
{
  "prompt_versions": [
    {
      "prompt_version_id": 3,
      "version_name": "v2.0",
      "is_active": true,
      "rating_count": 125,
      "avg_accuracy": 4.5,
      "avg_helpfulness": 4.7,
      "avg_actionability": 4.4,
      "avg_overall": 4.5,
      "false_positive_count": 8,
      "false_positive_rate": 6.4
    },
    {
      "prompt_version_id": 2,
      "version_name": "v1.5",
      "is_active": false,
      "rating_count": 80,
      "avg_accuracy": 4.2,
      "avg_helpfulness": 4.3,
      "avg_actionability": 4.0,
      "avg_overall": 4.2,
      "false_positive_count": 10,
      "false_positive_rate": 12.5
    }
  ]
}
```

**📊 Dashboard Visualizations:**

1. **Comparison Table**: Side-by-side prompt version metrics
2. **Radar Chart**: 4 dimensions (accuracy, helpfulness, actionability, overall) per version
3. **Bar Chart**: False positive rate comparison
4. **Trend Line**: avg_overall over time for active version

**🔬 A/B Testing Workflow:**

```
1. Baseline Recording
   ├─ Record current version metrics (v1.5): avg_overall=4.2
   └─ Note: false_positive_rate=12.5%

2. Deploy New Version
   ├─ Create new PromptVersion (v2.0)
   ├─ Update prompt template
   └─ Set is_active=True

3. Monitor Period (7-14 days)
   ├─ Collect ≥50 ratings
   ├─ Check daily avg_overall
   └─ Watch for false_positive_rate

4. Analysis
   ├─ Compare v2.0 vs v1.5
   ├─ Decision criteria:
   │   ├─ avg_overall improved by ≥0.2? → Keep v2.0
   │   ├─ false_positive_rate increased? → Investigate
   │   └─ rating_count < 50? → Continue monitoring
   └─ Action: Keep winner, deactivate loser

5. Documentation
   └─ Record results in changelog
```

**✅ Deciding Which Prompt Wins:**

| Scenario | v1.5 avg_overall | v2.0 avg_overall | Decision |
|----------|------------------|------------------|----------|
| Clear Winner | 4.2 | 4.5 (+0.3) | Deploy v2.0 |
| Marginal Improvement | 4.2 | 4.3 (+0.1) | More data needed |
| No Improvement | 4.2 | 4.1 (-0.1) | Roll back to v1.5 |
| False Positives Spike | 4.2 (12% FP) | 4.4 (25% FP) | Roll back, fix v2.0 |

---

### 3. Cache Performance Monitoring

**Endpoint:** `GET /api/cases/detailed-ratings/analytics/cache-performance/`

**Purpose:** Monitor effectiveness of AI feedback caching system.

**Query Parameters:**
- `days` (optional, default=30, max=365): Analysis period

**Key Metrics:**

| Metric | Description | Target Value |
|--------|-------------|--------------|
| `cache_hit_rate` | % requests from cache | ≥15% |
| `cost_savings_usd` | Money saved | Track monthly |
| `avg_cache_age_minutes` | How old is cache? | <1440 (24hr) |
| `expired_entries` | Stale cache entries | <50% of total |

**Example Response:**
```json
{
  "total_cached_entries": 450,
  "cache_hit_rate": 18.9,
  "avg_cache_age_minutes": 720.5,
  "expired_entries": 85,
  "cost_savings_usd": "3.825",
  "requests_using_cache": 85,
  "requests_not_cached": 365
}
```

**📊 Dashboard Visualizations:**

1. **Gauge Chart**: `cache_hit_rate` (target: 15-25%)
2. **Donut Chart**: `requests_using_cache` vs `requests_not_cached`
3. **Line Chart**: `cost_savings_usd` cumulative over time
4. **Histogram**: Distribution of cache ages

**🔧 Optimization Actions:**

| Observation | Action |
|-------------|--------|
| cache_hit_rate < 10% | Increase cache TTL (currently 24hr) |
| expired_entries > 50% | Run cleanup job more frequently |
| avg_cache_age > 1440min | Consider reducing TTL if data stale |
| cost_savings < $50/month | Acceptable for current scale |

---

## 🐛 False Positive Analysis

**Purpose:** Identify common patterns in AI feedback errors to improve prompts.

**Data Source:** `AIFeedbackDetailedRating` with `has_false_positives=True`

**Analysis Query (Django shell):**
```python
from cases.models import AIFeedbackDetailedRating

# Get recent false positives
fps = AIFeedbackDetailedRating.objects.filter(
    has_false_positives=True
).select_related('report__case').order_by('-rated_at')[:50]

# Analyze patterns
for fp in fps:
    print(f"Case: {fp.report.case.case_identifier}")
    print(f"Details: {fp.false_positive_details}")
    print(f"Overall Rating: {fp.overall_rating}/5")
    print("---")
```

**Common False Positive Patterns:**

1. **Overly Strict Language Requirements**
   - Symptom: AI flags missing terms that aren't clinically necessary
   - Fix: Update `key_concepts_text` to be more flexible
   - Example: AI requires "no fracture" but "intact bones" should suffice

2. **Context Misunderstanding**
   - Symptom: AI doesn't recognize valid alternative phrasings
   - Fix: Add examples to prompt template
   - Example: "pneumothorax" vs "collapsed lung"

3. **False Critical Discrepancies**
   - Symptom: AI labels non-critical items as critical
   - Fix: Refine severity assessment logic in prompt
   - Example: Missing measurement marked as critical for non-urgent finding

**📝 Action Workflow:**

```
1. Identify Pattern
   └─ Review false_positive_details from last 50 ratings

2. Categorize Issues
   ├─ Language/phrasing issues (50%)
   ├─ Severity assessment errors (30%)
   └─ Missing context (20%)

3. Update Prompt
   ├─ Add examples for common alternatives
   ├─ Clarify severity criteria
   └─ Improve context handling

4. Deploy & Monitor
   ├─ Create new PromptVersion
   ├─ Monitor false_positive_rate for 14 days
   └─ Compare to baseline

5. Document
   └─ Record pattern + fix in prompt changelog
```

---

## 📅 Recommended Monitoring Schedule

### Daily (5 minutes)

- [ ] Check cost trends for last 24 hours
- [ ] Verify cache hit rate >10%
- [ ] Alert if daily cost >$50

### Weekly (15 minutes)

- [ ] Review avg_overall for active prompt version
- [ ] Check false_positive_rate trend
- [ ] Review recent false positive comments
- [ ] Generate weekly cost report

### Monthly (1 hour)

- [ ] Full prompt version comparison analysis
- [ ] Decide on A/B test results
- [ ] Review cumulative cost savings from cache
- [ ] Update prompt based on false positive patterns
- [ ] Document changes in changelog

### Quarterly (2 hours)

- [ ] Deep dive into rating distribution
- [ ] User feedback synthesis
- [ ] Cost projection for next quarter
- [ ] Evaluate need for new prompt experiments

---

## 🎯 Key Performance Indicators (KPIs)

### Quality Metrics

| KPI | Target | Alert Threshold |
|-----|--------|-----------------|
| Average Overall Rating | ≥4.0/5.0 | <3.8 for 3 days |
| False Positive Rate | <10% | >15% for 1 week |
| Rating Participation | ≥30% of reports | <20% for 2 weeks |
| Prompt Version Improvement | +0.2 per iteration | No improvement after 3 versions |

### Cost Metrics

| KPI | Target | Alert Threshold |
|-----|--------|-----------------|
| Monthly AI API Cost | <$500 | >$600 |
| Cost Per Report | <$0.15 | >$0.25 |
| Cache Hit Rate | ≥15% | <10% for 3 days |
| Monthly Cache Savings | ≥$50 | <$20 |

### Engagement Metrics

| KPI | Target | Alert Threshold |
|-----|--------|-----------------|
| Reports with Feedback | 100% | <90% |
| Reports with Ratings | ≥30% | <20% |
| Avg Time to Rate | <24 hours | >72 hours |

---

## 🔧 Troubleshooting

### Issue: Low Cache Hit Rate (<10%)

**Possible Causes:**
1. Cache TTL too short (check `FeedbackCache.expires_at`)
2. Users submitting unique reports (good!)
3. Cache not being checked before API call

**Debug Steps:**
```python
from cases.models import FeedbackCache, TokenUsageLog
from django.utils import timezone
from datetime import timedelta

# Check cache table size
print(f"Total cache entries: {FeedbackCache.objects.count()}")

# Check recent cache usage
last_week = timezone.now() - timedelta(days=7)
logs = TokenUsageLog.objects.filter(created_at__gte=last_week)
print(f"Total requests: {logs.count()}")
print(f"Cached requests: {logs.filter(was_cached=True).count()}")
```

**Solutions:**
- If cache is empty → Check cache creation logic
- If cache full but low hits → Increase TTL or improve key generation
- If cache working as expected → Low hit rate may be normal for diverse reports

---

### Issue: Prompt Version Shows No Improvement

**Possible Causes:**
1. Insufficient sample size (<50 ratings)
2. Changes too subtle to detect
3. New version actually worse

**Debug Steps:**
```python
from cases.analytics_utils import get_prompt_version_comparison

# Compare versions
comparison = get_prompt_version_comparison(old_version_id, new_version_id)
print(f"v1 avg_overall: {comparison['version_1']['avg_overall']}")
print(f"v2 avg_overall: {comparison['version_2']['avg_overall']}")
print(f"Difference: {comparison['comparison']['overall_diff']}")
print(f"Sample sizes: v1={comparison['version_1']['rating_count']}, v2={comparison['version_2']['rating_count']}")
```

**Solutions:**
- If rating_count <50 → Continue monitoring
- If difference <0.1 → Changes too subtle, try bigger improvements
- If new version worse → Roll back, analyze what went wrong

---

### Issue: False Positive Rate Increasing

**Possible Causes:**
1. Prompt change introduced new issues
2. Cases getting more complex
3. Expert templates not updated

**Debug Steps:**
```python
from cases.models import AIFeedbackDetailedRating

# Analyze recent false positives
recent_fps = AIFeedbackDetailedRating.objects.filter(
    has_false_positives=True,
    rated_at__gte=timezone.now() - timedelta(days=7)
).select_related('report')

for fp in recent_fps:
    print(f"Report: {fp.report.id}")
    print(f"Details: {fp.false_positive_details}")
    print("---")
```

**Solutions:**
- If consistent pattern → Update prompt to address specific issue
- If random issues → May be case complexity (acceptable)
- If expert template issues → Update `key_concepts_text` for affected cases

---

## 📚 Advanced Analytics Queries

### Custom Queries (Django Shell)

```python
from cases.models import AIFeedbackDetailedRating, TokenUsageLog, PromptVersion
from django.db.models import Avg, Count, Sum
from django.utils import timezone
from datetime import timedelta

# 1. Rating distribution
rating_dist = AIFeedbackDetailedRating.objects.values('overall_rating').annotate(
    count=Count('id')
).order_by('overall_rating')

for item in rating_dist:
    print(f"{item['overall_rating']} stars: {item['count']} ratings")

# 2. Cost per prompt version
for version in PromptVersion.objects.all():
    logs = TokenUsageLog.objects.filter(prompt_version=version)
    total_cost = logs.aggregate(Sum('total_cost'))['total_cost__sum'] or 0
    count = logs.count()
    if count > 0:
        avg_cost = total_cost / count
        print(f"{version.version_number}: {count} requests, avg ${avg_cost:.4f}")

# 3. Ratings by case difficulty
difficulty_ratings = AIFeedbackDetailedRating.objects.values(
    'report__case__difficulty'
).annotate(
    avg_overall=Avg('overall_rating'),
    count=Count('id')
)

for item in difficulty_ratings:
    print(f"{item['report__case__difficulty']}: {item['avg_overall']:.2f} ({item['count']} ratings)")
```

---

## 📖 Related Documentation

- **API Endpoints**: See `API_ENDPOINTS.md` for endpoint details
- **Data Models**: See `@.claude/docs/DATA_MODELS.md` for database schema
- **Testing**: See `cases/tests/test_analytics.py` for analytics test examples

---

## 💡 Best Practices

### ✅ DO:
1. Monitor analytics at least weekly
2. Wait for ≥50 ratings before declaring A/B test winner
3. Document all prompt changes with baseline metrics
4. Track false positive patterns for continuous improvement
5. Set up cost alerts to avoid budget overruns

### ❌ DON'T:
1. Make multiple prompt changes simultaneously (confounds A/B testing)
2. Ignore low ratings without investigation
3. Deploy untested prompts to production
4. Skip documenting why a prompt version failed
5. Forget to deactivate old prompt versions after switching

---

**Last Updated:** 2025-01-12
**Phase:** 1 (Foundation)
**Maintainer:** AI Feedback Quality Team
