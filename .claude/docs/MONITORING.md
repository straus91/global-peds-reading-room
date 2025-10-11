# 📊 Monitoring, Metrics & Analytics

## 🎯 Overview

This guide covers data-driven monitoring strategies, analytics queries, and metrics collection for Global Peds Reading Room. Effective monitoring enables continuous improvement, early issue detection, and evidence-based decision-making.

---

## 📈 Key Metrics to Track

### 1️⃣ User Engagement Metrics

#### Case Views
**Purpose**: Understand which cases are most popular and engaging.

**Query**:
```python
from django.db.models import Count
from cases.models import Case

# Most viewed cases
popular_cases = Case.objects.filter(status='published') \
    .annotate(view_count=Count('viewed_by')) \
    .order_by('-view_count')[:10]

for case in popular_cases:
    print(f"{case.case_identifier}: {case.view_count} views")
```

**Dashboard Metrics**:
- Total views per case
- Views over time (trend)
- View-to-report conversion rate
- Average time between view and report submission

#### Report Submissions
**Purpose**: Track user activity and engagement with reporting feature.

**Query**:
```python
from cases.models import Report
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta

# Reports submitted in last 7 days
last_week = timezone.now() - timedelta(days=7)
recent_reports = Report.objects.filter(
    submitted_at__gte=last_week
).count()

# Reports by difficulty level
reports_by_difficulty = Report.objects.values(
    'case__difficulty'
).annotate(
    count=Count('id')
).order_by('-count')
```

**Dashboard Metrics**:
- Total reports submitted (daily/weekly/monthly)
- Reports per user (identify power users)
- Reports per case (identify engaging cases)
- Submission time distribution (when are users most active?)

#### User Progress Tracking
**Purpose**: Measure learning progression and improvement.

**Query**:
```python
from django.db.models import Q

def get_user_progress(user):
    """Calculate user learning metrics"""
    reports = Report.objects.filter(
        user=user,
        is_archived=False
    ).select_related('case')

    # Group by difficulty
    beginner_count = reports.filter(case__difficulty='beginner').count()
    intermediate_count = reports.filter(case__difficulty='intermediate').count()
    advanced_count = reports.filter(case__difficulty='advanced').count()

    return {
        'total_reports': reports.count(),
        'by_difficulty': {
            'beginner': beginner_count,
            'intermediate': intermediate_count,
            'advanced': advanced_count
        },
        'cases_attempted': reports.values('case').distinct().count()
    }
```

---

### 2️⃣ AI Feedback Quality Metrics

#### Average Ratings
**Purpose**: Monitor AI feedback quality to identify areas for prompt improvement.

**Query**:
```python
from django.db.models import Avg, Count
from cases.models import AIFeedbackRating

# Overall average rating
overall_avg = AIFeedbackRating.objects.aggregate(
    Avg('star_rating')
)['star_rating__avg']

# Average by case difficulty
ratings_by_difficulty = AIFeedbackRating.objects.values(
    'report__case__difficulty'
).annotate(
    avg_rating=Avg('star_rating'),
    rating_count=Count('id')
)

print(f"Overall AI Feedback Rating: {overall_avg:.2f}/5.00")
for item in ratings_by_difficulty:
    print(f"{item['report__case__difficulty']}: {item['avg_rating']:.2f} ({item['rating_count']} ratings)")
```

**⚠️ Important**: Track ratings over time to detect degradation after prompt changes!

#### Rating Distribution
**Purpose**: Understand sentiment distribution (are most ratings 5-star or 1-star?).

**Query**:
```python
# Distribution of ratings
rating_distribution = AIFeedbackRating.objects.values(
    'star_rating'
).annotate(
    count=Count('id')
).order_by('star_rating')

for item in rating_distribution:
    print(f"{item['star_rating']} stars: {item['count']} ratings")
```

#### Low-Rated Feedback Analysis
**Purpose**: Identify problematic AI responses for prompt refinement.

**Query**:
```python
# Get low-rated feedback for manual review
low_rated = AIFeedbackRating.objects.filter(
    star_rating__lte=2
).select_related('report__case').prefetch_related('report')[:20]

for rating in low_rated:
    print(f"Case: {rating.report.case.case_identifier}")
    print(f"Rating: {rating.star_rating}/5")
    print(f"Comment: {rating.comment}")
    print(f"AI Feedback: {rating.report.ai_feedback_content.get('raw_feedback', '')[:200]}")
    print("-" * 80)
```

**Data-Driven Action Items**:
1. If average rating drops below 3.5, review recent prompt changes
2. Analyze comments from low-rated feedback for patterns
3. Test prompt variations with historical reports
4. Track rating trends after each prompt update

---

### 3️⃣ AI Service Performance Metrics

#### API Call Volume
**Purpose**: Monitor usage against quotas and costs.

**Location**: `backend/cases/llm_feedback_service.py:23-24`

**Query**:
```python
import time
from cases.llm_feedback_service import API_CALL_HISTORY

# Check current rate
current_time = time.time()
recent_calls = [t for t in API_CALL_HISTORY if current_time - t < 60]
print(f"API calls in last minute: {len(recent_calls)}")
```

**Logging** (already implemented in llm_feedback_service.py:371-373):
```python
elapsed_time = time.time() - start_time
logger.info(f"LLM response received in {elapsed_time:.2f} seconds (Case ID: '{case_identifier_for_llm}')")
```

**Dashboard Metrics**:
- API calls per minute/hour/day
- Average response time
- Error rate (failed API calls)
- Cost per report (track against Google Cloud billing)
- Requests hitting rate limit

#### Cost Tracking
**Purpose**: Monitor AI service costs to stay within budget.

**Query**:
```python
# Count reports with AI feedback generated
from django.db.models import Q

reports_with_feedback = Report.objects.filter(
    ~Q(ai_feedback_content={})
).count()

# Estimate cost (example: $0.01 per request)
estimated_cost = reports_with_feedback * 0.01
print(f"Estimated AI cost: ${estimated_cost:.2f}")
```

**💡 Best Practice**: Set up billing alerts in Google Cloud Console!

---

### 4️⃣ System Health Metrics

#### Database Performance
**Purpose**: Detect slow queries before they impact users.

**Enable Slow Query Logging** (PostgreSQL):
```sql
-- Log queries taking longer than 100ms
ALTER SYSTEM SET log_min_duration_statement = 100;
SELECT pg_reload_conf();

-- View slow queries
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
WHERE mean_time > 100
ORDER BY mean_time DESC
LIMIT 10;
```

**Monitor Connection Pool**:
```python
from django.db import connection

def get_db_stats():
    """Get database connection statistics"""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT count(*) as total_connections
            FROM pg_stat_activity
            WHERE datname = current_database();
        """)
        return cursor.fetchone()[0]
```

#### API Response Times
**Purpose**: Ensure acceptable user experience.

**Django Middleware for Timing**:
```python
# backend/globalpeds_project/middleware.py
import time
import logging

logger = logging.getLogger('api_timing')

class APITimingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()

        response = self.get_response(request)

        duration = time.time() - start_time

        if request.path.startswith('/api/'):
            logger.info(f"{request.method} {request.path} - {response.status_code} - {duration:.3f}s")

            # Alert on slow requests
            if duration > 2.0:
                logger.warning(f"SLOW REQUEST: {request.path} took {duration:.3f}s")

        return response
```

**Add to settings.py**:
```python
MIDDLEWARE = [
    # ... other middleware
    'globalpeds_project.middleware.APITimingMiddleware',
]
```

---

## 📝 Logging Strategy

### Log Levels & Usage

| Level | When to Use | Example |
|-------|-------------|---------|
| DEBUG | Development only | Variable values, function entry/exit |
| INFO | Normal operation | API calls, user actions, performance metrics |
| WARNING | Recoverable issues | Rate limit reached, validation failures |
| ERROR | Operation failed | API errors, database errors, exceptions |
| CRITICAL | System-wide failure | Database down, service unavailable |

### Logging Configuration

**In settings.py**:
```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'django.log'),
            'maxBytes': 1024 * 1024 * 15,  # 15MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'api_timing_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'api_timing.log'),
            'maxBytes': 1024 * 1024 * 10,  # 10MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'cases': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'api_timing': {
            'handlers': ['api_timing_file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
```

**Create logs directory**:
```bash
mkdir backend/logs
# Add to .gitignore
echo "logs/" >> backend/.gitignore
```

### Logging Best Practices

**✅ DO**:
```python
# Good: Structured logging with context
logger.info(
    f"AI feedback generated for report {report.id}, "
    f"case {report.case.case_identifier}, "
    f"response time {elapsed:.2f}s"
)

# Good: Log exceptions with traceback
try:
    feedback = get_feedback_from_llm(...)
except Exception as e:
    logger.error(f"AI feedback failed for report {report.id}: {e}", exc_info=True)
```

**❌ DON'T**:
```python
# Bad: No context
logger.info("Feedback generated")

# Bad: Logging sensitive data
logger.info(f"User password: {password}")  # NEVER log passwords/keys!

# Bad: Logging in tight loops
for item in large_list:
    logger.debug(f"Processing {item}")  # Use INFO for aggregates instead
```

---

## 📊 Analytics Dashboard Queries

### User Engagement Dashboard

```python
from django.db.models import Count, Avg, Q
from django.utils import timezone
from datetime import timedelta

def get_engagement_metrics():
    """Get comprehensive engagement metrics"""
    last_30_days = timezone.now() - timedelta(days=30)

    return {
        'total_users': User.objects.filter(is_active=True).count(),
        'active_users_30d': User.objects.filter(
            reports__submitted_at__gte=last_30_days
        ).distinct().count(),

        'total_cases': Case.objects.filter(status='published').count(),
        'total_reports': Report.objects.filter(is_archived=False).count(),

        'reports_last_30d': Report.objects.filter(
            submitted_at__gte=last_30_days
        ).count(),

        'avg_reports_per_user': Report.objects.values('user').annotate(
            count=Count('id')
        ).aggregate(Avg('count'))['count__avg'],

        'most_popular_case': Case.objects.annotate(
            view_count=Count('viewed_by')
        ).order_by('-view_count').first(),
    }
```

### AI Feedback Quality Dashboard

```python
def get_ai_quality_metrics():
    """Get AI feedback quality metrics"""
    last_30_days = timezone.now() - timedelta(days=30)

    return {
        'overall_rating': AIFeedbackRating.objects.aggregate(
            Avg('star_rating')
        )['star_rating__avg'],

        'rating_trend_30d': AIFeedbackRating.objects.filter(
            rated_at__gte=last_30_days
        ).aggregate(Avg('star_rating'))['star_rating__avg'],

        'total_ratings': AIFeedbackRating.objects.count(),
        'ratings_with_comments': AIFeedbackRating.objects.exclude(
            Q(comment='') | Q(comment__isnull=True)
        ).count(),

        'low_rated_count': AIFeedbackRating.objects.filter(
            star_rating__lte=2
        ).count(),

        'rating_distribution': list(
            AIFeedbackRating.objects.values('star_rating').annotate(
                count=Count('id')
            ).order_by('star_rating')
        ),
    }
```

### System Performance Dashboard

```python
def get_performance_metrics():
    """Get system performance metrics"""
    last_hour = timezone.now() - timedelta(hours=1)

    # Requires logging analysis (parse logs for API timing)
    # This is a placeholder structure
    return {
        'avg_api_response_time': 0.35,  # Parse from api_timing.log
        'slow_requests_count': 5,  # Count requests > 2s
        'error_rate': 0.01,  # Parse from error logs

        'ai_calls_last_hour': len([
            t for t in API_CALL_HISTORY
            if timezone.now().timestamp() - t < 3600
        ]),

        'database_connections': get_db_stats(),
    }
```

---

## 🚨 Alerting & Notifications

### Critical Alerts (Immediate Action Required)

**1. AI Service Down**:
```python
# In llm_feedback_service.py error handling
if consecutive_failures > 5:
    send_alert(
        severity='critical',
        message='AI service has failed 5 times in a row',
        details={'error': str(error), 'timestamp': timezone.now()}
    )
```

**2. Database Connection Pool Exhausted**:
Monitor connection count and alert when > 80% capacity.

**3. Average AI Rating Drops Below 3.0**:
```python
def check_ai_quality():
    """Run daily to check AI feedback quality"""
    avg_rating = AIFeedbackRating.objects.filter(
        rated_at__gte=timezone.now() - timedelta(days=7)
    ).aggregate(Avg('star_rating'))['star_rating__avg']

    if avg_rating and avg_rating < 3.0:
        send_alert(
            severity='high',
            message=f'AI feedback quality degraded: {avg_rating:.2f}/5.00'
        )
```

### Warning Alerts (Monitor Closely)

1. API response time > 1s for more than 10 requests/hour
2. AI API calls approaching quota limit
3. Error rate > 1%
4. No reports submitted in 24 hours (unusual for active system)

---

## 📚 Data-Driven Decision Making

### Example: Improving AI Feedback Prompts

**1. Collect Data**:
```python
# Get feedback with low ratings and comments
problem_cases = AIFeedbackRating.objects.filter(
    star_rating__lte=2
).exclude(comment='').select_related('report__case')

# Analyze common themes in comments
comments = [rating.comment for rating in problem_cases]
```

**2. Identify Patterns**:
- Are low ratings concentrated in specific case difficulties?
- Do comments mention "too vague" or "not helpful"?
- Are certain sections consistently rated poorly?

**3. Test Changes**:
```python
# Before making prompt changes, save current metrics
baseline_rating = AIFeedbackRating.objects.filter(
    rated_at__gte=timezone.now() - timedelta(days=7)
).aggregate(Avg('star_rating'))['star_rating__avg']

# After deploying new prompt, compare
new_rating = AIFeedbackRating.objects.filter(
    rated_at__gte=timezone.now() - timedelta(days=7)
).aggregate(Avg('star_rating'))['star_rating__avg']

improvement = new_rating - baseline_rating
print(f"Rating change: {improvement:+.2f} points")
```

**4. Document Results**:
Track all prompt changes with before/after metrics in a changelog.

---

## 📚 Related Documentation

- @.claude/docs/DATA_MODELS.md - Understanding data relationships for queries
- @.claude/docs/PERFORMANCE.md - Optimizing analytics queries
- @.claude/docs/TESTING.md - Testing analytics logic
- @.claude/docs/RISK_ASSESSMENT.md - Assess impact of monitoring changes

---

**💡 Key Principle**: Monitor what matters to users (feedback quality, response times) and what matters to the business (costs, engagement). Data without action is just noise!
