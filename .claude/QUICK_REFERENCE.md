# ⚡ QUICK REFERENCE CARD

**Purpose**: Fast answers to common questions and tasks

**Last Updated**: 2025-10-14

---

## 🚨 I'm a New Claude Code Session - Where Do I Start?

### Step 1: READ THIS FIRST
**File**: `SESSION_ENTRY_POINT.md` (in project root)
**Time**: 5 minutes
**Why**: Single source of truth for project status, current phase, and next action

### Step 2: CHECK YOUR TASKS
**File**: `PROGRESS_TRACKER.md` (in project root)
**Action**: Find first unchecked box in "Current Phase" section
**Why**: Tells you exactly what to do next

### Step 3: GET DETAILS
**Files**: Depends on current phase (SESSION_ENTRY_POINT.md will tell you)
- **Phase 1 Backend**: `NEXT_STEPS.md`
- **Quality Audit**: `docs/QUALITY_AUDIT_PLAN.md`
- **Features**: `.claude/docs/ROADMAP.md`

### Step 4: EXECUTE
Follow the step-by-step instructions in the relevant plan document

### Step 5: UPDATE DOCS
- Check off task in `PROGRESS_TRACKER.md`
- Update `SESSION_ENTRY_POINT.md` "Last Session Summary"

---

## 🔧 COMMON TASKS

### Task: Continue Where Last Session Stopped

```bash
# 1. Read session entry point
cat SESSION_ENTRY_POINT.md | grep -A 10 "Next Action"

# 2. Read progress tracker
cat PROGRESS_TRACKER.md | grep -A 5 "Current Phase"

# 3. Find first unchecked box
# 4. Execute that task
# 5. Update both files when done
```

**Time**: Start immediately, no guessing needed

---

### Task: Fix a Bug

#### Step 1: Research (10-15 minutes)
```bash
# Check if bug was seen before
grep -i "bug_description" DEPLOYMENT_LOG.md

# Check known pitfalls
cat SESSION_ENTRY_POINT.md | grep -A 20 "KNOWN PITFALLS"
```

#### Step 2: Risk Assessment (10 minutes)
```bash
# Read risk assessment framework
cat .claude/docs/RISK_ASSESSMENT.md | head -100
```

#### Step 3: Fix (Time varies)
```bash
# If frontend API issue
cat .claude/docs/FRONTEND_API_PATTERNS.md

# If deployment issue
cat .claude/docs/DEPLOYMENT.md

# If database issue
cat .claude/docs/DATA_MODELS.md
```

#### Step 4: Test (10-20 minutes)
```bash
cd backend
. venv/bin/activate
python manage.py test cases

# Or specific test
python manage.py test cases.tests.TestClassName.test_method_name
```

#### Step 5: Document (5 minutes)
```bash
# Add to DEPLOYMENT_LOG.md
# Update PROGRESS_TRACKER.md
# Update SESSION_ENTRY_POINT.md
```

**Total Estimated Time**: 1-2 hours

---

### Task: Deploy Changes

#### Prerequisites Checklist
- [ ] ✅ Code tested locally
- [ ] ✅ All tests passing
- [ ] ✅ Risk assessment complete (if significant change)
- [ ] ✅ Commit message is descriptive
- [ ] ✅ No sensitive data in commit

#### Deployment Steps
```bash
# 1. Check git status
git status
git log -5

# 2. Commit changes
git add <files>
git commit -m "Descriptive message

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"

# 3. Push to deployment branch
git push origin online_beta

# 4. GitHub Actions deploys automatically (2-3 minutes)
# Watch: https://github.com/straus91/global-peds-reading-room/actions

# 5. Verify deployment (via DigitalOcean console)
ssh root@64.225.17.0
sudo systemctl status gunicorn nginx postgresql
```

#### Post-Deployment
```bash
# 6. Document in DEPLOYMENT_LOG.md
# 7. Update PROGRESS_TRACKER.md
# 8. Update SESSION_ENTRY_POINT.md
```

**Total Time**: 20-30 minutes (including verification)

---

### Task: Write Tests

#### Test Template
```python
# backend/cases/tests/test_feature.py

from django.test import TestCase
from cases.models import YourModel

class YourModelTest(TestCase):
    def setUp(self):
        """Set up test data before each test"""
        self.test_obj = YourModel.objects.create(
            field1='value1',
            field2='value2'
        )

    def test_your_feature(self):
        """Test that your feature works correctly"""
        result = self.test_obj.your_method()

        self.assertEqual(result, expected_value)
        self.assertTrue(condition)
        self.assertIsNotNone(self.test_obj.field1)
```

#### Run Tests
```bash
cd backend
. venv/bin/activate

# Run all tests
python manage.py test

# Run specific app
python manage.py test cases

# Run specific test
python manage.py test cases.tests.test_feature.YourModelTest.test_your_feature

# With coverage
coverage run --source='.' manage.py test
coverage report
```

**Time**: 15-30 minutes per test

---

### Task: Make Frontend API Call

#### CRITICAL: Read This First
```bash
cat .claude/docs/FRONTEND_API_PATTERNS.md
```

#### Correct Pattern
```javascript
// ✅ CORRECT - No /api/ prefix
apiRequest('/cases/reports/')              // Becomes: /api/cases/reports/
apiRequest('/users/me/')                   // Becomes: /api/users/me/
apiRequest(`/cases/reports/${id}/ai-feedback/`) // Becomes: /api/cases/reports/6/ai-feedback/
```

#### WRONG Pattern (Never Do This)
```javascript
// ❌ WRONG - Adding /api/ creates double prefix
apiRequest('/api/cases/reports/')          // Becomes: /api/api/cases/reports/ → 404
```

#### Pre-Commit Checklist
```bash
# Before committing frontend changes
cat .claude/FRONTEND_CHECKLIST.md

# Search for existing pattern
grep -n "apiRequest.*cases" frontend/js/main.js

# Copy exact pattern from working code
```

**Time**: 10-15 minutes (if you follow the pattern)

---

### Task: Make Database Changes

#### CRITICAL: Risk Assessment First
```bash
cat .claude/docs/RISK_ASSESSMENT.md | head -150
```

#### Safe Migration Process
```bash
# 1. Make model changes in backend/cases/models.py

# 2. Create migration
cd backend
. venv/bin/activate
python manage.py makemigrations --name descriptive_migration_name

# 3. Review generated migration
cat cases/migrations/0XXX_descriptive_migration_name.py

# 4. Test migration locally
python manage.py migrate

# 5. Test reversal
python manage.py migrate cases 0XXX_previous_migration

# 6. Re-apply
python manage.py migrate

# 7. Write tests for new fields/models

# 8. Commit migration file + model changes
git add cases/migrations/0XXX_*.py cases/models.py
git commit -m "Add [field/model] to [Model]"

# 9. Deploy (GitHub Actions applies migration automatically)
git push origin online_beta
```

**Time**: 30 minutes - 2 hours (depending on complexity)

---

## 📁 FILE LOCATION MAP

### Session Management
- **SESSION_ENTRY_POINT.md** - Start here for new sessions
- **PROGRESS_TRACKER.md** - Checkbox tracking for all work
- **.claude/SESSION_HANDOFF_CHECKLIST.md** - End-of-session checklist
- **INTEGRATION_MAP.md** - How all docs relate

### Plans (Long-term)
- **NEXT_STEPS.md** - Phase 1 backend (Days 1-4)
- **docs/QUALITY_AUDIT_PLAN.md** - 11-phase quality improvements
- **.claude/docs/ROADMAP.md** - 3-track feature roadmap

### History & Status
- **DEPLOYMENT_LOG.md** - Deployment history and lessons
- **DEPLOYMENT_STATUS.md** - Current server status

### Technical Reference (.claude/docs/)
- **FRONTEND_API_PATTERNS.md** ← Read before ANY frontend API changes
- **FRONTEND_CHECKLIST.md** ← Pre-commit checklist for frontend
- **DEPLOYMENT.md** ← Complete deployment guide
- **RISK_ASSESSMENT.md** ← Assess risk before changes
- **DATA_MODELS.md** ← Database model documentation
- **WORKFLOWS.md** ← Step-by-step procedures
- **TESTING.md** ← Testing strategies
- **SECURITY.md** ← Security best practices
- **PERFORMANCE.md** ← Performance optimization
- **MONITORING.md** ← Metrics and analytics
- **ENVIRONMENT.md** ← Environment variable setup

---

## 💻 COMMON COMMANDS

### Git Operations
```bash
# Check current status
git status
git log -5 --oneline

# Check current branch (should be online_beta for deployment)
git branch

# Create new branch
git checkout -b feature/branch-name

# Switch branch
git checkout online_beta

# View diff
git diff
git diff --cached

# Commit
git add <files>
git commit -m "Message"

# Push
git push origin online_beta
```

### Backend Operations
```bash
# Navigate to backend
cd /mnt/c/Users/strau/Desktop/gr4-gemini/backend

# Activate virtual environment
. venv/bin/activate

# Run server
python manage.py runserver

# Run tests
python manage.py test

# Run specific test
python manage.py test cases.tests.TestClass.test_method

# Make migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Django shell
python manage.py shell
```

### Droplet Operations (via DigitalOcean Console or SSH)
```bash
# Check services
sudo systemctl status gunicorn
sudo systemctl status nginx
sudo systemctl status postgresql

# Restart services
sudo systemctl restart gunicorn
sudo systemctl restart nginx

# View logs
sudo journalctl -u gunicorn -n 50 --no-pager
sudo tail -50 /var/log/nginx/globalpeds_error.log
sudo tail -20 /var/log/nginx/globalpeds_access.log

# Check nginx config
sudo nginx -t

# Reload nginx (after config change)
sudo systemctl reload nginx
```

### Testing & Coverage
```bash
cd backend
. venv/bin/activate

# Run tests with coverage
coverage run --source='.' manage.py test
coverage report

# HTML coverage report
coverage html
# Open: htmlcov/index.html in browser

# Run only fast tests
python manage.py test --keepdb
```

---

## 🎯 DECISION TREES

### "What Should I Do Next?"

```
┌─ Am I a new Claude session?
│
├─ YES → Read SESSION_ENTRY_POINT.md
│        Read PROGRESS_TRACKER.md
│        Find first unchecked task
│        Execute that task
│
└─ NO (Continuing work)
   └─ Check PROGRESS_TRACKER.md
      Find current task
      Continue from where I left off
```

### "User Reported a Bug"

```
┌─ Is it a frontend API 404 error?
│
├─ YES → Read .claude/docs/FRONTEND_API_PATTERNS.md
│        Check for double /api/ prefix
│        Fix: Remove /api/ from apiRequest() call
│
├─ Is it a deployment issue?
│  └─ YES → Read DEPLOYMENT.md
│            Check DEPLOYMENT_LOG.md for similar issues
│
├─ Is it a database issue?
│  └─ YES → Read DATA_MODELS.md
│            Check migration history
│
└─ Other bug
   └─ Read RISK_ASSESSMENT.md
      Complete risk assessment
      Read relevant .claude/docs/ file
```

### "User Requests New Feature"

```
┌─ Is it in ROADMAP.md?
│
├─ YES → Check priority
│        Is Phase 1 + Quality Audit complete?
│        ├─ YES → Plan feature, get approval
│        └─ NO → Defer to after quality work
│
└─ NO (New feature request)
   └─ Complete risk assessment
      Create implementation plan
      Add to PROGRESS_TRACKER.md
      Get user approval
      Execute
```

---

## 🚨 RED FLAGS & WARNINGS

### Stop Immediately If:
- ❌ You're about to add `/api/` to an `apiRequest()` call
- ❌ You're about to modify database without risk assessment
- ❌ You're about to deploy without testing locally
- ❌ You're about to commit with sensitive data (API keys, passwords)
- ❌ You're about to skip Phase 0 baseline before quality improvements

### Warning Signs:
- ⚠️ You can't find existing example of pattern you want to use
- ⚠️ You're guessing instead of searching for patterns
- ⚠️ You don't understand how apiRequest() works
- ⚠️ You haven't read the relevant .claude/docs/ file yet
- ⚠️ You're making changes without updating PROGRESS_TRACKER.md

**Action**: STOP, read documentation, then proceed

---

## 📊 KEY METRICS TO CHECK

### Code Quality
```bash
# Test count
cd backend
. venv/bin/activate
python manage.py test --dry-run | grep "Found"

# Coverage
coverage run --source='.' manage.py test
coverage report | grep TOTAL
```

### Database Health
```bash
# Requires droplet access or local DB
python manage.py shell -c "
from cases.models import Case, Report, User, AIFeedbackRating
from django.db.models import Avg
print(f'Cases: {Case.objects.count()}')
print(f'Reports: {Report.objects.count()}')
print(f'Users: {User.objects.count()}')
print(f'Ratings: {AIFeedbackRating.objects.count()}')
avg = AIFeedbackRating.objects.aggregate(Avg('star_rating'))['star_rating__avg']
print(f'Avg Rating: {avg:.2f}/5.00' if avg else 'No ratings')
"
```

### Deployment Status
```bash
# Check last deployment
git log -1

# Check GitHub Actions
# Visit: https://github.com/straus91/global-peds-reading-room/actions

# Check services on droplet
ssh root@64.225.17.0 "sudo systemctl status gunicorn nginx postgresql"
```

---

## 💡 PRODUCTIVITY TIPS

### For Claude Code Sessions

1. **Always start with SESSION_ENTRY_POINT.md** (5 min investment, 30 min saved)
2. **Update PROGRESS_TRACKER.md after EACH task** (not at end of session)
3. **Read .claude/docs/ files BEFORE coding** (prevents mistakes)
4. **Search for existing patterns** (don't reinvent the wheel)
5. **Complete session handoff checklist** (next session will thank you)

### For Debugging

1. **Check DEPLOYMENT_LOG.md first** (similar issue may have been solved)
2. **Search frontend/backend code for examples** (copy working patterns)
3. **Use git blame to understand why** (code history has context)
4. **Test in isolation** (isolate the problem)
5. **Document the fix** (help future sessions)

### For New Features

1. **Complete risk assessment FIRST** (saves time later)
2. **Check if it's in ROADMAP.md** (may already be planned)
3. **Write tests first** (test-driven development)
4. **Implement incrementally** (one piece at a time)
5. **Update docs as you go** (don't batch at end)

---

## 🔗 QUICK LINKS

| Need | Document |
|------|----------|
| Where to start | SESSION_ENTRY_POINT.md |
| What's next | PROGRESS_TRACKER.md |
| How to make API call | .claude/docs/FRONTEND_API_PATTERNS.md |
| How to deploy | .claude/docs/DEPLOYMENT.md |
| How to migrate database | .claude/docs/WORKFLOWS.md |
| Past mistakes | DEPLOYMENT_LOG.md |
| Server details | DEPLOYMENT_STATUS.md |
| Risk assessment | .claude/docs/RISK_ASSESSMENT.md |
| Model details | .claude/docs/DATA_MODELS.md |

---

## 📞 WHEN YOU'RE STUCK

1. **Read SESSION_ENTRY_POINT.md "Known Pitfalls"** - Your issue may be documented
2. **Search DEPLOYMENT_LOG.md** - Similar issue may have been solved before
3. **Read relevant .claude/docs/ file** - Detailed guidance available
4. **Search codebase for examples** - `grep -r "pattern" frontend/js`
5. **Check git history** - `git log --all --grep="keyword"`

**Remember**: The answer is usually in the documentation. Read first, code second!

---

**Last Updated**: 2025-10-14
**Next Review**: When new common tasks emerge
**Maintained By**: Claude Code + Human Developer
