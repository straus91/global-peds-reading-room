# backend/cases/tests/test_phase1_models.py

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import uuid

from cases.models import (
    AIFeedbackDetailedRating,
    FeedbackCache,
    PromptVersion,
    TokenUsageLog,
    Report,
    Case,
    MasterTemplate,
)

User = get_user_model()


class AIFeedbackDetailedRatingModelTest(TestCase):
    """Test cases for AIFeedbackDetailedRating model"""

    def setUp(self):
        """Set up test data before each test"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
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
            clinical_history='Test history',
            master_template=self.template
        )

        self.report = Report.objects.create(
            case=self.case,
            user=self.user,
            structured_content=[{'section_name': 'Findings', 'content': 'Test findings'}]
        )

    def test_uuid_primary_key_generation(self):
        """Test that UUID primary key is auto-generated"""
        rating = AIFeedbackDetailedRating.objects.create(
            report=self.report,
            user=self.user,
            accuracy_rating=5,
            helpfulness_rating=4,
            actionability_rating=5,
            overall_rating=5
        )

        self.assertIsNotNone(rating.id)
        self.assertIsInstance(rating.id, uuid.UUID)

    def test_create_detailed_rating(self):
        """Test creating rating with all fields"""
        rating = AIFeedbackDetailedRating.objects.create(
            report=self.report,
            user=self.user,
            accuracy_rating=5,
            helpfulness_rating=4,
            actionability_rating=5,
            overall_rating=5,
            has_false_positives=False,
            comment="Great feedback!"
        )

        self.assertEqual(rating.accuracy_rating, 5)
        self.assertEqual(rating.helpfulness_rating, 4)
        self.assertEqual(rating.actionability_rating, 5)
        self.assertEqual(rating.overall_rating, 5)
        self.assertFalse(rating.has_false_positives)
        self.assertEqual(rating.comment, "Great feedback!")

    def test_rating_range_validation(self):
        """Test that ratings must be 1-5"""
        # Valid ratings (1-5) should work
        for i in range(1, 6):
            rating = AIFeedbackDetailedRating.objects.create(
                report=self.report,
                user=self.user,
                accuracy_rating=i,
                helpfulness_rating=i,
                actionability_rating=i,
                overall_rating=i
            )
            self.assertEqual(rating.accuracy_rating, i)
            # Clean up for next iteration
            rating.delete()

    def test_unique_constraint(self):
        """Test that user can only rate once per report"""
        AIFeedbackDetailedRating.objects.create(
            report=self.report,
            user=self.user,
            accuracy_rating=5,
            helpfulness_rating=5,
            actionability_rating=5,
            overall_rating=5
        )

        # Attempt to create duplicate should fail
        with transaction.atomic():
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
        """Test false positive flag and details"""
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

    def test_cascade_delete_when_report_deleted(self):
        """Test that ratings are deleted when report is deleted"""
        rating = AIFeedbackDetailedRating.objects.create(
            report=self.report,
            user=self.user,
            accuracy_rating=5,
            helpfulness_rating=5,
            actionability_rating=5,
            overall_rating=5
        )

        rating_id = rating.id

        # Delete report
        self.report.delete()

        # Verify rating was also deleted
        self.assertFalse(AIFeedbackDetailedRating.objects.filter(id=rating_id).exists())

    def test_cascade_delete_when_user_deleted(self):
        """Test that ratings are deleted when user is deleted"""
        rating = AIFeedbackDetailedRating.objects.create(
            report=self.report,
            user=self.user,
            accuracy_rating=5,
            helpfulness_rating=5,
            actionability_rating=5,
            overall_rating=5
        )

        rating_id = rating.id

        # Delete user
        self.user.delete()

        # Verify rating was also deleted
        self.assertFalse(AIFeedbackDetailedRating.objects.filter(id=rating_id).exists())

    def test_string_representation(self):
        """Test string representation of rating"""
        rating = AIFeedbackDetailedRating.objects.create(
            report=self.report,
            user=self.user,
            accuracy_rating=4,
            helpfulness_rating=4,
            actionability_rating=4,
            overall_rating=4
        )

        str_repr = str(rating)

        self.assertIn(str(self.report.id), str_repr)
        self.assertIn(self.user.username, str_repr)
        self.assertIn("4/5", str_repr)

    def test_ordering(self):
        """Test that ratings are ordered by rated_at descending"""
        # Create multiple ratings (need different reports since unique constraint)
        report2 = Report.objects.create(
            case=self.case,
            user=self.user,
            structured_content=[{'content': 'test'}]
        )

        rating1 = AIFeedbackDetailedRating.objects.create(
            report=self.report,
            user=self.user,
            accuracy_rating=5,
            helpfulness_rating=5,
            actionability_rating=5,
            overall_rating=5
        )

        rating2 = AIFeedbackDetailedRating.objects.create(
            report=report2,
            user=self.user,
            accuracy_rating=4,
            helpfulness_rating=4,
            actionability_rating=4,
            overall_rating=4
        )

        # Query all ratings
        ratings = AIFeedbackDetailedRating.objects.all()

        # Most recent should be first
        self.assertEqual(ratings[0].id, rating2.id)
        self.assertEqual(ratings[1].id, rating1.id)


class FeedbackCacheModelTest(TestCase):
    """Test cases for FeedbackCache model"""

    def setUp(self):
        """Set up test data before each test"""
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
            clinical_history='Test history',
            master_template=self.template
        )

        self.prompt_version = PromptVersion.objects.create(
            version_number='v1.0.0',
            name='Test Version',
            description='Test prompt',
            prompt_template='Test template',
            is_active=True
        )

    def test_create_cache_entry(self):
        """Test creating cache entry with all fields"""
        cache_entry = FeedbackCache.objects.create(
            content_hash='abc123' * 10 + 'abcd',  # 64 chars
            feedback_content={'raw_feedback': 'test'},
            case=self.case,
            prompt_version=self.prompt_version,
            hit_count=0,
            expires_at=timezone.now() + timedelta(days=30)
        )

        self.assertIsNotNone(cache_entry.id)
        self.assertEqual(cache_entry.content_hash, 'abc123' * 10 + 'abcd')
        self.assertEqual(cache_entry.hit_count, 0)

    def test_unique_content_hash_constraint(self):
        """Test that content_hash must be unique"""
        hash_value = 'a' * 64

        FeedbackCache.objects.create(
            content_hash=hash_value,
            feedback_content={'test': 'data'},
            case=self.case,
            expires_at=timezone.now() + timedelta(days=30)
        )

        # Attempt to create duplicate should fail
        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                FeedbackCache.objects.create(
                    content_hash=hash_value,  # Same hash
                    feedback_content={'other': 'data'},
                    case=self.case,
                    expires_at=timezone.now() + timedelta(days=30)
                )

    def test_hit_count_increment(self):
        """Test that hit_count can be incremented"""
        cache_entry = FeedbackCache.objects.create(
            content_hash='b' * 64,
            feedback_content={'test': 'data'},
            case=self.case,
            hit_count=0,
            expires_at=timezone.now() + timedelta(days=30)
        )

        # Simulate cache hits
        cache_entry.hit_count += 1
        cache_entry.last_hit_at = timezone.now()
        cache_entry.save(update_fields=['hit_count', 'last_hit_at'])

        cache_entry.refresh_from_db()
        self.assertEqual(cache_entry.hit_count, 1)
        self.assertIsNotNone(cache_entry.last_hit_at)

    def test_cascade_delete_when_case_deleted(self):
        """Test that cache entries are deleted when case is deleted"""
        cache_entry = FeedbackCache.objects.create(
            content_hash='c' * 64,
            feedback_content={'test': 'data'},
            case=self.case,
            expires_at=timezone.now() + timedelta(days=30)
        )

        cache_id = cache_entry.id

        # Delete case
        self.case.delete()

        # Verify cache was also deleted
        self.assertFalse(FeedbackCache.objects.filter(id=cache_id).exists())

    def test_set_null_when_prompt_version_deleted(self):
        """Test that prompt_version is set to NULL when deleted"""
        cache_entry = FeedbackCache.objects.create(
            content_hash='d' * 64,
            feedback_content={'test': 'data'},
            case=self.case,
            prompt_version=self.prompt_version,
            expires_at=timezone.now() + timedelta(days=30)
        )

        # Delete prompt version
        self.prompt_version.delete()

        cache_entry.refresh_from_db()
        self.assertIsNone(cache_entry.prompt_version)

    def test_expired_cache_query(self):
        """Test querying for expired vs active caches"""
        # Create expired cache
        expired_cache = FeedbackCache.objects.create(
            content_hash='e' * 64,
            feedback_content={'test': 'data'},
            case=self.case,
            expires_at=timezone.now() - timedelta(days=1)  # Expired
        )

        # Create active cache
        active_cache = FeedbackCache.objects.create(
            content_hash='f' * 64,
            feedback_content={'test': 'data'},
            case=self.case,
            expires_at=timezone.now() + timedelta(days=30)  # Active
        )

        # Query for active caches
        active = FeedbackCache.objects.filter(expires_at__gt=timezone.now())
        self.assertEqual(active.count(), 1)
        self.assertEqual(active.first().id, active_cache.id)

        # Query for expired caches
        expired = FeedbackCache.objects.filter(expires_at__lt=timezone.now())
        self.assertEqual(expired.count(), 1)
        self.assertEqual(expired.first().id, expired_cache.id)


class PromptVersionModelTest(TestCase):
    """Test cases for PromptVersion model"""

    def setUp(self):
        """Set up test data before each test"""
        self.user = User.objects.create_user(
            username='testadmin',
            password='testpass123'
        )

    def test_create_prompt_version(self):
        """Test creating prompt version with all fields"""
        version = PromptVersion.objects.create(
            version_number='v1.0.0',
            name='Baseline Version',
            description='Initial prompt for AI feedback',
            prompt_template='You are an expert radiologist...',
            is_active=True,
            created_by=self.user
        )

        self.assertIsNotNone(version.id)
        self.assertEqual(version.version_number, 'v1.0.0')
        self.assertTrue(version.is_active)
        self.assertEqual(version.total_uses, 0)

    def test_unique_version_number_constraint(self):
        """Test that version_number must be unique"""
        PromptVersion.objects.create(
            version_number='v2.0.0',
            name='Version 1',
            description='Test',
            prompt_template='Template 1'
        )

        # Attempt to create duplicate version number should fail
        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                PromptVersion.objects.create(
                    version_number='v2.0.0',  # Same version number
                    name='Version 2',
                    description='Test',
                    prompt_template='Template 2'
                )

    def test_ab_test_configuration(self):
        """Test A/B testing fields"""
        version = PromptVersion.objects.create(
            version_number='v2.1.0',
            name='A/B Test Version',
            description='Testing improved wording',
            prompt_template='Template',
            is_active=False,
            is_ab_test=True,
            ab_test_weight=30  # 30% of traffic
        )

        self.assertTrue(version.is_ab_test)
        self.assertEqual(version.ab_test_weight, 30)

    def test_performance_metrics_defaults(self):
        """Test that performance metrics start as expected"""
        version = PromptVersion.objects.create(
            version_number='v2.2.0',
            name='Test Version',
            description='Test',
            prompt_template='Template'
        )

        self.assertEqual(version.total_uses, 0)
        self.assertIsNone(version.average_rating)
        self.assertIsNone(version.average_accuracy)
        self.assertIsNone(version.average_helpfulness)
        self.assertIsNone(version.average_actionability)
        self.assertEqual(version.total_tokens_used, 0)
        self.assertIsNone(version.average_tokens_per_use)

    def test_update_metrics(self):
        """Test updating performance metrics"""
        version = PromptVersion.objects.create(
            version_number='v2.3.0',
            name='Test Version',
            description='Test',
            prompt_template='Template'
        )

        # Simulate usage
        version.total_uses = 10
        version.total_tokens_used = 150000
        version.average_tokens_per_use = 15000
        version.average_rating = 4.5
        version.average_accuracy = 4.6
        version.average_helpfulness = 4.7
        version.average_actionability = 4.3
        version.save()

        version.refresh_from_db()
        self.assertEqual(version.total_uses, 10)
        self.assertEqual(version.average_rating, 4.5)
        self.assertEqual(version.average_tokens_per_use, 15000)

    def test_activation_timestamp(self):
        """Test that activated_at can be set"""
        version = PromptVersion.objects.create(
            version_number='v2.4.0',
            name='Test Version',
            description='Test',
            prompt_template='Template',
            is_active=False
        )

        # Activate version
        version.is_active = True
        version.activated_at = timezone.now()
        version.save()

        version.refresh_from_db()
        self.assertTrue(version.is_active)
        self.assertIsNotNone(version.activated_at)

    def test_string_representation(self):
        """Test string representation shows status"""
        # Active version
        active = PromptVersion.objects.create(
            version_number='v3.0.0',
            name='Active Version',
            description='Test',
            prompt_template='Template',
            is_active=True
        )
        self.assertIn("ACTIVE", str(active))

        # A/B test version
        ab_test = PromptVersion.objects.create(
            version_number='v3.1.0',
            name='AB Test Version',
            description='Test',
            prompt_template='Template',
            is_ab_test=True
        )
        self.assertIn("A/B TEST", str(ab_test))

        # Inactive version
        inactive = PromptVersion.objects.create(
            version_number='v3.2.0',
            name='Inactive Version',
            description='Test',
            prompt_template='Template',
            is_active=False
        )
        self.assertIn("INACTIVE", str(inactive))


class TokenUsageLogModelTest(TestCase):
    """Test cases for TokenUsageLog model"""

    def setUp(self):
        """Set up test data before each test"""
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
            clinical_history='Test history',
            master_template=self.template
        )

        self.report = Report.objects.create(
            case=self.case,
            user=self.user,
            structured_content=[{'content': 'test'}]
        )

        self.prompt_version = PromptVersion.objects.create(
            version_number='v1.0.0',
            name='Test Version',
            description='Test',
            prompt_template='Template',
            is_active=True
        )

    def test_create_token_log(self):
        """Test creating token usage log"""
        log_entry = TokenUsageLog.objects.create(
            report=self.report,
            case=self.case,
            prompt_version=self.prompt_version,
            input_tokens=12000,
            output_tokens=3000,
            total_tokens=15000,
            input_cost=Decimal('0.000900'),
            output_cost=Decimal('0.000900'),
            total_cost=Decimal('0.001800'),
            response_time_ms=2500,
            was_cached=False,
            model_name='gemini-2.5-flash'
        )

        self.assertIsNotNone(log_entry.id)
        self.assertEqual(log_entry.input_tokens, 12000)
        self.assertEqual(log_entry.output_tokens, 3000)
        self.assertEqual(log_entry.total_tokens, 15000)
        self.assertEqual(log_entry.total_cost, Decimal('0.001800'))
        self.assertFalse(log_entry.was_cached)

    def test_cached_request_log(self):
        """Test logging cached request with zero costs"""
        log_entry = TokenUsageLog.objects.create(
            report=self.report,
            case=self.case,
            prompt_version=self.prompt_version,
            input_tokens=0,
            output_tokens=0,
            total_tokens=0,
            input_cost=Decimal('0.000000'),
            output_cost=Decimal('0.000000'),
            total_cost=Decimal('0.000000'),
            response_time_ms=50,  # Fast cache lookup
            was_cached=True,
            model_name='cache'
        )

        self.assertTrue(log_entry.was_cached)
        self.assertEqual(log_entry.total_tokens, 0)
        self.assertEqual(log_entry.total_cost, Decimal('0.000000'))
        self.assertEqual(log_entry.model_name, 'cache')

    def test_cascade_delete_when_report_deleted(self):
        """Test that logs are deleted when report is deleted"""
        log_entry = TokenUsageLog.objects.create(
            report=self.report,
            case=self.case,
            input_tokens=15000,
            output_tokens=3000,
            total_tokens=18000,
            input_cost=Decimal('0.001125'),
            output_cost=Decimal('0.000900'),
            total_cost=Decimal('0.002025'),
            response_time_ms=3000,
            was_cached=False,
            model_name='gemini-2.5-flash'
        )

        log_id = log_entry.id

        # Delete report
        self.report.delete()

        # Verify log was also deleted
        self.assertFalse(TokenUsageLog.objects.filter(id=log_id).exists())

    def test_cascade_delete_when_case_deleted(self):
        """Test that logs are deleted when case is deleted"""
        log_entry = TokenUsageLog.objects.create(
            report=self.report,
            case=self.case,
            input_tokens=15000,
            output_tokens=3000,
            total_tokens=18000,
            input_cost=Decimal('0.001125'),
            output_cost=Decimal('0.000900'),
            total_cost=Decimal('0.002025'),
            response_time_ms=3000,
            was_cached=False,
            model_name='gemini-2.5-flash'
        )

        log_id = log_entry.id

        # Delete case (will also delete report which cascades to log)
        self.case.delete()

        # Verify log was also deleted
        self.assertFalse(TokenUsageLog.objects.filter(id=log_id).exists())

    def test_set_null_when_prompt_version_deleted(self):
        """Test that prompt_version is set to NULL when deleted"""
        log_entry = TokenUsageLog.objects.create(
            report=self.report,
            case=self.case,
            prompt_version=self.prompt_version,
            input_tokens=15000,
            output_tokens=3000,
            total_tokens=18000,
            input_cost=Decimal('0.001125'),
            output_cost=Decimal('0.000900'),
            total_cost=Decimal('0.002025'),
            response_time_ms=3000,
            was_cached=False,
            model_name='gemini-2.5-flash'
        )

        # Delete prompt version
        self.prompt_version.delete()

        log_entry.refresh_from_db()
        self.assertIsNone(log_entry.prompt_version)

    def test_string_representation(self):
        """Test string representation includes cost and cache status"""
        # Uncached log
        uncached_log = TokenUsageLog.objects.create(
            report=self.report,
            case=self.case,
            input_tokens=15000,
            output_tokens=3000,
            total_tokens=18000,
            input_cost=Decimal('0.001125'),
            output_cost=Decimal('0.000900'),
            total_cost=Decimal('0.002025'),
            response_time_ms=3000,
            was_cached=False,
            model_name='gemini-2.5-flash'
        )

        str_repr = str(uncached_log)
        self.assertIn('$0.002', str_repr)
        self.assertNotIn('CACHED', str_repr)

        # Cached log
        cached_log = TokenUsageLog.objects.create(
            report=self.report,
            case=self.case,
            input_tokens=0,
            output_tokens=0,
            total_tokens=0,
            input_cost=Decimal('0.000000'),
            output_cost=Decimal('0.000000'),
            total_cost=Decimal('0.000000'),
            response_time_ms=50,
            was_cached=True,
            model_name='cache'
        )

        str_repr_cached = str(cached_log)
        self.assertIn('CACHED', str_repr_cached)

    def test_cost_precision(self):
        """Test that costs maintain 6 decimal places precision"""
        log_entry = TokenUsageLog.objects.create(
            report=self.report,
            case=self.case,
            input_tokens=100,
            output_tokens=50,
            total_tokens=150,
            input_cost=Decimal('0.000008'),  # 6 decimal places
            output_cost=Decimal('0.000015'),  # 6 decimal places
            total_cost=Decimal('0.000023'),   # 6 decimal places
            response_time_ms=1500,
            was_cached=False,
            model_name='gemini-2.5-flash'
        )

        log_entry.refresh_from_db()
        # Verify precision is maintained
        self.assertEqual(log_entry.input_cost, Decimal('0.000008'))
        self.assertEqual(log_entry.output_cost, Decimal('0.000015'))
        self.assertEqual(log_entry.total_cost, Decimal('0.000023'))
