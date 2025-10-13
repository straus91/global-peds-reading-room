# backend/cases/tests/test_tutoring_models.py

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.utils import timezone
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


class TutoringSessionModelTest(TestCase):
    """Test cases for TutoringSession model"""

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
        session = TutoringSession.objects.create(
            report=self.report,
            user=self.user
        )

        self.assertIsNotNone(session.id)
        self.assertIsInstance(session.id, uuid.UUID)

    def test_default_values(self):
        """Test that default values are set correctly"""
        session = TutoringSession.objects.create(
            report=self.report,
            user=self.user
        )

        self.assertEqual(session.status, TutoringSessionStatusChoices.ACTIVE)
        self.assertEqual(session.turns_count, 0)
        self.assertEqual(session.max_turns, 10)
        self.assertIsNotNone(session.created_at)
        self.assertIsNotNone(session.last_turn_at)

    def test_unique_active_session_constraint(self):
        """Test that only one active session allowed per report/user"""
        # Create first active session
        session1 = TutoringSession.objects.create(
            report=self.report,
            user=self.user,
            status=TutoringSessionStatusChoices.ACTIVE
        )

        # Attempt to create duplicate active session should fail
        # Use atomic block with savepoint to handle transaction properly
        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                TutoringSession.objects.create(
                    report=self.report,
                    user=self.user,
                    status=TutoringSessionStatusChoices.ACTIVE
                )

        # But can create after marking first as completed
        session1.status = TutoringSessionStatusChoices.COMPLETED
        session1.save()

        # Now this should succeed
        session2 = TutoringSession.objects.create(
            report=self.report,
            user=self.user,
            status=TutoringSessionStatusChoices.ACTIVE
        )

        self.assertIsNotNone(session2)

    def test_multiple_non_active_sessions_allowed(self):
        """Test that multiple completed/abandoned sessions are allowed"""
        # Create multiple completed sessions
        session1 = TutoringSession.objects.create(
            report=self.report,
            user=self.user,
            status=TutoringSessionStatusChoices.COMPLETED
        )

        session2 = TutoringSession.objects.create(
            report=self.report,
            user=self.user,
            status=TutoringSessionStatusChoices.ABANDONED
        )

        # Both should exist
        sessions = TutoringSession.objects.filter(report=self.report, user=self.user)
        self.assertEqual(sessions.count(), 2)

    def test_cascade_delete_when_report_deleted(self):
        """Test that sessions are deleted when report is deleted"""
        session = TutoringSession.objects.create(
            report=self.report,
            user=self.user
        )

        session_id = session.id

        # Delete report
        self.report.delete()

        # Verify session was also deleted
        self.assertFalse(TutoringSession.objects.filter(id=session_id).exists())

    def test_cascade_delete_when_user_deleted(self):
        """Test that sessions are deleted when user is deleted"""
        session = TutoringSession.objects.create(
            report=self.report,
            user=self.user
        )

        session_id = session.id

        # Delete user
        self.user.delete()

        # Verify session was also deleted
        self.assertFalse(TutoringSession.objects.filter(id=session_id).exists())

    def test_string_representation(self):
        """Test string representation of session"""
        session = TutoringSession.objects.create(
            report=self.report,
            user=self.user
        )

        str_repr = str(session)

        self.assertIn(str(session.id), str_repr)
        self.assertIn(self.user.username, str_repr)
        self.assertIn(str(self.report.id), str_repr)

    def test_ordering(self):
        """Test that sessions are ordered by created_at descending"""
        # Create multiple sessions at different times
        session1 = TutoringSession.objects.create(
            report=self.report,
            user=self.user,
            status=TutoringSessionStatusChoices.COMPLETED
        )

        # Slight delay to ensure different timestamps
        session2 = TutoringSession.objects.create(
            report=self.report,
            user=self.user,
            status=TutoringSessionStatusChoices.COMPLETED
        )

        # Query all sessions
        sessions = TutoringSession.objects.filter(user=self.user)

        # Most recent should be first
        self.assertEqual(sessions[0].id, session2.id)
        self.assertEqual(sessions[1].id, session1.id)


class TutoringTurnModelTest(TestCase):
    """Test cases for TutoringTurn model"""

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

        self.session = TutoringSession.objects.create(
            report=self.report,
            user=self.user
        )

    def test_turn_creation(self):
        """Test basic turn creation"""
        turn = TutoringTurn.objects.create(
            session=self.session,
            turn_number=1,
            user_message="Why did I miss this finding?",
            ai_response="Let me explain...",
            response_time_ms=150
        )

        self.assertIsNotNone(turn.id)
        self.assertEqual(turn.turn_number, 1)
        self.assertEqual(turn.user_message, "Why did I miss this finding?")

    def test_unique_turn_number_constraint(self):
        """Test that (session, turn_number) must be unique"""
        # Create first turn
        TutoringTurn.objects.create(
            session=self.session,
            turn_number=1,
            user_message="Question 1",
            ai_response="Answer 1",
            response_time_ms=100
        )

        # Attempt duplicate turn number should fail
        with self.assertRaises(IntegrityError):
            TutoringTurn.objects.create(
                session=self.session,
                turn_number=1,  # Same turn number
                user_message="Question 2",
                ai_response="Answer 2",
                response_time_ms=100
            )

    def test_json_field_defaults(self):
        """Test that JSONField default values work correctly"""
        turn = TutoringTurn.objects.create(
            session=self.session,
            turn_number=1,
            user_message="Test",
            ai_response="Response",
            response_time_ms=100
        )

        # Should have empty lists by default
        self.assertEqual(turn.tools_used, [])
        self.assertEqual(turn.image_references, [])

    def test_json_field_with_data(self):
        """Test storing data in JSON fields"""
        turn = TutoringTurn.objects.create(
            session=self.session,
            turn_number=1,
            user_message="Why did I miss the pneumothorax in series 5 image 35?",
            ai_response="Let me analyze that image...",
            tools_used=['fetch_image', 'vlm_analysis', 'expert_comparison'],
            image_references=[{'series': 5, 'image': 35}],
            response_time_ms=3500
        )

        # Retrieve and verify
        turn.refresh_from_db()
        self.assertEqual(len(turn.tools_used), 3)
        self.assertIn('vlm_analysis', turn.tools_used)
        self.assertEqual(turn.image_references[0]['series'], 5)

    def test_cascade_delete_when_session_deleted(self):
        """Test that turns are deleted when session is deleted"""
        turn = TutoringTurn.objects.create(
            session=self.session,
            turn_number=1,
            user_message="Test",
            ai_response="Response",
            response_time_ms=100
        )

        turn_id = turn.id

        # Delete session
        self.session.delete()

        # Verify turn was also deleted
        self.assertFalse(TutoringTurn.objects.filter(id=turn_id).exists())

    def test_turn_ordering(self):
        """Test that turns are ordered by turn_number"""
        # Create turns out of order
        turn3 = TutoringTurn.objects.create(
            session=self.session,
            turn_number=3,
            user_message="Question 3",
            ai_response="Answer 3",
            response_time_ms=100
        )

        turn1 = TutoringTurn.objects.create(
            session=self.session,
            turn_number=1,
            user_message="Question 1",
            ai_response="Answer 1",
            response_time_ms=100
        )

        turn2 = TutoringTurn.objects.create(
            session=self.session,
            turn_number=2,
            user_message="Question 2",
            ai_response="Answer 2",
            response_time_ms=100
        )

        # Query all turns
        turns = self.session.turns.all()

        # Should be ordered by turn_number
        self.assertEqual(turns[0].turn_number, 1)
        self.assertEqual(turns[1].turn_number, 2)
        self.assertEqual(turns[2].turn_number, 3)

    def test_string_representation(self):
        """Test string representation of turn"""
        turn = TutoringTurn.objects.create(
            session=self.session,
            turn_number=5,
            user_message="Test",
            ai_response="Response",
            response_time_ms=100
        )

        str_repr = str(turn)

        self.assertIn('5', str_repr)
        self.assertIn(str(self.session.id), str_repr)

    def test_multiple_sessions_independent_turns(self):
        """Test that turn numbers are independent per session"""
        # Create second session
        report2 = Report.objects.create(
            case=self.case,
            user=self.user,
            structured_content=[{'content': 'test'}]
        )

        session2 = TutoringSession.objects.create(
            report=report2,
            user=self.user
        )

        # Create turn 1 in both sessions
        turn1_session1 = TutoringTurn.objects.create(
            session=self.session,
            turn_number=1,
            user_message="Question for session 1",
            ai_response="Answer",
            response_time_ms=100
        )

        turn1_session2 = TutoringTurn.objects.create(
            session=session2,
            turn_number=1,  # Same turn number, different session
            user_message="Question for session 2",
            ai_response="Answer",
            response_time_ms=100
        )

        # Both should exist
        self.assertTrue(TutoringTurn.objects.filter(id=turn1_session1.id).exists())
        self.assertTrue(TutoringTurn.objects.filter(id=turn1_session2.id).exists())
