# ✅ Phase 1 Production Deployment Checklist

Comprehensive checklist for deploying AI Feedback Quality Tracking System to production.

---

## 🎯 Pre-Deployment Verification

### Code Quality

- [x] All 160 tests pass
- [x] No pending TODOs in critical code paths
- [x] Code reviewed for security vulnerabilities
- [x] Performance tests validate query efficiency
- [x] Integration tests cover end-to-end flows

### Documentation

- [x] API endpoints documented in `docs/API_ENDPOINTS.md`
- [x] Analytics guide created in `docs/ANALYTICS_GUIDE.md`
- [x] Docstrings complete for all public functions
- [x] README updated with Phase 1 features
- [x] Data models documented in `@.claude/docs/DATA_MODELS.md`

### Database

- [ ] Migrations tested on production-like dataset
- [ ] Migration rollback procedure documented
- [ ] Database indexes created (already in migrations)
- [ ] Backup/restore procedure tested
- [ ] Connection pooling configured (PgBouncer recommended)

---

## 🔧 Environment Configuration

### Required Environment Variables

```bash
# Core Django
SECRET_KEY=<strong-unique-secret-50+chars>
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database
DB_NAME=globalpeds_production
DB_USER=globalpeds_app  # NOT postgres superuser!
DB_PASSWORD=<strong-password-16+chars>
DB_HOST=your-db-host.example.com
DB_PORT=5432

# AI Service
GEMINI_API_KEY=<your-production-api-key>

# CORS
CORS_ALLOWED_ORIGINS=https://yourdomain.com

# JWT
ACCESS_TOKEN_LIFETIME=30  # minutes
REFRESH_TOKEN_LIFETIME=7  # days
```

**Verification Steps:**

- [ ] `SECRET_KEY` is unique and never committed to Git
- [ ] `DEBUG=False` in production
- [ ] `ALLOWED_HOSTS` restricted to actual domains
- [ ] Database user has minimal permissions (not superuser)
- [ ] Database password is strong (16+ characters)
- [ ] CORS origins use HTTPS only
- [ ] Gemini API key is production key with monitoring

---

## 🚀 Deployment Steps

### Step 1: Database Migration

```bash
# 1. Backup current database
pg_dump -U postgres -d globalpeds_production > backup_before_phase1_$(date +%Y%m%d).sql

# 2. Test migrations on staging
python manage.py migrate --plan  # Dry run
python manage.py migrate  # Apply migrations

# 3. Verify migrations
python manage.py showmigrations cases
# Should show all Phase 1 migrations applied:
# [X] 0009_phase1_foundation

# 4. Verify models accessible
python manage.py shell
>>> from cases.models import TokenUsageLog, AIFeedbackDetailedRating, FeedbackCache, PromptVersion
>>> TokenUsageLog.objects.count()  # Should not error
>>> exit()
```

**Rollback Plan:**
```bash
# If migration fails
python manage.py migrate cases 0008_add_tutoring_models

# Restore from backup if needed
psql -U postgres -d globalpeds_production < backup_before_phase1_YYYYMMDD.sql
```

- [ ] Database backed up
- [ ] Migrations applied successfully
- [ ] Rollback procedure documented
- [ ] Models accessible in Django shell

---

### Step 2: Deploy Code

```bash
# 1. Pull latest code
git checkout main  # or your production branch
git pull origin main

# 2. Install dependencies
pip install -r requirements.txt

# 3. Collect static files
python manage.py collectstatic --noinput

# 4. Restart application
# Method depends on deployment (systemd, Docker, etc.)
sudo systemctl restart globalpeds  # Example for systemd
```

- [ ] Code deployed to production server
- [ ] Dependencies installed
- [ ] Static files collected
- [ ] Application restarted successfully
- [ ] Health check endpoint responding

---

### Step 3: Create Initial Prompt Version

```bash
python manage.py shell
```

```python
from cases.models import PromptVersion

# Create initial production prompt version
prompt_v1 = PromptVersion.objects.create(
    version_number='v1.0',
    name='Phase 1 Production Prompt',
    description='Initial production deployment of AI feedback prompt',
    prompt_template='<your-actual-prompt-template-text>',
    is_active=True
)

print(f"Created PromptVersion: {prompt_v1.id} - {prompt_v1.version_number}")
```

- [ ] PromptVersion v1.0 created
- [ ] Prompt template validated
- [ ] Set as active (`is_active=True`)

---

### Step 4: Verify Core Functionality

**Test Report Submission & Feedback:**

```bash
# Use actual frontend or API client
curl -X POST https://yourdomain.com/api/cases/reports/ \
  -H "Authorization: Bearer <test_user_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "case_id": 1,
    "section_details": [
      {"master_template_section_id": 1, "content": "Test findings"}
    ]
  }'

# Generate AI feedback
curl -X POST https://yourdomain.com/api/cases/reports/1/ai-feedback/ \
  -H "Authorization: Bearer <test_user_token>"

# Submit rating
curl -X POST https://yourdomain.com/api/cases/detailed-ratings/ \
  -H "Authorization: Bearer <test_user_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "report_id": 1,
    "accuracy_rating": 5,
    "helpfulness_rating": 5,
    "actionability_rating": 5,
    "overall_rating": 5,
    "comment": "Production test"
  }'
```

- [ ] Report submission works
- [ ] AI feedback generation works
- [ ] TokenUsageLog created
- [ ] Rating submission works
- [ ] No errors in logs

---

### Step 5: Configure Monitoring

**Set up monitoring for:**

1. **Error Tracking** (Sentry or similar):
   ```python
   # In settings.py
   import sentry_sdk
   sentry_sdk.init(
       dsn=os.environ.get('SENTRY_DSN'),
       environment='production'
   )
   ```

2. **Cost Alerts** (Google Cloud Console):
   - Set budget alert for AI API costs
   - Threshold: $500/month
   - Notification email configured

3. **Application Monitoring**:
   - Health check endpoint: `/health/`
   - Uptime monitoring (UptimeRobot, Pingdom, etc.)
   - Alert if downtime >5 minutes

4. **Database Monitoring**:
   - Query performance tracking
   - Connection pool usage
   - Disk space alerts

- [ ] Error tracking configured
- [ ] Cost alerts set up
- [ ] Uptime monitoring active
- [ ] Database monitoring configured

---

### Step 6: Admin Dashboard Setup

**Create admin user:**

```bash
python manage.py createsuperuser
# Username: admin
# Email: admin@yourdomain.com
# Password: <strong-unique-password>
```

**Test analytics endpoints:**

```bash
# Login as admin and get token
# Then test each analytics endpoint:

curl https://yourdomain.com/api/cases/detailed-ratings/analytics/cost-trends/ \
  -H "Authorization: Bearer <admin_token>"

curl https://yourdomain.com/api/cases/detailed-ratings/analytics/prompt-comparison/ \
  -H "Authorization: Bearer <admin_token>"

curl https://yourdomain.com/api/cases/detailed-ratings/analytics/cache-performance/ \
  -H "Authorization: Bearer <admin_token>"
```

- [ ] Admin user created
- [ ] Cost trends endpoint accessible
- [ ] Prompt comparison endpoint accessible
- [ ] Cache performance endpoint accessible
- [ ] Non-admin users receive 403 Forbidden

---

## 📊 Post-Deployment Monitoring (First 24 Hours)

### Immediate Checks (First Hour)

- [ ] No 500 errors in logs
- [ ] AI feedback generating successfully
- [ ] TokenUsageLogs being created
- [ ] Cache working (check FeedbackCache table)
- [ ] Ratings being submitted

### First Day Monitoring

- [ ] Check cost trends at 6 hours
- [ ] Verify cache hit rate >5%
- [ ] Monitor false positive rate
- [ ] Review user feedback on AI quality
- [ ] Check for any performance issues

### First Week Goals

- [ ] Collect ≥50 ratings
- [ ] Establish baseline avg_overall rating
- [ ] Identify any common false positive patterns
- [ ] Verify costs within budget ($50-100 expected for week 1)
- [ ] Document any issues encountered

---

## 🔐 Security Checklist

### Application Security

- [ ] `DEBUG=False` in production
- [ ] `SECRET_KEY` is strong and unique
- [ ] CORS restricted to actual frontend domains
- [ ] HTTPS enforced (SECURE_SSL_REDIRECT=True)
- [ ] HSTS enabled (SECURE_HSTS_SECONDS=31536000)
- [ ] Content security headers configured

### Database Security

- [ ] Database user has minimal permissions
- [ ] Database not exposed to public internet
- [ ] SSL/TLS enabled for database connections
- [ ] Backups encrypted
- [ ] Backup retention policy documented (30 days recommended)

### API Security

- [ ] JWT tokens expire appropriately (30min access, 7day refresh)
- [ ] Rate limiting considered for analytics endpoints (future)
- [ ] Input validation on all endpoints
- [ ] No sensitive data logged
- [ ] API keys rotated if accidentally exposed

### Secrets Management

- [ ] `.env` file never committed to Git
- [ ] Secrets stored securely (environment variables or secrets manager)
- [ ] Access to production secrets restricted
- [ ] Secret rotation procedure documented

---

## 🚨 Incident Response

### If Something Goes Wrong

**Severity Levels:**

| Severity | Examples | Response Time |
|----------|----------|---------------|
| **Critical** | Site down, data loss | < 1 hour |
| **High** | AI feedback failing, cost spike | < 4 hours |
| **Medium** | Analytics broken, cache not working | < 1 day |
| **Low** | Typo in UI, minor bug | Next sprint |

**Emergency Rollback:**

```bash
# 1. Revert code
git revert <commit-hash>
git push origin main

# 2. Rollback migrations if needed
python manage.py migrate cases 0008_add_tutoring_models

# 3. Restore database if critical
psql -U postgres -d globalpeds_production < backup_before_phase1_YYYYMMDD.sql

# 4. Restart application
sudo systemctl restart globalpeds
```

**Contact Information:**

- **On-call Engineer**: [Name/Phone]
- **Database Admin**: [Name/Phone]
- **DevOps Lead**: [Name/Phone]

---

## 📈 Success Metrics (Phase 1)

### Week 1 Targets

- [ ] ≥50 ratings collected
- [ ] Average overall rating ≥3.5/5.0
- [ ] False positive rate <20%
- [ ] AI API costs <$100
- [ ] Zero critical bugs
- [ ] Uptime ≥99.5%

### Month 1 Targets

- [ ] ≥200 ratings collected
- [ ] Average overall rating ≥4.0/5.0
- [ ] False positive rate <15%
- [ ] AI API costs <$400
- [ ] Cache hit rate ≥10%
- [ ] ≥30% of users rate AI feedback

---

## 🔄 Ongoing Maintenance

### Daily

- Check error logs for new issues
- Monitor cost trends
- Verify cache working

### Weekly

- Review avg_overall rating
- Check false positive rate
- Review recent false positive comments
- Verify costs on track

### Monthly

- Full analytics review
- A/B test new prompt versions
- Review and update documentation
- Cost optimization analysis

---

## 📚 Documentation Links

- **API Endpoints**: `backend/docs/API_ENDPOINTS.md`
- **Analytics Guide**: `backend/docs/ANALYTICS_GUIDE.md`
- **Data Models**: `@.claude/docs/DATA_MODELS.md`
- **Environment Setup**: `@.claude/docs/ENVIRONMENT.md`
- **Testing Guide**: `@.claude/docs/TESTING.md`

---

## ✅ Final Sign-Off

**Before marking as complete, verify:**

- [ ] All checklist items completed
- [ ] Deployment documented
- [ ] Monitoring configured
- [ ] Team trained on analytics dashboard
- [ ] Incident response plan reviewed
- [ ] Success metrics baseline established

**Deployed By:** _________________

**Date:** _________________

**Version:** Phase 1 Foundation (Days 5-7 Complete)

**Git Commit:** _________________

---

**Last Updated:** 2025-01-12
**Status:** Ready for Production
