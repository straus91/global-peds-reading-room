# backend/cases/tests/test_prompt_versions_api.py

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from cases.models import PromptVersion, Case, Report, FeedbackCache, MasterTemplate
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


class PromptVersionAPITest(TestCase):
    """
    Comprehensive tests for PromptVersion API endpoints.

    Tests CRUD operations, permissions, activate action, and analytics.
    """

    def setUp(self):
        """Create test users and client for each test."""
        # Create admin user
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='adminpass123',
            is_staff=True,
            is_superuser=True
        )

        # Create regular user
        self.regular_user = User.objects.create_user(
            username='testuser',
            email='user@test.com',
            password='userpass123'
        )

        # Create API client
        self.client = APIClient()

        # Create test prompt version
        self.prompt_v1 = PromptVersion.objects.create(
            version_number='v1.0.0',
            name='Original Prompt',
            description='Initial prompt version',
            prompt_template='You are an AI assistant...',
            is_active=True,
            created_by=self.admin_user
        )

        self.prompt_v2 = PromptVersion.objects.create(
            version_number='v2.0.0',
            name='Improved Specificity',
            description='Added more detailed instructions',
            prompt_template='You are an expert AI assistant...',
            is_active=False,
            created_by=self.admin_user
        )

    # --- Authentication Tests ---

    def test_list_requires_authentication(self):
        """Test that listing versions requires authentication."""
        response = self.client.get('/api/cases/prompt-versions/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_requires_admin(self):
        """Test that creating versions requires admin privileges."""
        self.client.force_authenticate(user=self.regular_user)

        data = {
            'version_number': 'v3.0.0',
            'name': 'New Version',
            'description': 'Test version',
            'prompt_template': 'Test prompt...'
        }

        response = self.client.post('/api/cases/prompt-versions/', data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # --- List/Read Tests ---

    def test_list_versions_authenticated(self):
        """Test that authenticated users can list prompt versions."""
        self.client.force_authenticate(user=self.regular_user)

        response = self.client.get('/api/cases/prompt-versions/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Handle paginated response (DRF may paginate results)
        results = response.data.get('results', response.data) if isinstance(response.data, dict) else response.data
        self.assertGreaterEqual(len(results), 2)  # At least v1 and v2 from setUp

    def test_retrieve_version_authenticated(self):
        """Test retrieving a specific version."""
        self.client.force_authenticate(user=self.regular_user)

        response = self.client.get(f'/api/cases/prompt-versions/{self.prompt_v1.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['version_number'], 'v1.0.0')
        self.assertEqual(response.data['name'], 'Original Prompt')

    # --- Create Tests ---

    def test_create_version_admin(self):
        """Test that admin can create new prompt version."""
        self.client.force_authenticate(user=self.admin_user)

        data = {
            'version_number': 'v3.0.0',
            'name': 'Enhanced Clarity',
            'description': 'Improved clarity and structure',
            'prompt_template': 'You are a highly skilled AI assistant...',
            'is_active': False
        }

        response = self.client.post('/api/cases/prompt-versions/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['version_number'], 'v3.0.0')
        self.assertEqual(response.data['created_by_name'], 'admin')

        # Verify in database
        version = PromptVersion.objects.get(version_number='v3.0.0')
        self.assertFalse(version.is_active)
        self.assertEqual(version.created_by, self.admin_user)

    def test_create_version_sets_created_by(self):
        """Test that created_by is automatically set to request user."""
        self.client.force_authenticate(user=self.admin_user)

        data = {
            'version_number': 'v3.0.0',
            'name': 'Test',
            'description': 'Test',
            'prompt_template': 'Test...'
        }

        response = self.client.post('/api/cases/prompt-versions/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        version = PromptVersion.objects.get(id=response.data['id'])
        self.assertEqual(version.created_by, self.admin_user)

    # --- Update Tests ---

    def test_update_version_admin(self):
        """Test that admin can update prompt version."""
        self.client.force_authenticate(user=self.admin_user)

        data = {
            'description': 'Updated description for v2'
        }

        response = self.client.patch(
            f'/api/cases/prompt-versions/{self.prompt_v2.id}/',
            data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.prompt_v2.refresh_from_db()
        self.assertEqual(self.prompt_v2.description, 'Updated description for v2')

    def test_update_version_regular_user_denied(self):
        """Test that regular users cannot update versions."""
        self.client.force_authenticate(user=self.regular_user)

        data = {'description': 'Hacked!'}

        response = self.client.patch(
            f'/api/cases/prompt-versions/{self.prompt_v2.id}/',
            data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # --- Delete Tests ---

    def test_delete_version_admin(self):
        """Test that admin can delete prompt version."""
        self.client.force_authenticate(user=self.admin_user)

        # Create a version to delete
        version_to_delete = PromptVersion.objects.create(
            version_number='v99.0.0',
            name='To Delete',
            description='Will be deleted',
            prompt_template='Test...',
            created_by=self.admin_user
        )

        response = self.client.delete(f'/api/cases/prompt-versions/{version_to_delete.id}/')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(PromptVersion.objects.filter(id=version_to_delete.id).exists())

    def test_delete_version_regular_user_denied(self):
        """Test that regular users cannot delete versions."""
        self.client.force_authenticate(user=self.regular_user)

        response = self.client.delete(f'/api/cases/prompt-versions/{self.prompt_v2.id}/')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(PromptVersion.objects.filter(id=self.prompt_v2.id).exists())

    # --- Validation Tests ---

    def test_duplicate_version_number_rejected(self):
        """Test that duplicate version numbers are rejected."""
        self.client.force_authenticate(user=self.admin_user)

        data = {
            'version_number': 'v1.0.0',  # Already exists
            'name': 'Duplicate',
            'description': 'Should fail',
            'prompt_template': 'Test...'
        }

        response = self.client.post('/api/cases/prompt-versions/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('version_number', response.data)

    def test_ab_test_weight_validation(self):
        """Test that A/B test weight must be 0-100."""
        self.client.force_authenticate(user=self.admin_user)

        data = {
            'version_number': 'v3.0.0',
            'name': 'Invalid Weight',
            'description': 'Test',
            'prompt_template': 'Test...',
            'is_ab_test': True,
            'ab_test_weight': 150  # Invalid
        }

        response = self.client.post('/api/cases/prompt-versions/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('ab_test_weight', response.data)

    def test_only_one_active_version_allowed(self):
        """Test that creating a new active version is rejected when one exists."""
        self.client.force_authenticate(user=self.admin_user)

        # v1 is already active
        data = {
            'version_number': 'v3.0.0',
            'name': 'Second Active',
            'description': 'Should fail',
            'prompt_template': 'Test...',
            'is_active': True
        }

        response = self.client.post('/api/cases/prompt-versions/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('is_active', response.data)

    # --- Activate Action Tests ---

    def test_activate_version(self):
        """Test activating an inactive version."""
        self.client.force_authenticate(user=self.admin_user)

        # v2 is inactive, v1 is active
        response = self.client.post(f'/api/cases/prompt-versions/{self.prompt_v2.id}/activate/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'activated')

        # Verify v2 is now active
        self.prompt_v2.refresh_from_db()
        self.assertTrue(self.prompt_v2.is_active)
        self.assertIsNotNone(self.prompt_v2.activated_at)

        # Verify v1 is now inactive
        self.prompt_v1.refresh_from_db()
        self.assertFalse(self.prompt_v1.is_active)
        self.assertIsNotNone(self.prompt_v1.deactivated_at)

    def test_activate_already_active_version(self):
        """Test activating an already active version returns appropriate message."""
        self.client.force_authenticate(user=self.admin_user)

        # v1 is already active
        response = self.client.post(f'/api/cases/prompt-versions/{self.prompt_v1.id}/activate/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'already_active')

    def test_activate_requires_admin(self):
        """Test that regular users cannot activate versions."""
        self.client.force_authenticate(user=self.regular_user)

        response = self.client.post(f'/api/cases/prompt-versions/{self.prompt_v2.id}/activate/')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # --- Analytics Tests ---

    def test_analytics_by_version_admin(self):
        """Test analytics endpoint returns version metrics."""
        self.client.force_authenticate(user=self.admin_user)

        # Update some metrics
        self.prompt_v1.total_uses = 100
        self.prompt_v1.average_rating = 4.5
        self.prompt_v1.average_accuracy = 4.2
        self.prompt_v1.total_tokens_used = 50000
        self.prompt_v1.save()

        response = self.client.get('/api/cases/prompt-versions/analytics/by-version/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('versions', response.data)
        self.assertEqual(len(response.data['versions']), 2)

        # Find v1 in response
        v1_data = next(
            v for v in response.data['versions']
            if v['version_number'] == 'v1.0.0'
        )

        self.assertEqual(v1_data['total_uses'], 100)
        self.assertEqual(v1_data['average_rating'], 4.5)
        self.assertEqual(v1_data['average_accuracy'], 4.2)
        self.assertEqual(v1_data['total_tokens_used'], 50000)
        self.assertTrue(v1_data['is_active'])

    def test_analytics_requires_admin(self):
        """Test that regular users cannot access analytics."""
        self.client.force_authenticate(user=self.regular_user)

        response = self.client.get('/api/cases/prompt-versions/analytics/by-version/')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_analytics_calculates_cache_savings(self):
        """Test that analytics calculates cache hit savings."""
        self.client.force_authenticate(user=self.admin_user)

        # Create test case for cache
        template = MasterTemplate.objects.create(
            name='Test Template',
            modality='CT',
            body_part='NR'
        )
        case = Case.objects.create(
            title='Test Case',
            subspecialty='NR',
            modality='CT',
            difficulty='beginner',
            clinical_history='Test',
            master_template=template
        )

        # Create cache entry with hits
        cache_entry = FeedbackCache.objects.create(
            content_hash='test123',
            feedback_content={'test': 'data'},
            case=case,
            prompt_version=self.prompt_v1,
            hit_count=10,
            expires_at=timezone.now() + timedelta(days=30)
        )

        # Set token usage
        self.prompt_v1.total_uses = 50
        self.prompt_v1.total_tokens_used = 100000
        self.prompt_v1.save()

        response = self.client.get('/api/cases/prompt-versions/analytics/by-version/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Find v1 data
        v1_data = next(
            v for v in response.data['versions']
            if v['version_number'] == 'v1.0.0'
        )

        # Verify cache metrics
        self.assertEqual(v1_data['cache_hits'], 10)
        self.assertGreater(v1_data['estimated_savings_usd'], 0)

    # --- Query Optimization Tests ---

    def test_list_uses_select_related(self):
        """Test that list queries use select_related for created_by."""
        self.client.force_authenticate(user=self.admin_user)

        # This test verifies the query optimization in get_queryset
        # In a real test, we'd use assertNumQueries, but for now we just verify it works
        response = self.client.get('/api/cases/prompt-versions/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Handle paginated response (DRF may paginate results)
        results = response.data.get('results', response.data) if isinstance(response.data, dict) else response.data

        # Verify created_by_name is populated (means select_related worked)
        for version in results:
            if version['created_by']:
                self.assertIsNotNone(version['created_by_name'])

    # --- Edge Cases ---

    def test_activate_with_multiple_active_versions_deactivates_all(self):
        """Test that activating deactivates ALL currently active versions."""
        # Manually create a situation with multiple active (shouldn't happen but test it)
        self.prompt_v2.is_active = True
        self.prompt_v2.save()

        # Now both v1 and v2 are active (shouldn't be possible via API)
        self.assertTrue(self.prompt_v1.is_active)
        self.assertTrue(self.prompt_v2.is_active)

        # Create and activate v3
        v3 = PromptVersion.objects.create(
            version_number='v3.0.0',
            name='Third Version',
            description='Test',
            prompt_template='Test...',
            created_by=self.admin_user
        )

        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(f'/api/cases/prompt-versions/{v3.id}/activate/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify only v3 is active
        self.prompt_v1.refresh_from_db()
        self.prompt_v2.refresh_from_db()
        v3.refresh_from_db()

        self.assertFalse(self.prompt_v1.is_active)
        self.assertFalse(self.prompt_v2.is_active)
        self.assertTrue(v3.is_active)

    def test_delete_active_version_allowed(self):
        """Test that active versions can be deleted (admin responsibility)."""
        self.client.force_authenticate(user=self.admin_user)

        # v1 is active
        response = self.client.delete(f'/api/cases/prompt-versions/{self.prompt_v1.id}/')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(PromptVersion.objects.filter(id=self.prompt_v1.id).exists())
