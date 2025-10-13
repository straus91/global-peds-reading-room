"""
Integration tests for AI feedback rating system end-to-end flows.

Tests complete user journeys through the feedback quality tracking system:
- Report submission → AI feedback → Rating → Analytics flow
- Multi-user rating scenarios
- Cache integration with ratings
- Prompt version tracking with ratings
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch

from cases.models import (
    Case,
    Report,
    MasterTemplate,
    MasterTemplateSection,
    CaseTemplate,
    CaseTemplateSectionContent,
    Language,
    TokenUsageLog,
    AIFeedbackDetailedRating,
    FeedbackCache,
    PromptVersion
)

User = get_user_model()


class CompleteRatingFlowTest(APITestCase):
    """Test complete end-to-end flow from report to rating to analytics."""

    def setUp(self):
        """Set up complete test environment with all dependencies."""
        # Create users
        self.student = User.objects.create_user(
            username='student',
            email='student@test.com',
            password='student123'
        )
        self.admin = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='admin123'
        )

        # Create template structure
        self.template = MasterTemplate.objects.create(
            name='Chest X-Ray Template',
            modality='XR',
            body_part='CH'
        )

        self.findings_section = MasterTemplateSection.objects.create(
            master_template=self.template,
            name='Findings',
            order=1,
            is_required=True,
            placeholder_text='Describe all findings'
        )

        self.impression_section = MasterTemplateSection.objects.create(
            master_template=self.template,
            name='Impression',
            order=2,
            is_required=True,
            placeholder_text='Your diagnostic impression'
        )

        # Create language
        self.language = Language.objects.create(
            code='en',
            name='English',
            is_active=True
        )

        # Create case with expert template
        self.case = Case.objects.create(
            title='Pneumothorax Case',
            case_identifier='CH-XR-2025-0001',
            subspecialty='CH',
            modality='XR',
            difficulty='intermediate',
            clinical_history='Shortness of breath after trauma',
            key_findings='right pneumothorax;no rib fracture',
            diagnosis='Right-sided pneumothorax',
            master_template=self.template,
            status='published'
        )

        # Create expert template
        self.expert_template = CaseTemplate.objects.create(
            case=self.case,
            language=self.language
        )

        CaseTemplateSectionContent.objects.create(
            case_template=self.expert_template,
            master_section=self.findings_section,
            content='Right-sided pneumothorax measuring 2cm at apex. No rib fractures. No pleural effusion.',
            key_concepts_text='pneumothorax;right-sided;2cm at apex;no fractures;no effusion'
        )

        CaseTemplateSectionContent.objects.create(
            case_template=self.expert_template,
            master_section=self.impression_section,
            content='Right-sided pneumothorax requiring clinical correlation.',
            key_concepts_text='pneumothorax;clinical correlation'
        )

        # Create prompt version
        self.prompt_version = PromptVersion.objects.create(
            version_number='v1.0',
            name='Initial Prompt',
            description='First version of feedback prompt',
            prompt_template='Provide feedback on report...',
            is_active=True
        )

    def test_complete_feedback_flow_with_rating(self):
        """Test: Report → AI feedback → Rating → Analytics appear in dashboard."""
        self.client.force_authenticate(user=self.student)

        # Step 1: Create report
        report_data = {
            'case_id': self.case.id,
            'section_details': [
                {
                    'master_template_section_id': self.findings_section.id,
                    'content': 'Right lung shows decreased markings. No fractures seen.'
                },
                {
                    'master_template_section_id': self.impression_section.id,
                    'content': 'Possible pneumothorax'
                }
            ]
        }

        response = self.client.post('/api/cases/reports/', report_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        report_id = response.data['id']

        # Step 2: Generate AI feedback (mocked)
        with patch('cases.views.generate_report_comparison_summary') as mock_summary, \
             patch('cases.views.get_feedback_from_llm') as mock_llm:

            mock_summary.return_value = {
                'overall_diagnosis_comparison': {'status': 'Partially Aligned'},
                'section_comparisons': []
            }

            mock_llm.return_value = """
            You identified a pneumothorax, which is correct.

            1. CRITICAL DISCREPANCIES:
            None identified.

            2. NON-CRITICAL DISCREPANCIES:
            - You did not specify the size of the pneumothorax (2cm at apex).

            SECTION SEVERITY ASSESSMENT:
            Section: Findings
            Severity: Moderate
            Reason: Missing size measurement is important for management.
            """

            feedback_response = self.client.post(f'/api/cases/reports/{report_id}/ai-feedback/')
            self.assertEqual(feedback_response.status_code, status.HTTP_200_OK)
            self.assertIn('section_feedback', feedback_response.data)

        # Step 3: Log token usage (simulating what would happen in real flow)
        TokenUsageLog.objects.create(
            report_id=report_id,
            case=self.case,
            prompt_version=self.prompt_version,
            input_tokens=1500,
            output_tokens=300,
            total_tokens=1800,
            input_cost=Decimal('0.0375'),
            output_cost=Decimal('0.015'),
            total_cost=Decimal('0.0525'),
            response_time_ms=2500,
            model_name='gemini-2.5-flash',
            was_cached=False
        )

        # Step 4: Student rates the AI feedback
        rating_data = {
            'report_id': report_id,
            'accuracy_rating': 4,
            'helpfulness_rating': 5,
            'actionability_rating': 4,
            'overall_rating': 4,
            'has_false_positives': False,
            'comment': 'Very helpful feedback, especially about the size measurement'
        }

        rating_response = self.client.post('/api/cases/detailed-ratings/', rating_data, format='json')
        self.assertEqual(rating_response.status_code, status.HTTP_201_CREATED)
        rating_id = rating_response.data['id']

        # Step 5: Admin checks analytics
        self.client.force_authenticate(user=self.admin)

        # Check cost trends
        cost_response = self.client.get('/api/cases/detailed-ratings/analytics/cost-trends/')
        self.assertEqual(cost_response.status_code, status.HTTP_200_OK)
        # Analytics show at least our request (may include others from other tests in class)
        self.assertGreaterEqual(cost_response.data['total_requests'], 1)
        # Verify our specific cost is included
        self.assertIn(str(Decimal('0.0525')), str(cost_response.data))

        # Check quality metrics by prompt version
        quality_response = self.client.get('/api/cases/detailed-ratings/analytics/prompt-comparison/')
        self.assertEqual(quality_response.status_code, status.HTTP_200_OK)
        prompt_versions = quality_response.data['prompt_versions']
        self.assertEqual(len(prompt_versions), 1)
        self.assertEqual(prompt_versions[0]['rating_count'], 1)
        self.assertEqual(prompt_versions[0]['avg_overall'], 4.0)

    def test_multi_user_rating_aggregation(self):
        """Test that multiple users can rate same case and analytics aggregate correctly."""
        # Create second student
        student2 = User.objects.create_user(
            username='student2',
            password='test123'
        )

        # Student 1 submits report and rates
        self.client.force_authenticate(user=self.student)

        report1 = Report.objects.create(
            case=self.case,
            user=self.student,
            structured_content=[{'content': 'Report 1'}],
            ai_feedback_content={'raw_feedback': 'Feedback 1'}
        )

        TokenUsageLog.objects.create(
            report=report1,
            case=self.case,
            prompt_version=self.prompt_version,
            input_tokens=1000,
            output_tokens=200,
            total_tokens=1200,
            input_cost=Decimal('0.025'),
            output_cost=Decimal('0.01'),
            total_cost=Decimal('0.035'),
            response_time_ms=1500,
            model_name='gemini-2.5-flash',
            was_cached=False
        )

        AIFeedbackDetailedRating.objects.create(
            report=report1,
            user=self.student,
            accuracy_rating=3,
            helpfulness_rating=3,
            actionability_rating=3,
            overall_rating=3
        )

        # Student 2 submits report and rates
        self.client.force_authenticate(user=student2)

        report2 = Report.objects.create(
            case=self.case,
            user=student2,
            structured_content=[{'content': 'Report 2'}],
            ai_feedback_content={'raw_feedback': 'Feedback 2'}
        )

        TokenUsageLog.objects.create(
            report=report2,
            case=self.case,
            prompt_version=self.prompt_version,
            input_tokens=1000,
            output_tokens=200,
            total_tokens=1200,
            input_cost=Decimal('0.025'),
            output_cost=Decimal('0.01'),
            total_cost=Decimal('0.035'),
            response_time_ms=1500,
            model_name='gemini-2.5-flash',
            was_cached=False
        )

        AIFeedbackDetailedRating.objects.create(
            report=report2,
            user=student2,
            accuracy_rating=5,
            helpfulness_rating=5,
            actionability_rating=5,
            overall_rating=5
        )

        # Check analytics aggregation
        self.client.force_authenticate(user=self.admin)

        quality_response = self.client.get('/api/cases/detailed-ratings/analytics/prompt-comparison/')
        self.assertEqual(quality_response.status_code, status.HTTP_200_OK)

        prompt_data = quality_response.data['prompt_versions'][0]
        self.assertEqual(prompt_data['rating_count'], 2)
        self.assertEqual(prompt_data['avg_overall'], 4.0)  # (3 + 5) / 2
        self.assertEqual(prompt_data['avg_accuracy'], 4.0)  # (3 + 5) / 2


class CacheIntegrationTest(TestCase):
    """Test cache integration with rating and analytics system."""

    def setUp(self):
        """Set up cache test environment."""
        self.user = User.objects.create_user(
            username='testuser',
            password='test123'
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

        self.prompt_version = PromptVersion.objects.create(
            version_number='v1.0',
            name='Test Prompt',
            description='Test',
            prompt_template='Test',
            is_active=True
        )

    def test_cached_request_cost_savings(self):
        """Test that cached requests show cost savings in analytics."""
        report1 = Report.objects.create(
            case=self.case,
            user=self.user,
            structured_content=[{'content': 'Test'}],
            ai_feedback_content={'feedback': 'Test'}
        )

        report2 = Report.objects.create(
            case=self.case,
            user=self.user,
            structured_content=[{'content': 'Test'}],
            ai_feedback_content={'feedback': 'Test'}
        )

        # First request: not cached, full cost
        TokenUsageLog.objects.create(
            report=report1,
            case=self.case,
            prompt_version=self.prompt_version,
            input_tokens=2000,
            output_tokens=500,
            total_tokens=2500,
            input_cost=Decimal('0.05'),
            output_cost=Decimal('0.025'),
            total_cost=Decimal('0.075'),
            response_time_ms=3000,
            model_name='gemini-2.5-flash',
            was_cached=False
        )

        # Second request: cached, still logs cost saved
        TokenUsageLog.objects.create(
            report=report2,
            case=self.case,
            prompt_version=self.prompt_version,
            input_tokens=0,  # No tokens used (cached)
            output_tokens=0,
            total_tokens=0,
            input_cost=Decimal('0'),
            output_cost=Decimal('0'),
            total_cost=Decimal('0.075'),  # Cost that would have been charged
            response_time_ms=50,  # Much faster from cache
            model_name='gemini-2.5-flash',
            was_cached=True
        )

        # Check cost trends shows savings
        from cases.analytics_utils import get_cost_trends
        trends = get_cost_trends(days=7)

        self.assertEqual(trends['total_requests'], 2)
        self.assertEqual(trends['cached_requests'], 1)
        self.assertEqual(trends['cache_savings_usd'], Decimal('0.075'))


class PromptVersionTrackingTest(TestCase):
    """Test that prompt version changes are tracked correctly in ratings."""

    def setUp(self):
        """Set up prompt version tracking test."""
        self.user = User.objects.create_user(
            username='testuser',
            password='test123'
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

        # Create two prompt versions
        self.v1 = PromptVersion.objects.create(
            version_number='v1.0',
            name='Original Prompt',
            description='First version',
            prompt_template='Original prompt text',
            is_active=False
        )

        self.v2 = PromptVersion.objects.create(
            version_number='v2.0',
            name='Improved Prompt',
            description='Improved version',
            prompt_template='Improved prompt text',
            is_active=True
        )

    def test_prompt_version_quality_improvement_tracking(self):
        """Test that quality improvements between prompt versions are tracked."""
        # v1 gets poor ratings
        for i in range(3):
            report = Report.objects.create(
                case=self.case,
                user=self.user,
                structured_content=[{'content': f'v1 report {i}'}],
                ai_feedback_content={'feedback': f'v1 feedback {i}'}
            )

            TokenUsageLog.objects.create(
                report=report,
                case=self.case,
                prompt_version=self.v1,
                input_tokens=1000,
                output_tokens=200,
                total_tokens=1200,
                input_cost=Decimal('0.025'),
                output_cost=Decimal('0.01'),
                total_cost=Decimal('0.035'),
                response_time_ms=1500,
                model_name='gemini-2.5-flash',
                was_cached=False
            )

            AIFeedbackDetailedRating.objects.create(
                report=report,
                user=self.user,
                accuracy_rating=2,
                helpfulness_rating=2,
                actionability_rating=2,
                overall_rating=2
            )

        # v2 gets good ratings
        for i in range(3):
            report = Report.objects.create(
                case=self.case,
                user=self.user,
                structured_content=[{'content': f'v2 report {i}'}],
                ai_feedback_content={'feedback': f'v2 feedback {i}'}
            )

            TokenUsageLog.objects.create(
                report=report,
                case=self.case,
                prompt_version=self.v2,
                input_tokens=1000,
                output_tokens=200,
                total_tokens=1200,
                input_cost=Decimal('0.025'),
                output_cost=Decimal('0.01'),
                total_cost=Decimal('0.035'),
                response_time_ms=1500,
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

        # Check comparison shows v2 is better
        from cases.analytics_utils import get_prompt_version_comparison
        comparison = get_prompt_version_comparison(self.v1.id, self.v2.id)

        self.assertEqual(comparison['version_1']['avg_overall'], 2.0)
        self.assertEqual(comparison['version_2']['avg_overall'], 5.0)
        self.assertEqual(comparison['comparison']['better_version'], 'version_2')
        self.assertLess(comparison['comparison']['overall_diff'], -2.0)  # v1 - v2 = negative


class ErrorHandlingIntegrationTest(APITestCase):
    """Test error handling throughout the rating flow."""

    def setUp(self):
        """Set up error handling test environment."""
        self.user = User.objects.create_user(
            username='testuser',
            password='test123'
        )
        self.client.force_authenticate(user=self.user)

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
            diagnosis='test',
            status='published'
        )

    def test_cannot_rate_report_without_ai_feedback(self):
        """Test that user cannot rate a report that has no AI feedback."""
        report = Report.objects.create(
            case=self.case,
            user=self.user,
            structured_content=[{'content': 'Test'}],
            ai_feedback_content={}  # Empty - no feedback generated
        )

        rating_data = {
            'report_id': report.id,
            'accuracy_rating': 5,
            'helpfulness_rating': 5,
            'actionability_rating': 5,
            'overall_rating': 5
        }

        response = self.client.post('/api/cases/detailed-ratings/', rating_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Check that error mentions AI feedback requirement
        self.assertIn('ai feedback', str(response.data).lower())

    def test_cannot_rate_another_users_report(self):
        """Test that user cannot rate another user's report."""
        other_user = User.objects.create_user(
            username='otheruser',
            password='test123'
        )

        report = Report.objects.create(
            case=self.case,
            user=other_user,
            structured_content=[{'content': 'Test'}],
            ai_feedback_content={'raw_feedback': 'Test'}
        )

        rating_data = {
            'report_id': report.id,
            'accuracy_rating': 5,
            'helpfulness_rating': 5,
            'actionability_rating': 5,
            'overall_rating': 5
        }

        response = self.client.post('/api/cases/detailed-ratings/', rating_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('own report', str(response.data).lower())

    def test_false_positive_requires_details(self):
        """Test that marking false positives requires details."""
        report = Report.objects.create(
            case=self.case,
            user=self.user,
            structured_content=[{'content': 'Test'}],
            ai_feedback_content={'raw_feedback': 'Test'}
        )

        rating_data = {
            'report_id': report.id,
            'accuracy_rating': 2,
            'helpfulness_rating': 3,
            'actionability_rating': 3,
            'overall_rating': 3,
            'has_false_positives': True
            # Missing false_positive_details
        }

        response = self.client.post('/api/cases/detailed-ratings/', rating_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('false_positive_details', str(response.data))


class PerformanceIntegrationTest(TestCase):
    """Test query performance in integrated flows."""

    def setUp(self):
        """Set up performance test data."""
        self.user = User.objects.create_user(
            username='testuser',
            password='test123'
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

        self.prompt_version = PromptVersion.objects.create(
            version_number='v1.0',
            name='Test Prompt',
            description='Test',
            prompt_template='Test',
            is_active=True
        )

    def test_analytics_query_performance_with_joins(self):
        """Test that analytics queries use efficient joins and avoid N+1 queries."""
        # Create 10 reports with ratings and token logs
        for i in range(10):
            report = Report.objects.create(
                case=self.case,
                user=self.user,
                structured_content=[{'content': f'Test {i}'}],
                ai_feedback_content={'feedback': f'Feedback {i}'}
            )

            TokenUsageLog.objects.create(
                report=report,
                case=self.case,
                prompt_version=self.prompt_version,
                input_tokens=1000,
                output_tokens=200,
                total_tokens=1200,
                input_cost=Decimal('0.025'),
                output_cost=Decimal('0.01'),
                total_cost=Decimal('0.035'),
                response_time_ms=1500,
                model_name='gemini-2.5-flash',
                was_cached=False
            )

            AIFeedbackDetailedRating.objects.create(
                report=report,
                user=self.user,
                accuracy_rating=4,
                helpfulness_rating=4,
                actionability_rating=4,
                overall_rating=4
            )

        # Test that quality_by_prompt_version doesn't cause N+1 queries
        from cases.analytics_utils import get_quality_by_prompt_version
        from django.test.utils import override_settings
        from django.db import connection, reset_queries

        # Enable query debugging
        with override_settings(DEBUG=True):
            reset_queries()

            result = get_quality_by_prompt_version()

            # Should be O(number of prompt versions), not O(number of ratings)
            # Expected: ~3-5 queries max (PromptVersion.all, TokenUsageLog filter, AIFeedbackDetailedRating aggregates)
            query_count = len(connection.queries)
            self.assertLess(query_count, 10,
                f"Expected fewer than 10 queries, got {query_count}. "
                f"May indicate N+1 query problem.")

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['rating_count'], 10)
        self.assertEqual(result[0]['avg_overall'], 4.0)

    def test_cost_trends_query_efficiency(self):
        """Test that cost trends analytics uses efficient aggregation."""
        # Create 20 token logs
        for i in range(20):
            report = Report.objects.create(
                case=self.case,
                user=self.user,
                structured_content=[{'content': f'Test {i}'}],
                ai_feedback_content={'feedback': f'Feedback {i}'}
            )

            TokenUsageLog.objects.create(
                report=report,
                case=self.case,
                prompt_version=self.prompt_version,
                input_tokens=1000,
                output_tokens=200,
                total_tokens=1200,
                input_cost=Decimal('0.025'),
                output_cost=Decimal('0.01'),
                total_cost=Decimal('0.035'),
                response_time_ms=1500,
                model_name='gemini-2.5-flash',
                was_cached=i % 5 == 0  # Every 5th is cached
            )

        from cases.analytics_utils import get_cost_trends
        from django.test.utils import override_settings
        from django.db import connection, reset_queries

        with override_settings(DEBUG=True):
            reset_queries()

            result = get_cost_trends(days=7)

            # Should use efficient aggregations, not iterate through all logs
            # Expected: ~3 queries (overall aggregate, daily breakdown, cached cost aggregate)
            query_count = len(connection.queries)
            self.assertLess(query_count, 5,
                f"Expected fewer than 5 queries for cost trends, got {query_count}")

        self.assertEqual(result['total_requests'], 20)
        self.assertEqual(result['cached_requests'], 4)  # 0, 5, 10, 15

    def test_cache_performance_query_count(self):
        """Test that cache performance analytics is efficient."""
        # Create 15 token logs and 5 cache entries
        for i in range(15):
            report = Report.objects.create(
                case=self.case,
                user=self.user,
                structured_content=[{'content': f'Test {i}'}],
                ai_feedback_content={'feedback': f'Feedback {i}'}
            )

            TokenUsageLog.objects.create(
                report=report,
                case=self.case,
                prompt_version=self.prompt_version,
                input_tokens=1000,
                output_tokens=200,
                total_tokens=1200,
                input_cost=Decimal('0.025'),
                output_cost=Decimal('0.01'),
                total_cost=Decimal('0.035'),
                response_time_ms=1500,
                model_name='gemini-2.5-flash',
                was_cached=i < 5
            )

        # Create cache entries
        for i in range(5):
            FeedbackCache.objects.create(
                content_hash=f'{i:064d}',
                feedback_content={'feedback': f'Cached {i}'},
                case=self.case,
                expires_at=timezone.now() + timedelta(days=30)
            )

        from cases.analytics_utils import get_cache_performance
        from django.test.utils import override_settings
        from django.db import connection, reset_queries

        with override_settings(DEBUG=True):
            reset_queries()

            result = get_cache_performance(days=7)

            # Should use efficient queries without N+1
            # Expected: ~4-5 queries (FeedbackCache count/all, TokenUsageLog counts/aggregates)
            query_count = len(connection.queries)
            self.assertLess(query_count, 8,
                f"Expected fewer than 8 queries for cache performance, got {query_count}")

        self.assertEqual(result['total_cached_entries'], 5)
        self.assertEqual(result['requests_using_cache'], 5)
