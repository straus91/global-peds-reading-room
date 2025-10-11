# 📊 Beta Monitoring Setup Guide

**For**: DigitalOcean Droplet Beta Environment
**Server**: global-readingroom (64.225.17.0)
**Last Updated**: 2025-10-11

> This guide sets up monitoring infrastructure for your beta deployment to enable data-driven decision making and track AI improvements.

---

## 🎯 Monitoring Goals

1. **📈 Track AI Feedback Quality**: Monitor metrics from AI_ITERATION_WORKFLOW.md
2. **🚨 Detect Issues Early**: System health, errors, performance degradation
3. **📊 Measure Improvements**: Before/after metrics for changes
4. **💰 Control Costs**: Track Gemini API usage and costs
5. **👥 Understand Usage**: User engagement and behavior patterns

---

## 🏗️ Monitoring Architecture

```
┌─────────────────────────────────────────────────┐
│  Application Logs (Django + Gunicorn)          │
│  /var/log/gunicorn/gunicorn.log                │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────┴───────────────────────────────┐
│  System Logs (Nginx + Systemd)                 │
│  /var/log/nginx/access.log, error.log          │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────┴───────────────────────────────┐
│  Database Metrics (PostgreSQL)                 │
│  Query performance, connections                │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────┴───────────────────────────────┐
│  Application Metrics (Django Shell Queries)    │
│  AIFeedbackRating, user activity, API usage    │
└─────────────────────────────────────────────────┘
```

---

## 📝 Phase 1: Log Monitoring

### Step 1: Centralize Django Logging

**On the droplet**, update Django logging configuration:

```bash
ssh root@64.225.17.0
cd /home/deploy/global-peds-reading-room/backend
nano globalpeds_project/settings.py
```

**Add/update logging configuration**:

```python
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Create logs directory if it doesn't exist
LOGS_DIR = '/var/log/gunicorn'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {asctime} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOGS_DIR, 'django.log'),
            'maxBytes': 1024 * 1024 * 15,  # 15MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'ai_feedback_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOGS_DIR, 'ai_feedback.log'),
            'maxBytes': 1024 * 1024 * 10,  # 10MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'cases': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'ai_feedback': {
            'handlers': ['ai_feedback_file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
```

**Restart Gunicorn** to apply changes:

```bash
sudo systemctl restart gunicorn
```

**Verify logs are being created**:

```bash
ls -lh /var/log/gunicorn/
tail -f /var/log/gunicorn/django.log
```

### Step 2: Enhanced AI Feedback Logging

**Update** `backend/cases/llm_feedback_service.py` to use the new logger:

```python
import logging

logger = logging.getLogger('ai_feedback')

# In get_feedback_from_llm function, add detailed logging:
def get_feedback_from_llm(...):
    logger.info(f"AI feedback request - Case: {case_identifier_for_llm}, Model: {model_name}")

    # ... existing code ...

    elapsed_time = time.time() - start_time
    logger.info(
        f"AI feedback completed - Case: {case_identifier_for_llm}, "
        f"Time: {elapsed_time:.2f}s, Tokens: ~{len(response.text)}"
    )

    return response.text
```

### Step 3: Log Rotation & Cleanup

**Verify logrotate is configured** (usually pre-installed on Ubuntu):

```bash
# Check logrotate configuration for nginx
cat /etc/logrotate.d/nginx

# Check logrotate configuration for custom logs
cat /etc/logrotate.d/gunicorn
```

**If not present, create** `/etc/logrotate.d/gunicorn`:

```bash
sudo nano /etc/logrotate.d/gunicorn
```

**Add configuration**:

```
/var/log/gunicorn/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    missingok
    create 0640 deploy deploy
    sharedscripts
    postrotate
        systemctl reload gunicorn > /dev/null 2>&1 || true
    endscript
}
```

**Test logrotate**:

```bash
sudo logrotate -d /etc/logrotate.d/gunicorn  # Dry run
sudo logrotate -f /etc/logrotate.d/gunicorn  # Force rotation (testing)
```

---

## 📊 Phase 2: Application Metrics

### Step 1: Create Monitoring Script

**On the droplet**, create a monitoring script:

```bash
cd /home/deploy/global-peds-reading-room
nano scripts/monitor_metrics.py
```

**Add script content**:

```python
#!/usr/bin/env python
"""
Beta Monitoring Script
Run: python scripts/monitor_metrics.py
"""

import os
import sys
import django
from datetime import timedelta
from django.utils import timezone

# Setup Django environment
sys.path.insert(0, '/home/deploy/global-peds-reading-room/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'globalpeds_project.settings')
django.setup()

from django.db.models import Avg, Count, Q
from cases.models import Case, Report, AIFeedbackRating, UserCaseView

def get_ai_quality_metrics(days=7):
    """Get AI feedback quality metrics"""
    since = timezone.now() - timedelta(days=days)

    recent_ratings = AIFeedbackRating.objects.filter(rated_at__gte=since)

    metrics = {
        'avg_rating': recent_ratings.aggregate(Avg('star_rating'))['star_rating__avg'],
        'total_ratings': recent_ratings.count(),
        'low_rated_count': recent_ratings.filter(star_rating__lte=2).count(),
        'distribution': list(
            recent_ratings.values('star_rating')
            .annotate(count=Count('id'))
            .order_by('star_rating')
        )
    }

    return metrics

def get_user_engagement_metrics(days=7):
    """Get user engagement metrics"""
    since = timezone.now() - timedelta(days=days)

    from django.contrib.auth import get_user_model
    User = get_user_model()

    metrics = {
        'active_users': User.objects.filter(
            reports__submitted_at__gte=since
        ).distinct().count(),
        'total_reports': Report.objects.filter(
            submitted_at__gte=since
        ).count(),
        'total_views': UserCaseView.objects.filter(
            timestamp__gte=since
        ).count(),
        'avg_reports_per_user': Report.objects.filter(
            submitted_at__gte=since
        ).values('user').annotate(count=Count('id')).aggregate(
            Avg('count')
        )['count__avg']
    }

    return metrics

def get_system_metrics():
    """Get current system state"""
    metrics = {
        'total_cases': Case.objects.filter(status='published').count(),
        'total_users': Case.objects.values('created_by').distinct().count(),
        'total_reports_all_time': Report.objects.filter(is_archived=False).count(),
    }

    return metrics

def main():
    print("=" * 60)
    print("BETA ENVIRONMENT METRICS")
    print(f"Generated: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # AI Quality Metrics (Last 7 Days)
    print("\n📊 AI FEEDBACK QUALITY (Last 7 Days)")
    print("-" * 60)
    ai_metrics = get_ai_quality_metrics(days=7)

    if ai_metrics['avg_rating']:
        print(f"Average Rating: {ai_metrics['avg_rating']:.2f}/5.00")
    else:
        print("Average Rating: No ratings yet")

    print(f"Total Ratings: {ai_metrics['total_ratings']}")
    print(f"Low-Rated (≤2): {ai_metrics['low_rated_count']}")

    if ai_metrics['distribution']:
        print("\nRating Distribution:")
        for item in ai_metrics['distribution']:
            stars = "⭐" * item['star_rating']
            print(f"  {stars} ({item['star_rating']}): {item['count']}")

    # User Engagement Metrics (Last 7 Days)
    print("\n👥 USER ENGAGEMENT (Last 7 Days)")
    print("-" * 60)
    engagement = get_user_engagement_metrics(days=7)
    print(f"Active Users: {engagement['active_users']}")
    print(f"Total Reports: {engagement['total_reports']}")
    print(f"Total Case Views: {engagement['total_views']}")

    if engagement['avg_reports_per_user']:
        print(f"Avg Reports/User: {engagement['avg_reports_per_user']:.1f}")

    # System Metrics (All Time)
    print("\n🔧 SYSTEM STATE (All Time)")
    print("-" * 60)
    system = get_system_metrics()
    print(f"Published Cases: {system['total_cases']}")
    print(f"Total Users: {system['total_users']}")
    print(f"Total Reports: {system['total_reports_all_time']}")

    print("\n" + "=" * 60)

if __name__ == '__main__':
    main()
```

**Make executable and test**:

```bash
chmod +x /home/deploy/global-peds-reading-room/scripts/monitor_metrics.py

source /home/deploy/global-peds-reading-room/backend/venv/bin/activate
python /home/deploy/global-peds-reading-room/scripts/monitor_metrics.py
```

### Step 2: Schedule Daily Metrics Collection

**Create cron job** to run daily and log results:

```bash
crontab -e
```

**Add entry** (runs daily at 8 AM):

```cron
# Daily metrics collection
0 8 * * * source /home/deploy/global-peds-reading-room/backend/venv/bin/activate && python /home/deploy/global-peds-reading-room/scripts/monitor_metrics.py >> /var/log/gunicorn/daily_metrics.log 2>&1
```

**Verify cron job**:

```bash
crontab -l
```

### Step 3: Create Baseline Metrics Script

**For AI iteration workflow**, create baseline tracking:

```bash
cd /home/deploy/global-peds-reading-room
nano scripts/track_ai_baseline.py
```

**Add content**:

```python
#!/usr/bin/env python
"""
Track AI Feedback Baseline
Usage: python scripts/track_ai_baseline.py "Description of what changed"
"""

import os
import sys
import django
from datetime import timedelta
from django.utils import timezone

sys.path.insert(0, '/home/deploy/global-peds-reading-room/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'globalpeds_project.settings')
django.setup()

from django.db.models import Avg, Count
from cases.models import AIFeedbackRating

def track_baseline(description="Baseline"):
    """Track current AI feedback metrics as baseline"""

    last_30_days = timezone.now() - timedelta(days=30)

    ratings = AIFeedbackRating.objects.filter(rated_at__gte=last_30_days)

    metrics = {
        'timestamp': timezone.now().isoformat(),
        'description': description,
        'avg_rating': ratings.aggregate(Avg('star_rating'))['star_rating__avg'],
        'total_ratings': ratings.count(),
        'rating_distribution': list(
            ratings.values('star_rating')
            .annotate(count=Count('id'))
            .order_by('star_rating')
        )
    }

    # Save to file
    import json
    baseline_file = '/home/deploy/global-peds-reading-room/ai_baseline_history.json'

    history = []
    if os.path.exists(baseline_file):
        with open(baseline_file, 'r') as f:
            history = json.load(f)

    history.append(metrics)

    with open(baseline_file, 'w') as f:
        json.dump(history, f, indent=2)

    print(f"✅ Baseline saved: {description}")
    print(f"   Average Rating: {metrics['avg_rating']:.2f}/5.00")
    print(f"   Total Ratings: {metrics['total_ratings']}")
    print(f"   Saved to: {baseline_file}")

if __name__ == '__main__':
    description = sys.argv[1] if len(sys.argv) > 1 else "Baseline"
    track_baseline(description)
```

**Make executable**:

```bash
chmod +x /home/deploy/global-peds-reading-room/scripts/track_ai_baseline.py
```

**Usage example**:

```bash
source /home/deploy/global-peds-reading-room/backend/venv/bin/activate
python /home/deploy/global-peds-reading-room/scripts/track_ai_baseline.py "Before prompt change v2.1"
```

---

## 🗄️ Phase 3: Database Monitoring

### Step 1: Enable PostgreSQL Query Logging

**Edit PostgreSQL configuration**:

```bash
sudo nano /etc/postgresql/*/main/postgresql.conf
```

**Add/uncomment these lines**:

```conf
# Log slow queries (queries taking > 100ms)
log_min_duration_statement = 100

# Log connections
log_connections = on
log_disconnections = on

# Log line prefix for better context
log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h '
```

**Restart PostgreSQL**:

```bash
sudo systemctl restart postgresql
```

**View PostgreSQL logs**:

```bash
sudo tail -f /var/log/postgresql/postgresql-*-main.log
```

### Step 2: Monitor Database Performance

**Create database monitoring script**:

```bash
cd /home/deploy/global-peds-reading-room
nano scripts/monitor_database.sh
```

**Add content**:

```bash
#!/bin/bash
# Database Monitoring Script

echo "====================================="
echo "DATABASE METRICS - globalpeds_db"
echo "====================================="
echo ""

# Database size
echo "📦 DATABASE SIZE:"
sudo -u postgres psql globalpeds_db -c "SELECT pg_size_pretty(pg_database_size('globalpeds_db')) as size;"
echo ""

# Connection count
echo "🔌 CONNECTIONS:"
sudo -u postgres psql globalpeds_db -c "SELECT count(*) as connections FROM pg_stat_activity WHERE datname = 'globalpeds_db';"
echo ""

# Top 5 largest tables
echo "📊 TOP 5 LARGEST TABLES:"
sudo -u postgres psql globalpeds_db -c "
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
LIMIT 5;
"
echo ""

# Cache hit ratio (should be > 90%)
echo "💾 CACHE HIT RATIO (should be > 90%):"
sudo -u postgres psql globalpeds_db -c "
SELECT
    round(100.0 * sum(blks_hit) / (sum(blks_hit) + sum(blks_read)), 2) AS cache_hit_ratio
FROM pg_stat_database
WHERE datname = 'globalpeds_db';
"

echo "====================================="
```

**Make executable and run**:

```bash
chmod +x /home/deploy/global-peds-reading-room/scripts/monitor_database.sh
/home/deploy/global-peds-reading-room/scripts/monitor_database.sh
```

---

## 🚨 Phase 4: Alerting

### Step 1: Create Alert Script

**Basic email alerting** (requires mailutils):

```bash
sudo apt-get install mailutils -y
```

**Create alert script**:

```bash
cd /home/deploy/global-peds-reading-room
nano scripts/check_alerts.py
```

**Add content**:

```python
#!/usr/bin/env python
"""
Alert Checking Script
Checks critical conditions and sends alerts
"""

import os
import sys
import django
from datetime import timedelta
from django.utils import timezone

sys.path.insert(0, '/home/deploy/global-peds-reading-room/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'globalpeds_project.settings')
django.setup()

from django.db.models import Avg
from cases.models import AIFeedbackRating

ALERT_EMAIL = "your-email@example.com"  # UPDATE THIS

def send_alert(subject, message):
    """Send email alert"""
    import subprocess

    try:
        subprocess.run(
            ['mail', '-s', subject, ALERT_EMAIL],
            input=message.encode(),
            check=True
        )
        print(f"✉️ Alert sent: {subject}")
    except Exception as e:
        print(f"❌ Failed to send alert: {e}")

def check_ai_quality():
    """Check if AI quality has degraded"""
    last_7_days = timezone.now() - timedelta(days=7)

    recent_avg = AIFeedbackRating.objects.filter(
        rated_at__gte=last_7_days
    ).aggregate(Avg('star_rating'))['star_rating__avg']

    if recent_avg and recent_avg < 3.0:
        message = f"""
⚠️ AI FEEDBACK QUALITY ALERT

The average AI feedback rating has dropped below 3.0.

Current 7-day average: {recent_avg:.2f}/5.00

Action required:
1. Review recent low-rated feedback comments
2. Check if recent prompt changes caused degradation
3. Consider rolling back to previous prompt version

Review at: http://64.225.17.0/admin/
        """
        send_alert("⚠️ AI Quality Degraded", message.strip())
        return False

    return True

def check_system_health():
    """Check system resource usage"""
    import psutil

    # Check disk space
    disk = psutil.disk_usage('/')
    if disk.percent > 80:
        message = f"""
⚠️ DISK SPACE ALERT

Disk usage is at {disk.percent}%

Free space: {disk.free / (1024**3):.1f} GB

Action required:
1. Clean old log files
2. Clean old database backups
3. Check for large files
        """
        send_alert("⚠️ Low Disk Space", message.strip())
        return False

    return True

def main():
    print("Running health checks...")

    ai_ok = check_ai_quality()
    system_ok = check_system_health()

    if ai_ok and system_ok:
        print("✅ All checks passed")
    else:
        print("⚠️ Some checks failed - alerts sent")

if __name__ == '__main__':
    main()
```

**Update email address and make executable**:

```bash
nano /home/deploy/global-peds-reading-room/scripts/check_alerts.py  # Update ALERT_EMAIL
chmod +x /home/deploy/global-peds-reading-room/scripts/check_alerts.py
```

**Schedule alerts** (run every 6 hours):

```bash
crontab -e
```

**Add entry**:

```cron
# Health check alerts every 6 hours
0 */6 * * * source /home/deploy/global-peds-reading-room/backend/venv/bin/activate && python /home/deploy/global-peds-reading-room/scripts/check_alerts.py
```

---

## 📈 Phase 5: Simple Dashboard

### Step 1: Create Status Page

**Create admin status page**:

```bash
cd /home/deploy/global-peds-reading-room/frontend/admin
nano status.html
```

**Add content**:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Beta Status Dashboard</title>
    <link rel="stylesheet" href="../styles.css">
    <style>
        .metric-card {
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin: 15px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .metric-value {
            font-size: 2em;
            font-weight: bold;
            color: #2c3e50;
        }
        .metric-label {
            color: #7f8c8d;
            margin-top: 5px;
        }
        .alert-good { color: #27ae60; }
        .alert-warning { color: #f39c12; }
        .alert-bad { color: #e74c3c; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Beta Environment Status</h1>
        <p id="last-updated">Loading...</p>

        <div class="metric-card">
            <h2>🤖 AI Feedback Quality (Last 7 Days)</h2>
            <div class="metric-value" id="avg-rating">--</div>
            <div class="metric-label">Average Rating</div>
            <div style="margin-top: 15px;">
                <span id="total-ratings">--</span> ratings |
                <span id="low-rated">--</span> low-rated (≤2)
            </div>
        </div>

        <div class="metric-card">
            <h2>👥 User Engagement (Last 7 Days)</h2>
            <div style="display: flex; gap: 30px;">
                <div>
                    <div class="metric-value" id="active-users">--</div>
                    <div class="metric-label">Active Users</div>
                </div>
                <div>
                    <div class="metric-value" id="total-reports">--</div>
                    <div class="metric-label">Reports Submitted</div>
                </div>
                <div>
                    <div class="metric-value" id="total-views">--</div>
                    <div class="metric-label">Case Views</div>
                </div>
            </div>
        </div>

        <div class="metric-card">
            <h2>🔧 System State</h2>
            <div style="display: flex; gap: 30px;">
                <div>
                    <div class="metric-value" id="published-cases">--</div>
                    <div class="metric-label">Published Cases</div>
                </div>
                <div>
                    <div class="metric-value" id="total-users">--</div>
                    <div class="metric-label">Total Users</div>
                </div>
            </div>
        </div>

        <div class="metric-card">
            <h2>📋 Quick Actions</h2>
            <button onclick="window.location.href='/admin'">Django Admin</button>
            <button onclick="refreshMetrics()">🔄 Refresh Metrics</button>
            <a href="http://64.225.17.0:8042" target="_blank">
                <button>🏥 Orthanc DICOM Server</button>
            </a>
        </div>
    </div>

    <script>
        // This would need a backend endpoint to fetch metrics
        // For now, this is a placeholder structure

        function refreshMetrics() {
            document.getElementById('last-updated').textContent =
                'Last updated: ' + new Date().toLocaleString();

            // TODO: Fetch from API endpoint
            // For beta, you can manually update or use Django template
            console.log('Metrics refresh - TODO: implement API endpoint');
        }

        // Refresh on load
        refreshMetrics();

        // Auto-refresh every 5 minutes
        setInterval(refreshMetrics, 300000);
    </script>
</body>
</html>
```

**Access at**: `http://64.225.17.0/admin/status.html`

---

## 🔍 Daily Monitoring Routine

### Morning Check (5 minutes)

```bash
ssh root@64.225.17.0

# 1. Check service status
sudo systemctl status gunicorn nginx postgresql

# 2. Check recent errors
tail -50 /var/log/gunicorn/gunicorn.log | grep -i error

# 3. Run metrics
source /home/deploy/global-peds-reading-room/backend/venv/bin/activate
python /home/deploy/global-peds-reading-room/scripts/monitor_metrics.py

# 4. Check disk space
df -h
```

### Weekly Review (30 minutes)

```bash
ssh root@64.225.17.0

# 1. Review AI feedback trends
cd /home/deploy/global-peds-reading-room
cat ai_baseline_history.json | jq '.'

# 2. Check database performance
scripts/monitor_database.sh

# 3. Review slow queries
sudo grep "duration:" /var/log/postgresql/postgresql-*-main.log | tail -20

# 4. Check for low-rated feedback
source backend/venv/bin/activate
python manage.py shell

# In Django shell:
from cases.models import AIFeedbackRating
from datetime import timedelta
from django.utils import timezone

last_week = timezone.now() - timedelta(days=7)
low_rated = AIFeedbackRating.objects.filter(
    rated_at__gte=last_week,
    star_rating__lte=2
).select_related('report__case')

for rating in low_rated:
    print(f"\nCase: {rating.report.case.case_identifier}")
    print(f"Rating: {rating.star_rating}/5")
    print(f"Comment: {rating.comment}")
```

---

## 📊 Key Metrics Reference

### AI Feedback Quality
- **Target**: Average rating ≥ 4.0/5.0
- **Warning**: Average rating < 3.5/5.0
- **Critical**: Average rating < 3.0/5.0
- **Action**: Review prompt, check for recent changes

### User Engagement
- **Active Users**: Track weekly trend
- **Reports/User**: Should increase over time (learning)
- **View-to-Report Rate**: Track conversion

### System Performance
- **Response Time**: < 500ms for API endpoints
- **Database Queries**: < 100ms average
- **Disk Usage**: < 80%
- **Cache Hit Ratio**: > 90%

---

## 🛠️ Troubleshooting

### Metrics Script Fails

```bash
# Check Python path
which python

# Check venv activation
source /home/deploy/global-peds-reading-room/backend/venv/bin/activate
which python  # Should show venv path

# Check Django settings
cd /home/deploy/global-peds-reading-room/backend
python manage.py check
```

### Cron Jobs Not Running

```bash
# Check cron service
sudo systemctl status cron

# Check cron logs
sudo tail -f /var/log/syslog | grep CRON

# Test manually
source /home/deploy/global-peds-reading-room/backend/venv/bin/activate
python /home/deploy/global-peds-reading-room/scripts/monitor_metrics.py
```

### Email Alerts Not Sending

```bash
# Check mail service
systemctl status postfix

# Test email
echo "Test message" | mail -s "Test" your-email@example.com

# Check mail logs
sudo tail -f /var/log/mail.log
```

---

## 📚 Related Documentation

- **AI_ITERATION_WORKFLOW.md** - Use metrics from this guide for baseline tracking
- **QUICK_REFERENCE.md** - Emergency procedures and quick commands
- **BETA_DEPLOYMENT.md** - Deployment workflow
- **.claude/docs/MONITORING.md** - Additional monitoring strategies

---

## 🎯 Next Steps

1. **Set up logging**: Phases 1 & 2 (30 min)
2. **Create monitoring scripts**: Phase 2 (20 min)
3. **Schedule cron jobs**: Phase 2 (10 min)
4. **Enable database logging**: Phase 3 (15 min)
5. **Configure alerts**: Phase 4 (20 min)
6. **Run baseline**: Before next AI change

**Total Setup Time**: ~2 hours

**Maintenance**: 5 min/day + 30 min/week

---

**💡 Remember**: Monitoring is only valuable if you act on the data! Review metrics regularly and use them to guide improvements.

**Last Updated**: 2025-10-11
**Server**: global-readingroom (64.225.17.0)
