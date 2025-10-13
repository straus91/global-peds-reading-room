"""
Cache utility functions for AI feedback caching.

This module provides functions to:
1. Generate deterministic cache keys from report content
2. Retrieve cached feedback (with hit tracking)
3. Store new feedback in cache with TTL
"""

import hashlib
import json
from django.utils import timezone
from datetime import timedelta
from cases.models import FeedbackCache


def generate_cache_key(user_sections, expert_sections, case_context):
    """
    Generate deterministic SHA256 hash for cache lookup.

    The cache key is based on normalized content (lowercase, stripped whitespace)
    to ensure identical reports produce identical keys even with minor formatting
    differences.

    Args:
        user_sections (list): List of user report sections, each containing:
            - master_template_section_id (int)
            - content (str)
        expert_sections (list): List of expert template sections, each containing:
            - master_section_id (int)
            - key_concepts_text (str)
        case_context (dict): Case context with:
            - diagnosis (str)
            - key_findings (str)

    Returns:
        str: 64-character SHA256 hash

    Example:
        >>> user_sections = [
        ...     {'master_template_section_id': 1, 'content': 'Findings text'}
        ... ]
        >>> expert_sections = [
        ...     {'master_section_id': 1, 'key_concepts_text': 'key1;key2'}
        ... ]
        >>> case_context = {'diagnosis': 'Test diagnosis', 'key_findings': 'Finding 1'}
        >>> cache_key = generate_cache_key(user_sections, expert_sections, case_context)
        >>> len(cache_key)
        64
    """
    # Normalize content (lowercase, strip whitespace)
    normalized = {
        'user': sorted([
            {
                'section_id': s.get('master_template_section_id'),
                'content': s.get('content', '').strip().lower()
            }
            for s in user_sections
        ], key=lambda x: x['section_id']),
        'expert': sorted([
            {
                'section_id': s.get('master_section_id'),
                'key_concepts': s.get('key_concepts_text', '').strip().lower()
            }
            for s in expert_sections
        ], key=lambda x: x['section_id']),
        'case': {
            'diagnosis': case_context.get('diagnosis', '').strip().lower(),
            'key_findings': case_context.get('key_findings', '').strip().lower()
        }
    }

    # Create deterministic JSON string (sorted keys)
    content_str = json.dumps(normalized, sort_keys=True)

    # Generate SHA256 hash
    return hashlib.sha256(content_str.encode()).hexdigest()


def get_cached_feedback(cache_key):
    """
    Retrieve cached feedback if valid (not expired).

    Updates hit metrics (hit_count, last_hit_at) when cache is accessed.

    Args:
        cache_key (str): SHA256 hash from generate_cache_key()

    Returns:
        dict or None: Cached feedback content (structured dict) or None if cache miss

    Cache Miss Reasons:
        - No entry exists for this cache_key
        - Entry exists but has expired (expires_at < now)

    Example:
        >>> cached = get_cached_feedback('abc123...')
        >>> if cached:
        ...     print("Cache HIT!")
        ...     print(cached['section_feedback'])
        ... else:
        ...     print("Cache MISS - call LLM")
    """
    try:
        cache_entry = FeedbackCache.objects.get(
            content_hash=cache_key,
            expires_at__gt=timezone.now()
        )

        # Update hit metrics (atomic update for thread safety)
        cache_entry.hit_count += 1
        cache_entry.last_hit_at = timezone.now()
        cache_entry.save(update_fields=['hit_count', 'last_hit_at'])

        return cache_entry.feedback_content

    except FeedbackCache.DoesNotExist:
        # Cache miss - either no entry or expired
        return None


def store_in_cache(cache_key, feedback_content, case, prompt_version, ttl_days=30):
    """
    Store feedback in cache with expiration.

    Args:
        cache_key (str): SHA256 hash from generate_cache_key()
        feedback_content (dict): Structured feedback dict from LLM parsing
        case (Case): Case instance for which feedback was generated
        prompt_version (PromptVersion): PromptVersion instance used (can be None)
        ttl_days (int): Time-to-live in days (default 30)

    Returns:
        FeedbackCache: Created cache entry

    Note:
        - If cache_key already exists, raises IntegrityError (unique constraint)
        - TTL should match prompt version lifecycle (invalidate on prompt changes)

    Example:
        >>> from cases.models import Case, PromptVersion
        >>> case = Case.objects.get(case_identifier='NR-CT-2025-0001')
        >>> prompt_version = PromptVersion.objects.filter(is_active=True).first()
        >>> feedback = {'raw_feedback': '...', 'section_feedback': [...]}
        >>> cache_entry = store_in_cache(cache_key, feedback, case, prompt_version)
        >>> cache_entry.hit_count
        0
    """
    return FeedbackCache.objects.create(
        content_hash=cache_key,
        feedback_content=feedback_content,
        case=case,
        prompt_version=prompt_version,
        hit_count=0,
        expires_at=timezone.now() + timedelta(days=ttl_days)
    )
