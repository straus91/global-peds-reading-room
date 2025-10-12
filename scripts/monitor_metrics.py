#!/usr/bin/env python
"""
Comprehensive Metrics Monitoring

Generates detailed metrics report for system health monitoring.
Tracks AI quality, user engagement, system performance.

Usage:
    python monitor_metrics.py [--days=7]

Example:
    python monitor_metrics.py              # Default 7 days
    python monitor_metrics.py --days=30    # Last 30 days

Aligns with:
- MONITORING_SETUP.md - Metrics collection strategy
- QUALITY_AUDIT_PLAN.md Phase 0 - Baseline metrics
- BETA_BEST_PRACTICES.md - Data-driven decisions
"""

import os
import sys
import django
from datetime import datetime, timedelta
from pathlib import Path

# Setup Django environment
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'globalpeds_project.settings')
django.setup()

from django.db.models import Avg, Count, Q
from django.utils import timezone
from cases.models import Case, Report, AIFeedbackRating, UserCaseView
from django.contrib.auth.models import User


def print_metrics(days=7):
    """
    Print comprehensive metrics report.

    Args:
        days (int): Number of days to look back for recent activity metrics
    """
    now = timezone.now()
    lookback = now - timedelta(days=days)
    last_30_days = now - timedelta(days=30)

    print("=" * 80)
    print(f"📊 GLOBAL PEDS READING ROOM - METRICS REPORT")
    print(f"Generated: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Lookback period: Last {days} days")
    print("=" * 80)

    # AI Quality Metrics
    print("\n" + "🤖 AI FEEDBACK QUALITY".center(80))
    print("-" * 80)

    overall_rating = AIFeedbackRating.objects.aggregate(Avg('star_rating'))
    overall_avg = overall_rating['star_rating__avg'] or 0
    print(f"Overall Average Rating: {overall_avg:.2f}/5.00")

    recent_rating = AIFeedbackRating.objects.filter(
        rated_at__gte=lookback
    ).aggregate(Avg('star_rating'))
    recent_avg = recent_rating['star_rating__avg'] or 0
    print(f"Last {days} Days: {recent_avg:.2f}/5.00", end="")

    # Show trend
    if overall_avg > 0 and recent_avg > 0:
        change = recent_avg - overall_avg
        if change > 0.1:
            print(f" ✅ (+{change:.2f} trending up)")
        elif change < -0.1:
            print(f" ⚠️ ({change:.2f} trending down)")
        else:
            print(" → (stable)")
    else:
        print()

    # Total ratings
    total_ratings = AIFeedbackRating.objects.count()
    recent_ratings_count = AIFeedbackRating.objects.filter(rated_at__gte=lookback).count()
    print(f"Total Ratings: {total_ratings} (last {days} days: {recent_ratings_count})")

    # Rating distribution
    rating_dist = AIFeedbackRating.objects.values('star_rating').annotate(
        count=Count('id')
    ).order_by('star_rating')

    print("\nRating Distribution (All Time):")
    for rating in range(5, 0, -1):
        item = next((r for r in rating_dist if r['star_rating'] == rating), None)
        count = item['count'] if item else 0
        percentage = (count / total_ratings * 100) if total_ratings > 0 else 0
        stars = "⭐" * rating
        bar = "█" * (count // max(1, total_ratings // 40))  # Scale bar
        print(f"  {stars} ({rating}): {count:3d} ({percentage:5.1f}%) {bar}")

    # Low ratings analysis
    low_rated = AIFeedbackRating.objects.filter(star_rating__lte=2).count()
    low_percentage = (low_rated / total_ratings * 100) if total_ratings > 0 else 0
    print(f"\nLow Ratings (≤2 stars): {low_rated} ({low_percentage:.1f}%)")

    # Ratings with comments
    with_comments = AIFeedbackRating.objects.exclude(
        Q(comment='') | Q(comment__isnull=True)
    ).count()
    comment_percentage = (with_comments / total_ratings * 100) if total_ratings > 0 else 0
    print(f"Ratings with Comments: {with_comments} ({comment_percentage:.1f}%)")

    # User Engagement
    print("\n" + "👥 USER ENGAGEMENT".center(80))
    print("-" * 80)

    total_users = User.objects.filter(is_active=True).count()
    print(f"Total Active Users: {total_users}")

    active_users_recent = User.objects.filter(
        reports__submitted_at__gte=lookback
    ).distinct().count()
    print(f"Active Users (last {days} days): {active_users_recent}")

    if total_users > 0:
        engagement_rate = (active_users_recent / total_users * 100)
        print(f"Engagement Rate: {engagement_rate:.1f}%")

    active_users_30d = User.objects.filter(
        reports__submitted_at__gte=last_30_days
    ).distinct().count()
    print(f"Active Users (last 30 days): {active_users_30d}")

    # Report Metrics
    print("\n" + "📝 REPORT SUBMISSIONS".center(80))
    print("-" * 80)

    total_reports = Report.objects.filter(is_archived=False).count()
    print(f"Total Reports (non-archived): {total_reports}")

    reports_recent = Report.objects.filter(submitted_at__gte=lookback).count()
    print(f"Last {days} Days: {reports_recent}")

    reports_30d = Report.objects.filter(submitted_at__gte=last_30_days).count()
    print(f"Last 30 Days: {reports_30d}")

    # Average reports per active user
    if active_users_recent > 0:
        avg_reports = reports_recent / active_users_recent
        print(f"Avg Reports per Active User ({days}d): {avg_reports:.1f}")

    # Reports by difficulty
    reports_by_difficulty = Report.objects.filter(
        submitted_at__gte=lookback
    ).values(
        'case__difficulty'
    ).annotate(count=Count('id')).order_by('-count')

    print(f"\nReports by Difficulty (last {days} days):")
    for item in reports_by_difficulty:
        difficulty = item['case__difficulty'] or 'unknown'
        count = item['count']
        print(f"  {difficulty.capitalize():12s}: {count:3d}")

    # Reports with AI feedback
    reports_with_feedback = Report.objects.filter(
        submitted_at__gte=lookback
    ).exclude(
        Q(ai_feedback_content={}) | Q(ai_feedback_content__isnull=True)
    ).count()
    feedback_rate = (reports_with_feedback / reports_recent * 100) if reports_recent > 0 else 0
    print(f"\nReports with AI Feedback: {reports_with_feedback}/{reports_recent} ({feedback_rate:.1f}%)")

    # Case Metrics
    print("\n" + "📚 CASE METRICS".center(80))
    print("-" * 80)

    total_cases = Case.objects.filter(status='published').count()
    draft_cases = Case.objects.filter(status='draft').count()
    print(f"Published Cases: {total_cases}")
    print(f"Draft Cases: {draft_cases}")

    cases_by_difficulty = Case.objects.filter(status='published').values(
        'difficulty'
    ).annotate(count=Count('id')).order_by('difficulty')

    print("\nCases by Difficulty:")
    for item in cases_by_difficulty:
        print(f"  {item['difficulty'].capitalize():12s}: {item['count']:3d}")

    # Most viewed cases (recent activity)
    popular_cases = Case.objects.filter(
        status='published'
    ).annotate(
        view_count=Count('viewed_by'),
        report_count=Count('reports')
    ).order_by('-view_count')[:5]

    print(f"\nTop 5 Most Viewed Cases:")
    for i, case in enumerate(popular_cases, 1):
        print(f"  {i}. {case.case_identifier}: {case.view_count} views, {case.report_count} reports")

    # System Health
    print("\n" + "🔧 SYSTEM HEALTH".center(80))
    print("-" * 80)

    total_views = UserCaseView.objects.count()
    recent_views = UserCaseView.objects.filter(timestamp__gte=lookback).count()
    print(f"Total Case Views: {total_views}")
    print(f"Recent Views ({days}d): {recent_views}")

    # View to report conversion
    if recent_views > 0:
        conversion_rate = (reports_recent / recent_views * 100)
        print(f"View-to-Report Conversion: {conversion_rate:.1f}%")

    # Database stats
    print("\nDatabase Statistics:")
    print(f"  Total Users: {User.objects.count()}")
    print(f"  Total Cases: {Case.objects.count()}")
    print(f"  Total Reports: {Report.objects.count()}")
    print(f"  Total Ratings: {AIFeedbackRating.objects.count()}")
    print(f"  Total Case Views: {UserCaseView.objects.count()}")

    # Check for potential issues
    print("\n" + "⚠️ HEALTH CHECKS".center(80))
    print("-" * 80)

    issues_found = False

    # Check 1: AI quality degradation
    if recent_avg > 0 and overall_avg > 0 and (recent_avg < overall_avg - 0.2):
        print("⚠️ AI quality has degraded by >0.2 points - investigate recent changes")
        issues_found = True

    # Check 2: Low engagement
    if total_users > 10 and active_users_recent < (total_users * 0.1):
        print("⚠️ Low user engagement (<10% active) - investigate retention")
        issues_found = True

    # Check 3: High low-rating rate
    if total_ratings > 20 and low_percentage > 20:
        print(f"⚠️ High rate of low ratings ({low_percentage:.1f}%) - review AI feedback quality")
        issues_found = True

    # Check 4: No recent activity
    if reports_recent == 0 and days <= 7:
        print(f"⚠️ No reports submitted in last {days} days - check system availability")
        issues_found = True

    if not issues_found:
        print("✅ No issues detected")

    print("\n" + "=" * 80)
    print("✅ Report complete!")
    print("=" * 80)
    print("\n💡 Tips:")
    print("  - Compare metrics to baseline (see ai_baseline_history.json)")
    print("  - Monitor trends after deployments (per BETA_BEST_PRACTICES.md)")
    print("  - Review low-rated feedback for improvement opportunities")
    print("  - Track engagement rate to measure user retention")
    print("=" * 80)


if __name__ == '__main__':
    # Parse days argument
    days = 7
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg.startswith('--days='):
            try:
                days = int(arg.split('=')[1])
            except ValueError:
                print("Invalid days value. Using default: 7")
        elif arg in ['-h', '--help']:
            print("Usage: python monitor_metrics.py [--days=N]")
            print("\nOptions:")
            print("  --days=N    Number of days for recent activity metrics (default: 7)")
            print("\nExamples:")
            print("  python monitor_metrics.py           # Last 7 days")
            print("  python monitor_metrics.py --days=30 # Last 30 days")
            sys.exit(0)

    print_metrics(days)
