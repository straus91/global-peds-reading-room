#!/usr/bin/env python
"""
Track AI Feedback Quality Baseline

This script saves current AI feedback quality metrics for comparison over time.
Used to track improvements/regressions after prompt changes or quality improvements.

Usage:
    python track_ai_baseline.py "Description of this baseline"

Example:
    python track_ai_baseline.py "Before quality audit - Phase 0 baseline"
    python track_ai_baseline.py "After AI prompt v2.1 deployment"

Aligns with:
- AI_ITERATION_WORKFLOW.md - Data-driven AI improvement methodology
- QUALITY_AUDIT_PLAN.md Phase 0 - Baseline metrics collection
- MONITORING_SETUP.md - AI quality tracking
"""

import os
import sys
import django
import json
from datetime import datetime, timedelta
from pathlib import Path

# Setup Django environment
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'globalpeds_project.settings')
django.setup()

from django.db.models import Avg, Count
from cases.models import AIFeedbackRating
from django.utils import timezone


def track_baseline(description):
    """
    Save current AI quality metrics as baseline for future comparison.

    Args:
        description (str): Description of this baseline (e.g., "Before quality audit")

    Saves to: ai_baseline_history.json
    """

    # Collect metrics from last 30 days
    last_30_days = timezone.now() - timedelta(days=30)

    metrics = AIFeedbackRating.objects.filter(
        rated_at__gte=last_30_days
    ).aggregate(
        avg_rating=Avg('star_rating'),
        total_ratings=Count('id')
    )

    # Also get rating distribution
    rating_distribution = {}
    for rating in range(1, 6):
        count = AIFeedbackRating.objects.filter(
            rated_at__gte=last_30_days,
            star_rating=rating
        ).count()
        rating_distribution[str(rating)] = count

    # Create baseline entry
    baseline_entry = {
        'timestamp': datetime.now().isoformat(),
        'description': description,
        'avg_rating': round(float(metrics['avg_rating'] or 0), 2),
        'total_ratings': metrics['total_ratings'],
        'rating_distribution': rating_distribution,
        'period_days': 30,
        'git_commit': os.popen('git rev-parse --short HEAD 2>/dev/null').read().strip() or 'unknown'
    }

    # Load existing history
    history_file = project_root / 'ai_baseline_history.json'
    history = []
    if history_file.exists():
        try:
            with open(history_file, 'r') as f:
                history = json.load(f)
        except json.JSONDecodeError:
            print("⚠️ Warning: Could not parse existing history file, starting fresh")
            history = []

    # Append new entry
    history.append(baseline_entry)

    # Save history
    with open(history_file, 'w') as f:
        json.dump(history, f, indent=2)

    # Print summary
    print("=" * 80)
    print("✅ AI FEEDBACK QUALITY BASELINE SAVED")
    print("=" * 80)
    print(f"Description: {description}")
    print(f"Average Rating: {baseline_entry['avg_rating']:.2f}/5.00")
    print(f"Total Ratings: {baseline_entry['total_ratings']} (last 30 days)")
    print(f"\nRating Distribution:")
    for rating in range(5, 0, -1):
        count = rating_distribution[str(rating)]
        stars = "⭐" * rating
        bar = "█" * (count // 2 if count > 0 else 0)
        print(f"  {stars} ({rating}): {count:3d} {bar}")
    print(f"\nGit Commit: {baseline_entry['git_commit']}")
    print(f"Saved to: {history_file}")
    print(f"History entries: {len(history)}")
    print("=" * 80)

    # Show comparison if there's previous data
    if len(history) > 1:
        previous = history[-2]
        change = baseline_entry['avg_rating'] - previous['avg_rating']
        print(f"\n📊 Compared to previous baseline:")
        print(f"   Previous: {previous['avg_rating']:.2f}/5.00 ({previous['description']})")
        if change > 0:
            print(f"   Change: +{change:.2f} ✅ IMPROVED")
        elif change < 0:
            print(f"   Change: {change:.2f} ⚠️ DEGRADED")
        else:
            print(f"   Change: {change:.2f} → STABLE")
        print("=" * 80)


def show_history():
    """Display all baseline history"""
    history_file = Path(__file__).parent.parent / 'ai_baseline_history.json'

    if not history_file.exists():
        print("No baseline history found. Run with a description to create first baseline.")
        return

    with open(history_file, 'r') as f:
        history = json.load(f)

    print("=" * 80)
    print("📊 AI FEEDBACK QUALITY BASELINE HISTORY")
    print("=" * 80)

    for i, entry in enumerate(history, 1):
        timestamp = datetime.fromisoformat(entry['timestamp']).strftime('%Y-%m-%d %H:%M')
        print(f"\n{i}. {entry['description']}")
        print(f"   Date: {timestamp}")
        print(f"   Rating: {entry['avg_rating']:.2f}/5.00 ({entry['total_ratings']} ratings)")
        print(f"   Commit: {entry.get('git_commit', 'unknown')}")

    print("\n" + "=" * 80)


if __name__ == '__main__':
    if len(sys.argv) == 1:
        print("Usage: python track_ai_baseline.py 'Description of this baseline'")
        print("   or: python track_ai_baseline.py --history")
        print("\nExamples:")
        print("  python track_ai_baseline.py 'Before quality audit - baseline'")
        print("  python track_ai_baseline.py 'After AI prompt v2.1 deployment'")
        print("  python track_ai_baseline.py --history  # Show all baselines")
        sys.exit(1)

    if sys.argv[1] == '--history':
        show_history()
    else:
        description = sys.argv[1]
        track_baseline(description)
