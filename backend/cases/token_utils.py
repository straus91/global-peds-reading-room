"""
Token usage tracking and cost calculation utilities.

This module provides functions to:
1. Calculate costs based on token usage and model pricing
2. Log token usage for analytics and cost monitoring
"""

from decimal import Decimal
from cases.models import TokenUsageLog


# Gemini 2.5 Flash pricing (as of January 2025)
# Source: https://ai.google.dev/pricing
PRICING = {
    'gemini-2.5-flash': {
        'input': Decimal('0.075') / 1_000_000,   # $0.075 per 1M tokens
        'output': Decimal('0.30') / 1_000_000     # $0.30 per 1M tokens
    },
    'gemini-1.5-flash': {
        'input': Decimal('0.075') / 1_000_000,   # $0.075 per 1M tokens
        'output': Decimal('0.30') / 1_000_000     # $0.30 per 1M tokens
    },
    'gemini-1.5-flash-8b': {
        'input': Decimal('0.0375') / 1_000_000,  # $0.0375 per 1M tokens
        'output': Decimal('0.15') / 1_000_000     # $0.15 per 1M tokens
    }
}


def calculate_cost(input_tokens, output_tokens, model_name='gemini-2.5-flash'):
    """
    Calculate costs based on token usage.

    Args:
        input_tokens (int): Number of tokens in prompt (input to LLM)
        output_tokens (int): Number of tokens in response (output from LLM)
        model_name (str): Model identifier (default: 'gemini-2.5-flash')

    Returns:
        dict: Cost breakdown with keys:
            - input_cost (Decimal): Cost for input tokens
            - output_cost (Decimal): Cost for output tokens
            - total_cost (Decimal): Combined cost
            All values in USD with 6 decimal precision

    Example:
        >>> costs = calculate_cost(1000, 500, 'gemini-2.5-flash')
        >>> print(f"Total: ${costs['total_cost']}")
        Total: $0.000225
        >>> print(f"Input: ${costs['input_cost']}, Output: ${costs['output_cost']}")
        Input: $0.000075, Output: $0.000150

    Note:
        - Costs are calculated with 6 decimal precision for accuracy
        - Unknown models default to gemini-2.5-flash pricing
        - Costs are in USD
    """
    # Get pricing for model (default to gemini-2.5-flash if unknown)
    rates = PRICING.get(model_name, PRICING['gemini-2.5-flash'])

    # Calculate costs (convert ints to Decimal for precision)
    input_cost = Decimal(str(input_tokens)) * rates['input']
    output_cost = Decimal(str(output_tokens)) * rates['output']

    # Return with 6 decimal precision (matches TokenUsageLog model)
    return {
        'input_cost': input_cost.quantize(Decimal('0.000001')),
        'output_cost': output_cost.quantize(Decimal('0.000001')),
        'total_cost': (input_cost + output_cost).quantize(Decimal('0.000001'))
    }


def log_token_usage(report, case, prompt_version, token_data, response_time_ms, was_cached=False):
    """
    Create TokenUsageLog entry for analytics and cost tracking.

    Args:
        report (Report): Report instance for which feedback was generated
        case (Case): Case instance (for cost-per-case analytics)
        prompt_version (PromptVersion): PromptVersion used (can be None for legacy)
        token_data (dict): Token usage and cost data with keys:
            - input_tokens (int)
            - output_tokens (int)
            - total_tokens (int)
            - input_cost (Decimal)
            - output_cost (Decimal)
            - total_cost (Decimal)
            - model_name (str)
        response_time_ms (int): Response time in milliseconds
        was_cached (bool): Whether this was served from cache (default: False)

    Returns:
        TokenUsageLog: Created log entry

    Example:
        >>> from cases.models import Report, Case, PromptVersion
        >>> from decimal import Decimal
        >>> report = Report.objects.get(id=...)
        >>> case = report.case
        >>> prompt_version = PromptVersion.objects.filter(is_active=True).first()
        >>> token_data = {
        ...     'input_tokens': 1000,
        ...     'output_tokens': 500,
        ...     'total_tokens': 1500,
        ...     'input_cost': Decimal('0.000075'),
        ...     'output_cost': Decimal('0.000150'),
        ...     'total_cost': Decimal('0.000225'),
        ...     'model_name': 'gemini-2.5-flash'
        ... }
        >>> log = log_token_usage(report, case, prompt_version, token_data, 2500, was_cached=False)
        >>> log.total_cost
        Decimal('0.000225')

    Note:
        - For cached requests, token counts and costs should be 0
        - response_time_ms should also be 0 for cached requests
        - Used for cost analytics and monitoring API usage trends
    """
    return TokenUsageLog.objects.create(
        report=report,
        case=case,
        prompt_version=prompt_version,
        input_tokens=token_data['input_tokens'],
        output_tokens=token_data['output_tokens'],
        total_tokens=token_data['total_tokens'],
        input_cost=token_data['input_cost'],
        output_cost=token_data['output_cost'],
        total_cost=token_data['total_cost'],
        response_time_ms=response_time_ms,
        was_cached=was_cached,
        model_name=token_data['model_name']
    )
