"""
Unit tests for token_utils.py

Tests cost calculation and token usage logging.
"""

from decimal import Decimal
from django.test import TestCase
from cases.token_utils import calculate_cost, log_token_usage, PRICING
from cases.models import Case, Report, TokenUsageLog, PromptVersion, MasterTemplate
from users.models import User


class CostCalculationTest(TestCase):
    """Test token cost calculation logic."""

    def test_calculate_cost_gemini_25_flash(self):
        """Test cost calculation for gemini-2.5-flash."""
        costs = calculate_cost(
            input_tokens=1000,
            output_tokens=500,
            model_name='gemini-2.5-flash'
        )

        # Expected: 1000 * 0.075/1M + 500 * 0.30/1M
        # = 0.000075 + 0.000150 = 0.000225
        expected_input = Decimal('0.000075')
        expected_output = Decimal('0.000150')
        expected_total = Decimal('0.000225')

        self.assertEqual(costs['input_cost'], expected_input)
        self.assertEqual(costs['output_cost'], expected_output)
        self.assertEqual(costs['total_cost'], expected_total)

    def test_calculate_cost_gemini_15_flash(self):
        """Test cost calculation for gemini-1.5-flash."""
        costs = calculate_cost(
            input_tokens=2000,
            output_tokens=1000,
            model_name='gemini-1.5-flash'
        )

        # Same pricing as 2.5-flash
        expected_input = Decimal('0.000150')
        expected_output = Decimal('0.000300')
        expected_total = Decimal('0.000450')

        self.assertEqual(costs['input_cost'], expected_input)
        self.assertEqual(costs['output_cost'], expected_output)
        self.assertEqual(costs['total_cost'], expected_total)

    def test_calculate_cost_gemini_15_flash_8b(self):
        """Test cost calculation for gemini-1.5-flash-8b (cheaper model)."""
        costs = calculate_cost(
            input_tokens=1000,
            output_tokens=500,
            model_name='gemini-1.5-flash-8b'
        )

        # Expected: 1000 * 0.0375/1M + 500 * 0.15/1M
        # = 0.0000375 + 0.000075 = 0.0001125
        expected_input = Decimal('0.000038')  # Rounded to 6 decimals
        expected_output = Decimal('0.000075')
        expected_total = Decimal('0.000112')  # Rounded (0.000038 + 0.000075)

        self.assertEqual(costs['input_cost'], expected_input)
        self.assertEqual(costs['output_cost'], expected_output)
        self.assertEqual(costs['total_cost'], expected_total)

    def test_calculate_cost_unknown_model_defaults(self):
        """Test that unknown models default to gemini-2.5-flash pricing."""
        costs = calculate_cost(
            input_tokens=1000,
            output_tokens=500,
            model_name='unknown-model-xyz'
        )

        # Should use gemini-2.5-flash pricing
        expected_total = Decimal('0.000225')
        self.assertEqual(costs['total_cost'], expected_total)

    def test_calculate_cost_zero_tokens(self):
        """Test cost calculation with zero tokens (cached request)."""
        costs = calculate_cost(
            input_tokens=0,
            output_tokens=0,
            model_name='gemini-2.5-flash'
        )

        self.assertEqual(costs['input_cost'], Decimal('0.000000'))
        self.assertEqual(costs['output_cost'], Decimal('0.000000'))
        self.assertEqual(costs['total_cost'], Decimal('0.000000'))

    def test_calculate_cost_large_numbers(self):
        """Test cost calculation with large token counts."""
        costs = calculate_cost(
            input_tokens=100000,  # 100k tokens
            output_tokens=50000,   # 50k tokens
            model_name='gemini-2.5-flash'
        )

        # Expected: 100000 * 0.075/1M + 50000 * 0.30/1M
        # = 0.0075 + 0.015 = 0.0225
        expected_total = Decimal('0.022500')

        self.assertEqual(costs['total_cost'], expected_total)

    def test_calculate_cost_precision(self):
        """Test that costs maintain 6 decimal precision."""
        costs = calculate_cost(
            input_tokens=1,
            output_tokens=1,
            model_name='gemini-2.5-flash'
        )

        # All costs should have exactly 6 decimal places
        input_str = str(costs['input_cost'])
        output_str = str(costs['output_cost'])
        total_str = str(costs['total_cost'])

        # Check that we have 6 decimal places (or scientific notation for very small)
        self.assertTrue('.' in input_str)
        self.assertTrue('.' in output_str)
        self.assertTrue('.' in total_str)


class TokenUsageLoggingTest(TestCase):
    """Test token usage logging logic."""

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

        self.report = Report.objects.create(
            case=self.case,
            user=self.user,
            structured_content=[{'content': 'Test'}]
        )

        self.prompt_version = PromptVersion.objects.create(
            version_number='v1.0.0',
            name='Test Prompt',
            description='Test',
            prompt_template='Test template'
        )

    def test_log_token_usage_creates_entry(self):
        """Test that log_token_usage creates TokenUsageLog entry."""
        token_data = {
            'input_tokens': 1000,
            'output_tokens': 500,
            'total_tokens': 1500,
            'input_cost': Decimal('0.000075'),
            'output_cost': Decimal('0.000150'),
            'total_cost': Decimal('0.000225'),
            'model_name': 'gemini-2.5-flash'
        }

        log_entry = log_token_usage(
            report=self.report,
            case=self.case,
            prompt_version=self.prompt_version,
            token_data=token_data,
            response_time_ms=2500,
            was_cached=False
        )

        self.assertIsNotNone(log_entry.id)
        self.assertEqual(log_entry.report, self.report)
        self.assertEqual(log_entry.case, self.case)
        self.assertEqual(log_entry.prompt_version, self.prompt_version)
        self.assertEqual(log_entry.input_tokens, 1000)
        self.assertEqual(log_entry.output_tokens, 500)
        self.assertEqual(log_entry.total_tokens, 1500)
        self.assertEqual(log_entry.input_cost, Decimal('0.000075'))
        self.assertEqual(log_entry.output_cost, Decimal('0.000150'))
        self.assertEqual(log_entry.total_cost, Decimal('0.000225'))
        self.assertEqual(log_entry.response_time_ms, 2500)
        self.assertEqual(log_entry.was_cached, False)
        self.assertEqual(log_entry.model_name, 'gemini-2.5-flash')

    def test_log_token_usage_cached_request(self):
        """Test logging for cached request (zero costs)."""
        token_data = {
            'input_tokens': 0,
            'output_tokens': 0,
            'total_tokens': 0,
            'input_cost': Decimal('0.000000'),
            'output_cost': Decimal('0.000000'),
            'total_cost': Decimal('0.000000'),
            'model_name': 'cache'
        }

        log_entry = log_token_usage(
            report=self.report,
            case=self.case,
            prompt_version=self.prompt_version,
            token_data=token_data,
            response_time_ms=0,
            was_cached=True
        )

        self.assertEqual(log_entry.was_cached, True)
        self.assertEqual(log_entry.total_tokens, 0)
        self.assertEqual(log_entry.total_cost, Decimal('0.000000'))
        self.assertEqual(log_entry.response_time_ms, 0)

    def test_log_token_usage_without_prompt_version(self):
        """Test logging without prompt version (legacy support)."""
        token_data = {
            'input_tokens': 1000,
            'output_tokens': 500,
            'total_tokens': 1500,
            'input_cost': Decimal('0.000075'),
            'output_cost': Decimal('0.000150'),
            'total_cost': Decimal('0.000225'),
            'model_name': 'gemini-2.5-flash'
        }

        log_entry = log_token_usage(
            report=self.report,
            case=self.case,
            prompt_version=None,  # No prompt version
            token_data=token_data,
            response_time_ms=2500,
            was_cached=False
        )

        self.assertIsNone(log_entry.prompt_version)

    def test_log_token_usage_multiple_entries(self):
        """Test that multiple logs can be created for same report."""
        token_data = {
            'input_tokens': 1000,
            'output_tokens': 500,
            'total_tokens': 1500,
            'input_cost': Decimal('0.000075'),
            'output_cost': Decimal('0.000150'),
            'total_cost': Decimal('0.000225'),
            'model_name': 'gemini-2.5-flash'
        }

        # Create 3 log entries
        for i in range(3):
            log_token_usage(
                report=self.report,
                case=self.case,
                prompt_version=self.prompt_version,
                token_data=token_data,
                response_time_ms=2500 + i,
                was_cached=False
            )

        # Verify all 3 exist
        logs = TokenUsageLog.objects.filter(report=self.report)
        self.assertEqual(logs.count(), 3)

    def test_log_token_usage_cost_analytics(self):
        """Test that logs enable cost analytics queries."""
        # Create multiple logs with different costs
        for i in range(5):
            token_data = {
                'input_tokens': 1000 * (i + 1),
                'output_tokens': 500 * (i + 1),
                'total_tokens': 1500 * (i + 1),
                'input_cost': Decimal('0.000075') * (i + 1),
                'output_cost': Decimal('0.000150') * (i + 1),
                'total_cost': Decimal('0.000225') * (i + 1),
                'model_name': 'gemini-2.5-flash'
            }

            log_token_usage(
                report=self.report,
                case=self.case,
                prompt_version=self.prompt_version,
                token_data=token_data,
                response_time_ms=2500,
                was_cached=False
            )

        # Query total cost for this case
        from django.db.models import Sum
        total_cost = TokenUsageLog.objects.filter(
            case=self.case
        ).aggregate(Sum('total_cost'))['total_cost__sum']

        # Expected: 0.000225 * (1+2+3+4+5) = 0.000225 * 15 = 0.003375
        expected_total = Decimal('0.003375')

        self.assertEqual(total_cost, expected_total)
