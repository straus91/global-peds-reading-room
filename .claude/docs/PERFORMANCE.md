# ⚡ Performance & Scalability Guide

## 🎯 Overview

This guide covers performance optimization and scalability strategies for Global Peds Reading Room. Focus areas include database query optimization, API rate limiting, caching strategies, and AI service efficiency.

---

## 📊 Current Performance Characteristics

### System Baseline
- **Database**: PostgreSQL with Django ORM
- **API Framework**: Django REST Framework
- **AI Service**: Google Gemini 2.5 Flash (fallback to 1.5)
- **Frontend**: Vanilla JavaScript (no framework overhead)

### Known Bottlenecks
1. **🤖 AI Feedback Generation**: 2-5 seconds per report
2. **🗄️ Complex Queries**: Case with full template structure
3. **🔢 Case Identifier Generation**: Sequential lookup on large datasets
4. **📊 Analytics Queries**: Aggregations without proper indexing

---

## 🔥 API Rate Limiting

### Google Gemini API Limits

**Location**: `backend/cases/llm_feedback_service.py:23-24`

**Current Configuration**:
```python
MAX_CALLS_PER_MINUTE = getattr(settings, 'GEMINI_API_RATE_LIMIT', 10)
API_CALL_HISTORY = []
```

**Free Tier Limits**:
- 60 requests per minute (RPM)
- 1,500 requests per day (RPD)

**Implementation Details** (lines 136-154):
- Sliding window rate limiting
- Automatic cleanup of old timestamps
- Built-in delay with jitter on limit reached

### Configuring Rate Limits

**In settings.py**:
```python
# backend/globalpeds_project/settings.py
GEMINI_API_RATE_LIMIT = 10  # Requests per minute
```

**In .env** (for environment-specific limits):
```env
GEMINI_API_RATE_LIMIT=10
```

### Monitoring API Usage

**Check rate limit status**:
```python
from cases.llm_feedback_service import API_CALL_HISTORY
import time

current_time = time.time()
recent_calls = [t for t in API_CALL_HISTORY if current_time - t < 60]
print(f"API calls in last minute: {len(recent_calls)}")
```

### Scalability Strategies

#### 1️⃣ Request Queuing
```python
# Implement Celery task queue for AI feedback
from celery import shared_task

@shared_task
def generate_ai_feedback_async(report_id):
    """Generate AI feedback asynchronously"""
    report = Report.objects.get(id=report_id)
    # Generate feedback...
    report.ai_feedback_content = feedback
    report.save()
```

#### 2️⃣ Response Caching
```python
# Cache identical reports to avoid redundant API calls
from django.core.cache import cache
import hashlib

def get_cached_feedback(user_content, expert_content):
    """Check cache before calling LLM"""
    cache_key = hashlib.md5(
        f"{user_content}{expert_content}".encode()
    ).hexdigest()

    cached = cache.get(f"ai_feedback_{cache_key}")
    if cached:
        return cached

    # Generate new feedback...
    feedback = get_feedback_from_llm(...)
    cache.set(f"ai_feedback_{cache_key}", feedback, timeout=3600*24)  # 24 hours
    return feedback
```

#### 3️⃣ Batch Processing
- Process multiple reports during off-peak hours
- Pre-generate feedback for common patterns
- Use priority queue for urgent vs background requests

---

## 🗄️ Database Optimization

### 1️⃣ Query Optimization Patterns

**Always Use select_related for Foreign Keys**:
```python
# ❌ BAD: N+1 queries
cases = Case.objects.filter(status='published')
for case in cases:
    print(case.master_template.name)  # New query each iteration!

# ✅ GOOD: 1 query with JOIN
cases = Case.objects.filter(status='published').select_related('master_template')
for case in cases:
    print(case.master_template.name)  # No additional query
```

**Always Use prefetch_related for Reverse Relations**:
```python
# ❌ BAD: N+1 queries
cases = Case.objects.filter(status='published')
for case in cases:
    reports = case.reports.all()  # New query each iteration!

# ✅ GOOD: 2 queries total (1 for cases, 1 for all reports)
cases = Case.objects.filter(status='published').prefetch_related('reports')
for case in cases:
    reports = case.reports.all()  # No additional query
```

**Complex Prefetch Example**:
```python
# Get cases with full template structure efficiently
cases = Case.objects.filter(status='published') \
    .select_related('master_template', 'created_by') \
    .prefetch_related(
        'master_template__sections',
        'applied_expert_templates__language',
        'applied_expert_templates__section_contents__master_section'
    )
```

### 2️⃣ Database Indexing

**Recommended Indexes**:

```python
# In backend/cases/models.py - Add to relevant models:

class Case(models.Model):
    # ...fields...

    class Meta:
        indexes = [
            models.Index(fields=['status']),  # Frequently filtered
            models.Index(fields=['case_identifier']),  # Unique lookups
            models.Index(fields=['-created_at']),  # Ordering
            models.Index(fields=['subspecialty', 'modality']),  # Combined filters
        ]

class Report(models.Model):
    # ...fields...

    class Meta:
        indexes = [
            models.Index(fields=['case', 'user', 'is_archived']),  # Common query
            models.Index(fields=['-submitted_at']),  # Ordering
        ]
```

**Create Migration for Indexes**:
```bash
python manage.py makemigrations --name add_performance_indexes
python manage.py migrate
```

### 3️⃣ Query Performance Monitoring

**Django Debug Toolbar** (Development Only):
```python
# In settings.py (only for DEBUG=True)
if DEBUG:
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
    INTERNAL_IPS = ['127.0.0.1']
```

**Query Logging** (Production):
```python
# In settings.py
LOGGING = {
    'version': 1,
    'handlers': {
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'queries.log',
        },
    },
    'loggers': {
        'django.db.backends': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}
```

**Slow Query Analysis**:
```sql
-- In PostgreSQL, enable slow query logging
ALTER DATABASE globalpeds_db SET log_min_duration_statement = 100;  -- Log queries > 100ms
```

---

## 💾 Caching Strategies

### 1️⃣ Template Structure Caching

```python
from django.core.cache import cache

def get_master_template_cached(template_id):
    """Cache template structure to avoid repeated queries"""
    cache_key = f"master_template_{template_id}"
    cached = cache.get(cache_key)

    if cached:
        return cached

    template = MasterTemplate.objects.get(id=template_id) \
        .prefetch_related('sections')

    cache.set(cache_key, template, timeout=3600)  # 1 hour
    return template
```

### 2️⃣ Published Cases Caching

```python
def get_published_cases_cached():
    """Cache list of published cases"""
    cache_key = "published_cases_list"
    cached = cache.get(cache_key)

    if cached:
        return cached

    cases = list(
        Case.objects.filter(status='published')
        .select_related('master_template')
        .values('id', 'case_identifier', 'title', 'difficulty')
    )

    cache.set(cache_key, cases, timeout=300)  # 5 minutes
    return cases
```

### 3️⃣ Cache Configuration

**Redis Backend** (Recommended for Production):
```python
# In settings.py
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'globalpeds',
        'TIMEOUT': 300,  # Default 5 minutes
    }
}
```

**Cache Invalidation**:
```python
# Invalidate cache when case published
def publish_case(case_id):
    case = Case.objects.get(id=case_id)
    case.status = 'published'
    case.save()

    # Invalidate caches
    cache.delete('published_cases_list')
    cache.delete(f"master_template_{case.master_template_id}")
```

---

## 🚀 Scalability Roadmap

### Phase 1: Current Scale (< 1000 users)
✅ **Implemented**:
- Basic query optimization
- LLM rate limiting
- JWT authentication

🔄 **Recommended**:
- Add database indexes
- Implement basic caching (template structures)
- Monitor query performance

### Phase 2: Growing Scale (1,000 - 10,000 users)
🎯 **Priority Actions**:
1. Implement Redis caching
2. Add Celery for async AI feedback
3. Optimize case identifier generation (database sequence)
4. Implement API endpoint rate limiting
5. Add database connection pooling (PgBouncer)

### Phase 3: Large Scale (10,000+ users)
⚡ **Advanced Strategies**:
1. PostgreSQL read replicas for analytics
2. CDN for static assets
3. Database partitioning (reports by date)
4. Load balancer with multiple app servers
5. Separate AI feedback service
6. Implement materialized views for analytics

---

## 📈 Performance Benchmarks

### Target Response Times

| Operation | Target | Acceptable | Action Required |
|-----------|--------|------------|-----------------|
| Case List API | < 200ms | < 500ms | > 500ms: Optimize queries |
| Case Detail API | < 300ms | < 700ms | > 700ms: Review prefetch |
| Report Submission | < 400ms | < 1s | > 1s: Check validators |
| AI Feedback | < 5s | < 10s | > 10s: Check API limits |
| Analytics Query | < 1s | < 3s | > 3s: Add indexes/caching |

### Load Testing

**Using Locust** (Python load testing tool):
```python
# locustfile.py
from locust import HttpUser, task, between

class GlobalPedsUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        """Login before testing"""
        response = self.client.post("/api/auth/login/", {
            "username": "testuser",
            "password": "testpass"
        })
        self.token = response.json()['access']

    @task(3)
    def view_cases(self):
        """Most common operation"""
        self.client.get(
            "/api/cases/",
            headers={"Authorization": f"Bearer {self.token}"}
        )

    @task(1)
    def submit_report(self):
        """Less frequent but important"""
        self.client.post(
            "/api/reports/",
            json={"case": 1, "structured_content": [...]},
            headers={"Authorization": f"Bearer {self.token}"}
        )
```

**Run Load Test**:
```bash
pip install locust
locust -f locustfile.py --host=http://localhost:8000
# Open http://localhost:8089 to start test
```

---

## 🔍 Performance Monitoring

### Key Metrics to Track

1. **📊 API Response Times**
   - Average, p50, p95, p99
   - By endpoint

2. **🗄️ Database Performance**
   - Query count per request
   - Slow query frequency (> 100ms)
   - Connection pool usage

3. **🤖 AI Service**
   - Requests per minute
   - Average response time
   - Error rate
   - API cost per request

4. **💾 Cache Performance**
   - Hit rate
   - Miss rate
   - Eviction rate

5. **👥 User Metrics**
   - Concurrent users
   - Requests per minute
   - User session duration

### Monitoring Tools

**Django Silk** (Query profiling):
```bash
pip install django-silk

# In settings.py
MIDDLEWARE += ['silk.middleware.SilkyMiddleware']
INSTALLED_APPS += ['silk']

# Run migration
python manage.py migrate

# Access at /silk/
```

**Sentry** (Error tracking & performance):
```python
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn=os.environ.get('SENTRY_DSN'),
    integrations=[DjangoIntegration()],
    traces_sample_rate=0.1,  # Sample 10% of transactions
    profiles_sample_rate=0.1,
)
```

---

## 💡 Optimization Checklist

### Before Deploying New Features

- [ ] Complete risk assessment (@.claude/docs/RISK_ASSESSMENT.md)
- [ ] Use select_related/prefetch_related for all queries
- [ ] Test with realistic data volume (100+ records)
- [ ] Check query count with Django Debug Toolbar
- [ ] Verify no N+1 query patterns
- [ ] Add database indexes for new filters
- [ ] Consider caching for frequently accessed data
- [ ] Test AI feedback with rate limiting active
- [ ] Benchmark response times under load
- [ ] Review API payload size (minimize data transfer)

### Regular Performance Audits

**Monthly**:
- [ ] Review slow query log
- [ ] Analyze cache hit rates
- [ ] Check AI API usage and costs
- [ ] Review user growth trends

**Quarterly**:
- [ ] Load test with 2x current user base
- [ ] Database vacuum and analyze
- [ ] Review and update indexes
- [ ] Audit unused queries in code
- [ ] Update scalability plan based on growth

---

## 🛠️ Troubleshooting Performance Issues

### Issue: Slow Case List Loading

**Diagnosis**:
```python
from django.db import connection
from django.test.utils import override_settings

with override_settings(DEBUG=True):
    cases = Case.objects.filter(status='published')
    list(cases)  # Force evaluation
    print(f"Query count: {len(connection.queries)}")
    for q in connection.queries:
        print(q['sql'][:100])
```

**Solutions**:
1. Add select_related for master_template
2. Add prefetch_related for reports if needed
3. Use values() if only need specific fields
4. Implement pagination
5. Add caching

### Issue: AI Feedback Timeouts

**Diagnosis**:
```python
# Check API call history
from cases.llm_feedback_service import API_CALL_HISTORY
print(f"Recent API calls: {len(API_CALL_HISTORY)}")
```

**Solutions**:
1. Increase rate limit if within API quota
2. Implement async processing with Celery
3. Add user notification when feedback ready
4. Cache feedback for identical reports
5. Consider upgrading to paid API tier

### Issue: Database Connection Pool Exhausted

**Symptoms**: "Too many connections" errors

**Solutions**:
```python
# In settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'CONN_MAX_AGE': 600,  # Reuse connections for 10 minutes
        # ... other settings
    }
}

# Or use PgBouncer connection pooler
```

---

## 📚 Related Documentation

- @.claude/docs/DATA_MODELS.md - Understand query relationships
- @.claude/docs/RISK_ASSESSMENT.md - Assess performance impact of changes
- @.claude/docs/MONITORING.md - Production performance monitoring
- @.claude/docs/TESTING.md - Performance testing strategies

---

**💡 Remember**: Premature optimization is the root of all evil, but planning for scalability from the start prevents costly rewrites later. Always measure before and after optimizations to validate improvements.
