"""
Unit tests for AIFeedbackDetailedRating model, serializers, and API endpoints.

Tests multi-dimensional rating system with false positive tracking.
Target: 15+ tests for comprehensive coverage.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from cases.models import (
    AIFeedbackDetailedRating,
    Report,
    Case,
    MasterTemplate,
    Language,
)

User = get_user_model()


class AIFeedbackDetailedRatingModelTest(TestCase):
    """Test AIFeedbackDetailedRating model constraints and relationships."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
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
            key_findings='test findings',
            diagnosis='test diagnosis'
        )

        self.report = Report.objects.create(
            case=self.case,
            user=self.user,
            structured_content=[{'section_name': 'Findings', 'content': 'Test findings'}],
            ai_feedback_content={'raw_feedback': 'Test feedback'}
        )

    def test_create_detailed_rating_all_fields(self):
        """Test creating detailed rating with all fields."""
        rating = AIFeedbackDetailedRating.objects.create(
            report=self.report,
            user=self.user,
            accuracy_rating=4,
            helpfulness_rating=5,
            actionability_rating=3,
            overall_rating=4,
            has_false_positives=True,
            false_positive_details='Found incorrect discrepancy',
            comment='Overall good feedback'
        )

        self.assertEqual(rating.accuracy_rating, 4)
        self.assertEqual(rating.helpfulness_rating, 5)
        self.assertEqual(rating.actionability_rating, 3)
        self.assertEqual(rating.overall_rating, 4)
        self.assertTrue(rating.has_false_positives)
        self.assertEqual(rating.false_positive_details, 'Found incorrect discrepancy')
        self.assertEqual(rating.comment, 'Overall good feedback')

    def test_create_detailed_rating_minimal_fields(self):
        """Test creating rating with only required fields."""
        rating = AIFeedbackDetailedRating.objects.create(
            report=self.report,
            user=self.user,
            accuracy_rating=3,
            helpfulness_rating=3,
            actionability_rating=3,
            overall_rating=3
        )

        self.assertFalse(rating.has_false_positives)
        # false_positive_details is nullable, defaults to None
        self.assertIn(rating.false_positive_details, [None, ''])
        # comment is also nullable, defaults to None
        self.assertIn(rating.comment, [None, ''])

    def test_unique_constraint_report_user(self):
        """Test that user can only rate each report once."""
        AIFeedbackDetailedRating.objects.create(
            report=self.report,
            user=self.user,
            accuracy_rating=4,
            helpfulness_rating=4,
            actionability_rating=4,
            overall_rating=4
        )

        # Attempting to create duplicate should raise error
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            AIFeedbackDetailedRating.objects.create(
                report=self.report,
                user=self.user,
                accuracy_rating=5,
                helpfulness_rating=5,
                actionability_rating=5,
                overall_rating=5
            )

    def test_different_users_can_rate_same_report(self):
        """Test that different users can rate the same report."""
        user2 = User.objects.create_user(
            username='testuser2',
            password='testpass123'
        )

        rating1 = AIFeedbackDetailedRating.objects.create(
            report=self.report,
            user=self.user,
            accuracy_rating=4,
            helpfulness_rating=4,
            actionability_rating=4,
            overall_rating=4
        )

        rating2 = AIFeedbackDetailedRating.objects.create(
            report=self.report,
            user=user2,
            accuracy_rating=3,
            helpfulness_rating=3,
            actionability_rating=3,
            overall_rating=3
        )

        self.assertNotEqual(rating1.id, rating2.id)
        self.assertEqual(AIFeedbackDetailedRating.objects.filter(report=self.report).count(), 2)

    def test_cascade_delete_on_report(self):
        """Test that rating is deleted when report is deleted."""
        rating = AIFeedbackDetailedRating.objects.create(
            report=self.report,
            user=self.user,
            accuracy_rating=4,
            helpfulness_rating=4,
            actionability_rating=4,
            overall_rating=4
        )

        rating_id = rating.id
        self.report.delete()

        # Rating should be deleted
        self.assertFalse(AIFeedbackDetailedRating.objects.filter(id=rating_id).exists())

    def test_cascade_delete_on_user(self):
        """Test that rating is deleted when user is deleted."""
        rating = AIFeedbackDetailedRating.objects.create(
            report=self.report,
            user=self.user,
            accuracy_rating=4,
            helpfulness_rating=4,
            actionability_rating=4,
            overall_rating=4
        )

        rating_id = rating.id
        user_id = self.user.id
        self.user.delete()

        # Rating should be deleted
        self.assertFalse(AIFeedbackDetailedRating.objects.filter(id=rating_id).exists())


class AIFeedbackDetailedRatingSerializerTest(APITestCase):
    """Test AIFeedbackDetailedRatingSerializer validation."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
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
            clinical_history='Test history',
            master_template=self.template,
            key_findings='test findings',
            diagnosis='test diagnosis'
        )

        self.report = Report.objects.create(
            case=self.case,
            user=self.user,
            structured_content=[{'section_name': 'Findings', 'content': 'Test findings'}],
            ai_feedback_content={'raw_feedback': 'Test feedback'}
        )

    def test_serializer_valid_data(self):
        """Test serializer with valid data."""
        from cases.serializers import AIFeedbackDetailedRatingSerializer
        from rest_framework.test import APIRequestFactory

        factory = APIRequestFactory()
        request = factory.post('/api/cases/detailed-ratings/')
        request.user = self.user

        data = {
            'report_id': self.report.id,
            'accuracy_rating': 4,
            'helpfulness_rating': 5,
            'actionability_rating': 4,
            'overall_rating': 4,
            'comment': 'Good feedback'
        }

        serializer = AIFeedbackDetailedRatingSerializer(
            data=data,
            context={'request': request}
        )

        # Validate data structure
        self.assertTrue(serializer.is_valid())

    def test_serializer_validates_false_positive_details(self):
        """Test that false positive details are required when has_false_positives=True."""
        from cases.serializers import AIFeedbackDetailedRatingSerializer
        from rest_framework.test import APIRequestFactory

        factory = APIRequestFactory()
        request = factory.post('/api/cases/detailed-ratings/')
        request.user = self.user

        data = {
            'report_id': self.report.id,
            'accuracy_rating': 4,
            'helpfulness_rating': 4,
            'actionability_rating': 4,
            'overall_rating': 4,
            'has_false_positives': True,
            # Missing false_positive_details
        }

        serializer = AIFeedbackDetailedRatingSerializer(
            data=data,
            context={'request': request}
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn('false_positive_details', str(serializer.errors))


class AIFeedbackDetailedRatingAPITest(APITestCase):
    """Test AIFeedbackDetailedRating API endpoints."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
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
            clinical_history='Test history',
            master_template=self.template,
            key_findings='test findings',
            diagnosis='test diagnosis'
        )

        self.report = Report.objects.create(
            case=self.case,
            user=self.user,
            structured_content=[{'section_name': 'Findings', 'content': 'Test findings'}],
            ai_feedback_content={'raw_feedback': 'Test feedback'}
        )

    def test_create_detailed_rating_success(self):
        """Test creating detailed rating via API."""
        url = '/api/cases/detailed-ratings/'
        data = {
            'report_id': self.report.id,
            'accuracy_rating': 4,
            'helpfulness_rating': 5,
            'actionability_rating': 4,
            'overall_rating': 4,
            'comment': 'Very helpful feedback'
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['accuracy_rating'], 4)
        self.assertEqual(response.data['helpfulness_rating'], 5)
        self.assertEqual(AIFeedbackDetailedRating.objects.count(), 1)

    def test_create_rating_with_false_positives(self):
        """Test creating rating with false positive flag."""
        url = '/api/cases/detailed-ratings/'
        data = {
            'report_id': self.report.id,
            'accuracy_rating': 2,
            'helpfulness_rating': 3,
            'actionability_rating': 3,
            'overall_rating': 3,
            'has_false_positives': True,
            'false_positive_details': 'AI incorrectly flagged section as missing'
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['has_false_positives'])
        self.assertEqual(
            response.data['false_positive_details'],
            'AI incorrectly flagged section as missing'
        )

    def test_create_rating_prevents_duplicate(self):
        """Test that user cannot rate same report twice."""
        url = '/api/cases/detailed-ratings/'
        data = {
            'report_id': self.report.id,
            'accuracy_rating': 4,
            'helpfulness_rating': 4,
            'actionability_rating': 4,
            'overall_rating': 4
        }

        # First rating succeeds
        response1 = self.client.post(url, data, format='json')
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)

        # Second rating fails
        response2 = self.client.post(url, data, format='json')
        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_user_own_ratings(self):
        """Test that user can list their own ratings."""
        # Create multiple ratings
        AIFeedbackDetailedRating.objects.create(
            report=self.report,
            user=self.user,
            accuracy_rating=4,
            helpfulness_rating=4,
            actionability_rating=4,
            overall_rating=4
        )

        # Create another report and rating
        report2 = Report.objects.create(
            case=self.case,
            user=self.user,
            structured_content=[{'section_name': 'Findings', 'content': 'Test 2'}],
            ai_feedback_content={'raw_feedback': 'Test 2'}
        )
        AIFeedbackDetailedRating.objects.create(
            report=report2,
            user=self.user,
            accuracy_rating=5,
            helpfulness_rating=5,
            actionability_rating=5,
            overall_rating=5
        )

        url = '/api/cases/detailed-ratings/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Response might be paginated or include metadata
        results = response.data.get('results', response.data)
        self.assertEqual(len(results), 2)

    def test_cannot_rate_another_users_report(self):
        """Test that user cannot rate another user's report."""
        other_user = User.objects.create_user(
            username='otheruser',
            password='testpass123'
        )

        other_report = Report.objects.create(
            case=self.case,
            user=other_user,
            structured_content=[{'section_name': 'Findings', 'content': 'Other'}],
            ai_feedback_content={'raw_feedback': 'Test'}
        )

        url = '/api/cases/detailed-ratings/'
        data = {
            'report_id': other_report.id,
            'accuracy_rating': 4,
            'helpfulness_rating': 4,
            'actionability_rating': 4,
            'overall_rating': 4
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_rate_report_without_ai_feedback(self):
        """Test that user cannot rate report without AI feedback."""
        report_no_feedback = Report.objects.create(
            case=self.case,
            user=self.user,
            structured_content=[{'section_name': 'Findings', 'content': 'Test'}],
            ai_feedback_content={}  # Empty feedback
        )

        url = '/api/cases/detailed-ratings/'
        data = {
            'report_id': report_no_feedback.id,
            'accuracy_rating': 4,
            'helpfulness_rating': 4,
            'actionability_rating': 4,
            'overall_rating': 4
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_analytics_endpoint_requires_admin(self):
        """Test that analytics endpoint requires admin privileges."""
        url = '/api/cases/detailed-ratings/analytics/'
        response = self.client.get(url)

        # Non-admin should be forbidden
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_analytics_endpoint_works_for_admin(self):
        """Test analytics endpoint for admin user."""
        # Create admin user
        admin = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='adminpass'
        )
        self.client.force_authenticate(user=admin)

        # Create some ratings
        AIFeedbackDetailedRating.objects.create(
            report=self.report,
            user=self.user,
            accuracy_rating=4,
            helpfulness_rating=5,
            actionability_rating=4,
            overall_rating=4
        )

        url = '/api/cases/detailed-ratings/analytics/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_ratings', response.data)
        self.assertIn('average_accuracy', response.data)
        self.assertEqual(response.data['total_ratings'], 1)
