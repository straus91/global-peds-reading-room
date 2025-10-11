# 🧪 Testing Strategy & Best Practices

## 🎯 Overview

Comprehensive testing is critical for maintaining code quality, preventing regressions, and ensuring data integrity. This guide provides testing strategies with emphasis on data-driven testing, scalability validation, and risk mitigation.

---

## 📋 Testing Philosophy

### Core Principles

1. **🔒 Test Data Integrity**: All database operations must maintain data consistency
2. **📊 Data-Driven Validation**: Test analytics queries and metrics calculations
3. **🤖 AI System Testing**: Validate AI feedback generation and quality
4. **⚡ Performance Testing**: Ensure queries scale with data volume
5. **🔄 Risk Mitigation**: Test before deploying (see @.claude/docs/RISK_ASSESSMENT.md)

### Coverage Expectations

| Component | Target Coverage | Priority |
|-----------|----------------|----------|
| Models | 90%+ | 🔴 Critical |
| Views/APIs | 85%+ | 🔴 Critical |
| Serializers | 80%+ | 🟡 High |
| Utils/Services | 90%+ | 🔴 Critical |
| Forms | 75%+ | 🟡 High |

---

## 🚀 Running Tests

### Basic Test Commands

```bash
# Navigate to backend directory
cd backend

# Run all tests
python manage.py test

# Run tests for specific app
python manage.py test cases
python manage.py test users

# Run specific test class
python manage.py test cases.tests.CaseModelTest

# Run specific test method
python manage.py test cases.tests.CaseModelTest.test_case_identifier_generation

# Run with verbosity for detailed output
python manage.py test --verbosity=2

# Run tests in parallel (faster on multi-core systems)
python manage.py test --parallel

# Keep test database for inspection
python manage.py test --keepdb
```

### Running Tests with Coverage

```bash
# Install coverage tool
pip install coverage

# Run tests with coverage
coverage run --source='.' manage.py test

# Generate coverage report
coverage report

# Generate HTML coverage report (opens in browser)
coverage html
# Open htmlcov/index.html in browser

# Show missing lines
coverage report --show-missing

# Focus on specific app
coverage run --source='cases' manage.py test cases
coverage report
```

---

## 📝 Test Organization

### File Structure

```
backend/
├── cases/
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_models.py          # Model tests
│   │   ├── test_views.py           # API endpoint tests
│   │   ├── test_serializers.py     # Serializer tests
│   │   ├── test_utils.py           # Utility function tests
│   │   └── test_llm_service.py     # AI feedback service tests
│   └── tests.py                    # Legacy (migrate to tests/ dir)
├── users/
│   └── tests/
│       ├── __init__.py
│       ├── test_models.py
│       └── test_views.py
└── api/
    └── tests/
        ├── __init__.py
        └── test_authentication.py
```

**💡 Best Practice**: Use `tests/` directory structure for better organization as your test suite grows.

---

## 🗄️ Model Testing

### 1️⃣ Testing Case Identifier Auto-Generation

**Location**: `backend/cases/models.py:213-273`

**What to Test**:
- Identifier is auto-generated when not provided
- Format follows `{SUBSPECIALTY}-{MODALITY}-{YEAR}-{SEQUENCE}` pattern
- Sequential numbering works correctly
- Collision handling (concurrent case creation)

**Example Tests**:

```python
from django.test import TestCase
from cases.models import Case, MasterTemplate
from users.models import User

class CaseModelTest(TestCase):
    def setUp(self):
        """Set up test data before each test"""
        self.user = User.objects.create_user(
            username='testadmin',
            email='admin@test.com',
            password='testpass123'
        )
        self.template = MasterTemplate.objects.create(
            name='Test Template',
            modality='CT',
            body_part='NR'
        )

    def test_case_identifier_auto_generation(self):
        """Test that case_identifier is auto-generated correctly"""
        case = Case.objects.create(
            title='Test Case',
            subspecialty='NR',
            modality='CT',
            difficulty='beginner',
            clinical_history='Test history',
            master_template=self.template,
            created_by=self.user
        )

        # Verify identifier was generated
        self.assertIsNotNone(case.case_identifier)

        # Verify format
        self.assertRegex(
            case.case_identifier,
            r'^[A-Z]{2,3}-[A-Z]{2,3}-\d{4}-\d{4}$'
        )

        # Verify starts with correct subspecialty and modality
        self.assertTrue(case.case_identifier.startswith('NR-CT-'))

    def test_case_identifier_sequential_numbering(self):
        """Test that sequential cases get incrementing identifiers"""
        case1 = Case.objects.create(
            title='Test Case 1',
            subspecialty='NR',
            modality='CT',
            difficulty='beginner',
            clinical_history='Test',
            master_template=self.template
        )

        case2 = Case.objects.create(
            title='Test Case 2',
            subspecialty='NR',
            modality='CT',
            difficulty='beginner',
            clinical_history='Test',
            master_template=self.template
        )

        # Extract sequence numbers
        seq1 = int(case1.case_identifier.split('-')[-1])
        seq2 = int(case2.case_identifier.split('-')[-1])

        # Verify case2 has higher sequence
        self.assertEqual(seq2, seq1 + 1)

    def test_case_identifier_manual_override(self):
        """Test that manually provided identifier is preserved"""
        custom_id = 'CUSTOM-ID-2025-9999'
        case = Case.objects.create(
            title='Test Case',
            case_identifier=custom_id,
            subspecialty='NR',
            modality='CT',
            difficulty='beginner',
            clinical_history='Test',
            master_template=self.template
        )

        self.assertEqual(case.case_identifier, custom_id)

    def test_case_identifier_uniqueness(self):
        """Test that duplicate identifiers raise error"""
        identifier = 'NR-CT-2025-0001'

        Case.objects.create(
            title='Test Case 1',
            case_identifier=identifier,
            subspecialty='NR',
            modality='CT',
            difficulty='beginner',
            clinical_history='Test',
            master_template=self.template
        )

        # Attempting to create duplicate should raise IntegrityError
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            Case.objects.create(
                title='Test Case 2',
                case_identifier=identifier,
                subspecialty='NR',
                modality='CT',
                difficulty='beginner',
                clinical_history='Test',
                master_template=self.template
            )
```

### 2️⃣ Testing Report Versioning

**What to Test**:
- Multiple reports per user/case allowed
- `is_archived` flag works correctly
- Querying non-archived reports

**Example Test**:

```python
def test_report_versioning(self):
    """Test that users can have multiple versions of reports"""
    case = Case.objects.create(
        title='Test Case',
        subspecialty='NR',
        modality='CT',
        difficulty='beginner',
        clinical_history='Test',
        master_template=self.template
    )

    user = User.objects.create_user(username='testuser', password='test123')

    # Create first report
    report1 = Report.objects.create(
        case=case,
        user=user,
        structured_content=[{'section_name': 'Findings', 'content': 'First attempt'}]
    )

    # Archive first report
    report1.is_archived = True
    report1.save()

    # Create second report
    report2 = Report.objects.create(
        case=case,
        user=user,
        structured_content=[{'section_name': 'Findings', 'content': 'Second attempt'}]
    )

    # Verify both reports exist
    all_reports = Report.objects.filter(case=case, user=user)
    self.assertEqual(all_reports.count(), 2)

    # Verify only one is not archived
    current_report = Report.objects.filter(
        case=case,
        user=user,
        is_archived=False
    ).first()

    self.assertEqual(current_report.id, report2.id)
```

### 3️⃣ Testing Cascading Deletes

**What to Test**:
- Deleting Case cascades to Reports
- Deleting User cascades to Reports
- MasterTemplate uses SET_NULL for Cases

```python
def test_case_deletion_cascades_to_reports(self):
    """Test that deleting a case deletes associated reports"""
    case = Case.objects.create(
        title='Test Case',
        subspecialty='NR',
        modality='CT',
        difficulty='beginner',
        clinical_history='Test',
        master_template=self.template
    )

    user = User.objects.create_user(username='testuser', password='test123')

    report = Report.objects.create(
        case=case,
        user=user,
        structured_content=[{'content': 'test'}]
    )

    report_id = report.id

    # Delete case
    case.delete()

    # Verify report was also deleted
    self.assertFalse(Report.objects.filter(id=report_id).exists())
```

---

## 🔌 API Testing

### 1️⃣ Authentication Testing

```python
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse

class AuthenticationTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_login_with_valid_credentials(self):
        """Test JWT token generation with valid credentials"""
        url = reverse('token_obtain_pair')
        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_api_requires_authentication(self):
        """Test that API endpoints require authentication"""
        url = reverse('case-list')  # Adjust to your URL name

        response = self.client.get(url)

        # Should return 401 Unauthorized
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_api_with_valid_token(self):
        """Test API access with valid JWT token"""
        # Get token
        token_url = reverse('token_obtain_pair')
        token_response = self.client.post(
            token_url,
            {'username': 'testuser', 'password': 'testpass123'},
            format='json'
        )
        access_token = token_response.data['access']

        # Use token to access API
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        url = reverse('case-list')
        response = self.client.get(url)

        # Should succeed (200 or 204)
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_204_NO_CONTENT])
```

### 2️⃣ Testing AI Feedback API

```python
from unittest.mock import patch, MagicMock

class AIFeedbackAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='test123'
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
            key_findings='test finding',
            diagnosis='test diagnosis',
            master_template=self.template
        )

        self.report = Report.objects.create(
            case=self.case,
            user=self.user,
            structured_content=[{'section_name': 'Findings', 'content': 'Test findings'}]
        )

    @patch('cases.llm_feedback_service.get_feedback_from_llm')
    def test_ai_feedback_generation(self, mock_llm):
        """Test AI feedback endpoint with mocked LLM"""
        # Mock LLM response
        mock_llm.return_value = """
        You correctly identified the diagnosis.

        1. CRITICAL DISCREPANCIES:
        None identified.

        2. NON-CRITICAL DISCREPANCIES:
        None identified.

        SECTION SEVERITY ASSESSMENT:
        Section: Findings
        Severity: Consistent
        Reason: Your findings align well with the expert assessment.
        """

        url = reverse('ai-feedback', kwargs={'report_id': self.report.id})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('raw_feedback', response.data)
        self.assertIn('section_feedback', response.data)

        # Verify LLM was called
        self.assertTrue(mock_llm.called)

    def test_ai_feedback_rate_limiting(self):
        """Test that rate limiting is enforced"""
        # This test would need actual rate limiting implementation
        # Example structure:
        url = reverse('ai-feedback', kwargs={'report_id': self.report.id})

        # Make multiple rapid requests
        responses = []
        for i in range(15):  # Exceed rate limit
            response = self.client.post(url)
            responses.append(response)

        # At least one should be rate limited
        rate_limited = any(
            r.status_code == status.HTTP_429_TOO_MANY_REQUESTS
            for r in responses
        )

        # Note: This test requires rate limiting to be implemented
        # self.assertTrue(rate_limited)
```

---

## 📊 Data-Driven Testing

### 1️⃣ Testing Report Comparison Logic

**Location**: `backend/cases/utils.py` (generate_report_comparison_summary)

```python
from cases.utils import generate_report_comparison_summary

class ReportComparisonTest(TestCase):
    def test_missing_key_concepts_detection(self):
        """Test that missing key concepts are identified"""
        user_sections = [
            {
                'master_template_section_id': 1,
                'section_name': 'Findings',
                'content': 'Lungs are clear'
            }
        ]

        expert_sections = [
            {
                'master_section_id': 1,
                'content': 'Lungs are clear. No pneumothorax. No effusion.',
                'key_concepts_text': 'clear lungs;no pneumothorax;no effusion',
                'section_name': 'Findings'
            }
        ]

        case_diagnosis = 'Normal chest'

        result = generate_report_comparison_summary(
            user_sections,
            expert_sections,
            case_diagnosis
        )

        # Verify missing concepts identified
        section_comparison = result['section_comparisons'][0]
        self.assertIn('no pneumothorax', section_comparison.get('missing_key_concepts', []))
        self.assertIn('no effusion', section_comparison.get('missing_key_concepts', []))
```

### 2️⃣ Testing Analytics Queries

```python
from django.db.models import Count, Avg

class AnalyticsTest(TestCase):
    def setUp(self):
        """Create test data for analytics"""
        self.template = MasterTemplate.objects.create(
            name='Test Template',
            modality='CT',
            body_part='NR'
        )

        # Create 10 cases with varying view counts
        for i in range(10):
            case = Case.objects.create(
                title=f'Case {i}',
                subspecialty='NR',
                modality='CT',
                difficulty='beginner',
                clinical_history='Test',
                master_template=self.template,
                status='published'
            )

            # Add views
            for j in range(i):
                user = User.objects.create_user(
                    username=f'user{i}_{j}',
                    password='test123'
                )
                case.viewed_by.add(user)

    def test_case_popularity_query(self):
        """Test query for most popular cases"""
        popular_cases = Case.objects.annotate(
            view_count=Count('viewed_by')
        ).order_by('-view_count')[:5]

        # Verify results ordered correctly
        view_counts = [case.view_count for case in popular_cases]
        self.assertEqual(view_counts, sorted(view_counts, reverse=True))

        # Verify top case has most views
        self.assertEqual(popular_cases[0].view_count, 9)

    def test_ai_feedback_quality_metrics(self):
        """Test average rating calculation"""
        user = User.objects.create_user(username='testuser', password='test123')

        case = Case.objects.create(
            title='Test Case',
            subspecialty='NR',
            modality='CT',
            difficulty='beginner',
            clinical_history='Test',
            master_template=self.template
        )

        # Create reports with ratings
        for i in range(5):
            report = Report.objects.create(
                case=case,
                user=user,
                structured_content=[{'content': 'test'}]
            )

            AIFeedbackRating.objects.create(
                report=report,
                user=user,
                star_rating=i + 1  # Ratings 1-5
            )

        # Calculate average
        avg_rating = AIFeedbackRating.objects.aggregate(
            Avg('star_rating')
        )['star_rating__avg']

        # Verify calculation
        self.assertEqual(avg_rating, 3.0)  # (1+2+3+4+5)/5 = 3
```

---

## ⚡ Performance Testing

### 1️⃣ Testing Query Performance

```python
from django.test.utils import override_settings
from django.db import connection
from django.test import TestCase

class QueryPerformanceTest(TestCase):
    def setUp(self):
        """Create realistic data volume"""
        self.template = MasterTemplate.objects.create(
            name='Test Template',
            modality='CT',
            body_part='NR'
        )

        # Create 100 cases
        cases = []
        for i in range(100):
            cases.append(Case(
                title=f'Case {i}',
                subspecialty='NR',
                modality='CT',
                difficulty='beginner',
                clinical_history='Test',
                master_template=self.template
            ))
        Case.objects.bulk_create(cases)

    def test_case_list_query_count(self):
        """Test that case list doesn't have N+1 queries"""
        # Reset query count
        with self.assertNumQueries(2):  # Adjust expected count
            cases = Case.objects.filter(status='published') \
                .select_related('master_template', 'created_by')

            # Force evaluation
            list(cases)

    def test_case_detail_with_reports_query_count(self):
        """Test optimized query for case with reports"""
        case = Case.objects.first()
        user = User.objects.create_user(username='test', password='test123')

        # Create 10 reports
        for i in range(10):
            Report.objects.create(
                case=case,
                user=user,
                structured_content=[{'content': f'Report {i}'}]
            )

        # Test optimized query
        with self.assertNumQueries(3):  # Should be low number
            case_with_reports = Case.objects.filter(id=case.id) \
                .select_related('master_template') \
                .prefetch_related('reports')

            case_obj = case_with_reports.first()
            reports = list(case_obj.reports.all())  # Should not trigger new query
```

---

## 🤖 Testing AI Feedback Service

### 1️⃣ Testing LLM Service with Mocks

```python
from unittest.mock import patch, MagicMock
from cases.llm_feedback_service import get_feedback_from_llm

class LLMFeedbackServiceTest(TestCase):
    @patch('cases.llm_feedback_service.genai.GenerativeModel')
    def test_feedback_generation_with_mock(self, mock_model_class):
        """Test LLM feedback generation with mocked API"""
        # Create mock response
        mock_response = MagicMock()
        mock_response.text = """
        You correctly identified the diagnosis.

        1. CRITICAL DISCREPANCIES:
        None identified.

        2. NON-CRITICAL DISCREPANCIES:
        - You did not mention patient positioning.

        SECTION SEVERITY ASSESSMENT:
        Section: Findings
        Severity: Consistent
        Reason: Your findings align well with expert.
        """

        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_response
        mock_model_class.return_value = mock_model

        # Call service
        user_sections = [{'section_name': 'Findings', 'content': 'Test findings'}]
        expert_sections = [{'master_section_id': 1, 'content': 'Expert findings', 'section_name': 'Findings'}]
        pre_analysis = {'overall_diagnosis_comparison': {'status': 'Aligned'}, 'section_comparisons': []}

        result = get_feedback_from_llm(
            user_sections,
            expert_sections,
            pre_analysis,
            case_identifier_for_llm='TEST-CT-2025-0001'
        )

        # Verify result
        self.assertIsInstance(result, str)
        self.assertIn('correctly identified', result.lower())
```

---

## 🔄 Testing Workflows & Integration

### 1️⃣ Testing Complete User Report Flow

```python
class ReportSubmissionFlowTest(APITestCase):
    def test_complete_report_submission_flow(self):
        """Integration test for entire report submission process"""
        # 1. Create user
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=user)

        # 2. Create case with expert template
        template = MasterTemplate.objects.create(
            name='Test Template',
            modality='CT',
            body_part='NR'
        )

        section = MasterTemplateSection.objects.create(
            master_template=template,
            name='Findings',
            order=1,
            is_required=True
        )

        case = Case.objects.create(
            title='Test Case',
            subspecialty='NR',
            modality='CT',
            difficulty='beginner',
            clinical_history='Test history',
            key_findings='test findings',
            diagnosis='test diagnosis',
            master_template=template,
            status='published'
        )

        language = Language.objects.create(code='en', name='English')

        expert_template = CaseTemplate.objects.create(
            case=case,
            language=language
        )

        CaseTemplateSectionContent.objects.create(
            case_template=expert_template,
            master_section=section,
            content='Expert findings text',
            key_concepts_text='finding1;finding2'
        )

        # 3. Submit report
        report_url = reverse('report-list')  # Adjust to your URL
        report_data = {
            'case': case.id,
            'structured_content': [
                {
                    'master_template_section_id': section.id,
                    'section_name': 'Findings',
                    'content': 'User findings text'
                }
            ]
        }

        response = self.client.post(report_url, report_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        report_id = response.data['id']

        # 4. Request AI feedback (with mocked LLM)
        with patch('cases.llm_feedback_service.get_feedback_from_llm') as mock_llm:
            mock_llm.return_value = "Test feedback"

            feedback_url = reverse('ai-feedback', kwargs={'report_id': report_id})
            feedback_response = self.client.post(feedback_url)

            self.assertEqual(feedback_response.status_code, status.HTTP_200_OK)
            self.assertIn('raw_feedback', feedback_response.data)

        # 5. Rate AI feedback
        rating_url = reverse('feedback-rating-list')  # Adjust to your URL
        rating_data = {
            'report': report_id,
            'star_rating': 5,
            'comment': 'Very helpful!'
        }

        rating_response = self.client.post(rating_url, rating_data, format='json')
        self.assertEqual(rating_response.status_code, status.HTTP_201_CREATED)

        # 6. Verify data integrity
        report = Report.objects.get(id=report_id)
        self.assertIsNotNone(report.ai_feedback_content)
        self.assertEqual(report.ai_feedback_ratings.count(), 1)
```

---

## 📚 Best Practices Summary

### ✅ DO:
1. **Use setUp() for common test data** - Reduces duplication
2. **Test one thing per test method** - Clearer failures
3. **Use descriptive test names** - `test_what_should_happen_when_condition`
4. **Mock external services** - Tests should be fast and reliable
5. **Test edge cases** - Null values, empty strings, max lengths
6. **Test data integrity** - Especially cascading deletes
7. **Test permissions** - Ensure users can't access unauthorized data
8. **Use transactions** - Test database is reset after each test
9. **Test analytics queries** - Validate metrics calculations
10. **Benchmark performance** - Use `assertNumQueries` for optimization

### ❌ DON'T:
1. **Don't test Django internals** - Trust the framework
2. **Don't depend on test order** - Each test should be independent
3. **Don't use production database** - Tests use separate test DB
4. **Don't make real API calls** - Mock external services
5. **Don't ignore failing tests** - Fix or update them
6. **Don't test UI in backend tests** - Use separate frontend tests

---

## 🚀 Continuous Integration

### GitHub Actions Example

Create `.github/workflows/django-tests.yml`:

```yaml
name: Django Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:13
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

    steps:
    - uses: actions/checkout@v2

    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.8'

    - name: Install dependencies
      run: |
        cd backend
        pip install -r requirements.txt
        pip install coverage

    - name: Run tests with coverage
      env:
        SECRET_KEY: test-secret-key
        DEBUG: 'False'
        DB_NAME: test_db
        DB_USER: postgres
        DB_PASSWORD: postgres
        DB_HOST: localhost
        DB_PORT: 5432
        GEMINI_API_KEY: test-key-not-used
      run: |
        cd backend
        coverage run --source='.' manage.py test
        coverage report
```

---

## 📚 Related Documentation

- @.claude/docs/RISK_ASSESSMENT.md - Assess risks before changes
- @.claude/docs/DATA_MODELS.md - Understand what to test
- @.claude/docs/WORKFLOWS.md - Safe testing workflows
- @.claude/docs/MONITORING.md - Production monitoring

---

**💡 Remember**: Write tests before fixing bugs (reproduce the bug in a test first) and before adding new features (test-driven development). Tests are documentation that never goes out of date!
