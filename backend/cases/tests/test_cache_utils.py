"""
Unit tests for cache_utils.py

Tests cache key generation, cache retrieval with hit tracking,
and cache storage with TTL.
"""

from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from cases.cache_utils import generate_cache_key, get_cached_feedback, store_in_cache
from cases.models import Case, Report, FeedbackCache, PromptVersion, MasterTemplate
from users.models import User


class CacheKeyGenerationTest(TestCase):
    """Test cache key generation logic."""

    def test_generate_cache_key_deterministic(self):
        """Test that same input produces same hash."""
        user_sections = [
            {'master_template_section_id': 1, 'content': 'Test findings'}
        ]
        expert_sections = [
            {'master_section_id': 1, 'key_concepts_text': 'finding1;finding2'}
        ]
        case_context = {
            'diagnosis': 'Test diagnosis',
            'key_findings': 'Test findings'
        }

        key1 = generate_cache_key(user_sections, expert_sections, case_context)
        key2 = generate_cache_key(user_sections, expert_sections, case_context)

        self.assertEqual(key1, key2)
        self.assertEqual(len(key1), 64)  # SHA256 produces 64 hex chars

    def test_generate_cache_key_normalized(self):
        """Test that case and whitespace differences produce same hash."""
        user_sections1 = [
            {'master_template_section_id': 1, 'content': '  Test Findings  '}
        ]
        user_sections2 = [
            {'master_template_section_id': 1, 'content': 'test findings'}
        ]

        expert_sections = [
            {'master_section_id': 1, 'key_concepts_text': 'finding1;finding2'}
        ]
        case_context = {
            'diagnosis': 'Test diagnosis',
            'key_findings': 'Test findings'
        }

        key1 = generate_cache_key(user_sections1, expert_sections, case_context)
        key2 = generate_cache_key(user_sections2, expert_sections, case_context)

        self.assertEqual(key1, key2)

    def test_generate_cache_key_different_content(self):
        """Test that different content produces different hash."""
        user_sections1 = [
            {'master_template_section_id': 1, 'content': 'Test findings A'}
        ]
        user_sections2 = [
            {'master_template_section_id': 1, 'content': 'Test findings B'}
        ]

        expert_sections = [
            {'master_section_id': 1, 'key_concepts_text': 'finding1;finding2'}
        ]
        case_context = {
            'diagnosis': 'Test diagnosis',
            'key_findings': 'Test findings'
        }

        key1 = generate_cache_key(user_sections1, expert_sections, case_context)
        key2 = generate_cache_key(user_sections2, expert_sections, case_context)

        self.assertNotEqual(key1, key2)

    def test_generate_cache_key_section_order_independent(self):
        """Test that section order doesn't affect hash (they're sorted)."""
        user_sections1 = [
            {'master_template_section_id': 1, 'content': 'Findings'},
            {'master_template_section_id': 2, 'content': 'Impression'}
        ]
        user_sections2 = [
            {'master_template_section_id': 2, 'content': 'Impression'},
            {'master_template_section_id': 1, 'content': 'Findings'}
        ]

        expert_sections = [
            {'master_section_id': 1, 'key_concepts_text': 'key1'}
        ]
        case_context = {'diagnosis': 'Test', 'key_findings': 'Test'}

        key1 = generate_cache_key(user_sections1, expert_sections, case_context)
        key2 = generate_cache_key(user_sections2, expert_sections, case_context)

        self.assertEqual(key1, key2)

    def test_generate_cache_key_handles_missing_fields(self):
        """Test that missing optional fields don't cause errors."""
        user_sections = [
            {'master_template_section_id': 1}  # Missing 'content'
        ]
        expert_sections = [
            {'master_section_id': 1}  # Missing 'key_concepts_text'
        ]
        case_context = {}  # Missing 'diagnosis' and 'key_findings'

        # Should not raise exception
        cache_key = generate_cache_key(user_sections, expert_sections, case_context)

        self.assertIsNotNone(cache_key)
        self.assertEqual(len(cache_key), 64)


class CacheLookupTest(TestCase):
    """Test cache retrieval logic."""

    def setUp(self):
        """Create test data."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

        self.template = MasterTemplate.objects.create(
            name='Test Template',
            modality='CT',
            body_part='NR'
        )

        self.case = Case.objects.create(
            title='Test Case',
            subspecialty='NR',
            modality='CT',
            difficulty='beginner',
            clinical_history='Test',
            master_template=self.template
        )

        self.prompt_version = PromptVersion.objects.create(
            version_number='v1.0.0',
            name='Test Prompt',
            description='Test',
            prompt_template='Test template'
        )

    def test_get_cached_feedback_hit(self):
        """Test cache hit updates metrics."""
        cache_key = 'abc123' * 10 + 'abcd'  # 64 chars
        feedback_content = {
            'raw_feedback': 'Test feedback',
            'section_feedback': []
        }

        # Store in cache
        cache_entry = FeedbackCache.objects.create(
            content_hash=cache_key,
            feedback_content=feedback_content,
            case=self.case,
            prompt_version=self.prompt_version,
            hit_count=0,
            expires_at=timezone.now() + timedelta(days=30)
        )

        # Retrieve from cache
        cached_feedback = get_cached_feedback(cache_key)

        self.assertIsNotNone(cached_feedback)
        self.assertEqual(cached_feedback, feedback_content)

        # Verify hit count updated
        cache_entry.refresh_from_db()
        self.assertEqual(cache_entry.hit_count, 1)
        self.assertIsNotNone(cache_entry.last_hit_at)

    def test_get_cached_feedback_miss_no_entry(self):
        """Test cache miss when no entry exists."""
        cache_key = 'nonexistent' * 5 + '1234'  # 64 chars

        cached_feedback = get_cached_feedback(cache_key)

        self.assertIsNone(cached_feedback)

    def test_get_cached_feedback_miss_expired(self):
        """Test cache miss when entry has expired."""
        cache_key = 'expired123' * 6 + '1234'  # 64 chars
        feedback_content = {'raw_feedback': 'Test'}

        # Store with past expiration
        FeedbackCache.objects.create(
            content_hash=cache_key,
            feedback_content=feedback_content,
            case=self.case,
            prompt_version=self.prompt_version,
            hit_count=0,
            expires_at=timezone.now() - timedelta(days=1)  # Already expired
        )

        # Should return None (expired)
        cached_feedback = get_cached_feedback(cache_key)

        self.assertIsNone(cached_feedback)

    def test_get_cached_feedback_increments_hit_count(self):
        """Test that hit count increments on each access."""
        cache_key = 'multiHit12' * 5 + '1234'  # 64 chars
        feedback_content = {'raw_feedback': 'Test'}

        cache_entry = FeedbackCache.objects.create(
            content_hash=cache_key,
            feedback_content=feedback_content,
            case=self.case,
            prompt_version=self.prompt_version,
            hit_count=0,
            expires_at=timezone.now() + timedelta(days=30)
        )

        # Access cache 3 times
        for i in range(3):
            get_cached_feedback(cache_key)

        # Verify hit count is 3
        cache_entry.refresh_from_db()
        self.assertEqual(cache_entry.hit_count, 3)


class CacheStorageTest(TestCase):
    """Test cache storage logic."""

    def setUp(self):
        """Create test data."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

        self.template = MasterTemplate.objects.create(
            name='Test Template',
            modality='CT',
            body_part='NR'
        )

        self.case = Case.objects.create(
            title='Test Case',
            subspecialty='NR',
            modality='CT',
            difficulty='beginner',
            clinical_history='Test',
            master_template=self.template
        )

        self.prompt_version = PromptVersion.objects.create(
            version_number='v1.0.0',
            name='Test Prompt',
            description='Test',
            prompt_template='Test template'
        )

    def test_store_in_cache_creates_entry(self):
        """Test that store_in_cache creates cache entry."""
        cache_key = 'newCache123' * 5 + '1234'  # 64 chars
        feedback_content = {
            'raw_feedback': 'Test feedback',
            'section_feedback': []
        }

        cache_entry = store_in_cache(
            cache_key,
            feedback_content,
            self.case,
            self.prompt_version
        )

        self.assertIsNotNone(cache_entry.id)
        self.assertEqual(cache_entry.content_hash, cache_key)
        self.assertEqual(cache_entry.feedback_content, feedback_content)
        self.assertEqual(cache_entry.case, self.case)
        self.assertEqual(cache_entry.prompt_version, self.prompt_version)
        self.assertEqual(cache_entry.hit_count, 0)

    def test_store_in_cache_sets_ttl(self):
        """Test that TTL is set correctly."""
        cache_key = 'ttlTest1234' * 5 + '1234'  # 64 chars
        feedback_content = {'raw_feedback': 'Test'}

        before_store = timezone.now()
        cache_entry = store_in_cache(
            cache_key,
            feedback_content,
            self.case,
            self.prompt_version,
            ttl_days=30
        )
        after_store = timezone.now()

        # Verify expires_at is ~30 days from now
        expected_expiry = before_store + timedelta(days=30)
        expiry_difference = abs((cache_entry.expires_at - expected_expiry).total_seconds())

        # Allow 5 second tolerance for test execution time
        self.assertLess(expiry_difference, 5)

    def test_store_in_cache_custom_ttl(self):
        """Test that custom TTL values work."""
        cache_key = 'customTTL12' * 5 + '1234'  # 64 chars
        feedback_content = {'raw_feedback': 'Test'}

        cache_entry = store_in_cache(
            cache_key,
            feedback_content,
            self.case,
            self.prompt_version,
            ttl_days=7  # Custom 7-day TTL
        )

        expected_expiry = timezone.now() + timedelta(days=7)
        expiry_difference = abs((cache_entry.expires_at - expected_expiry).total_seconds())

        self.assertLess(expiry_difference, 5)

    def test_store_in_cache_allows_none_prompt_version(self):
        """Test that prompt_version can be None (legacy support)."""
        cache_key = 'noPVKey1234' * 5 + '1234'  # 64 chars
        feedback_content = {'raw_feedback': 'Test'}

        # Should not raise exception
        cache_entry = store_in_cache(
            cache_key,
            feedback_content,
            self.case,
            None  # No prompt version
        )

        self.assertIsNone(cache_entry.prompt_version)
