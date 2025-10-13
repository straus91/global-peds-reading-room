"""
Analytics utility functions for AI feedback quality and cost monitoring.

Provides helper functions for:
- Cost trend analysis (token usage over time)
- Quality metrics by prompt version
- Cache performance metrics
- False positive pattern analysis

Used by ViewSet analytics endpoints for admin dashboard.
"""

from django.db.models import Avg, Count, Sum, Q, F
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from .models import (
    TokenUsageLog,
    AIFeedbackDetailedRating,
    FeedbackCache,
    PromptVersion,
    Report
)


def get_cost_trends(days=30):
    """
    Calculate token usage and cost trends over specified period.

    Args:
        days (int): Number of days to analyze (default 30)

    Returns:
        dict: {
            'total_requests': int,
            'total_prompt_tokens': int,
            'total_completion_tokens': int,
            'total_cost_usd': Decimal,
            'cached_requests': int,
            'cache_savings_usd': Decimal,
            'daily_breakdown': [
                {
                    'date': 'YYYY-MM-DD',
                    'requests': int,
                    'prompt_tokens': int,
                    'completion_tokens': int,
                    'cost_usd': Decimal,
                    'cached_count': int
                },
                ...
            ]
        }
    """
    cutoff_date = timezone.now() - timedelta(days=days)

    logs = TokenUsageLog.objects.filter(created_at__gte=cutoff_date)

    # Overall aggregates
    overall = logs.aggregate(
        total_requests=Count('id'),
        total_prompt_tokens=Sum('input_tokens'),
        total_completion_tokens=Sum('output_tokens'),
        total_cost_usd=Sum('total_cost'),
        cached_requests=Count('id', filter=Q(was_cached=True))
    )

    # Cache savings calculation
    # Assume cached requests save 100% of cost
    cached_cost_saved = logs.filter(was_cached=True).aggregate(
        Sum('total_cost')
    )['total_cost__sum'] or Decimal('0.00')

    # Daily breakdown
    from django.db.models.functions import TruncDate
    daily_data = logs.annotate(
        date=TruncDate('created_at')
    ).values('date').annotate(
        requests=Count('id'),
        prompt_tokens=Sum('input_tokens'),
        completion_tokens=Sum('output_tokens'),
        cost_usd=Sum('total_cost'),
        cached_count=Count('id', filter=Q(was_cached=True))
    ).order_by('date')

    return {
        'total_requests': overall['total_requests'] or 0,
        'total_prompt_tokens': overall['total_prompt_tokens'] or 0,
        'total_completion_tokens': overall['total_completion_tokens'] or 0,
        'total_cost_usd': overall['total_cost_usd'] or Decimal('0.00'),
        'cached_requests': overall['cached_requests'] or 0,
        'cache_savings_usd': cached_cost_saved,
        'daily_breakdown': [
            {
                'date': item['date'].strftime('%Y-%m-%d'),
                'requests': item['requests'],
                'prompt_tokens': item['prompt_tokens'] or 0,
                'completion_tokens': item['completion_tokens'] or 0,
                'cost_usd': item['cost_usd'] or Decimal('0.00'),
                'cached_count': item['cached_count']
            }
            for item in daily_data
        ]
    }


def get_quality_by_prompt_version():
    """
    Compare AI feedback quality ratings across prompt versions.

    Returns:
        list: [
            {
                'prompt_version_id': int,
                'version_name': str,
                'is_active': bool,
                'rating_count': int,
                'avg_accuracy': float,
                'avg_helpfulness': float,
                'avg_actionability': float,
                'avg_overall': float,
                'false_positive_count': int,
                'false_positive_rate': float
            },
            ...
        ]
    """
    # Get all prompt versions with associated token logs
    versions = PromptVersion.objects.all()

    results = []
    for version in versions:
        # Get token logs for this version
        token_logs = TokenUsageLog.objects.filter(prompt_version=version)

        # Get report IDs from token logs
        report_ids = token_logs.values_list('report_id', flat=True)

        # Get ratings for those reports
        ratings = AIFeedbackDetailedRating.objects.filter(
            report_id__in=report_ids
        )

        if ratings.exists():
            aggregates = ratings.aggregate(
                rating_count=Count('id'),
                avg_accuracy=Avg('accuracy_rating'),
                avg_helpfulness=Avg('helpfulness_rating'),
                avg_actionability=Avg('actionability_rating'),
                avg_overall=Avg('overall_rating'),
                false_positive_count=Count('id', filter=Q(has_false_positives=True))
            )

            false_positive_rate = (
                (aggregates['false_positive_count'] / aggregates['rating_count'] * 100)
                if aggregates['rating_count'] > 0 else 0.0
            )

            results.append({
                'prompt_version_id': version.id,
                'version_name': version.version_number,
                'is_active': version.is_active,
                'rating_count': aggregates['rating_count'],
                'avg_accuracy': round(aggregates['avg_accuracy'], 2) if aggregates['avg_accuracy'] else None,
                'avg_helpfulness': round(aggregates['avg_helpfulness'], 2) if aggregates['avg_helpfulness'] else None,
                'avg_actionability': round(aggregates['avg_actionability'], 2) if aggregates['avg_actionability'] else None,
                'avg_overall': round(aggregates['avg_overall'], 2) if aggregates['avg_overall'] else None,
                'false_positive_count': aggregates['false_positive_count'],
                'false_positive_rate': round(false_positive_rate, 1)
            })
        else:
            # Version has no ratings yet
            results.append({
                'prompt_version_id': version.id,
                'version_name': version.version_number,
                'is_active': version.is_active,
                'rating_count': 0,
                'avg_accuracy': None,
                'avg_helpfulness': None,
                'avg_actionability': None,
                'avg_overall': None,
                'false_positive_count': 0,
                'false_positive_rate': 0.0
            })

    # Sort by rating count (most rated first), then by version name
    results.sort(key=lambda x: (-x['rating_count'], x['version_name']))

    return results


def get_cache_performance(days=30):
    """
    Calculate cache effectiveness metrics.

    Args:
        days (int): Number of days to analyze (default 30)

    Returns:
        dict: {
            'total_cached_entries': int,
            'cache_hit_rate': float (percentage),
            'avg_cache_age_minutes': float,
            'expired_entries': int,
            'cost_savings_usd': Decimal,
            'requests_using_cache': int,
            'requests_not_cached': int
        }
    """
    cutoff_date = timezone.now() - timedelta(days=days)

    # Total cache entries
    total_cached_entries = FeedbackCache.objects.count()

    # Token logs in period
    logs = TokenUsageLog.objects.filter(created_at__gte=cutoff_date)
    total_requests = logs.count()
    cached_requests = logs.filter(was_cached=True).count()

    # Cache hit rate
    cache_hit_rate = (
        (cached_requests / total_requests * 100)
        if total_requests > 0 else 0.0
    )

    # Average cache age
    cache_entries = FeedbackCache.objects.all()
    if cache_entries.exists():
        now = timezone.now()
        total_age_seconds = sum(
            (now - entry.created_at).total_seconds()
            for entry in cache_entries
        )
        avg_age_minutes = (total_age_seconds / cache_entries.count()) / 60
    else:
        avg_age_minutes = 0.0

    # Expired entries (older than 24 hours)
    expiry_cutoff = timezone.now() - timedelta(hours=24)
    expired_entries = FeedbackCache.objects.filter(
        created_at__lt=expiry_cutoff
    ).count()

    # Cost savings from cache
    cost_savings = logs.filter(was_cached=True).aggregate(
        Sum('total_cost')
    )['total_cost__sum'] or Decimal('0.00')

    return {
        'total_cached_entries': total_cached_entries,
        'cache_hit_rate': round(cache_hit_rate, 1),
        'avg_cache_age_minutes': round(avg_age_minutes, 1),
        'expired_entries': expired_entries,
        'cost_savings_usd': cost_savings,
        'requests_using_cache': cached_requests,
        'requests_not_cached': total_requests - cached_requests
    }


def get_false_positive_patterns(limit=50):
    """
    Extract common themes from false positive reports.

    Args:
        limit (int): Maximum number of recent FP reports to analyze (default 50)

    Returns:
        dict: {
            'total_false_positives': int,
            'false_positive_rate': float (percentage),
            'recent_examples': [
                {
                    'rating_id': int,
                    'report_case_identifier': str,
                    'details': str,
                    'overall_rating': int,
                    'rated_at': str (ISO format)
                },
                ...
            ]
        }
    """
    # Get all ratings with false positives
    fp_ratings = AIFeedbackDetailedRating.objects.filter(
        has_false_positives=True
    ).select_related('report', 'report__case').order_by('-rated_at')[:limit]

    # Total ratings and FP count
    total_ratings = AIFeedbackDetailedRating.objects.count()
    total_fp = AIFeedbackDetailedRating.objects.filter(
        has_false_positives=True
    ).count()

    fp_rate = (
        (total_fp / total_ratings * 100)
        if total_ratings > 0 else 0.0
    )

    recent_examples = [
        {
            'rating_id': rating.id,
            'report_case_identifier': rating.report.case.case_identifier,
            'details': rating.false_positive_details or '',
            'overall_rating': rating.overall_rating,
            'rated_at': rating.rated_at.isoformat()
        }
        for rating in fp_ratings
    ]

    return {
        'total_false_positives': total_fp,
        'false_positive_rate': round(fp_rate, 1),
        'recent_examples': recent_examples
    }


def get_prompt_version_comparison(version_id_1, version_id_2):
    """
    Compare two specific prompt versions side-by-side.

    Args:
        version_id_1 (int): First prompt version ID
        version_id_2 (int): Second prompt version ID

    Returns:
        dict: {
            'version_1': {details...},
            'version_2': {details...},
            'comparison': {
                'accuracy_diff': float,
                'helpfulness_diff': float,
                'actionability_diff': float,
                'overall_diff': float,
                'fp_rate_diff': float,
                'better_version': str ('version_1', 'version_2', or 'tie')
            }
        }

    Raises:
        PromptVersion.DoesNotExist: If either version not found
    """
    version_1 = PromptVersion.objects.get(id=version_id_1)
    version_2 = PromptVersion.objects.get(id=version_id_2)

    # Get metrics for each version
    all_versions = get_quality_by_prompt_version()

    v1_data = next((v for v in all_versions if v['prompt_version_id'] == version_id_1), None)
    v2_data = next((v for v in all_versions if v['prompt_version_id'] == version_id_2), None)

    if not v1_data or not v2_data:
        raise ValueError("One or both versions have no rating data")

    # Calculate differences (positive = v1 better, negative = v2 better)
    accuracy_diff = (v1_data['avg_accuracy'] or 0) - (v2_data['avg_accuracy'] or 0)
    helpfulness_diff = (v1_data['avg_helpfulness'] or 0) - (v2_data['avg_helpfulness'] or 0)
    actionability_diff = (v1_data['avg_actionability'] or 0) - (v2_data['avg_actionability'] or 0)
    overall_diff = (v1_data['avg_overall'] or 0) - (v2_data['avg_overall'] or 0)
    fp_rate_diff = (v2_data['false_positive_rate'] or 0) - (v1_data['false_positive_rate'] or 0)  # Lower is better, so reversed

    # Determine better version (based on overall rating)
    if overall_diff > 0.1:
        better_version = 'version_1'
    elif overall_diff < -0.1:
        better_version = 'version_2'
    else:
        better_version = 'tie'

    return {
        'version_1': v1_data,
        'version_2': v2_data,
        'comparison': {
            'accuracy_diff': round(accuracy_diff, 2),
            'helpfulness_diff': round(helpfulness_diff, 2),
            'actionability_diff': round(actionability_diff, 2),
            'overall_diff': round(overall_diff, 2),
            'fp_rate_diff': round(fp_rate_diff, 1),
            'better_version': better_version
        }
    }
