# 🧪 Beta Testing Workflow

**For**: Global Peds Reading Room Beta Environment
**Server**: global-readingroom (64.225.17.0)
**Last Updated**: 2025-10-11

> Systematic testing procedures to ensure quality and prevent regressions before deploying to production.

---

## 🎯 Testing Philosophy

**Beta is for finding bugs** - It's better to discover issues here than in production!

**Principles**:
1. **🔒 Test locally first** - Catch obvious issues before deploying
2. **📊 Data-driven validation** - Use metrics to verify improvements
3. **👥 Test as users would** - Real-world scenarios
4. **🔄 Regression testing** - Ensure old features still work
5. **📝 Document findings** - Learn from every deployment

---

## 📋 Testing Checklist Matrix

| Test Type | Local Dev | Beta | Production | Frequency |
|-----------|:---------:|:----:|:----------:|-----------|
| Unit Tests | ✅ | ✅ | ✅ | Every commit |
| API Tests | ✅ | ✅ | ✅ | Every commit |
| UI Manual Test | ✅ | ✅ | ❌ | Every feature |
| AI Feedback | ✅ | ✅ | ✅ | AI changes |
| Performance | ❌ | ✅ | ✅ | Weekly |
| Integration | ✅ | ✅ | ✅ | Every deploy |
| User Acceptance | ❌ | ✅ | ❌ | New features |

---

## 🔧 Phase 1: Local Testing

### Step 1: Pre-Deployment Checklist

**Before starting any changes**:

```bash
cd /mnt/c/Users/strau/Desktop/gr4-gemini

# 1. Ensure on correct branch
git branch  # Should show * online_beta

# 2. Pull latest changes
git pull origin online_beta

# 3. Check status
git status  # Should be clean or show your changes

# 4. Activate virtual environment
cd backend
source venv/bin/activate  # Linux/WSL

# 5. Ensure dependencies up to date
pip install -r requirements.txt
```

### Step 2: Run Unit Tests

**Run all tests**:

```bash
cd backend
python manage.py test

# Expected output: OK (XX tests)
# Any failures must be fixed before deploying!
```

**Run specific app tests**:

```bash
# Test cases app only
python manage.py test cases

# Test specific test class
python manage.py test cases.tests.CaseModelTest

# Test with verbosity
python manage.py test --verbosity=2
```

**✅ Success Criteria**:
- All tests pass
- No new warnings
- No deprecation notices

**❌ If tests fail**:
1. Fix the failing test
2. Re-run tests
3. Do NOT deploy until all pass

### Step 3: Test Database Migrations

**Check for pending migrations**:

```bash
python manage.py makemigrations --dry-run

# If output shows "No changes detected" → Good!
# If migrations needed → Review carefully
```

**If migrations needed**:

```bash
# Create migration
python manage.py makemigrations

# Review migration file
cat cases/migrations/00XX_migration_name.py

# Test migration locally
python manage.py migrate

# Test rollback works
python manage.py migrate cases 00XX_previous_migration

# Re-apply
python manage.py migrate
```

**✅ Success Criteria**:
- Migration is reversible
- No data loss
- All tests still pass after migration

### Step 4: Manual Local Testing

**Start development server**:

```bash
cd backend
python manage.py runserver
```

**Start frontend** (separate terminal):

```bash
cd frontend
python -m http.server 5500
```

**Test workflow**:

1. **Login**: http://127.0.0.1:5500/login.html
   - [ ] Login with test credentials works
   - [ ] Invalid credentials show error
   - [ ] JWT token stored correctly

2. **View Cases**: http://127.0.0.1:5500/index.html
   - [ ] Cases load without errors
   - [ ] Images display (if Orthanc running)
   - [ ] Filtering works
   - [ ] Sorting works

3. **Submit Report**:
   - [ ] Can select case
   - [ ] Report form displays correctly
   - [ ] Template sections populate
   - [ ] Can submit report
   - [ ] Submission shows success message

4. **AI Feedback**:
   - [ ] Can request AI feedback
   - [ ] Feedback generates (check for API key)
   - [ ] Feedback displays formatted correctly
   - [ ] Can rate feedback

5. **Admin Functions**: http://127.0.0.1:8000/admin
   - [ ] Can login as admin
   - [ ] Can create case
   - [ ] Can create expert template
   - [ ] Can manage users

**Check browser console**:
- [ ] No JavaScript errors
- [ ] No CORS errors
- [ ] No 404s for resources

**Check server logs**:
```bash
# In terminal running manage.py runserver
# Look for errors, warnings, or unusual activity
```

### Step 5: AI Feedback Testing (If AI Changes)

**If you modified AI prompts or logic**:

```bash
cd backend
python manage.py shell
```

**In Django shell**:

```python
from cases.models import Report, Case
from cases.llm_feedback_service import get_feedback_from_llm
from cases.utils import generate_report_comparison_summary

# Get a test report
report = Report.objects.filter(is_archived=False).first()

if report and report.case.applied_expert_templates.exists():
    user_sections = report.structured_content
    expert_template = report.case.applied_expert_templates.first()

    expert_sections = [
        {
            'master_section_id': section.master_section_id,
            'content': section.content,
            'key_concepts_text': section.key_concepts_text,
            'section_name': section.master_section.name
        }
        for section in expert_template.section_contents.all()
    ]

    pre_analysis = generate_report_comparison_summary(
        user_sections,
        expert_sections,
        report.case.diagnosis
    )

    # Test feedback generation
    feedback = get_feedback_from_llm(
        user_sections,
        expert_sections,
        pre_analysis,
        case_identifier_for_llm=report.case.case_identifier,
        case_patient_age=report.case.patient_age,
        case_patient_sex=report.case.patient_sex,
        case_clinical_history=report.case.clinical_history,
        case_expert_key_findings=report.case.key_findings,
        case_expert_diagnosis=report.case.diagnosis,
        case_expert_discussion=report.case.discussion,
        case_difficulty=report.case.difficulty
    )

    print("\n" + "="*60)
    print("AI FEEDBACK TEST")
    print("="*60)
    print(feedback)
    print("="*60)

    # Manually review: Is feedback helpful? Properly formatted?
else:
    print("No suitable test report found")
```

**Manual Review**:
- [ ] Feedback addresses actual discrepancies
- [ ] Tone is constructive
- [ ] Format follows expected structure
- [ ] No prompt injection visible
- [ ] No sensitive data leaked

---

## 🚀 Phase 2: Beta Deployment Testing

### Step 1: Create Baseline Metrics (Before Deployment)

**If making AI changes**:

```bash
ssh root@64.225.17.0
source /home/deploy/global-peds-reading-room/backend/venv/bin/activate
python /home/deploy/global-peds-reading-room/scripts/track_ai_baseline.py "Before [describe change]"
```

**Document baseline** (save this output!):

```bash
python /home/deploy/global-peds-reading-room/scripts/monitor_metrics.py > ~/baseline_$(date +%Y%m%d).txt
```

### Step 2: Deploy to Beta

**Follow deployment procedure** from BETA_DEPLOYMENT.md:

```bash
# On local machine
cd /mnt/c/Users/strau/Desktop/gr4-gemini
git add -A
git commit -m "Descriptive commit message"
git push origin online_beta

# On beta server
ssh root@64.225.17.0
cd /home/deploy/global-peds-reading-room

# Backup database
mkdir -p ~/backups
sudo -u postgres pg_dump globalpeds_db > ~/backups/globalpeds_$(date +%Y%m%d_%H%M%S).sql

# Deploy
git pull origin online_beta
source backend/venv/bin/activate
pip install -r backend/requirements.txt  # If deps changed
cd backend
python manage.py migrate  # If models changed
python manage.py collectstatic --noinput  # If frontend changed
sudo systemctl restart gunicorn

# Monitor logs immediately
tail -f /var/log/gunicorn/gunicorn.log
```

**✅ Deployment Success Criteria**:
- [ ] Gunicorn restarts without errors
- [ ] No errors in logs
- [ ] Migrations applied successfully (if any)

### Step 3: Immediate Health Checks

**Test API endpoints**:

```bash
# From server (or local machine)

# 1. Test API root
curl http://64.225.17.0/api/

# 2. Test cases endpoint (requires auth in production)
curl http://64.225.17.0/api/cases/

# 3. Check Django admin
curl http://64.225.17.0/admin/

# All should return HTTP 200 or 401 (auth required), NOT 500
```

**Check service status**:

```bash
sudo systemctl status gunicorn
sudo systemctl status nginx
sudo systemctl status postgresql
```

**Monitor logs for 5 minutes**:

```bash
# Watch for errors
tail -f /var/log/gunicorn/gunicorn.log | grep -i error

# In separate terminal, watch access
tail -f /var/log/nginx/access.log
```

### Step 4: Functional Testing on Beta

**Test as real user** (use actual beta URL):

**1. Login Test**:
```
URL: http://64.225.17.0/login.html

Test:
- [ ] Page loads without errors
- [ ] Can login with test credentials
- [ ] Invalid login shows error
- [ ] Redirect to index.html after login
```

**2. Case Viewing**:
```
URL: http://64.225.17.0/index.html

Test:
- [ ] Cases load (check network tab: should be 200 OK)
- [ ] DICOM images display (if Orthanc configured)
- [ ] Case details modal works
- [ ] No JavaScript errors in console
```

**3. Report Submission**:
```
Test:
- [ ] Can select a case
- [ ] Report form displays with template sections
- [ ] Can fill out report
- [ ] Submit button works
- [ ] Success message displays
- [ ] Report appears in user's submissions
```

**4. AI Feedback**:
```
Test:
- [ ] Can request AI feedback on report
- [ ] Feedback generates within reasonable time (< 10s)
- [ ] Feedback displays correctly formatted
- [ ] No errors in console
- [ ] Can rate feedback (1-5 stars)
- [ ] Rating saves successfully
```

**5. Admin Functions**:
```
URL: http://64.225.17.0/admin/

Test (if you have admin access):
- [ ] Can login to Django admin
- [ ] Can view cases
- [ ] Can view reports
- [ ] Can view users
- [ ] Can view AI feedback ratings
```

**Browser Developer Tools Check**:

```
F12 → Console tab:
- [ ] No errors (red text)
- [ ] No CORS warnings

F12 → Network tab:
- [ ] All requests return 200 or expected status
- [ ] No 404s for missing resources
- [ ] API responses contain expected data

F12 → Application → Local Storage:
- [ ] JWT tokens stored correctly (if using localStorage)
```

### Step 5: AI Feedback Quality Testing

**If you made AI changes**:

**Test with known reports**:

```bash
ssh root@64.225.17.0
source /home/deploy/global-peds-reading-room/backend/venv/bin/activate
cd /home/deploy/global-peds-reading-room/backend
python manage.py shell
```

```python
# In Django shell
from cases.models import Report, AIFeedbackRating
from datetime import timedelta
from django.utils import timezone

# Get 5 recent reports
recent_reports = Report.objects.filter(
    is_archived=False
).order_by('-submitted_at')[:5]

# Check their feedback
for report in recent_reports:
    print(f"\n{'='*60}")
    print(f"Case: {report.case.case_identifier}")
    print(f"User: {report.user.username}")
    print(f"Submitted: {report.submitted_at}")

    if report.ai_feedback_content:
        print(f"Has AI Feedback: Yes")

        # Check rating if exists
        rating = report.ai_feedback_ratings.first()
        if rating:
            print(f"Rating: {rating.star_rating}/5")
            if rating.comment:
                print(f"Comment: {rating.comment}")
    else:
        print(f"Has AI Feedback: No")

    print('='*60)
```

**Manual AI feedback test**:

1. Login to beta: http://64.225.17.0/login.html
2. Submit a test report on a case with expert template
3. Request AI feedback
4. **Manually review**:
   - [ ] Feedback is relevant to the case
   - [ ] Feedback identifies actual discrepancies
   - [ ] Tone is constructive and educational
   - [ ] Format is clean and readable
   - [ ] No strange formatting or errors

### Step 6: Performance Testing

**Response time check**:

```bash
# Test API response times
time curl http://64.225.17.0/api/cases/

# Should complete in < 1 second for cases list
```

**Database query performance**:

```bash
ssh root@64.225.17.0

# Check for slow queries in PostgreSQL log
sudo grep "duration:" /var/log/postgresql/postgresql-*-main.log | tail -20

# Look for queries > 100ms
```

**Gunicorn worker health**:

```bash
# Check if all workers responding
ps aux | grep gunicorn

# Should see:
# - 1 master process
# - 3 worker processes (as configured)
```

**Resource usage**:

```bash
# Check disk space
df -h
# /dev/vda1 should be < 80% used

# Check memory
free -m
# Should have available memory

# Check CPU
top
# Press 'q' to quit
# CPU should not be constantly at 100%
```

### Step 7: Regression Testing

**Test existing features still work**:

**User Registration/Login**:
- [ ] Can create new user (if registration enabled)
- [ ] Can login with existing user
- [ ] Can logout
- [ ] Password reset works (if enabled)

**Case Management**:
- [ ] Existing cases still display
- [ ] Case identifiers unchanged
- [ ] Expert templates still accessible
- [ ] All case fields display correctly

**Report History**:
- [ ] Old reports still accessible
- [ ] Report content displays correctly
- [ ] AI feedback on old reports intact
- [ ] Ratings on old reports intact

**Admin Panel**:
- [ ] Can still access /admin/
- [ ] Can filter cases
- [ ] Can search users
- [ ] Can export data (if configured)

---

## 📊 Phase 3: Monitoring & Validation

### Step 1: Monitor Metrics (First 24 Hours)

**Check metrics after 24 hours**:

```bash
ssh root@64.225.17.0
source /home/deploy/global-peds-reading-room/backend/venv/bin/activate
python /home/deploy/global-peds-reading-room/scripts/monitor_metrics.py
```

**Compare to baseline**:

```bash
# View baseline saved before deployment
cat ~/baseline_YYYYMMDD.txt

# Current metrics
python /home/deploy/global-peds-reading-room/scripts/monitor_metrics.py

# Compare AI quality if AI changes made
cat /home/deploy/global-peds-reading-room/ai_baseline_history.json | jq '.'
```

**Key metrics to watch**:

| Metric | Expected | Action if Not Met |
|--------|----------|-------------------|
| AI Avg Rating | ≥ 4.0 | Review low-rated feedback |
| Error Rate | < 1% | Check logs for errors |
| API Response Time | < 500ms | Optimize queries |
| User Activity | Stable or ↑ | Check for UX issues |

### Step 2: Review Error Logs

**Check for errors**:

```bash
# Gunicorn errors
grep -i error /var/log/gunicorn/gunicorn.log | tail -50

# Nginx errors
grep -i error /var/log/nginx/error.log | tail -50

# Django errors (if separate log configured)
grep -i error /var/log/gunicorn/django.log | tail -50

# Database errors
sudo grep -i error /var/log/postgresql/postgresql-*-main.log | tail -20
```

**✅ Success**: No new errors beyond normal rate

**❌ Action Required**:
- Multiple errors of same type → Investigate and fix
- Critical errors → Consider rollback

### Step 3: User Feedback Collection

**If beta users are testing**:

1. **Ask for feedback**:
   - What worked well?
   - What broke or felt wrong?
   - Any error messages?
   - Any features slower/faster?

2. **Check low-rated AI feedback**:

```bash
ssh root@64.225.17.0
source /home/deploy/global-peds-reading-room/backend/venv/bin/activate
cd /home/deploy/global-peds-reading-room/backend
python manage.py shell
```

```python
from cases.models import AIFeedbackRating
from datetime import timedelta
from django.utils import timezone

last_24h = timezone.now() - timedelta(hours=24)

low_rated = AIFeedbackRating.objects.filter(
    rated_at__gte=last_24h,
    star_rating__lte=2
).select_related('report__case')

print(f"Low-rated feedback (last 24h): {low_rated.count()}")

for rating in low_rated:
    print(f"\n{'-'*60}")
    print(f"Case: {rating.report.case.case_identifier}")
    print(f"Rating: {rating.star_rating}/5")
    if rating.comment:
        print(f"Comment: {rating.comment}")
```

---

## 🔄 Phase 4: Rollback Testing

**It's important to know rollback works BEFORE you need it!**

### Test Rollback Procedure (Quarterly)

**Practice rollback** on beta environment:

```bash
ssh root@64.225.17.0
cd /home/deploy/global-peds-reading-room

# 1. Note current commit
git log -1 --oneline

# 2. Rollback to previous commit
git reset --hard HEAD~1

# 3. Restart services
sudo systemctl restart gunicorn

# 4. Test that system works
curl http://localhost:8001/api/

# 5. If successful, restore to latest
git reset --hard origin/online_beta
sudo systemctl restart gunicorn

# 6. Verify back to current
git log -1 --oneline
```

**✅ Verify**:
- [ ] Rollback completed without errors
- [ ] Application started successfully
- [ ] API endpoints responded
- [ ] No data loss (reports/ratings intact)
- [ ] Restore to latest worked

**Document rollback time**: ___ minutes

---

## 📋 Testing Templates

### New Feature Testing Checklist

When deploying a new feature:

```markdown
## Feature: [Feature Name]

### Pre-Deployment
- [ ] Unit tests written and passing
- [ ] Local manual testing completed
- [ ] Database migrations tested
- [ ] No existing tests broken

### Beta Testing
- [ ] Feature works as expected
- [ ] No errors in browser console
- [ ] No errors in server logs
- [ ] API responses correct
- [ ] UI displays correctly
- [ ] Mobile responsive (if applicable)

### Regression Testing
- [ ] Login still works
- [ ] Case viewing still works
- [ ] Report submission still works
- [ ] AI feedback still works
- [ ] Existing data intact

### Monitoring (24h)
- [ ] No increase in error rate
- [ ] Performance acceptable
- [ ] User feedback positive
```

### Bug Fix Testing Checklist

When fixing a bug:

```markdown
## Bug Fix: [Bug Description]

### Pre-Deployment
- [ ] Bug reproduced locally
- [ ] Fix implemented
- [ ] Test written to prevent regression
- [ ] All tests pass

### Beta Testing
- [ ] Bug no longer occurs
- [ ] No new bugs introduced
- [ ] Related functionality works

### Verification (48h)
- [ ] Bug has not reoccurred
- [ ] No similar issues reported
```

### AI Prompt Change Testing Checklist

When modifying AI prompts:

```markdown
## AI Change: [Change Description]

### Pre-Deployment
- [ ] Baseline metrics collected
- [ ] Old prompt saved (commented in code)
- [ ] New prompt tested with 3-5 sample reports
- [ ] Feedback format validated

### Beta Testing
- [ ] Generate AI feedback on 5 diverse cases
- [ ] Manually review each feedback
- [ ] Check for proper format
- [ ] Check for helpful content
- [ ] Check for appropriate tone

### Monitoring (7 days)
- [ ] Average rating tracked daily
- [ ] Low-rated feedback reviewed
- [ ] User comments analyzed
- [ ] Comparison to baseline

### Decision (Day 7)
- [ ] Rating improved or stable: ✅ Keep
- [ ] Rating degraded: ❌ Rollback prompt
```

---

## 🎯 Testing Frequency

### Every Commit (Local)
- Unit tests
- Linting (if configured)
- Basic functionality check

### Every Deployment (Beta)
- Full functional testing
- Regression testing
- Error log review
- Immediate health checks

### Weekly (Beta)
- Performance testing
- Database cleanup
- Metrics review
- Low-rated feedback analysis

### Monthly (Beta)
- Full regression suite
- Rollback procedure test
- Security review
- Dependency updates check

### Before Production Deploy
- Complete beta testing passed
- 7+ days stable on beta
- No unresolved critical issues
- Metrics show improvement or stability
- User feedback positive

---

## 🚨 When to Rollback

**Immediate Rollback** if:
- [ ] Application won't start
- [ ] Database corruption detected
- [ ] Critical feature completely broken
- [ ] Security vulnerability introduced
- [ ] Data loss occurring

**Consider Rollback** if:
- [ ] Error rate > 5%
- [ ] AI average rating drops by > 0.5
- [ ] Multiple user complaints
- [ ] Performance degraded significantly
- [ ] Cannot identify/fix issue quickly

**Rollback Procedure**: See QUICK_REFERENCE.md#emergency-rollback

---

## 📚 Related Documentation

- **BETA_DEPLOYMENT.md** - Deployment procedures
- **QUICK_REFERENCE.md** - Emergency rollback
- **MONITORING_SETUP.md** - Metrics collection
- **AI_ITERATION_WORKFLOW.md** - AI-specific testing
- **SERVER_CHEATSHEET.md** - Quick commands

---

## 💡 Best Practices

1. **Test in order**: Local → Beta → Production
2. **Document everything**: Test results, metrics, issues found
3. **Never skip testing**: Even for "small" changes
4. **Monitor after deployment**: First 24 hours are critical
5. **Keep baselines**: Track metrics before every AI change
6. **Test rollbacks**: Practice before you need them
7. **Automate when possible**: Write tests instead of manual checks
8. **Use beta as intended**: It's for finding bugs!

---

**Remember**: Time spent testing is time saved debugging production issues!

**Last Updated**: 2025-10-11
**Server**: global-readingroom (64.225.17.0)
