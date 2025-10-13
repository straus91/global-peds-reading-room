# 🚀 Phase 1 Next Steps - Day 2: Cache Integration

## 📍 Current Status (After Day 1)

✅ **COMPLETED:**
- 4 new models created (AIFeedbackDetailedRating, FeedbackCache, PromptVersion, TokenUsageLog)
- Migration `0009_phase1_foundation.py` generated and tested
- 29 unit tests written and passing
- All database indexes and constraints in place

⏳ **NEXT UP (Day 2):**
- Implement cache key generation
- Enhance llm_feedback_service.py with caching
- Implement token tracking
- Write cache integration tests

---

## 🎯 Day 2 Implementation Tasks

### Task 1: Create Cache Utility Functions

**File**: `backend/cases/cache_utils.py` (NEW FILE)

**Functions to implement:**

```python
import hashlib
import json
from django.utils import timezone
from datetime import timedelta
from cases.models import FeedbackCache

def generate_cache_key(user_sections, expert_sections, case_context):
    """
    Generate deterministic SHA256 hash for cache lookup.

    Args:
        user_sections: List of user report sections
        expert_sections: List of expert template sections
        case_context: Dict with diagnosis, key_findings

    Returns:
        str: 64-character SHA256 hash
    """
    # Normalize content (lowercase, strip whitespace)
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
            'diagnosis': case_context.get('diagnosis', '').strip().lower(),
            'key_findings': case_context.get('key_findings', '').strip().lower()
        }
    }

    content_str = json.dumps(normalized, sort_keys=True)
    return hashlib.sha256(content_str.encode()).hexdigest()


def get_cached_feedback(cache_key):
    """
    Retrieve cached feedback if valid (not expired).

    Returns:
        dict or None: Cached feedback content or None if miss
    """
    try:
        cache_entry = FeedbackCache.objects.get(
            content_hash=cache_key,
            expires_at__gt=timezone.now()
        )

        # Update hit metrics
        cache_entry.hit_count += 1
        cache_entry.last_hit_at = timezone.now()
        cache_entry.save(update_fields=['hit_count', 'last_hit_at'])

        return cache_entry.feedback_content
    except FeedbackCache.DoesNotExist:
        return None


def store_in_cache(cache_key, feedback_content, case, prompt_version, ttl_days=30):
    """
    Store feedback in cache with expiration.

    Args:
        cache_key: SHA256 hash key
        feedback_content: Structured feedback dict
        case: Case instance
        prompt_version: PromptVersion instance
        ttl_days: Time-to-live in days (default 30)
    """
    FeedbackCache.objects.create(
        content_hash=cache_key,
        feedback_content=feedback_content,
        case=case,
        prompt_version=prompt_version,
        hit_count=0,
        expires_at=timezone.now() + timedelta(days=ttl_days)
    )
```

**Tests to write** (in `test_cache_utils.py`):
- `test_generate_cache_key_deterministic` - Same input = same hash
- `test_generate_cache_key_normalized` - Case/whitespace normalization
- `test_get_cached_feedback_hit` - Cache hit updates metrics
- `test_get_cached_feedback_miss` - Returns None when not found
- `test_get_cached_feedback_expired` - Expired cache ignored
- `test_store_in_cache` - Creates entry with correct TTL

---

### Task 2: Implement Token Tracking

**File**: `backend/cases/token_utils.py` (NEW FILE)

```python
from decimal import Decimal
from cases.models import TokenUsageLog

# Gemini 2.5 Flash pricing (as of 2025)
PRICING = {
    'gemini-2.5-flash': {
        'input': Decimal('0.075') / 1_000_000,  # per token
        'output': Decimal('0.30') / 1_000_000
    },
    'gemini-1.5-flash': {
        'input': Decimal('0.075') / 1_000_000,
        'output': Decimal('0.30') / 1_000_000
    }
}

def calculate_cost(input_tokens, output_tokens, model_name='gemini-2.5-flash'):
    """Calculate costs based on token usage."""
    rates = PRICING.get(model_name, PRICING['gemini-2.5-flash'])

    input_cost = Decimal(str(input_tokens)) * rates['input']
    output_cost = Decimal(str(output_tokens)) * rates['output']

    return {
        'input_cost': input_cost.quantize(Decimal('0.000001')),
        'output_cost': output_cost.quantize(Decimal('0.000001')),
        'total_cost': (input_cost + output_cost).quantize(Decimal('0.000001'))
    }


def log_token_usage(report, case, prompt_version, token_data, response_time_ms, was_cached=False):
    """
    Create TokenUsageLog entry.

    Args:
        token_data: Dict with input_tokens, output_tokens, total_tokens, costs, model_name
    """
    TokenUsageLog.objects.create(
        report=report,
        case=case,
        prompt_version=prompt_version,
        input_tokens=token_data['input_tokens'],
        output_tokens=token_data['output_tokens'],
        total_tokens=token_data['total_tokens'],
        input_cost=token_data['input_cost'],
        output_cost=token_data['output_cost'],
        total_cost=token_data['total_cost'],
        response_time_ms=response_time_ms,
        was_cached=was_cached,
        model_name=token_data['model_name']
    )
```

---

### Task 3: Enhance llm_feedback_service.py

**Location**: `backend/cases/llm_feedback_service.py`

**Changes needed:**

1. **Import new utilities** (top of file):
```python
from cases.cache_utils import generate_cache_key, get_cached_feedback, store_in_cache
from cases.token_utils import calculate_cost, log_token_usage
from cases.models import PromptVersion
```

2. **Modify `get_feedback_from_llm` function** (around line 216):

```python
def get_feedback_from_llm_with_cache(
    user_report_sections,
    expert_report_sections,
    programmatic_pre_analysis_summary,
    case,  # ADD: Case instance for cache
    report,  # ADD: Report instance for logging
    # ... existing parameters ...
):
    """Enhanced with caching and token tracking."""

    # 1. Generate cache key
    case_context = {
        'diagnosis': case.diagnosis or '',
        'key_findings': case.key_findings or ''
    }
    cache_key = generate_cache_key(
        user_report_sections,
        expert_report_sections,
        case_context
    )

    # 2. Check cache
    cached_feedback = get_cached_feedback(cache_key)
    if cached_feedback:
        logger.info(f"Cache HIT for case {case.case_identifier}")

        # Log as cached request (zero cost)
        log_token_usage(
            report=report,
            case=case,
            prompt_version=None,  # Get from cache entry if needed
            token_data={
                'input_tokens': 0,
                'output_tokens': 0,
                'total_tokens': 0,
                'input_cost': Decimal('0.000000'),
                'output_cost': Decimal('0.000000'),
                'total_cost': Decimal('0.000000'),
                'model_name': 'cache'
            },
            response_time_ms=0,
            was_cached=True
        )

        return cached_feedback

    # 3. Cache MISS - call API
    logger.info(f"Cache MISS for case {case.case_identifier} - calling LLM")

    # Get active prompt version (implement select_prompt_version later)
    prompt_version = PromptVersion.objects.filter(is_active=True).first()
    if not prompt_version:
        # Fallback: use current hardcoded prompt
        prompt_version = None

    start_time = time.time()

    # Existing API call logic...
    response = model.generate_content(prompt)

    response_time_ms = int((time.time() - start_time) * 1000)

    # 4. Extract token usage from response
    token_usage = response.usage_metadata
    input_tokens = token_usage.prompt_token_count
    output_tokens = token_usage.candidates_token_count
    total_tokens = token_usage.total_token_count

    # 5. Calculate costs
    costs = calculate_cost(input_tokens, output_tokens, model_name)

    # 6. Log token usage
    log_token_usage(
        report=report,
        case=case,
        prompt_version=prompt_version,
        token_data={
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'total_tokens': total_tokens,
            'input_cost': costs['input_cost'],
            'output_cost': costs['output_cost'],
            'total_cost': costs['total_cost'],
            'model_name': model_name
        },
        response_time_ms=response_time_ms,
        was_cached=False
    )

    # 7. Parse response (existing logic)
    parsed_feedback = parse_llm_response(response.text)

    # 8. Store in cache
    if prompt_version:
        store_in_cache(cache_key, parsed_feedback, case, prompt_version)

    # 9. Update prompt version metrics
    if prompt_version:
        prompt_version.total_uses += 1
        prompt_version.total_tokens_used += total_tokens
        if prompt_version.total_uses > 0:
            prompt_version.average_tokens_per_use = (
                float(prompt_version.total_tokens_used) / prompt_version.total_uses
            )
        prompt_version.save(update_fields=[
            'total_uses',
            'total_tokens_used',
            'average_tokens_per_use'
        ])

    return parsed_feedback
```

3. **Update API view** (`backend/cases/views.py`):

Modify `AIReportFeedbackView` to pass `case` and `report` instances:

```python
feedback = get_feedback_from_llm_with_cache(
    user_sections,
    expert_sections,
    pre_analysis,
    case=report.case,  # ADD
    report=report,  # ADD
    # ... other params ...
)
```

---

### Task 4: Write Integration Tests

**File**: `backend/cases/tests/test_cache_integration.py`

**Test cases:**
- `test_cache_miss_calls_api` - First request hits API
- `test_cache_hit_returns_cached` - Second identical request uses cache
- `test_cache_hit_increments_count` - Hit count updates
- `test_token_log_created_uncached` - Token log with real costs
- `test_token_log_created_cached` - Token log with zero costs
- `test_prompt_version_metrics_updated` - total_uses increments

---

## 🧪 Testing Checklist

After implementing:

1. Run model tests: `python manage.py test cases.tests.test_phase1_models`
2. Run cache utils tests: `python manage.py test cases.tests.test_cache_utils`
3. Run integration tests: `python manage.py test cases.tests.test_cache_integration`
4. Run ALL tests: `python manage.py test cases`

**Target**: 45+ tests passing

---

## 📊 Success Criteria for Day 2

- ✅ Cache hit/miss logic working
- ✅ Token usage logged for all requests
- ✅ Costs calculated correctly (6 decimal precision)
- ✅ Cache hit rate measurable
- ✅ 15+ new tests passing
- ✅ No N+1 queries (use `assertNumQueries`)

---

## 💡 Tips for Next Session

1. **Start by reading**:
   - This file (NEXT_STEPS.md)
   - PHASE1_IMPLEMENTATION_PLAN.md
   - Current llm_feedback_service.py to understand structure

2. **Check existing code**:
   - How `get_feedback_from_llm` is currently called in views.py
   - What parameters are available

3. **Test incrementally**:
   - Create cache_utils.py → test it
   - Create token_utils.py → test it
   - Modify llm_feedback_service.py → test integration

4. **Monitor token usage**:
   - After implementing, manually test and check TokenUsageLog table
   - Verify costs are calculated correctly

---

## 🔮 After Day 2: Days 3-4 Preview

- **Day 3**: Prompt version selection, A/B testing logic
- **Day 4**: Integration testing, refinement

By end of Day 4, backend core logic should be complete and ready for API endpoints (Days 6-7).

---

**Last Updated**: 2025-10-12 (after Day 1 completion)
**Next Session Start**: Day 2 - Cache Integration
**Estimated Time**: 2-3 hours
