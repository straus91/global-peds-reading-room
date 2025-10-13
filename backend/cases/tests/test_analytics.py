"""
Unit tests for analytics_utils.py and analytics endpoints.

Tests data-driven metrics calculations for:
- Cost trends and token usage
- Quality metrics by prompt version
- Cache performance and hit rates
- False positive pattern analysis
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from rest_framework.test import APITestCase
from rest_framework import status

from cases.models import (
    Case,
    Report,
    MasterTemplate,
    TokenUsageLog,
    AIFeedbackDetailedRating,
    FeedbackCache,
    PromptVersion
)
from cases.analytics_utils import (
    get_cost_trends,
    get_quality_by_prompt_version,
    get_cache_performance,
    get_false_positive_patterns,
    get_prompt_version_comparison
)

User = get_user_model()


class CostTrendsAnalyticsTest(TestCase):
    """Test cost and token usage trend calculations."""

    def setUp(self):
        """Set up test data with token logs."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

        self.template = MasterTemplate.objects.create(
            name='Test Template',
            modality='CT',
            body_part='CH'
        )

        self.case = Case.objects.create(
            title='Test Case',
            subspecialty='CH',
            modality='CT',
            difficulty='beginner',
            clinical_history='Test history',
            master_template=self.template,
            key_findings='test',
            diagnosis='test diagnosis'
        )

        self.report = Report.objects.create(
            case=self.case,
            user=self.user,
            structured_content=[{'section_name': 'Findings', 'content': 'Test'}],
            ai_feedback_content={'raw_feedback': 'Test feedback'}
        )

        # Create prompt version
        self.prompt_version = PromptVersion.objects.create(
            version_number='v1.0',
            name='Test Prompt Version 1',
            description='Test prompt for analytics',
            prompt_template='Test prompt',
            is_active=True
        )

    def test_cost_trends_with_logs(self):
        """Test cost trend calculation with sample logs."""
        # Create token logs for last 5 days
        now = timezone.now()
        for i in range(5):
            date = now - timedelta(days=i)
            log = TokenUsageLog.objects.create(
                report=self.report,
                case=self.case,
                prompt_version=self.prompt_version,
                input_tokens=1000 + (i * 100),
                output_tokens=500 + (i * 50),
                total_tokens=(1000 + (i * 100)) + (500 + (i * 50)),
                input_cost=Decimal('0.025') + Decimal(str(i * 0.005)),
                output_cost=Decimal('0.025') + Decimal(str(i * 0.005)),
                total_cost=Decimal('0.05') + Decimal(str(i * 0.01)),
                response_time_ms=500,
                was_cached=False,
                model_name='gemini-2.5-flash'
            )
            log.created_at = date
            log.save()

        # Get cost trends
        trends = get_cost_trends(days=7)

        # Verify aggregates
        self.assertEqual(trends['total_requests'], 5)
        self.assertEqual(trends['total_prompt_tokens'], 1000 + 1100 + 1200 + 1300 + 1400)
        self.assertEqual(trends['total_completion_tokens'], 500 + 550 + 600 + 650 + 700)
        self.assertIsInstance(trends['total_cost_usd'], Decimal)
        self.assertEqual(trends['cached_requests'], 0)

        # Verify daily breakdown exists
        self.assertEqual(len(trends['daily_breakdown']), 5)

    def test_cost_trends_with_cached_requests(self):
        """Test that cached requests are counted and savings calculated."""
        # Create mix of cached and non-cached logs
        for i in range(3):
            TokenUsageLog.objects.create(
                report=self.report,
                case=self.case,
                prompt_version=self.prompt_version,
                input_tokens=1000,
                output_tokens=500,
                total_tokens=1500,
                input_cost=Decimal('0.025'),
                output_cost=Decimal('0.025'),
                total_cost=Decimal('0.05'),
                response_time_ms=500,
                model_name='gemini-2.5-flash',
                was_cached=(i % 2 == 0)  # Every other one cached
            )

        trends = get_cost_trends(days=7)

        self.assertEqual(trends['total_requests'], 3)
        self.assertEqual(trends['cached_requests'], 2)  # 0 and 2 are cached
        self.assertGreater(trends['cache_savings_usd'], Decimal('0'))

    def test_cost_trends_empty_data(self):
        """Test cost trends with no token logs."""
        trends = get_cost_trends(days=30)

        self.assertEqual(trends['total_requests'], 0)
        self.assertEqual(trends['total_prompt_tokens'], 0)
        self.assertEqual(trends['total_cost_usd'], Decimal('0.00'))
        self.assertEqual(len(trends['daily_breakdown']), 0)


class PromptVersionQualityTest(TestCase):
    """Test quality metrics by prompt version."""

    def setUp(self):
        """Set up test data with multiple prompt versions and ratings."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

        self.template = MasterTemplate.objects.create(
            name='Test Template',
            modality='CT',
            body_part='CH'
        )

        self.case = Case.objects.create(
            title='Test Case',
            subspecialty='CH',
            modality='CT',
            difficulty='beginner',
            clinical_history='Test history',
            master_template=self.template,
            key_findings='test',
            diagnosis='test diagnosis'
        )

        # Create two prompt versions
        self.version_1 = PromptVersion.objects.create(
            version_number='v1.0',
            name='Test Prompt Version 1',
            description='Old prompt for testing',
            prompt_template='Old prompt',
            is_active=False
        )

        self.version_2 = PromptVersion.objects.create(
            version_number='v2.0',
            name='Test Prompt Version 2',
            description='New improved prompt for testing',
            prompt_template='New improved prompt',
            is_active=True
        )

    def test_quality_comparison_with_ratings(self):
        """Test quality metrics for different prompt versions."""
        # Create reports and ratings for version 1
        for i in range(3):
            report = Report.objects.create(
                case=self.case,
                user=self.user,
                structured_content=[{'content': f'Report {i}'}],
                ai_feedback_content={'feedback': f'Feedback {i}'}
            )

            # Create token log to associate report with prompt version
            TokenUsageLog.objects.create(
                report=report,
                case=self.case,
                prompt_version=self.version_1,
                input_tokens=1000,
                output_tokens=500,
                total_tokens=1500,
                input_cost=Decimal('0.025'),
                output_cost=Decimal('0.025'),
                total_cost=Decimal('0.05'),
                response_time_ms=500,
                model_name='gemini-2.5-flash',
                was_cached=False
            )

            # Create rating (v1: avg accuracy 3.0)
            AIFeedbackDetailedRating.objects.create(
                report=report,
                user=self.user,
                accuracy_rating=3,
                helpfulness_rating=3,
                actionability_rating=3,
                overall_rating=3,
                has_false_positives=(i == 0)  # First one has FP
            )

        # Create reports and ratings for version 2
        for i in range(2):
            report = Report.objects.create(
                case=self.case,
                user=self.user,
                structured_content=[{'content': f'Report v2 {i}'}],
                ai_feedback_content={'feedback': f'Feedback v2 {i}'}
            )

            TokenUsageLog.objects.create(
                report=report,
                case=self.case,
                prompt_version=self.version_2,
                input_tokens=1000,
                output_tokens=500,
                total_tokens=1500,
                input_cost=Decimal('0.025'),
                output_cost=Decimal('0.025'),
                total_cost=Decimal('0.05'),
                response_time_ms=500,
                model_name='gemini-2.5-flash',
                was_cached=False
            )

            # Create rating (v2: avg accuracy 4.5)
            AIFeedbackDetailedRating.objects.create(
                report=report,
                user=self.user,
                accuracy_rating=4 + i,  # 4, 5
                helpfulness_rating=4 + i,
                actionability_rating=4 + i,
                overall_rating=4 + i,
                has_false_positives=False
            )

        # Get quality comparison
        quality_data = get_quality_by_prompt_version()

        # Should have data for both versions
        self.assertEqual(len(quality_data), 2)

        # Find each version in results
        v1_data = next(v for v in quality_data if v['prompt_version_id'] == self.version_1.id)
        v2_data = next(v for v in quality_data if v['prompt_version_id'] == self.version_2.id)

        # Verify v1 metrics
        self.assertEqual(v1_data['rating_count'], 3)
        self.assertEqual(v1_data['avg_accuracy'], 3.0)
        self.assertEqual(v1_data['false_positive_count'], 1)
        self.assertFalse(v1_data['is_active'])

        # Verify v2 metrics (should be better)
        self.assertEqual(v2_data['rating_count'], 2)
        self.assertEqual(v2_data['avg_accuracy'], 4.5)
        self.assertEqual(v2_data['false_positive_count'], 0)
        self.assertTrue(v2_data['is_active'])

    def test_quality_with_no_ratings(self):
        """Test prompt version with no ratings yet."""
        quality_data = get_quality_by_prompt_version()

        # Should include versions even without ratings
        self.assertEqual(len(quality_data), 2)

        # All should have zero ratings
        for version_data in quality_data:
            self.assertEqual(version_data['rating_count'], 0)
            self.assertIsNone(version_data['avg_accuracy'])

    def test_prompt_version_direct_comparison(self):
        """Test direct comparison between two specific versions."""
        # Create sample data for both versions (same as above test)
        for i in range(3):
            report = Report.objects.create(
                case=self.case,
                user=self.user,
                structured_content=[{'content': f'Report {i}'}],
                ai_feedback_content={'feedback': f'Feedback {i}'}
            )

            TokenUsageLog.objects.create(
                report=report,
                case=self.case,
                prompt_version=self.version_1,
                input_tokens=1000,
                output_tokens=500,
                total_tokens=1500,
                input_cost=Decimal('0.025'),
                output_cost=Decimal('0.025'),
                total_cost=Decimal('0.05'),
                response_time_ms=500,
                model_name='gemini-2.5-flash',
                was_cached=False
            )

            AIFeedbackDetailedRating.objects.create(
                report=report,
                user=self.user,
                accuracy_rating=3,
                helpfulness_rating=3,
                actionability_rating=3,
                overall_rating=3
            )

        for i in range(2):
            report = Report.objects.create(
                case=self.case,
                user=self.user,
                structured_content=[{'content': f'Report v2 {i}'}],
                ai_feedback_content={'feedback': f'Feedback v2 {i}'}
            )

            TokenUsageLog.objects.create(
                report=report,
                case=self.case,
                prompt_version=self.version_2,
                input_tokens=1000,
                output_tokens=500,
                total_tokens=1500,
                input_cost=Decimal('0.025'),
                output_cost=Decimal('0.025'),
                total_cost=Decimal('0.05'),
                response_time_ms=500,
                model_name='gemini-2.5-flash',
                was_cached=False
            )

            AIFeedbackDetailedRating.objects.create(
                report=report,
                user=self.user,
                accuracy_rating=5,
                helpfulness_rating=5,
                actionability_rating=5,
                overall_rating=5
            )

        # Compare the two versions
        comparison = get_prompt_version_comparison(self.version_1.id, self.version_2.id)

        # Verify comparison structure
        self.assertIn('version_1', comparison)
        self.assertIn('version_2', comparison)
        self.assertIn('comparison', comparison)

        # Verify version 2 is better (overall_diff = v1 - v2, so negative means v2 better)
        self.assertEqual(comparison['comparison']['better_version'], 'version_2')
        self.assertLess(comparison['comparison']['overall_diff'], -1.0)  # v2 much better (negative diff)


class CachePerformanceTest(TestCase):
    """Test cache effectiveness metrics."""

    def setUp(self):
        """Set up test data with cache entries and token logs."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

        self.template = MasterTemplate.objects.create(
            name='Test Template',
            modality='CT',
            body_part='CH'
        )

        self.case = Case.objects.create(
            title='Test Case',
            subspecialty='CH',
            modality='CT',
            difficulty='beginner',
            clinical_history='Test history',
            master_template=self.template,
            key_findings='test',
            diagnosis='test diagnosis'
        )

        self.report = Report.objects.create(
            case=self.case,
            user=self.user,
            structured_content=[{'section_name': 'Findings', 'content': 'Test'}],
            ai_feedback_content={'raw_feedback': 'Test feedback'}
        )

        self.prompt_version = PromptVersion.objects.create(
            version_number='v1.0',
            name='Test Prompt Version 1',
            description='Test prompt for cache performance',
            prompt_template='Test prompt',
            is_active=True
        )

    def test_cache_performance_with_hits(self):
        """Test cache performance calculation with cache hits."""
        # Create cache entries
        for i in range(5):
            FeedbackCache.objects.create(
                content_hash=f'{i:064d}',  # Exactly 64-char hash
                feedback_content={'feedback': f'Cached {i}'},
                case=self.case,
                expires_at=timezone.now() + timedelta(days=30)
            )

        # Create token logs (3 cached, 2 not cached)
        for i in range(5):
            TokenUsageLog.objects.create(
                report=self.report,
                case=self.case,
                prompt_version=self.prompt_version,
                input_tokens=1000,
                output_tokens=500,
                total_tokens=1500,
                input_cost=Decimal('0.025'),
                output_cost=Decimal('0.025'),
                total_cost=Decimal('0.05'),
                response_time_ms=500,
                model_name='gemini-2.5-flash',
                was_cached=(i < 3)  # First 3 are cached
            )

        performance = get_cache_performance(days=30)

        self.assertEqual(performance['total_cached_entries'], 5)
        self.assertEqual(performance['requests_using_cache'], 3)
        self.assertEqual(performance['requests_not_cached'], 2)
        self.assertEqual(performance['cache_hit_rate'], 60.0)  # 3/5 = 60%
        self.assertGreater(performance['cost_savings_usd'], Decimal('0'))

    def test_cache_performance_expired_entries(self):
        """Test detection of expired cache entries."""
        # Create old cache entry (> 24 hours)
        old_time = timezone.now() - timedelta(hours=25)
        old_entry = FeedbackCache.objects.create(
            content_hash='1' * 64,  # Exactly 64-char hash
            feedback_content={'feedback': 'Old'},
            case=self.case,
            expires_at=timezone.now() + timedelta(days=30)
        )
        old_entry.created_at = old_time
        old_entry.save()

        # Create fresh cache entry
        FeedbackCache.objects.create(
            content_hash='2' * 64,  # Exactly 64-char hash
            feedback_content={'feedback': 'Fresh'},
            case=self.case,
            expires_at=timezone.now() + timedelta(days=30)
        )

        performance = get_cache_performance(days=30)

        self.assertEqual(performance['total_cached_entries'], 2)
        self.assertEqual(performance['expired_entries'], 1)

    def test_cache_performance_zero_requests(self):
        """Test cache performance with no requests."""
        performance = get_cache_performance(days=30)

        self.assertEqual(performance['cache_hit_rate'], 0.0)
        self.assertEqual(performance['requests_using_cache'], 0)
        self.assertEqual(performance['cost_savings_usd'], Decimal('0.00'))


class FalsePositivePatternsTest(TestCase):
    """Test false positive pattern extraction."""

    def setUp(self):
        """Set up test data with false positive ratings."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

        self.template = MasterTemplate.objects.create(
            name='Test Template',
            modality='CT',
            body_part='CH'
        )

        self.case = Case.objects.create(
            title='Test Case',
            case_identifier='TEST-CT-2025-0001',
            subspecialty='CH',
            modality='CT',
            difficulty='beginner',
            clinical_history='Test history',
            master_template=self.template,
            key_findings='test',
            diagnosis='test diagnosis'
        )

        self.report = Report.objects.create(
            case=self.case,
            user=self.user,
            structured_content=[{'section_name': 'Findings', 'content': 'Test'}],
            ai_feedback_content={'raw_feedback': 'Test feedback'}
        )

    def test_false_positive_patterns_extraction(self):
        """Test extraction of false positive examples."""
        # Create ratings with false positives (need separate reports for each rating)
        for i in range(3):
            report = Report.objects.create(
                case=self.case,
                user=self.user,
                structured_content=[{'section_name': 'Findings', 'content': f'Test FP {i}'}],
                ai_feedback_content={'raw_feedback': f'Feedback FP {i}'}
            )
            AIFeedbackDetailedRating.objects.create(
                report=report,
                user=self.user,
                accuracy_rating=2 + i,
                helpfulness_rating=3,
                actionability_rating=3,
                overall_rating=3,
                has_false_positives=True,
                false_positive_details=f'AI incorrectly flagged issue {i}'
            )

        # Create normal ratings (also need separate reports)
        for i in range(2):
            report = Report.objects.create(
                case=self.case,
                user=self.user,
                structured_content=[{'section_name': 'Findings', 'content': f'Test normal {i}'}],
                ai_feedback_content={'raw_feedback': f'Feedback normal {i}'}
            )
            AIFeedbackDetailedRating.objects.create(
                report=report,
                user=self.user,
                accuracy_rating=5,
                helpfulness_rating=5,
                actionability_rating=5,
                overall_rating=5,
                has_false_positives=False
            )

        patterns = get_false_positive_patterns(limit=50)

        self.assertEqual(patterns['total_false_positives'], 3)
        self.assertEqual(patterns['false_positive_rate'], 60.0)  # 3/5 = 60%
        self.assertEqual(len(patterns['recent_examples']), 3)

        # Verify example structure
        example = patterns['recent_examples'][0]
        self.assertIn('rating_id', example)
        self.assertIn('report_case_identifier', example)
        self.assertEqual(example['report_case_identifier'], 'TEST-CT-2025-0001')
        self.assertIn('details', example)

    def test_false_positive_patterns_limit(self):
        """Test that limit parameter works correctly."""
        # Create 10 FP ratings (need separate reports for each)
        for i in range(10):
            report = Report.objects.create(
                case=self.case,
                user=self.user,
                structured_content=[{'section_name': 'Findings', 'content': f'Test FP limit {i}'}],
                ai_feedback_content={'raw_feedback': f'Feedback FP limit {i}'}
            )
            AIFeedbackDetailedRating.objects.create(
                report=report,
                user=self.user,
                accuracy_rating=3,
                helpfulness_rating=3,
                actionability_rating=3,
                overall_rating=3,
                has_false_positives=True,
                false_positive_details=f'Issue {i}'
            )

        # Request only 5
        patterns = get_false_positive_patterns(limit=5)

        self.assertEqual(patterns['total_false_positives'], 10)
        self.assertEqual(len(patterns['recent_examples']), 5)  # Limited to 5


class AnalyticsAPIEndpointsTest(APITestCase):
    """Test analytics API endpoints require admin and return correct data."""

    def setUp(self):
        """Set up test users and data."""
        self.regular_user = User.objects.create_user(
            username='regular',
            password='test123'
        )

        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='admin123'
        )

        self.template = MasterTemplate.objects.create(
            name='Test Template',
            modality='CT',
            body_part='CH'
        )

        self.case = Case.objects.create(
            title='Test Case',
            subspecialty='CH',
            modality='CT',
            difficulty='beginner',
            clinical_history='Test',
            master_template=self.template,
            key_findings='test',
            diagnosis='test'
        )

        self.report = Report.objects.create(
            case=self.case,
            user=self.regular_user,
            structured_content=[{'content': 'Test'}],
            ai_feedback_content={'feedback': 'Test'}
        )

    def test_cost_trends_endpoint_requires_admin(self):
        """Test cost trends endpoint requires admin permission."""
        self.client.force_authenticate(user=self.regular_user)
        url = '/api/cases/detailed-ratings/analytics/cost-trends/'

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cost_trends_endpoint_works_for_admin(self):
        """Test cost trends endpoint works for admin."""
        self.client.force_authenticate(user=self.admin_user)
        url = '/api/cases/detailed-ratings/analytics/cost-trends/'

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_requests', response.data)
        self.assertIn('daily_breakdown', response.data)

    def test_prompt_comparison_endpoint_requires_admin(self):
        """Test prompt comparison endpoint requires admin."""
        self.client.force_authenticate(user=self.regular_user)
        url = '/api/cases/detailed-ratings/analytics/prompt-comparison/'

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_prompt_comparison_endpoint_works_for_admin(self):
        """Test prompt comparison endpoint works for admin."""
        self.client.force_authenticate(user=self.admin_user)
        url = '/api/cases/detailed-ratings/analytics/prompt-comparison/'

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('prompt_versions', response.data)
        self.assertIn('note', response.data)

    def test_cache_performance_endpoint_requires_admin(self):
        """Test cache performance endpoint requires admin."""
        self.client.force_authenticate(user=self.regular_user)
        url = '/api/cases/detailed-ratings/analytics/cache-performance/'

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cache_performance_endpoint_works_for_admin(self):
        """Test cache performance endpoint works for admin."""
        self.client.force_authenticate(user=self.admin_user)
        url = '/api/cases/detailed-ratings/analytics/cache-performance/'

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('cache_hit_rate', response.data)
        self.assertIn('cost_savings_usd', response.data)
