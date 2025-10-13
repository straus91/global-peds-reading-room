# 📋 Phase 1: Foundation Improvements - Comprehensive Implementation Plan

## 🎯 Executive Summary

**Goal**: Build data-driven iteration infrastructure to monitor, optimize, and scale AI feedback system.

**Duration**: 2 weeks (10 working days)

**Risk Level**: 🟡 MEDIUM (database schema changes, new caching layer, cost tracking)

**Success Criteria**:
- ✅ Dashboard operational with real-time metrics
- ✅ Baseline metrics established (14 days of data collection)
- ✅ Cache hit rate >20% after 1 month
- ✅ Token usage tracked per case/subspecialty
- ✅ Prompt version management with A/B testing capability

---

## 📊 Architecture Design

### 1️⃣ Database Schema Design

#### **New Model: AIFeedbackDetailedRating**
**Purpose**: Replace single star rating with multi-dimensional quality tracking

**Schema**:
```python
class AIFeedbackDetailedRating(models.Model):
    """
    Multi-dimensional rating for AI feedback quality.
    Replaces simple star rating with category-specific scoring.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Relationships
    report = models.ForeignKey(
        'Report',
        on_delete=models.CASCADE,
        related_name='detailed_feedback_ratings'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='detailed_feedback_ratings_given'
    )

    # Multi-dimensional ratings (1-5 scale)
    accuracy_rating = models.IntegerField(
        choices=[(i, str(i)) for i in range(1, 6)],
        help_text="How accurate was the AI feedback?"
    )
    helpfulness_rating = models.IntegerField(
        choices=[(i, str(i)) for i in range(1, 6)],
        help_text="How helpful was the feedback for learning?"
    )
    actionability_rating = models.IntegerField(
        choices=[(i, str(i)) for i in range(1, 6)],
        help_text="How actionable/specific were the suggestions?"
    )

    # Overall satisfaction (derived or separate)
    overall_rating = models.IntegerField(
        choices=[(i, str(i)) for i in range(1, 6)],
        help_text="Overall satisfaction with AI feedback"
    )

    # False positive tracking
    has_false_positives = models.BooleanField(
        default=False,
        help_text="Did AI incorrectly flag issues?"
    )
    false_positive_details = models.TextField(
        blank=True,
        null=True,
        help_text="Details about false positives if any"
    )

    # Optional comment
    comment = models.TextField(blank=True, null=True)

    # Timestamps
    rated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-rated_at']
        unique_together = ('report', 'user')
        indexes = [
            models.Index(fields=['rated_at']),
            models.Index(fields=['accuracy_rating']),
            models.Index(fields=['helpfulness_rating']),
            models.Index(fields=['actionability_rating']),
            models.Index(fields=['has_false_positives']),
        ]
```

**Indexes Rationale**:
- `rated_at`: Time-series analytics (ratings over time)
- Individual rating fields: Distribution analysis and filtering
- `has_false_positives`: Quick filtering for quality issues

**Cascade Behavior**:
- Report deleted → Rating deleted (CASCADE)
- User deleted → Rating deleted (CASCADE)

---

#### **New Model: FeedbackCache**
**Purpose**: Hash-based report caching to reduce AI API costs

**Schema**:
```python
class FeedbackCache(models.Model):
    """
    Cache for AI-generated feedback based on report content hash.
    Reduces API costs by serving cached feedback for identical reports.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Cache key (hash of report content)
    content_hash = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        help_text="SHA256 hash of (user_sections + expert_sections + case_context)"
    )

    # Cached data
    feedback_content = models.JSONField(
        help_text="Cached AI feedback response (structured JSON)"
    )

    # Metadata
    case = models.ForeignKey(
        'Case',
        on_delete=models.CASCADE,
        related_name='feedback_caches',
        help_text="Case for which feedback was generated"
    )
    prompt_version = models.ForeignKey(
        'PromptVersion',
        on_delete=models.SET_NULL,
        null=True,
        related_name='cached_feedbacks'
    )

    # Usage tracking
    hit_count = models.IntegerField(
        default=0,
        help_text="Number of times this cache entry was served"
    )
    last_hit_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last time cache was hit"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(
        help_text="Cache expiration (invalidate after prompt changes)"
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['content_hash']),  # Primary lookup
            models.Index(fields=['case', 'created_at']),  # Analytics
            models.Index(fields=['expires_at']),  # Cleanup queries
            models.Index(fields=['hit_count']),  # Popular cache entries
        ]
```

**Cache Key Strategy**:
```python
def generate_cache_key(user_sections, expert_sections, case_context):
    """
    Generate deterministic cache key from report content.

    Components:
    - user_sections: User's report content (normalized)
    - expert_sections: Expert template content
    - case_context: Case-specific data (diagnosis, key_findings)

    Returns: SHA256 hash (64 chars)
    """
    import hashlib
    import json

    # Normalize and sort for deterministic hashing
    normalized = {
        'user': sorted([
            {
                'section_id': s['master_template_section_id'],
                'content': s['content'].strip().lower()
            }
            for s in user_sections
        ], key=lambda x: x['section_id']),
        'expert': sorted([
            {
                'section_id': s['master_section_id'],
                'key_concepts': s.get('key_concepts_text', '').strip().lower()
            }
            for s in expert_sections
        ], key=lambda x: x['section_id']),
        'case': {
            'diagnosis': case_context['diagnosis'].strip().lower(),
            'key_findings': case_context['key_findings'].strip().lower()
        }
    }

    content_str = json.dumps(normalized, sort_keys=True)
    return hashlib.sha256(content_str.encode()).hexdigest()
```

**Cache Invalidation Strategy**:
1. **Time-based**: Expire after 30 days (or when prompt version changes)
2. **Prompt-based**: When new PromptVersion is set as active, mark old caches as expired
3. **Manual**: Admin can clear cache for specific cases/subspecialties

**Indexes Rationale**:
- `content_hash`: PRIMARY cache lookup (O(1) performance critical)
- `case + created_at`: Analytics per case
- `expires_at`: Efficient cleanup of expired entries
- `hit_count`: Identify most valuable cache entries

---

#### **New Model: PromptVersion**
**Purpose**: Store, version, and A/B test different AI feedback prompts

**Schema**:
```python
class PromptVersion(models.Model):
    """
    Version control for AI feedback prompts.
    Enables A/B testing, performance tracking, and easy rollback.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Version metadata
    version_number = models.CharField(
        max_length=20,
        unique=True,
        help_text="Semantic version (e.g., 'v1.2.3', 'v2.0.0')"
    )
    name = models.CharField(
        max_length=200,
        help_text="Human-readable name (e.g., 'Improved Specificity v2')"
    )
    description = models.TextField(
        help_text="What changed in this version and why"
    )

    # Prompt content
    prompt_template = models.TextField(
        help_text="Full prompt template with placeholders"
    )

    # Status
    is_active = models.BooleanField(
        default=False,
        help_text="Is this version currently in use?"
    )
    is_ab_test = models.BooleanField(
        default=False,
        help_text="Is this version part of an A/B test?"
    )
    ab_test_weight = models.IntegerField(
        default=0,
        help_text="Weight for A/B testing (0-100, higher = more traffic)"
    )

    # Performance tracking
    total_uses = models.IntegerField(
        default=0,
        help_text="Number of times this prompt was used"
    )
    average_rating = models.FloatField(
        null=True,
        blank=True,
        help_text="Average rating for feedback from this prompt (calculated)"
    )
    average_accuracy = models.FloatField(null=True, blank=True)
    average_helpfulness = models.FloatField(null=True, blank=True)
    average_actionability = models.FloatField(null=True, blank=True)

    # Cost tracking
    total_tokens_used = models.BigIntegerField(
        default=0,
        help_text="Total tokens consumed by this prompt version"
    )
    average_tokens_per_use = models.FloatField(
        null=True,
        blank=True,
        help_text="Average tokens per feedback generation"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    activated_at = models.DateTimeField(null=True, blank=True)
    deactivated_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='prompt_versions_created'
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['version_number']),
            models.Index(fields=['is_active']),
            models.Index(fields=['is_ab_test', 'ab_test_weight']),
            models.Index(fields=['average_rating']),
            models.Index(fields=['created_at']),
        ]
```

**A/B Testing Strategy**:
```python
def select_prompt_version():
    """
    Select prompt version based on A/B test weights.

    If A/B testing is active:
    - Get all prompt versions with is_ab_test=True
    - Select based on weighted random (ab_test_weight)

    Otherwise:
    - Return the single version with is_active=True
    """
    ab_test_versions = PromptVersion.objects.filter(
        is_ab_test=True
    ).values('id', 'ab_test_weight')

    if ab_test_versions.exists():
        # Weighted random selection
        import random
        total_weight = sum(v['ab_test_weight'] for v in ab_test_versions)
        rand = random.randint(1, total_weight)

        cumulative = 0
        for version in ab_test_versions:
            cumulative += version['ab_test_weight']
            if rand <= cumulative:
                return PromptVersion.objects.get(id=version['id'])

    # Fallback to active version
    return PromptVersion.objects.get(is_active=True)
```

**Rollback Procedure**:
1. Admin marks current version as `is_active=False`
2. Admin marks previous version as `is_active=True`
3. System invalidates all caches referencing old version
4. New feedback uses rolled-back prompt

**Indexes Rationale**:
- `version_number`: Lookup by version string
- `is_active`: Quick retrieval of active prompt
- `is_ab_test + ab_test_weight`: A/B test selection
- `average_rating`: Performance comparisons
- `created_at`: Version history timeline

---

#### **New Model: TokenUsageLog**
**Purpose**: Track AI API token consumption and costs per request

**Schema**:
```python
class TokenUsageLog(models.Model):
    """
    Log of token usage for each AI feedback generation.
    Enables cost tracking, budget monitoring, and optimization.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Request context
    report = models.ForeignKey(
        'Report',
        on_delete=models.CASCADE,
        related_name='token_usage_logs'
    )
    case = models.ForeignKey(
        'Case',
        on_delete=models.CASCADE,
        related_name='token_usage_logs'
    )
    prompt_version = models.ForeignKey(
        'PromptVersion',
        on_delete=models.SET_NULL,
        null=True,
        related_name='token_usage_logs'
    )

    # Token metrics
    input_tokens = models.IntegerField(
        help_text="Tokens in prompt (input)"
    )
    output_tokens = models.IntegerField(
        help_text="Tokens in response (output)"
    )
    total_tokens = models.IntegerField(
        help_text="input_tokens + output_tokens"
    )

    # Cost calculation (example: Gemini 2.5 Flash pricing)
    input_cost = models.DecimalField(
        max_digits=10,
        decimal_places=6,
        help_text="Cost for input tokens (USD)"
    )
    output_cost = models.DecimalField(
        max_digits=10,
        decimal_places=6,
        help_text="Cost for output tokens (USD)"
    )
    total_cost = models.DecimalField(
        max_digits=10,
        decimal_places=6,
        help_text="Total cost for this request (USD)"
    )

    # Performance metrics
    response_time_ms = models.IntegerField(
        help_text="Time to receive response (milliseconds)"
    )

    # Cache status
    was_cached = models.BooleanField(
        default=False,
        help_text="Was this served from cache?"
    )

    # Model details
    model_name = models.CharField(
        max_length=100,
        help_text="AI model used (e.g., 'gemini-2.5-flash')"
    )

    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['created_at']),  # Time-series queries
            models.Index(fields=['case', 'created_at']),  # Cost per case
            models.Index(fields=['was_cached']),  # Cache effectiveness
            models.Index(fields=['total_cost']),  # Expensive requests
            models.Index(fields=['prompt_version', 'created_at']),  # Cost per version
        ]
```

**Cost Calculation Logic**:
```python
# Gemini 2.5 Flash pricing (as of 2025)
# Input: $0.075 per 1M tokens
# Output: $0.30 per 1M tokens

def calculate_cost(input_tokens, output_tokens, model_name='gemini-2.5-flash'):
    """Calculate cost based on token usage and model pricing."""
    pricing = {
        'gemini-2.5-flash': {
            'input': 0.075 / 1_000_000,  # per token
            'output': 0.30 / 1_000_000
        },
        'gemini-1.5-flash': {
            'input': 0.075 / 1_000_000,
            'output': 0.30 / 1_000_000
        }
    }

    rates = pricing.get(model_name, pricing['gemini-2.5-flash'])
    input_cost = input_tokens * rates['input']
    output_cost = output_tokens * rates['output']

    return {
        'input_cost': round(input_cost, 6),
        'output_cost': round(output_cost, 6),
        'total_cost': round(input_cost + output_cost, 6)
    }
```

**Budget Alerting**:
```python
def check_budget_threshold():
    """Alert if daily cost exceeds threshold."""
    from django.utils import timezone
    from datetime import timedelta

    today = timezone.now().date()
    daily_cost = TokenUsageLog.objects.filter(
        created_at__date=today
    ).aggregate(Sum('total_cost'))['total_cost__sum'] or 0

    DAILY_BUDGET = 10.00  # $10/day threshold

    if daily_cost > DAILY_BUDGET:
        # Send alert to admins
        send_alert(
            severity='warning',
            message=f'Daily AI cost exceeded: ${daily_cost:.2f} (threshold: ${DAILY_BUDGET})'
        )
```

**Indexes Rationale**:
- `created_at`: Time-series cost analysis
- `case + created_at`: Cost per case/subspecialty
- `was_cached`: Cache savings calculation
- `total_cost`: Identify expensive outliers
- `prompt_version + created_at`: Cost comparison between versions

---

### 2️⃣ Data Relationships Diagram

```
┌─────────────────────────┐
│     PromptVersion       │
│  (Version control for   │
│   AI feedback prompts)  │
└───────────┬─────────────┘
            │
            │ FK (prompt_version)
            │
┌───────────▼─────────────┐        ┌─────────────────────────┐
│    FeedbackCache        │        │         Report          │
│  (Hash-based caching)   │        │  (User submissions)     │
└───────────┬─────────────┘        └──────────┬──────────────┘
            │                                  │
            │                                  │
            │ FK (case)                        │ FK (report)
            │                                  │
            │                      ┌───────────▼──────────────────────┐
            │                      │ AIFeedbackDetailedRating         │
            │                      │ (Multi-dimensional quality)      │
            │                      └──────────────────────────────────┘
            │
            │                      ┌──────────────────────────────────┐
            └──────────────────────┤      TokenUsageLog               │
                                   │ (Cost & performance tracking)    │
                                   └──────────────────────────────────┘
```

**Cascade Behavior Summary**:
- Report deleted → AIFeedbackDetailedRating deleted (CASCADE)
- Report deleted → TokenUsageLog deleted (CASCADE)
- Case deleted → FeedbackCache deleted (CASCADE)
- Case deleted → TokenUsageLog deleted (CASCADE)
- PromptVersion deleted → FeedbackCache.prompt_version = NULL (SET_NULL)
- PromptVersion deleted → TokenUsageLog.prompt_version = NULL (SET_NULL)

---

### 3️⃣ API Endpoint Specifications

#### **POST /api/reports/{report_id}/detailed-rating/**
**Purpose**: Submit multi-dimensional rating for AI feedback

**Request**:
```json
{
  "accuracy_rating": 5,
  "helpfulness_rating": 4,
  "actionability_rating": 5,
  "overall_rating": 5,
  "has_false_positives": false,
  "false_positive_details": "",
  "comment": "Very specific feedback, helped me understand my mistakes!"
}
```

**Response (201 Created)**:
```json
{
  "id": "uuid-here",
  "report_id": 123,
  "accuracy_rating": 5,
  "helpfulness_rating": 4,
  "actionability_rating": 5,
  "overall_rating": 5,
  "has_false_positives": false,
  "comment": "Very specific feedback...",
  "rated_at": "2025-10-12T14:30:00Z"
}
```

**Validation**:
- All ratings must be 1-5
- `has_false_positives=True` requires `false_positive_details`
- User can only rate once per report (unique constraint)

---

#### **GET /api/analytics/feedback-quality/**
**Purpose**: Dashboard metrics for feedback quality

**Query Parameters**:
- `start_date` (optional): Filter from date (ISO format)
- `end_date` (optional): Filter to date
- `case_difficulty` (optional): Filter by difficulty
- `subspecialty` (optional): Filter by subspecialty

**Response (200 OK)**:
```json
{
  "overall_metrics": {
    "total_ratings": 450,
    "average_accuracy": 4.2,
    "average_helpfulness": 4.5,
    "average_actionability": 4.1,
    "average_overall": 4.3,
    "false_positive_rate": 0.08
  },
  "by_difficulty": [
    {
      "difficulty": "beginner",
      "avg_accuracy": 4.5,
      "avg_helpfulness": 4.7,
      "avg_actionability": 4.4,
      "count": 150
    },
    {
      "difficulty": "intermediate",
      "avg_accuracy": 4.2,
      "avg_helpfulness": 4.4,
      "avg_actionability": 4.0,
      "count": 200
    },
    {
      "difficulty": "advanced",
      "avg_accuracy": 3.9,
      "avg_helpfulness": 4.2,
      "avg_actionability": 3.8,
      "count": 100
    }
  ],
  "trend_last_30_days": [
    {"date": "2025-09-12", "avg_overall": 4.1},
    {"date": "2025-09-13", "avg_overall": 4.2}
  ]
}
```

---

#### **GET /api/analytics/cache-performance/**
**Purpose**: Cache effectiveness metrics

**Response (200 OK)**:
```json
{
  "overall": {
    "total_requests": 1000,
    "cache_hits": 250,
    "cache_misses": 750,
    "hit_rate": 0.25,
    "estimated_savings": 62.50
  },
  "by_case": [
    {
      "case_identifier": "NR-MR-2025-0015",
      "hits": 50,
      "misses": 10,
      "hit_rate": 0.83
    }
  ],
  "cache_size": {
    "total_entries": 150,
    "expired_entries": 5,
    "active_entries": 145
  }
}
```

---

#### **GET /api/analytics/token-usage/**
**Purpose**: Cost tracking and budget monitoring

**Query Parameters**:
- `start_date`, `end_date`: Date range
- `groupby`: `day` | `case` | `subspecialty` | `prompt_version`

**Response (200 OK)**:
```json
{
  "summary": {
    "total_requests": 1000,
    "cached_requests": 250,
    "uncached_requests": 750,
    "total_tokens": 15000000,
    "total_cost": 3.75,
    "avg_cost_per_request": 0.00375
  },
  "by_day": [
    {
      "date": "2025-10-10",
      "requests": 45,
      "total_cost": 0.15,
      "avg_tokens": 15000
    }
  ],
  "expensive_cases": [
    {
      "case_identifier": "NR-MR-2025-0020",
      "avg_tokens": 20000,
      "avg_cost": 0.0075,
      "request_count": 10
    }
  ],
  "budget_status": {
    "daily_budget": 10.00,
    "today_cost": 0.42,
    "remaining": 9.58,
    "on_track": true
  }
}
```

---

#### **GET /api/admin/prompt-versions/**
**Purpose**: List all prompt versions with performance stats

**Response (200 OK)**:
```json
{
  "versions": [
    {
      "id": "uuid-1",
      "version_number": "v2.1.0",
      "name": "Improved Specificity",
      "is_active": true,
      "is_ab_test": false,
      "total_uses": 500,
      "average_rating": 4.5,
      "average_accuracy": 4.6,
      "average_helpfulness": 4.7,
      "average_actionability": 4.3,
      "total_tokens_used": 7500000,
      "average_tokens_per_use": 15000,
      "created_at": "2025-10-01T10:00:00Z"
    }
  ]
}
```

---

#### **POST /api/admin/prompt-versions/**
**Purpose**: Create new prompt version

**Request**:
```json
{
  "version_number": "v2.2.0",
  "name": "Enhanced Error Detection",
  "description": "Added section-specific error patterns...",
  "prompt_template": "You are an expert radiologist...",
  "is_active": false,
  "is_ab_test": false
}
```

---

#### **PATCH /api/admin/prompt-versions/{id}/activate/**
**Purpose**: Activate a prompt version (deactivates others)

**Response (200 OK)**:
```json
{
  "message": "Prompt version v2.2.0 activated successfully",
  "invalidated_caches": 150
}
```

**Side Effects**:
- Sets `is_active=True` for this version
- Sets `is_active=False` for all other versions
- Marks all `FeedbackCache` entries as expired

---

### 4️⃣ llm_feedback_service.py Enhancements

**Key Changes**:

1. **Cache lookup before API call**:
```python
def get_feedback_from_llm_with_cache(...):
    """
    Enhanced version with caching and token tracking.
    """
    # 1. Generate cache key
    cache_key = generate_cache_key(user_sections, expert_sections, case_context)

    # 2. Check cache
    cached = FeedbackCache.objects.filter(
        content_hash=cache_key,
        expires_at__gt=timezone.now()
    ).first()

    if cached:
        # Update hit metrics
        cached.hit_count += 1
        cached.last_hit_at = timezone.now()
        cached.save(update_fields=['hit_count', 'last_hit_at'])

        # Log as cached request (no token cost)
        TokenUsageLog.objects.create(
            report=report,
            case=case,
            prompt_version=cached.prompt_version,
            input_tokens=0,
            output_tokens=0,
            total_tokens=0,
            input_cost=0,
            output_cost=0,
            total_cost=0,
            was_cached=True,
            model_name='cache',
            response_time_ms=0
        )

        return cached.feedback_content

    # 3. Cache miss - call API
    prompt_version = select_prompt_version()

    start_time = time.time()
    response = call_gemini_api(prompt_version.prompt_template, ...)
    response_time_ms = int((time.time() - start_time) * 1000)

    # 4. Extract token usage from response
    token_usage = response.usage_metadata
    input_tokens = token_usage.prompt_token_count
    output_tokens = token_usage.candidates_token_count
    total_tokens = token_usage.total_token_count

    # 5. Calculate costs
    costs = calculate_cost(input_tokens, output_tokens, model_name)

    # 6. Log token usage
    TokenUsageLog.objects.create(
        report=report,
        case=case,
        prompt_version=prompt_version,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=total_tokens,
        input_cost=costs['input_cost'],
        output_cost=costs['output_cost'],
        total_cost=costs['total_cost'],
        was_cached=False,
        model_name=model_name,
        response_time_ms=response_time_ms
    )

    # 7. Store in cache
    FeedbackCache.objects.create(
        content_hash=cache_key,
        feedback_content=parsed_feedback,
        case=case,
        prompt_version=prompt_version,
        hit_count=0,
        expires_at=timezone.now() + timedelta(days=30)
    )

    # 8. Update prompt version metrics
    prompt_version.total_uses += 1
    prompt_version.total_tokens_used += total_tokens
    prompt_version.average_tokens_per_use = (
        prompt_version.total_tokens_used / prompt_version.total_uses
    )
    prompt_version.save()

    return parsed_feedback
```

---

## 🎯 Best Practices Analysis

### 1️⃣ Django Model Best Practices

✅ **UUID Primary Keys**:
- All new models use UUID for distributed systems compatibility
- Prevents ID enumeration attacks
- Safe for public API exposure

✅ **Meta Class Configuration**:
```python
class Meta:
    ordering = ['-created_at']  # Default ordering
    indexes = [...]  # Explicit index definitions
    unique_together = [...]  # Composite uniqueness
```

✅ **Related Names**:
- Descriptive `related_name` for reverse lookups
- Example: `report.detailed_feedback_ratings.all()`

✅ **Help Text**:
- Every field has comprehensive help_text
- Aids admin interface usability

✅ **on_delete Behavior**:
- `CASCADE`: Delete ratings when report deleted (data tied to report)
- `SET_NULL`: Keep logs when prompt version deleted (historical tracking)

---

### 2️⃣ Database Design Best Practices

✅ **Normalization**:
- Separate concerns (ratings, caching, logs, versions)
- No redundant data storage
- Clear single responsibility per model

✅ **Denormalization for Performance**:
- `PromptVersion.average_rating` (calculated field, updated periodically)
- `FeedbackCache.hit_count` (incremented on access)
- Trade-off: Slight redundancy for faster queries

✅ **Index Strategy**:
- Index all foreign keys (Django does this automatically)
- Index fields used in WHERE clauses
- Index fields used in ORDER BY
- Composite indexes for common filter combinations
- **Avoid over-indexing**: Every index slows down writes

✅ **JSONField Usage**:
- `feedback_content`: Variable structure (different feedback formats)
- **Downside**: Can't efficiently query JSON content
- **Mitigation**: Store queryable fields as separate columns

---

### 3️⃣ API Design Best Practices

✅ **RESTful Conventions**:
- `POST /reports/{id}/detailed-rating/` - Create rating
- `GET /analytics/feedback-quality/` - Read metrics
- `PATCH /prompt-versions/{id}/activate/` - Partial update

✅ **Versioning Strategy**:
- URL versioning: `/api/v1/...`
- Allows backward compatibility when changes needed

✅ **Pagination**:
- Large result sets paginated (Django REST Framework default)
- Example: 20 results per page for analytics endpoints

✅ **Error Handling**:
```python
# Standardized error responses
{
  "error": "Validation failed",
  "details": {
    "accuracy_rating": ["This field is required"],
    "overall_rating": ["Must be between 1 and 5"]
  }
}
```

✅ **Authentication**:
- JWT tokens required for all endpoints
- Analytics endpoints: Admin-only

---

### 4️⃣ Security Best Practices

✅ **Input Validation**:
- Django serializers validate all inputs
- Rating values constrained to 1-5 range
- Text fields sanitized (existing `sanitize_text` function)

✅ **SQL Injection Prevention**:
- Django ORM automatically parameterizes queries
- **Never** use raw SQL with string formatting

✅ **Access Control**:
```python
# Admin-only endpoints
permission_classes = [IsAdminUser]

# User can only rate their own reports
def perform_create(self, serializer):
    if serializer.validated_data['report'].user != self.request.user:
        raise PermissionDenied("Cannot rate another user's report")
    serializer.save(user=self.request.user)
```

✅ **Rate Limiting**:
- Existing rate limiting for AI API (10 calls/min)
- Consider adding rate limiting for analytics endpoints (prevent abuse)

---

## 📊 Data-Driven Strategy

### 1️⃣ Metrics Collection Methodology

**Phase 1: Baseline Establishment (Days 1-14)**
- Deploy models with all tracking enabled
- Collect data WITHOUT changing AI prompts
- Establish baseline metrics:
  - Average accuracy rating: ___ (target: 4.0+)
  - Average helpfulness: ___ (target: 4.0+)
  - Average actionability: ___ (target: 4.0+)
  - Cache hit rate: ___ (target: 20%+)
  - Average cost per report: ___ (target: <$0.01)
  - False positive rate: ___ (target: <10%)

**Phase 2: Continuous Monitoring (Ongoing)**
- Daily dashboard review
- Weekly trend analysis
- Monthly prompt optimization based on ratings

---

### 2️⃣ Dashboard Design

**Primary Dashboard: Feedback Quality**

Layout:
```
┌─────────────────────────────────────────────────────┐
│  AI Feedback Quality Dashboard                      │
├─────────────────────────────────────────────────────┤
│  Overall Metrics (Last 30 Days)                     │
│  ┌─────────────┬─────────────┬─────────────┐       │
│  │ Accuracy    │ Helpfulness │ Actionability│       │
│  │   4.2/5.0   │   4.5/5.0   │   4.1/5.0    │       │
│  └─────────────┴─────────────┴─────────────┘       │
│                                                      │
│  Trend Chart (30 days)                              │
│  [Line chart showing daily averages]                │
│                                                      │
│  By Difficulty                                      │
│  ┌─────────────────────────────────────────┐       │
│  │ Beginner:    4.5 / 4.7 / 4.4  (150 ratings)│     │
│  │ Intermediate: 4.2 / 4.4 / 4.0  (200)       │     │
│  │ Advanced:     3.9 / 4.2 / 3.8  (100)       │     │
│  └─────────────────────────────────────────┘       │
│                                                      │
│  False Positives                                    │
│  ┌─────────────────────────────────────────┐       │
│  │ Rate: 8% (36 / 450 ratings)             │       │
│  │ [View Details →]                         │       │
│  └─────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────┘
```

**Secondary Dashboard: Cost Tracking**

Layout:
```
┌─────────────────────────────────────────────────────┐
│  AI Cost Tracking Dashboard                         │
├─────────────────────────────────────────────────────┤
│  Today's Usage                                      │
│  ┌──────────────────────────────────────────┐      │
│  │ Total Cost: $0.42 / $10.00 budget        │      │
│  │ [Progress bar: 4% used]                  │      │
│  │ Requests: 112 (cached: 28, uncached: 84) │      │
│  └──────────────────────────────────────────┘      │
│                                                      │
│  Last 30 Days                                       │
│  [Bar chart: daily costs]                           │
│                                                      │
│  Cache Performance                                  │
│  ┌──────────────────────────────────────────┐      │
│  │ Hit Rate: 25%                            │      │
│  │ Estimated Savings: $62.50                │      │
│  └──────────────────────────────────────────┘      │
│                                                      │
│  Most Expensive Cases                               │
│  ┌──────────────────────────────────────────┐      │
│  │ 1. NR-MR-2025-0020  $0.0075 avg (10 req)│      │
│  │ 2. CH-CT-2025-0015  $0.0068 avg (8 req) │      │
│  └──────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────┘
```

---

### 3️⃣ Analysis Methodology

**Weekly Analysis Questions**:
1. Are ratings trending up or down?
2. Which difficulty levels have lowest ratings?
3. What are common themes in false positive reports?
4. Is cache hit rate improving over time?
5. Are any cases unusually expensive?

**Monthly Deep Dive**:
1. Compare prompt versions if A/B testing
2. Identify top 10 false positive patterns
3. Review cache effectiveness by subspecialty
4. Budget forecast for next month
5. Plan prompt improvements based on data

---

### 4️⃣ Alert Thresholds

**Critical Alerts** (Immediate Action):
- Daily cost exceeds $10.00
- Average rating drops below 3.0 (any category)
- False positive rate exceeds 20%
- API error rate exceeds 5%

**Warning Alerts** (Review Soon):
- Daily cost exceeds $5.00
- Average rating drops below 3.5
- Cache hit rate below 15% after 30 days
- API response time exceeds 10 seconds

---

## ⚠️ Risk Assessment

### 1️⃣ Technical Risks

#### Risk: Database Performance Degradation
**Severity**: 🟡 MEDIUM

**Description**: New models add 4 tables with indexes. Write operations will be slower.

**Impact**:
- Report submission slightly slower (additional writes)
- Analytics queries could slow down over time

**Mitigation**:
1. **Indexes**: Carefully designed indexes for query patterns
2. **Periodic Archiving**: Archive old TokenUsageLog entries (>90 days)
3. **Database Monitoring**: Track query performance with Django Debug Toolbar
4. **Load Testing**: Test with 1000+ reports before production

**Rollback**: Drop tables if performance unacceptable (after backup)

---

#### Risk: Cache Invalidation Bugs
**Severity**: 🟡 MEDIUM

**Description**: Incorrect cache keys or invalidation logic could serve stale feedback.

**Impact**:
- Users receive outdated feedback
- Defeats purpose of prompt versioning

**Mitigation**:
1. **Comprehensive Tests**: Test cache key generation with edge cases
2. **Expiration Safety Net**: 30-day expiration regardless of prompt changes
3. **Manual Override**: Admin can clear cache for specific cases
4. **Monitoring**: Track cache hit rate (sudden spike = potential issue)

**Rollback**: Disable caching (set cache TTL to 0, always generate fresh)

---

#### Risk: Budget Overruns
**Severity**: 🟡 MEDIUM

**Description**: Token tracking has bugs, or usage spikes unexpectedly.

**Impact**:
- AI API costs exceed budget
- Need to throttle or disable feature

**Mitigation**:
1. **Daily Budget Alerts**: Alert at $5, $10, $20 thresholds
2. **Rate Limiting**: Existing 10 calls/min limit
3. **Cost Caps**: Implement hard stop at $50/day
4. **Google Cloud Billing Alerts**: Set up in GCP console

**Rollback**: Disable AI feedback temporarily, revert to basic mode

---

#### Risk: Prompt Version Confusion
**Severity**: 🟢 LOW

**Description**: Multiple active versions or A/B test misconfiguration.

**Impact**:
- Inconsistent feedback to users
- Difficult to analyze results

**Mitigation**:
1. **Database Constraint**: Only one version can have `is_active=True` (enforce in code)
2. **Admin UI Validation**: Clear warnings in UI
3. **Logging**: Log which version was used for each request
4. **Documentation**: Clear process for activating versions

**Rollback**: Admin deactivates problem version, activates previous stable

---

### 2️⃣ Data Integrity Risks

#### Risk: Rating Manipulation
**Severity**: 🟢 LOW

**Description**: Users could submit fake ratings to skew metrics.

**Impact**:
- Inaccurate quality metrics
- Bad prompt decisions

**Mitigation**:
1. **Authentication Required**: Only authenticated users can rate
2. **Unique Constraint**: One rating per user per report
3. **Outlier Detection**: Flag users with extreme rating patterns
4. **Rate Limiting**: Prevent bulk rating submissions

---

#### Risk: Data Loss During Migration
**Severity**: 🟡 MEDIUM

**Description**: Migration fails midway, corrupting database.

**Impact**:
- Downtime
- Potential data loss

**Mitigation**:
1. **Backup Before Migration**: Full database backup
2. **Test on Staging**: Run migration on staging environment first
3. **Migration Plan**: Reversible migrations (no data transformations)
4. **Monitoring**: Watch logs during deployment

**Rollback**: Restore from backup, revert migration

---

### 3️⃣ Scalability Risks

#### Risk: Analytics Query Slowdown
**Severity**: 🟡 MEDIUM

**Description**: As data grows, analytics queries become slow.

**Impact**:
- Dashboard takes >5 seconds to load
- Admins frustrated

**Mitigation**:
1. **Indexes**: All analytics queries covered by indexes
2. **Caching**: Cache dashboard data for 5 minutes
3. **Pagination**: Limit result sets
4. **Denormalization**: Pre-calculate daily aggregates (future optimization)

**Performance Target**: Dashboard loads in <2 seconds with 10,000+ reports

---

#### Risk: Cache Size Growth
**Severity**: 🟢 LOW

**Description**: FeedbackCache table grows unbounded.

**Impact**:
- Database bloat
- Slower cache lookups

**Mitigation**:
1. **Automatic Cleanup**: Periodic job deletes expired caches
2. **LRU Policy**: Delete least-hit caches if size exceeds threshold
3. **Monitoring**: Track cache table size

**Cleanup Strategy**:
```python
# Daily cleanup task
def cleanup_expired_caches():
    """Delete expired cache entries."""
    deleted = FeedbackCache.objects.filter(
        expires_at__lt=timezone.now()
    ).delete()

    logger.info(f"Deleted {deleted[0]} expired cache entries")
```

---

## 📈 Scalability Plan

### 1️⃣ Current Capacity Estimates

**Baseline Assumptions**:
- 100 active users
- 50 reports submitted per day
- 30% cache hit rate
- Average 15,000 tokens per uncached request

**Database Growth**:
- `AIFeedbackDetailedRating`: ~50 rows/day = 18,000/year
- `TokenUsageLog`: ~35 rows/day (uncached) = 12,775/year
- `FeedbackCache`: ~35 rows/day initially, plateau at ~500 entries
- `PromptVersion`: ~10 rows/year

**Database Size Projection**:
- Year 1: ~30,000 rows across new tables
- Year 2: ~60,000 rows
- **Impact**: Negligible (PostgreSQL handles millions of rows easily)

---

### 2️⃣ Query Optimization Strategy

**Analytics Query Example**:
```python
# ❌ BAD: N+1 queries
ratings = AIFeedbackDetailedRating.objects.all()
for rating in ratings:
    print(rating.report.case.case_identifier)  # New query each iteration!

# ✅ GOOD: select_related
ratings = AIFeedbackDetailedRating.objects.select_related(
    'report__case'
).all()
for rating in ratings:
    print(rating.report.case.case_identifier)  # No additional query
```

**Dashboard Query Optimization**:
```python
# Feedback quality metrics with one query
from django.db.models import Avg, Count

metrics = AIFeedbackDetailedRating.objects.aggregate(
    avg_accuracy=Avg('accuracy_rating'),
    avg_helpfulness=Avg('helpfulness_rating'),
    avg_actionability=Avg('actionability_rating'),
    total_ratings=Count('id'),
    false_positive_count=Count('id', filter=Q(has_false_positives=True))
)
```

**Use `assertNumQueries` in tests**:
```python
def test_dashboard_query_count(self):
    """Ensure dashboard doesn't have N+1 queries."""
    with self.assertNumQueries(5):  # Should be low number
        response = self.client.get('/api/analytics/feedback-quality/')
```

---

### 3️⃣ Caching Strategy

**Level 1: Database Query Cache** (Implemented)
- FeedbackCache model caches AI responses
- 30-day TTL
- Hash-based key

**Level 2: Dashboard Data Cache** (Future)
```python
from django.core.cache import cache

def get_dashboard_metrics():
    """Cache dashboard data for 5 minutes."""
    cache_key = 'dashboard_feedback_quality'
    cached = cache.get(cache_key)

    if cached:
        return cached

    # Calculate metrics (expensive aggregations)
    metrics = calculate_metrics()

    cache.set(cache_key, metrics, timeout=300)  # 5 minutes
    return metrics
```

**Level 3: Redis for Session Storage** (Future)
- Move session storage to Redis
- Faster than database sessions

---

### 4️⃣ Horizontal Scaling Readiness

**Current Blocker**: Synchronous AI calls block request threads

**Solution Path**:
1. **Phase 1** (Current): Caching reduces synchronous calls by 20-30%
2. **Phase 2** (Future): Celery async task queue
   - User submits report → Returns immediately
   - Background task generates feedback
   - User polls for completion or receives notification
3. **Phase 3** (Future): Multiple Gunicorn workers
   - Load balancer distributes requests
   - Stateless design (JWT) allows horizontal scaling

**UUID Primary Keys**: Already prepared for distributed database (no auto-increment conflicts)

---

### 5️⃣ Performance Benchmarks

**Target Response Times**:
| Endpoint | Target | Acceptable | Action Needed |
|----------|--------|------------|---------------|
| POST detailed-rating | <200ms | <500ms | >500ms: Check indexes |
| GET feedback-quality | <500ms | <1s | >1s: Add caching |
| GET token-usage | <500ms | <1s | >1s: Add caching |
| AI feedback (cached) | <100ms | <300ms | >300ms: Check cache lookup |
| AI feedback (uncached) | <5s | <10s | >10s: Check API rate limit |

**Load Testing Plan**:
```bash
# Use Locust to simulate load
# Target: 10 concurrent users submitting ratings

# Install
pip install locust

# Run
locust -f locustfile.py --host=http://localhost:8000
```

---

## 🧪 Testing Strategy

### 1️⃣ Unit Tests (Models)

**Coverage Target**: 95%+

**Test Cases for AIFeedbackDetailedRating**:
```python
class AIFeedbackDetailedRatingTest(TestCase):
    def test_create_detailed_rating(self):
        """Test creating rating with all fields."""
        rating = AIFeedbackDetailedRating.objects.create(
            report=self.report,
            user=self.user,
            accuracy_rating=5,
            helpfulness_rating=4,
            actionability_rating=5,
            overall_rating=5,
            has_false_positives=False
        )
        self.assertEqual(rating.accuracy_rating, 5)

    def test_unique_constraint(self):
        """Test that user can only rate once per report."""
        AIFeedbackDetailedRating.objects.create(
            report=self.report,
            user=self.user,
            accuracy_rating=5,
            helpfulness_rating=5,
            actionability_rating=5,
            overall_rating=5
        )

        with self.assertRaises(IntegrityError):
            AIFeedbackDetailedRating.objects.create(
                report=self.report,
                user=self.user,  # Same user, same report
                accuracy_rating=4,
                helpfulness_rating=4,
                actionability_rating=4,
                overall_rating=4
            )

    def test_false_positive_tracking(self):
        """Test false positive flag and details."""
        rating = AIFeedbackDetailedRating.objects.create(
            report=self.report,
            user=self.user,
            accuracy_rating=2,
            helpfulness_rating=2,
            actionability_rating=2,
            overall_rating=2,
            has_false_positives=True,
            false_positive_details="AI said I missed pneumothorax but it's in my report"
        )
        self.assertTrue(rating.has_false_positives)
        self.assertIn("pneumothorax", rating.false_positive_details)
```

---

### 2️⃣ Integration Tests (API)

**Test Cases for Rating Submission**:
```python
class DetailedRatingAPITest(APITestCase):
    def test_submit_detailed_rating(self):
        """Test submitting multi-dimensional rating."""
        self.client.force_authenticate(user=self.user)

        url = reverse('detailed-rating', kwargs={'report_id': self.report.id})
        data = {
            'accuracy_rating': 5,
            'helpfulness_rating': 4,
            'actionability_rating': 5,
            'overall_rating': 5,
            'has_false_positives': False,
            'comment': 'Great feedback!'
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(AIFeedbackDetailedRating.objects.count(), 1)
```

---

### 3️⃣ Performance Tests

**Test Cache Performance**:
```python
def test_cache_reduces_api_calls(self):
    """Test that cache reduces Gemini API calls."""
    with patch('cases.llm_feedback_service.call_gemini_api') as mock_api:
        mock_api.return_value = {'text': 'feedback'}

        # First call - should hit API
        feedback1 = get_feedback_with_cache(...)
        self.assertEqual(mock_api.call_count, 1)

        # Second call with identical content - should use cache
        feedback2 = get_feedback_with_cache(...)
        self.assertEqual(mock_api.call_count, 1)  # No additional call
```

---

## 🚀 Implementation Roadmap

### Week 1: Database & Core Logic (Days 1-5)

#### Day 1: Database Models ✅ **COMPLETED**
- ✅ Create 4 new models in `models.py` (478 lines added)
- ✅ Add indexes and constraints (18 indexes created)
- ✅ Write comprehensive docstrings (business rules documented)
- ✅ Generate migration: `python manage.py makemigrations --name phase1_foundation`
- ✅ Review migration file (verified all operations)
- ✅ Write model unit tests (29 tests written)
- ✅ Run tests: `python manage.py test cases.tests.test_phase1_models`

**Deliverable**: ✅ Migration applied successfully, **29 tests PASSING**

**Models Created**:
1. AIFeedbackDetailedRating (UUID PK, 5 indexes)
2. FeedbackCache (UUID PK, 4 indexes)
3. PromptVersion (UUID PK, 5 indexes)
4. TokenUsageLog (UUID PK, 5 indexes)

**Test Coverage**:
- CRUD operations: ✅
- Unique constraints: ✅
- Cascade deletes: ✅
- UUID generation: ✅
- String representations: ✅
- Ordering: ✅
- All edge cases: ✅

**Date Completed**: 2025-10-12

---

#### Day 2: Cache Integration
- ✅ Implement `generate_cache_key()` function
- ✅ Implement `get_feedback_with_cache()` wrapper
- ✅ Modify `llm_feedback_service.py`:
  - Add cache lookup before API call
  - Store feedback in cache after generation
  - Update hit metrics
- ✅ Write cache integration tests (15 tests)
- ✅ Test cache hit/miss scenarios

**Deliverable**: Caching functional, 15+ passing tests

---

#### Day 3: Token Tracking
- ✅ Implement token extraction from Gemini response
- ✅ Implement cost calculation logic
- ✅ Create `TokenUsageLog` entries in `llm_feedback_service.py`
- ✅ Add budget alert function
- ✅ Write token tracking tests (10 tests)

**Deliverable**: Token usage logged, cost tracking operational

---

#### Day 4: Prompt Version Management
- ✅ Implement `select_prompt_version()` logic
- ✅ Implement A/B test weighted selection
- ✅ Update `llm_feedback_service.py` to use versioned prompts
- ✅ Create initial prompt version (v1.0.0 baseline)
- ✅ Write prompt version tests (12 tests)

**Deliverable**: Prompt versioning functional, tests passing

---

#### Day 5: Integration Testing & Refinement
- ✅ Run full test suite (target: 70+ tests passing)
- ✅ Fix any test failures
- ✅ Test end-to-end flow:
  1. Submit report
  2. Generate feedback (cache miss)
  3. Submit rating
  4. Submit identical report
  5. Generate feedback (cache hit)
- ✅ Code review and cleanup

**Deliverable**: All backend logic complete, tests passing

---

### Week 2: API & Dashboard (Days 6-10)

#### Day 6: API Endpoints (Serializers & Views)
- ✅ Create serializers:
  - `AIFeedbackDetailedRatingSerializer`
  - `FeedbackQualityMetricsSerializer`
  - `TokenUsageMetricsSerializer`
  - `PromptVersionSerializer`
- ✅ Create views:
  - `DetailedRatingViewSet` (POST)
  - `FeedbackQualityAnalyticsView` (GET)
  - `CachePerformanceView` (GET)
  - `TokenUsageView` (GET)
  - `PromptVersionViewSet` (GET, POST, PATCH)
- ✅ Add URL routing
- ✅ Write API tests (20 tests)

**Deliverable**: 5 new API endpoints functional

---

#### Day 7: Analytics Logic
- ✅ Implement dashboard metric calculations:
  - Overall averages
  - By difficulty breakdown
  - Time-series trends
  - Cache performance stats
  - Token usage summaries
- ✅ Optimize queries with annotations and aggregations
- ✅ Add query performance tests
- ✅ Test with realistic data volume (1000+ records)

**Deliverable**: Analytics endpoints return correct data efficiently

---

#### Day 8: Admin Dashboard UI (HTML/CSS)
- ✅ Create `admin-feedback-dashboard.html`
- ✅ Create `admin-cost-dashboard.html`
- ✅ Create `admin-prompt-versions.html`
- ✅ Design layout with charts placeholders
- ✅ Add navigation links in admin panel

**Deliverable**: Dashboard HTML pages ready for JavaScript

---

#### Day 9: Dashboard JavaScript (Data Fetching & Charts)
- ✅ Create `admin-feedback-dashboard.js`:
  - Fetch data from `/api/analytics/feedback-quality/`
  - Render metrics cards
  - Render trend charts (Chart.js)
  - Render by-difficulty breakdown
- ✅ Create `admin-cost-dashboard.js`:
  - Fetch token usage data
  - Render cost summary
  - Render cache performance
  - Render expensive cases list
- ✅ Create `admin-prompt-versions.js`:
  - List all prompt versions
  - Activate/deactivate versions
  - Create new versions
- ✅ Test dashboard in browser

**Deliverable**: Dashboards functional with real data

---

#### Day 10: Testing, Documentation, Deployment
- ✅ Run full test suite (target: 90+ tests, 90%+ coverage)
- ✅ Fix any remaining bugs
- ✅ Write deployment documentation:
  - Migration steps
  - Rollback procedure
  - Admin user guide for dashboards
- ✅ Update `ROADMAP.md` with Phase 1 completion
- ✅ Prepare deployment to Beta Droplet:
  - Commit changes
  - Push to `online_beta` branch
  - Monitor GitHub Actions deployment
  - Verify on Beta Droplet (64.225.17.0)
- ✅ Create baseline metrics snapshot

**Deliverable**: Phase 1 deployed, documentation complete, baseline established

---

## 📝 Deployment Strategy

### Pre-Deployment Checklist

- [ ] All tests passing (90+ tests, 90%+ coverage)
- [ ] Migration reviewed and tested locally
- [ ] Backup Beta Droplet database
- [ ] Read `DEPLOYMENT_LOG.md` for lessons learned
- [ ] Complete risk assessment documented
- [ ] Rollback plan documented

---

### Deployment Steps (GitHub Actions)

1. **Commit changes**:
```bash
git add .
git commit -m "Phase 1: Foundation Improvements - AI Feedback Quality Tracking

Implements:
- 4 new models: AIFeedbackDetailedRating, FeedbackCache, PromptVersion, TokenUsageLog
- Multi-dimensional feedback ratings (accuracy, helpfulness, actionability)
- Hash-based report caching (reduce AI costs)
- Prompt version management with A/B testing
- Token usage tracking and cost monitoring
- 5 new analytics API endpoints
- Admin dashboards for feedback quality and cost tracking

Tests: 90+ tests, 92% coverage
Migration: phase1_foundation.py

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

2. **Push to online_beta**:
```bash
git push origin online_beta
```

3. **Monitor GitHub Actions**:
- Go to https://github.com/straus91/global-peds-reading-room/actions
- Watch deployment workflow
- Verify all steps complete successfully

4. **Verify on Beta Droplet**:
```bash
# SSH to droplet (or use DigitalOcean console)
ssh deploy@64.225.17.0

# Activate virtual environment
cd /home/deploy/global-peds-reading-room/backend
source venv/bin/activate

# Check migration applied
python manage.py showmigrations cases | tail -5

# Check new models accessible
python manage.py shell
>>> from cases.models import AIFeedbackDetailedRating, FeedbackCache, PromptVersion, TokenUsageLog
>>> print("All models imported successfully")
>>> exit()

# Check services running
sudo systemctl status gunicorn nginx postgresql
```

---

### Rollback Procedure

If deployment fails or causes issues:

1. **Revert code**:
```bash
cd /home/deploy/global-peds-reading-room/backend
git log -5  # Find previous commit hash
git reset --hard <previous-commit-hash>
sudo systemctl restart gunicorn
```

2. **Rollback migration**:
```bash
python manage.py migrate cases <previous-migration-name>
```

3. **Restore database** (if corrupted):
```bash
# Restore from backup taken pre-deployment
psql globalpeds_db < backup_before_phase1.sql
```

---

## 🎯 Success Criteria

### Phase 1 Complete When:

✅ **Technical Criteria**:
- [ ] 4 new models deployed to production
- [ ] Migration applied successfully
- [ ] 90+ tests passing, 90%+ coverage
- [ ] All 5 API endpoints functional
- [ ] Dashboards operational and displaying data
- [ ] Caching reduces API calls (measurable)
- [ ] Token usage tracked for all requests

✅ **Data Criteria**:
- [ ] Baseline metrics established (14 days of data)
- [ ] Cache hit rate >20% after 30 days
- [ ] False positive rate documented
- [ ] Average ratings documented (accuracy, helpfulness, actionability)
- [ ] Average cost per report documented

✅ **Documentation Criteria**:
- [ ] Admin dashboard guide complete
- [ ] Deployment log updated
- [ ] Data models documentation updated
- [ ] Rollback procedure documented

---

## 📊 Post-Deployment Monitoring (First 30 Days)

### Daily Checks (Days 1-7):
- Monitor error logs for new exceptions
- Check dashboard loads correctly
- Verify cache hit rate trending up
- Check daily cost within budget
- Review any user-reported issues

### Weekly Analysis (Weeks 1-4):
- Generate weekly metrics report:
  - Average ratings by category
  - Cache hit rate trend
  - Cost per report trend
  - Top 5 most expensive cases
  - False positive count
- Identify any anomalies
- Plan prompt optimizations if ratings low

### 30-Day Review:
- Compare to baseline metrics
- Assess if cache hit rate goal met (>20%)
- Calculate total cost savings from caching
- Review false positive patterns
- Decide on prompt version updates
- Plan Phase 2 implementation

---

## 🔄 Iteration Strategy

### Continuous Improvement Loop:

```
┌─────────────────────────────────────────────┐
│  1. Collect Data (14+ days)                 │
│     - Ratings                               │
│     - Cache performance                     │
│     - Costs                                 │
│     - False positives                       │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│  2. Analyze Patterns                        │
│     - Low-rated feedback themes             │
│     - Expensive cases                       │
│     - Cache effectiveness by subspecialty   │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│  3. Formulate Hypothesis                    │
│     - "Adding specific examples will        │
│       improve actionability"                │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│  4. Create New Prompt Version               │
│     - Version v2.3.0: "Enhanced Examples"   │
│     - Set is_ab_test=True (20% traffic)     │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│  5. A/B Test (14 days)                      │
│     - Compare v2.2.0 vs v2.3.0              │
│     - Track ratings, costs                  │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│  6. Decide                                  │
│     - If v2.3.0 better: Activate 100%       │
│     - If worse: Deactivate, iterate         │
│     - If unclear: Continue test longer      │
└────────────────┬────────────────────────────┘
                 │
                 ▼
                [REPEAT]
```

---

## ❓ Open Questions for User Approval

1. **Budget Threshold**: Is $10/day acceptable for AI API costs? Should we set lower?
2. **Cache TTL**: Is 30 days appropriate for cache expiration?
3. **A/B Test Duration**: Is 14 days sufficient for prompt A/B tests?
4. **Dashboard Access**: Should dashboards be admin-only or accessible to all users?
5. **False Positive Review**: Should there be a workflow for admins to review flagged false positives?

---

**Ready to proceed with implementation!** This comprehensive plan covers all aspects of Phase 1 Foundation with emphasis on best practices, data-driven methodology, risk assessment, and scalability.
