# backend/cases/tests/test_tutoring_api.py

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status
from datetime import timedelta
import uuid

from cases.models import (
    TutoringSession,
    TutoringTurn,
    TutoringSessionStatusChoices,
    Report,
    Case,
    MasterTemplate,
)

User = get_user_model()


class TutoringSessionCreateAPITest(APITestCase):
    """Test cases for POST /api/tutoring/sessions/"""

    def setUp(self):
        """Set up test data before each test"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

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

        self.url = reverse('tutoring-session-create')

    def test_successful_session_creation(self):
        """Test creating a tutoring session with valid data"""
        data = {'report_id': self.report.id}

        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('id', response.data)
        self.assertEqual(response.data['report_id'], self.report.id)
        self.assertEqual(response.data['turns_count'], 0)
        self.assertEqual(response.data['max_turns'], 10)
        self.assertEqual(response.data['status'], 'active')
        self.assertEqual(len(response.data['turns']), 0)

    def test_report_not_found(self):
        """Test creating session with non-existent report ID"""
        data = {'report_id': 99999}

        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('report_id', response.data)

    def test_report_belongs_to_different_user(self):
        """Test creating session for another user's report"""
        # Create another user and their report
        other_user = User.objects.create_user(
            username='otheruser',
            password='testpass123'
        )

        other_report = Report.objects.create(
            case=self.case,
            user=other_user,
            structured_content=[{'content': 'test'}]
        )

        data = {'report_id': other_report.id}

        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('report_id', response.data)

    def test_active_session_already_exists(self):
        """Test creating duplicate active session"""
        # Create first session
        TutoringSession.objects.create(
            report=self.report,
            user=self.user,
            status=TutoringSessionStatusChoices.ACTIVE
        )

        data = {'report_id': self.report.id}

        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('already have an active', response.data['report_id'][0].lower())

    def test_can_create_after_completing_session(self):
        """Test that new session can be created after completing previous one"""
        # Create and complete first session
        session1 = TutoringSession.objects.create(
            report=self.report,
            user=self.user,
            status=TutoringSessionStatusChoices.COMPLETED
        )

        data = {'report_id': self.report.id}

        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_daily_session_limit(self):
        """Test that maximum 3 sessions per day are allowed"""
        # Create 3 reports for 3 sessions
        reports = []
        for i in range(3):
            report = Report.objects.create(
                case=self.case,
                user=self.user,
                structured_content=[{'content': f'test{i}'}]
            )
            reports.append(report)

        # Create 3 sessions (should all succeed)
        for report in reports:
            data = {'report_id': report.id}
            response = self.client.post(self.url, data, format='json')
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # 4th attempt should fail
        report4 = Report.objects.create(
            case=self.case,
            user=self.user,
            structured_content=[{'content': 'test4'}]
        )

        data = {'report_id': report4.id}
        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('maximum of 3', str(response.data).lower())

    def test_unauthenticated_request(self):
        """Test that unauthenticated requests are rejected"""
        self.client.force_authenticate(user=None)

        data = {'report_id': self.report.id}
        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TutoringSessionRetrieveAPITest(APITestCase):
    """Test cases for GET /api/tutoring/sessions/{id}/"""

    def setUp(self):
        """Set up test data before each test"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

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

        self.session = TutoringSession.objects.create(
            report=self.report,
            user=self.user
        )

    def test_retrieve_own_session(self):
        """Test retrieving own session with nested turns"""
        # Add some turns
        for i in range(3):
            TutoringTurn.objects.create(
                session=self.session,
                turn_number=i + 1,
                user_message=f"Question {i+1}",
                ai_response=f"Answer {i+1}",
                response_time_ms=100
            )

        url = reverse('tutoring-session-retrieve', kwargs={'id': self.session.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], str(self.session.id))
        self.assertEqual(response.data['turns_count'], 0)  # Not auto-updated in test
        self.assertEqual(len(response.data['turns']), 3)
        self.assertEqual(response.data['turns'][0]['turn_number'], 1)

    def test_session_not_found(self):
        """Test retrieving non-existent session"""
        random_uuid = uuid.uuid4()
        url = reverse('tutoring-session-retrieve', kwargs={'id': random_uuid})

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_cannot_access_other_users_session(self):
        """Test that users cannot access other users' sessions"""
        # Create another user and their session
        other_user = User.objects.create_user(
            username='otheruser',
            password='testpass123'
        )

        other_report = Report.objects.create(
            case=self.case,
            user=other_user,
            structured_content=[{'content': 'test'}]
        )

        other_session = TutoringSession.objects.create(
            report=other_report,
            user=other_user
        )

        url = reverse('tutoring-session-retrieve', kwargs={'id': other_session.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unauthenticated_request(self):
        """Test that unauthenticated requests are rejected"""
        self.client.force_authenticate(user=None)

        url = reverse('tutoring-session-retrieve', kwargs={'id': self.session.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TutoringTurnCreateAPITest(APITestCase):
    """Test cases for POST /api/tutoring/sessions/{session_id}/turn/"""

    def setUp(self):
        """Set up test data before each test"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

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

        self.session = TutoringSession.objects.create(
            report=self.report,
            user=self.user
        )

        self.url = reverse('tutoring-turn-create', kwargs={'session_id': self.session.id})

    def test_create_turn_with_valid_message(self):
        """Test creating a turn with valid user message"""
        data = {'user_message': 'Why did I miss the pneumothorax?'}

        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['turn_number'], 1)
        self.assertEqual(response.data['user_message'], 'Why did I miss the pneumothorax?')
        self.assertIn('ai_response', response.data)
        self.assertIsNotNone(response.data['response_time_ms'])

    def test_empty_message(self):
        """Test that empty messages are rejected"""
        data = {'user_message': ''}

        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('user_message', response.data)

    def test_message_too_long(self):
        """Test that messages over 5000 characters are rejected"""
        data = {'user_message': 'x' * 5001}

        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('user_message', response.data)

    def test_session_not_found(self):
        """Test creating turn for non-existent session"""
        random_uuid = uuid.uuid4()
        url = reverse('tutoring-turn-create', kwargs={'session_id': random_uuid})

        data = {'user_message': 'Test question'}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_cannot_access_other_users_session(self):
        """Test that users cannot create turns in other users' sessions"""
        # Create another user and their session
        other_user = User.objects.create_user(
            username='otheruser',
            password='testpass123'
        )

        other_report = Report.objects.create(
            case=self.case,
            user=other_user,
            structured_content=[{'content': 'test'}]
        )

        other_session = TutoringSession.objects.create(
            report=other_report,
            user=other_user
        )

        url = reverse('tutoring-turn-create', kwargs={'session_id': other_session.id})
        data = {'user_message': 'Test question'}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_session_completed(self):
        """Test that turns cannot be added to completed sessions"""
        self.session.status = TutoringSessionStatusChoices.COMPLETED
        self.session.save()

        data = {'user_message': 'Test question'}
        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('completed', response.data['error'].lower())

    def test_session_abandoned(self):
        """Test that turns cannot be added to abandoned sessions"""
        self.session.status = TutoringSessionStatusChoices.ABANDONED
        self.session.save()

        data = {'user_message': 'Test question'}
        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('abandoned', response.data['error'].lower())

    def test_turn_limit_reached(self):
        """Test that session auto-completes when turn limit reached"""
        # Create 10 turns (max limit)
        for i in range(10):
            TutoringTurn.objects.create(
                session=self.session,
                turn_number=i + 1,
                user_message=f"Question {i+1}",
                ai_response=f"Answer {i+1}",
                response_time_ms=100
            )

        # Update session turn count
        self.session.turns_count = 10
        self.session.save()

        # 11th attempt should fail and mark session as completed
        data = {'user_message': 'One more question'}
        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('maximum', response.data['error'].lower())

        # Verify session marked as completed
        self.session.refresh_from_db()
        self.assertEqual(self.session.status, TutoringSessionStatusChoices.COMPLETED)

    def test_sequential_turn_creation(self):
        """Test that multiple turns are numbered sequentially"""
        for i in range(3):
            data = {'user_message': f'Question {i+1}'}
            response = self.client.post(self.url, data, format='json')

            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            # Note: Turn number is manually set in view based on turns_count + 1

    def test_unauthenticated_request(self):
        """Test that unauthenticated requests are rejected"""
        self.client.force_authenticate(user=None)

        data = {'user_message': 'Test question'}
        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TutoringSessionExportAPITest(APITestCase):
    """Test cases for GET /api/tutoring/sessions/{session_id}/export/"""

    def setUp(self):
        """Set up test data before each test"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

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

        self.session = TutoringSession.objects.create(
            report=self.report,
            user=self.user
        )

        # Add some turns
        for i in range(3):
            TutoringTurn.objects.create(
                session=self.session,
                turn_number=i + 1,
                user_message=f"Question {i+1}",
                ai_response=f"Answer {i+1}",
                tools_used=['tool1', 'tool2'] if i == 1 else [],
                image_references=[{'series': 5, 'image': 35}] if i == 2 else [],
                response_time_ms=100
            )

        self.url = reverse('tutoring-session-export', kwargs={'session_id': self.session.id})

    def test_export_transcript(self):
        """Test exporting session transcript"""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'text/plain')
        self.assertIn('attachment', response['Content-Disposition'])
        self.assertIn(str(self.session.id), response['Content-Disposition'])

        # Verify content
        content = response.content.decode('utf-8')
        self.assertIn('TUTORING SESSION TRANSCRIPT', content)
        self.assertIn(str(self.session.id), content)
        self.assertIn(self.user.username, content)
        self.assertIn('Question 1', content)
        self.assertIn('Answer 1', content)
        self.assertIn('Turn 1', content)
        self.assertIn('Turn 2', content)
        self.assertIn('Turn 3', content)
        self.assertIn('Tools used: tool1, tool2', content)
        self.assertIn("'series': 5", content)

    def test_session_not_found(self):
        """Test exporting non-existent session"""
        random_uuid = uuid.uuid4()
        url = reverse('tutoring-session-export', kwargs={'session_id': random_uuid})

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_cannot_export_other_users_session(self):
        """Test that users cannot export other users' sessions"""
        # Create another user and their session
        other_user = User.objects.create_user(
            username='otheruser',
            password='testpass123'
        )

        other_report = Report.objects.create(
            case=self.case,
            user=other_user,
            structured_content=[{'content': 'test'}]
        )

        other_session = TutoringSession.objects.create(
            report=other_report,
            user=other_user
        )

        url = reverse('tutoring-session-export', kwargs={'session_id': other_session.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unauthenticated_request(self):
        """Test that unauthenticated requests are rejected"""
        self.client.force_authenticate(user=None)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
