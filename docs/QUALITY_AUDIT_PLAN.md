# 🔍 Comprehensive Quality Audit Plan

**Project**: Global Peds Reading Room
**Purpose**: Systematic quality improvement across code, security, testing, performance, and documentation
**Last Updated**: 2025-10-11

> A phased approach to achieving production-grade code quality, comprehensive test coverage, and robust security.

---

## 📊 Current State Assessment

### ✅ Strengths
- **Well-organized architecture**: Clean Django backend + vanilla JS frontend
- **Excellent documentation**: Comprehensive guides created (BETA_DEPLOYMENT.md, etc.)
- **Good model design**: Well-documented models with help text
- **Security awareness**: Input sanitization, rate limiting implemented

### ❌ Critical Gaps
- **NO automated testing**: Empty test files in cases/, users/, api/
- **NO code quality tools**: No linters, formatters, or quality checks
- **NO CI/CD**: No automated quality gates
- **requirements.txt formatting**: Unusual character spacing issues
- **NO frontend testing**: No test framework for JavaScript

### ⚠️ Moderate Gaps
- **Limited docstrings**: Many functions lack documentation
- **No performance profiling**: No baseline metrics
- **No pre-commit hooks**: Manual quality checks only

---

## 🎯 Quality Goals

| Area | Current | Target | Priority |
|------|---------|--------|----------|
| **Test Coverage** | 0% | 80%+ | 🔴 Critical |
| **Code Quality (Python)** | Unknown | Flake8 < 10 issues | 🔴 Critical |
| **Code Quality (JS)** | Unknown | ESLint 0 errors | 🟡 High |
| **Security Vulnerabilities** | Unknown | 0 high/critical | 🔴 Critical |
| **Documentation** | Good | Excellent | 🟢 Medium |
| **Performance** | Unknown | < 500ms API responses | 🟡 High |

---

## 🔗 Integration Requirements

**IMPORTANT**: This quality audit integrates with your existing workflows to ensure data-driven, safe improvements.

### Before Starting

Ensure these are set up:

- [ ] **MONITORING_SETUP.md** - Monitoring scripts installed on beta droplet
- [ ] **AI_ITERATION_WORKFLOW.md** - Baseline tracking scripts configured (`track_ai_baseline.py`)
- [ ] **BETA_DEPLOYMENT.md** - Understand deployment workflow to beta
- [ ] **.claude/docs/RISK_ASSESSMENT.md** - Risk assessment framework reviewed
- [ ] **BETA_BEST_PRACTICES.md** - Safety-first principles internalized

### For Each Phase

- [ ] Complete risk assessment (use RISK_ASSESSMENT.md template)
- [ ] Deploy fixes to **beta first** (never directly to production)
- [ ] Monitor AI quality for 24-48h (no degradation allowed)
- [ ] Validate no user-facing regressions
- [ ] Document results before proceeding

### 🚨 Red Flags (STOP Immediately)

If any of these occur during quality improvements:

- 🚨 **AI average rating drops > 0.2 points** (check `scripts/monitor_metrics.py`)
- 🚨 **Error rate increases > 2%** (check logs: `/var/log/gunicorn/gunicorn.log`)
- 🚨 **User reports/day drops > 20%** (check engagement metrics)
- 🚨 **API response time increases > 50%** (performance degradation)

**Action**: Immediately rollback changes, investigate root cause, revise approach.

---

## 📋 Phase 0: Baseline Metrics Collection

**Timeline**: 1 day (MUST DO FIRST)
**Priority**: 🔴 Critical

### Purpose

Establish **current state metrics** before making any quality improvements. This enables:
- Validation that quality improvements don't break AI feedback
- Detection of user-facing regressions
- Data-driven decision making
- Rollback criteria

### Step 0.1: Collect AI Feedback Quality Baseline

**On beta droplet**:

```bash
ssh root@64.225.17.0
cd /home/deploy/global-peds-reading-room

# Activate environment
source backend/venv/bin/activate

# Track current AI quality
python scripts/track_ai_baseline.py "Before quality audit - baseline"

# Run comprehensive metrics
python scripts/monitor_metrics.py > reports/baseline_metrics_$(date +%Y%m%d).txt
```

**Save results**:
```bash
cat reports/baseline_metrics_*.txt
# Document: Average rating, total ratings, distribution
```

### Step 0.2: Collect User Engagement Baseline

**In Django shell** (on beta):

```python
from cases.models import Report, UserCaseView
from django.contrib.auth import get_user_model
from datetime import timedelta
from django.utils import timezone

User = get_user_model()
last_7_days = timezone.now() - timedelta(days=7)

# User engagement
active_users = User.objects.filter(
    reports__submitted_at__gte=last_7_days
).distinct().count()

reports_submitted = Report.objects.filter(
    submitted_at__gte=last_7_days
).count()

case_views = UserCaseView.objects.filter(
    timestamp__gte=last_7_days
).count()

print(f"Baseline User Engagement:")
print(f"  Active Users: {active_users}")
print(f"  Reports Submitted: {reports_submitted}")
print(f"  Case Views: {case_views}")
print(f"  Reports per Active User: {reports_submitted/active_users if active_users > 0 else 0:.1f}")
```

**Document results** in `reports/baseline_user_engagement.txt`

### Step 0.3: Collect System Performance Baseline

**Check API response times**:

```bash
# From local machine, test API
time curl -H "Authorization: Bearer <token>" http://64.225.17.0/api/cases/

# Or from droplet
cd /home/deploy/global-peds-reading-room
time curl http://localhost:8001/api/cases/
```

**Check error rates**:

```bash
# Recent errors (last 1000 lines)
tail -1000 /var/log/gunicorn/gunicorn.log | grep -i error | wc -l

# Total requests (last 1000 lines)
tail -1000 /var/log/gunicorn/gunicorn.log | wc -l

# Calculate error rate
# Error rate = (error lines / total lines) * 100
```

### Step 0.4: Initial Code Quality Scan

**Run quick scans** (before installing tools):

```bash
cd /mnt/c/Users/strau/Desktop/gr4-gemini/backend

# Check for obvious issues
find . -name "*.py" -not -path "./venv/*" -not -path "./migrations/*" | xargs wc -l

# Count TODO/FIXME comments
grep -r "TODO\|FIXME" --include="*.py" --exclude-dir=venv --exclude-dir=migrations | wc -l
```

### Step 0.5: Create Baseline Report

**Create** `reports/BASELINE_REPORT.md`:

```markdown
# Quality Audit Baseline Report

**Date**: 2025-10-XX
**Server**: global-readingroom (64.225.17.0)

## AI Feedback Quality
- Average Rating: X.XX / 5.00
- Total Ratings (30 days): XX
- Distribution: 5★: X%, 4★: X%, 3★: X%, 2★: X%, 1★: X%
- Low-Rated (≤2): X

## User Engagement (Last 7 Days)
- Active Users: XX
- Reports Submitted: XX
- Case Views: XX
- Reports per Active User: X.X

## System Performance
- API Response Time: ~XXXms
- Error Rate: X.XX%
- Database Size: XXGB

## Code Quality (Initial Assessment)
- Total Python Lines: XXXXX
- TODO/FIXME Count: XX
- Empty Test Files: Yes (cases/, users/, api/)
- requirements.txt Status: Formatting issues detected

## Notes
- [Any observations about current state]
- [Known issues to track]
```

### Phase 0 Deliverables

- [ ] `reports/BASELINE_REPORT.md` - Complete baseline documentation
- [ ] `ai_baseline_history.json` - AI quality tracked
- [ ] `reports/baseline_metrics_YYYYMMDD.txt` - Full metrics dump
- [ ] Baseline documented in change log

**⚠️ STOP**: Do not proceed to Phase 1 until baseline is documented and reviewed!

---

## 📋 Phase 1: Python Code Quality Audit

**Timeline**: 2 days
**Priority**: 🔴 Critical

### Tools to Install

```bash
pip install flake8 pylint black isort bandit
```

### 1.1 Flake8 (Style & Basic Linting)

**Purpose**: PEP 8 compliance, unused imports, code complexity

**Run**:
```bash
cd backend
flake8 . --exclude=venv,migrations --max-line-length=120 --count --statistics
```

**Creates**: Report of style violations

**Configuration** (`.flake8`):
```ini
[flake8]
max-line-length = 120
exclude = venv,migrations,__pycache__,.git
ignore = E203,W503  # Black compatibility
max-complexity = 10
```

### 1.2 Pylint (Comprehensive Linting)

**Purpose**: Deep code analysis, potential bugs, code smells

**Run**:
```bash
cd backend
pylint cases users api globalpeds_project --ignore=migrations,venv
```

**Creates**: Detailed quality report with score (0-10)

**Configuration** (`.pylintrc`):
```ini
[MASTER]
ignore=migrations,venv

[MESSAGES CONTROL]
disable=C0111,R0903,C0103

[FORMAT]
max-line-length=120

[DESIGN]
max-args=7
max-attributes=12
```

### 1.3 Black (Auto-Formatter)

**Purpose**: Consistent code formatting

**Run** (check only):
```bash
cd backend
black --check . --exclude venv
```

**Run** (auto-format):
```bash
cd backend
black . --exclude venv
```

**Configuration** (`pyproject.toml`):
```toml
[tool.black]
line-length = 120
target-version = ['py38']
exclude = '''
/(
    \.git
  | \.venv
  | venv
  | migrations
)/
'''
```

### 1.4 isort (Import Organizer)

**Purpose**: Sort and organize imports

**Run**:
```bash
cd backend
isort . --check-only --skip venv --skip migrations
```

**Configuration** (`pyproject.toml`):
```toml
[tool.isort]
profile = "black"
line_length = 120
skip = ["venv", "migrations"]
```

### 1.5 Bandit (Security Linter)

**Purpose**: Scan for common security issues

**Run**:
```bash
cd backend
bandit -r . -x venv,migrations
```

**Creates**: Security vulnerability report

### Phase 1 Deliverables

- [ ] `reports/python_quality_report.md` - Consolidated findings
- [ ] `.flake8` configuration
- [ ] `.pylintrc` configuration
- [ ] `pyproject.toml` with Black/isort config
- [ ] List of issues to fix (categorized by priority)

### Phase 1: Beta Testing & Validation

**After implementing code quality fixes, BEFORE proceeding to Phase 2**:

#### Step 1: Risk Assessment

Complete `.claude/docs/RISK_ASSESSMENT.md` template:

```markdown
## RISK ASSESSMENT: Phase 1 Code Quality Fixes

### Direct Impact
- Files modified: [list all Python files changed]
- Breaking changes: [Yes/No - describe]
- Dependencies updated: [Yes/No - which ones]

### Cascading Effects
- AI feedback affected: [Could formatting changes affect prompts?]
- User-facing changes: [Any API response changes?]
- Performance impact: [Code changes affect query performance?]

### Risk Level: [🟢 LOW / 🟡 MEDIUM / 🔴 HIGH]

### Mitigation Plan:
1. Deploy to beta first
2. Monitor AI quality for 48h
3. Check error logs for new issues
4. Rollback plan: git revert <commit-hash>
```

#### Step 2: Deploy to Beta

Follow **BETA_DEPLOYMENT.md**:

```bash
# LOCAL: Commit and push
git add -A
git commit -m "Phase 1: Python code quality fixes - Flake8/Pylint/Black/isort"
git push origin online_beta

# DROPLET: Deploy
ssh root@64.225.17.0
cd /home/deploy/global-peds-reading-room
git pull origin online_beta
source backend/venv/bin/activate
python backend/manage.py check  # Verify no errors
sudo systemctl restart gunicorn

# Monitor immediately
tail -f /var/log/gunicorn/gunicorn.log
# Watch for 5-10 minutes for errors
```

#### Step 3: Validate No Regressions (24-48h)

**Day 1 After Deployment**:

```bash
ssh root@64.225.17.0
cd /home/deploy/global-peds-reading-room
source backend/venv/bin/activate

# Check AI quality hasn't degraded
python scripts/monitor_metrics.py

# Compare to baseline
python scripts/track_ai_baseline.py "After Phase 1 quality fixes"

# Check for errors
tail -500 /var/log/gunicorn/gunicorn.log | grep -i error
```

**Expected Results**:
- ✅ AI average rating: No decrease (within 0.1 points of baseline)
- ✅ Error rate: No increase (should remain < 1%)
- ✅ User activity: Stable (reports/day within 20% of baseline)

**Day 2 Validation**:

```python
# Django shell - compare engagement
from cases.models import Report, AIFeedbackRating
from datetime import timedelta
from django.utils import timezone
from django.db.models import Avg

last_48h = timezone.now() - timedelta(hours=48)

# Recent AI ratings
recent_avg = AIFeedbackRating.objects.filter(
    rated_at__gte=last_48h
).aggregate(Avg('star_rating'))['star_rating__avg']

print(f"AI Rating (last 48h): {recent_avg:.2f}")
print(f"Baseline: [from Phase 0]")
print(f"Change: {recent_avg - baseline:.2f}")

# Recent reports
recent_reports = Report.objects.filter(
    submitted_at__gte=last_48h
).count()

print(f"Reports (last 48h): {recent_reports}")
```

#### Step 4: Go/No-Go Decision

**✅ PROCEED to Phase 2 IF**:
- AI rating within 0.1 points of baseline
- Error rate unchanged or improved
- No user complaints
- All services stable

**❌ ROLLBACK IF**:
- AI rating drops > 0.2 points
- Error rate increases > 2%
- User activity drops > 20%
- Critical errors in logs

**Rollback Procedure**:

```bash
ssh root@64.225.17.0
cd /home/deploy/global-peds-reading-room
git log --oneline -5  # Find commit before Phase 1
git revert <commit-hash>
sudo systemctl restart gunicorn
tail -f /var/log/gunicorn/gunicorn.log  # Verify stability
```

#### Step 5: Document Results

Update `reports/PHASE_1_VALIDATION.md`:

```markdown
# Phase 1 Validation Results

**Date**: 2025-10-XX
**Duration**: 48 hours monitoring

## Metrics Comparison

| Metric | Baseline | After Phase 1 | Change | Status |
|--------|----------|---------------|--------|--------|
| AI Rating | X.XX | X.XX | ±X.XX | ✅/❌ |
| Reports/Day | XX | XX | ±XX% | ✅/❌ |
| Error Rate | X.X% | X.X% | ±X.X% | ✅/❌ |
| API Response | XXXms | XXXms | ±XXms | ✅/❌ |

## Decision: ✅ PROCEED / ❌ ROLLBACK

## Notes:
- [Any observations]
- [Issues encountered]
- [Recommendations for next phase]
```

**⚠️ CRITICAL**: Do NOT proceed to Phase 2 until validation is complete and documented!

---

## 📋 Phase 2: JavaScript Code Quality Audit

**Timeline**: 1 day
**Priority**: 🟡 High

### Tools to Install

```bash
# If using npm (create package.json first)
npm install --save-dev eslint prettier eslint-config-prettier
npx eslint --init
```

### 2.1 ESLint (JavaScript Linter)

**Purpose**: Detect errors, enforce code style

**Configuration** (`.eslintrc.json`):
```json
{
  "env": {
    "browser": true,
    "es2021": true
  },
  "extends": ["eslint:recommended", "prettier"],
  "parserOptions": {
    "ecmaVersion": 12,
    "sourceType": "module"
  },
  "rules": {
    "no-unused-vars": "warn",
    "no-console": "off",
    "semi": ["error", "always"]
  }
}
```

**Run**:
```bash
cd frontend
npx eslint js/ --ext .js
```

### 2.2 Prettier (Code Formatter)

**Configuration** (`.prettierrc`):
```json
{
  "semi": true,
  "trailingComma": "es5",
  "singleQuote": true,
  "printWidth": 100,
  "tabWidth": 2
}
```

**Run** (check):
```bash
npx prettier --check "js/**/*.js"
```

**Run** (format):
```bash
npx prettier --write "js/**/*.js"
```

### Phase 2 Deliverables

- [ ] `reports/javascript_quality_report.md`
- [ ] `.eslintrc.json` configuration
- [ ] `.prettierrc` configuration
- [ ] `package.json` with dev dependencies
- [ ] List of JS issues to fix

---

## 📋 Phase 3: Testing Infrastructure

**Timeline**: 4-5 days
**Priority**: 🔴 Critical

### 3.1 Backend Testing Setup

**Install**:
```bash
pip install pytest pytest-django pytest-cov factory-boy
```

**Configuration** (`pytest.ini`):
```ini
[pytest]
DJANGO_SETTINGS_MODULE = globalpeds_project.settings
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = --cov=. --cov-report=html --cov-report=term
```

### 3.2 Test Structure

```
backend/
├── cases/
│   └── tests/
│       ├── __init__.py
│       ├── test_models.py         # Model tests
│       ├── test_views.py          # API endpoint tests
│       ├── test_serializers.py    # Serializer tests
│       ├── test_utils.py          # Utility function tests
│       ├── test_llm_service.py    # AI service tests
│       └── factories.py           # Test data factories
├── users/
│   └── tests/
│       ├── test_models.py
│       ├── test_views.py
│       └── test_auth.py
└── conftest.py                    # Shared fixtures
```

### 3.3 Critical Tests to Write

**Model Tests** (cases/tests/test_models.py):
```python
# Test case identifier generation
# Test report versioning (is_archived)
# Test cascading deletes
# Test model relationships
# Test field validation
```

**View Tests** (cases/tests/test_views.py):
```python
# Test authentication required
# Test CRUD operations
# Test AI feedback generation (mocked)
# Test permissions
# Test error handling
```

**Utils Tests** (cases/tests/test_utils.py):
```python
# Test report comparison logic
# Test sanitization functions
# Test key concept matching
```

**LLM Service Tests** (cases/tests/test_llm_service.py):
```python
# Test rate limiting
# Test prompt injection prevention
# Test API error handling (mocked)
# Test response parsing
```

### 3.4 Frontend Testing Setup

**Option A: Jest** (Recommended)
```bash
npm install --save-dev jest @testing-library/jest-dom
```

**Option B: Mocha + Chai**
```bash
npm install --save-dev mocha chai
```

**Tests to Write**:
- API client functions (api.js)
- Authentication logic (auth.js)
- Form validation
- Error handling

### Phase 3 Deliverables

- [ ] Complete backend test suite (80%+ coverage)
- [ ] Frontend test setup and critical tests
- [ ] `reports/test_coverage_report.html`
- [ ] Testing documentation in `.claude/docs/TESTING.md` (update)
- [ ] Test running in CI/CD

**Coverage Targets**:
- Models: 90%+
- Views: 85%+
- Utils: 90%+
- Overall: 80%+

---

## 📋 Phase 4: Security Audit

**Timeline**: 2 days
**Priority**: 🔴 Critical

### 4.1 Automated Security Scans

**Safety** (Python dependency vulnerabilities):
```bash
pip install safety
safety check
```

**pip-audit** (Alternative):
```bash
pip install pip-audit
pip-audit
```

**Bandit** (Already covered in Phase 1):
```bash
bandit -r backend -x venv,migrations -f json -o reports/security_scan.json
```

**npm audit** (If package.json exists):
```bash
cd frontend
npm audit
```

**git-secrets** (Prevent committing secrets):
```bash
# Install git-secrets
brew install git-secrets  # macOS
# or download from GitHub

# Setup
cd /path/to/repo
git secrets --install
git secrets --register-aws
git secrets --add 'GEMINI_API_KEY.*'
git secrets --add 'SECRET_KEY.*'

# Scan
git secrets --scan
```

### 4.2 Manual Security Checklist

**Environment Variables**:
- [ ] `.env` in `.gitignore` ✅
- [ ] No secrets hardcoded in code
- [ ] `.env.example` has no real secrets
- [ ] Production uses different secrets than dev

**Input Validation**:
- [ ] LLM prompt sanitization (check llm_feedback_service.py)
- [ ] SQL injection prevention (using ORM) ✅
- [ ] XSS prevention (Django templates escape by default) ✅
- [ ] File upload validation (if applicable)
- [ ] JSON input validation

**Authentication & Authorization**:
- [ ] JWT tokens properly secured
- [ ] Password requirements enforced
- [ ] Session timeout configured
- [ ] CORS correctly configured ✅
- [ ] Permission classes on all views

**Database**:
- [ ] Database user not superuser (check deployment)
- [ ] Connection uses SSL in production
- [ ] Backups encrypted (check beta setup)
- [ ] No raw SQL without parameterization

**Django Settings** (Production):
- [ ] `DEBUG = False`
- [ ] `SECRET_KEY` strong and unique
- [ ] `ALLOWED_HOSTS` restrictive
- [ ] `SECURE_SSL_REDIRECT = True`
- [ ] `SESSION_COOKIE_SECURE = True`
- [ ] `CSRF_COOKIE_SECURE = True`
- [ ] `SECURE_HSTS_SECONDS` set

**API Security**:
- [ ] Rate limiting on AI endpoints ✅
- [ ] Rate limiting on auth endpoints
- [ ] API versioning strategy
- [ ] Error messages don't leak info

### Phase 4 Deliverables

- [ ] `reports/SECURITY_AUDIT_REPORT.md`
- [ ] Vulnerability list with severity ratings
- [ ] Remediation plan with timeline
- [ ] Updated security documentation
- [ ] git-secrets configured

---

## 📋 Phase 5: Performance Analysis

**Timeline**: 2 days
**Priority**: 🟡 High

### 5.1 Database Query Analysis

**Install Django Debug Toolbar** (Development):
```bash
pip install django-debug-toolbar
```

**Configuration** (settings.py):
```python
if DEBUG:
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
    INTERNAL_IPS = ['127.0.0.1']
```

**Check for N+1 Queries**:
- Review Case list views
- Review Report detail views
- Ensure `select_related()` and `prefetch_related()` used

**Install django-silk** (Profiling):
```bash
pip install django-silk
```

### 5.2 API Response Time Benchmarks

**Create benchmark script**:
```bash
# Simple curl timing
time curl http://localhost:8000/api/cases/

# Or use Apache Bench
ab -n 100 -c 10 http://localhost:8000/api/cases/
```

**Targets**:
- Case list: < 300ms
- Case detail: < 400ms
- Report submission: < 500ms
- AI feedback: < 10s (depends on LLM)

### 5.3 LLM API Usage Analysis

**Check**:
- Current rate limiting settings
- Average tokens per request
- Cost per feedback
- Cache hit rate (if implemented)

**Track** (using monitoring from MONITORING_SETUP.md):
```python
# Token usage by case difficulty
# API calls per hour
# Failed requests
# Rate limit hits
```

### 5.4 Frontend Performance

**Tools**:
- Chrome DevTools (Lighthouse)
- Network tab analysis
- Bundle size analysis

**Metrics**:
- Page load time
- Time to Interactive
- Largest Contentful Paint
- JavaScript bundle size

### Phase 5 Deliverables

- [ ] `reports/PERFORMANCE_REPORT.md`
- [ ] Database query optimization recommendations
- [ ] API endpoint benchmarks
- [ ] LLM usage analysis
- [ ] Frontend performance report
- [ ] Optimization priority list

---

## 📋 Phase 6: Documentation Quality

**Timeline**: 1 day
**Priority**: 🟢 Medium

### 6.1 Code Documentation Audit

**Checks**:
- [ ] Docstrings for all public functions
- [ ] Docstrings for all classes
- [ ] Complex logic has inline comments
- [ ] API endpoints documented
- [ ] Model fields have help_text ✅ (already good!)

**Generate Missing Docstrings Report**:
```bash
# Check for missing docstrings
pylint backend --disable=all --enable=missing-docstring
```

### 6.2 Documentation Consistency

**Verify**:
- [ ] README.md accuracy ✅
- [ ] API documentation matches code
- [ ] Environment variable docs complete ✅
- [ ] Deployment docs current ✅
- [ ] All .md files have "Last Updated" dates

### Phase 6 Deliverables

- [ ] `reports/documentation_audit.md`
- [ ] List of functions needing docstrings
- [ ] Documentation improvement plan

---

## 📋 Phase 7: Configuration Validation

**Timeline**: 1 day
**Priority**: 🔴 Critical

### 7.1 Critical Fixes

**Fix requirements.txt** (currently has spacing issues):
```bash
# Current format has spaces: a n n o t a t e d - t y p e s
# Should be: annotated-types==0.7.0

# Regenerate clean requirements.txt:
pip freeze > requirements_new.txt
# Review and replace
```

### 7.2 .gitignore Completeness

**Verify excluded**:
- [ ] `.env` ✅
- [ ] `venv/` ✅
- [ ] `__pycache__/` ✅
- [ ] `*.pyc` ✅
- [ ] `db.sqlite3` ✅
- [ ] `media/` ✅
- [ ] `.coverage`
- [ ] `htmlcov/`
- [ ] `node_modules/` (if added)
- [ ] `.pytest_cache/`
- [ ] `*.log` ✅

### 7.3 .env.example Validation

**Ensure includes** (check against .claude/docs/ENVIRONMENT.md):
- [ ] All required variables
- [ ] Example values (not real secrets)
- [ ] Comments explaining each variable
- [ ] Grouped logically

### 7.4 Django Settings Review

**Development vs Production**:
```python
# settings.py should have environment-specific configs
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

# Check all critical settings documented
```

### Phase 7 Deliverables

- [ ] Fixed `requirements.txt`
- [ ] Updated `.gitignore`
- [ ] Validated `.env.example`
- [ ] `reports/configuration_audit.md`
- [ ] Settings checklist for production

---

## 📋 Phase 8: Database Integrity Check

**Timeline**: 1 day
**Priority**: 🟡 High

### 8.1 Migration Consistency

**Check**:
```bash
cd backend
python manage.py showmigrations
python manage.py migrate --plan
```

**Verify**:
- [ ] No conflicting migrations
- [ ] All migrations applied
- [ ] Migrations are reversible
- [ ] Data migrations documented

### 8.2 Model Relationships

**Review** (using .claude/docs/DATA_MODELS.md):
- [ ] Cascade behaviors correct
- [ ] No orphaned records possible
- [ ] Foreign keys have proper on_delete
- [ ] Many-to-many relationships documented

### 8.3 Database Indexes

**Check for missing indexes**:
```python
# Fields that should have indexes:
# - case_identifier (Case)
# - status (Case)
# - is_archived (Report)
# - submitted_at (Report)
```

**Add indexes** (if missing):
```python
class Meta:
    indexes = [
        models.Index(fields=['case_identifier']),
        models.Index(fields=['status']),
    ]
```

### 8.4 Data Integrity Constraints

**Verify**:
- [ ] Unique constraints enforced
- [ ] Required fields not null (unless intentional)
- [ ] Choice fields have valid choices
- [ ] Date fields have proper defaults

### Phase 8 Deliverables

- [ ] `reports/database_health_report.md`
- [ ] Missing index recommendations
- [ ] Migration documentation
- [ ] Data integrity improvements

---

## 📋 Phase 9: Dependency Audit

**Timeline**: 1 day
**Priority**: 🟡 High

### 9.1 Outdated Packages

**Check**:
```bash
pip list --outdated
```

**Categorize**:
- Critical security updates
- Major version upgrades (breaking changes)
- Minor/patch updates (safe)

### 9.2 Security Vulnerabilities

**Run** (from Phase 4):
```bash
safety check
pip-audit
```

### 9.3 Unused Dependencies

**Analyze**:
```bash
pip install pipdeptree
pipdeptree --warn
```

**Find unused**:
```bash
# Compare requirements.txt with actual imports
# (manual review or use tools like pipreqs)
```

### 9.4 License Compatibility

**Check licenses**:
```bash
pip install pip-licenses
pip-licenses
```

**Verify** no incompatible licenses for your use case

### 9.5 Version Pinning Strategy

**Current**: Exact versions (good!)
```
Django==5.2
```

**Recommendation**: Keep exact pinning for reproducibility

### Phase 9 Deliverables

- [ ] `reports/DEPENDENCY_AUDIT.md`
- [ ] Update recommendations (prioritized)
- [ ] Cleanup plan for unused packages
- [ ] License compatibility report

---

## 📋 Phase 10: Pre-Commit Hooks & CI/CD

**Timeline**: 1 day
**Priority**: 🟡 High

### 10.1 Pre-Commit Hooks Setup

**Install**:
```bash
pip install pre-commit
```

**Configuration** (`.pre-commit-config.yaml`):
```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-merge-conflict

  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
        exclude: migrations/

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        exclude: migrations/
        args: ['--max-line-length=120']

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        exclude: migrations/

  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.5
    hooks:
      - id: bandit
        exclude: migrations/
        args: ['-ll']
```

**Install hooks**:
```bash
pre-commit install
```

**Test**:
```bash
pre-commit run --all-files
```

### 10.2 GitHub Actions CI/CD

**Create** `.github/workflows/quality-checks.yml`:
```yaml
name: Quality Checks

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
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'

    - name: Install dependencies
      run: |
        cd backend
        pip install -r requirements.txt
        pip install pytest pytest-django pytest-cov flake8

    - name: Run Flake8
      run: |
        cd backend
        flake8 . --exclude=venv,migrations --max-line-length=120

    - name: Run Tests
      env:
        SECRET_KEY: test-secret-key
        DEBUG: 'False'
        DB_NAME: test_db
        DB_USER: postgres
        DB_PASSWORD: postgres
        DB_HOST: localhost
        DB_PORT: 5432
        GEMINI_API_KEY: test-key
      run: |
        cd backend
        pytest --cov=. --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

### Phase 10 Deliverables

- [ ] `.pre-commit-config.yaml` configured
- [ ] Pre-commit hooks installed
- [ ] `.github/workflows/quality-checks.yml` created
- [ ] CI/CD pipeline running on push
- [ ] Quality gates enforced

---

## 📋 Phase 11: Post-Audit Validation & Decision

**Timeline**: 3-7 days (data collection period)
**Priority**: 🔴 Critical

### Purpose

**Final validation** that all quality improvements have not degraded:
- AI feedback quality
- User engagement
- System performance
- User experience

This phase determines **Go/No-Go for production deployment**.

### Step 11.1: Collect Post-Audit Metrics

**Run all baseline scripts again**:

```bash
ssh root@64.225.17.0
cd /home/deploy/global-peds-reading-room
source backend/venv/bin/activate

# AI quality
python scripts/monitor_metrics.py > reports/post_audit_metrics_$(date +%Y%m%d).txt
python scripts/track_ai_baseline.py "After complete quality audit"

# System health
scripts/monitor_database.sh > reports/post_audit_database.txt
```

**Check error logs** (last 7 days):

```bash
# Count errors
tail -10000 /var/log/gunicorn/gunicorn.log | grep -i error | wc -l

# Review error types
tail -10000 /var/log/gunicorn/gunicorn.log | grep -i error | cut -d' ' -f5- | sort | uniq -c | sort -rn
```

### Step 11.2: Compare Before/After Metrics

**Create comparison table** in Django shell:

```python
# Load baseline and current metrics
import json

# Load AI baseline history
with open('/home/deploy/global-peds-reading-room/ai_baseline_history.json', 'r') as f:
    history = json.load(f)

# Find baseline (first entry) and current (last entry)
baseline = history[0]  # "Before quality audit - baseline"
current = history[-1]   # "After complete quality audit"

print("=" * 60)
print("QUALITY AUDIT IMPACT ANALYSIS")
print("=" * 60)

print(f"\n📊 AI FEEDBACK QUALITY")
print(f"  Baseline: {baseline['avg_rating']:.2f}/5.00 ({baseline['total_ratings']} ratings)")
print(f"  Current:  {current['avg_rating']:.2f}/5.00 ({current['total_ratings']} ratings)")

change = current['avg_rating'] - baseline['avg_rating']
percent_change = (change / baseline['avg_rating']) * 100
print(f"  Change: {change:+.2f} ({percent_change:+.1f}%)")

if abs(change) < 0.1:
    print("  Status: ✅ STABLE (within acceptable range)")
elif change > 0:
    print(f"  Status: ✅ IMPROVED by {change:.2f} points!")
else:
    print(f"  Status: ⚠️ DEGRADED by {abs(change):.2f} points - INVESTIGATE")
```

**User engagement comparison**:

```python
from cases.models import Report, UserCaseView
from django.contrib.auth import get_user_model
from datetime import timedelta, datetime
from django.utils import timezone

User = get_user_model()

# Define baseline period (before audit started)
baseline_start = datetime(2025, 10, 1)  # UPDATE to actual start
baseline_end = datetime(2025, 10, 11)   # Day audit started

# Define current period (last 7 days)
current_end = timezone.now()
current_start = current_end - timedelta(days=7)

# Baseline engagement
baseline_users = User.objects.filter(
    reports__submitted_at__range=(baseline_start, baseline_end)
).distinct().count()

baseline_reports = Report.objects.filter(
    submitted_at__range=(baseline_start, baseline_end)
).count()

# Current engagement
current_users = User.objects.filter(
    reports__submitted_at__range=(current_start, current_end)
).distinct().count()

current_reports = Report.objects.filter(
    submitted_at__range=(current_start, current_end)
).count()

print(f"\n👥 USER ENGAGEMENT")
print(f"  Baseline Period: {baseline_start.date()} to {baseline_end.date()}")
print(f"    Active Users: {baseline_users}")
print(f"    Reports: {baseline_reports}")
print(f"    Reports/User: {baseline_reports/baseline_users if baseline_users > 0 else 0:.1f}")

print(f"  Current Period: {current_start.date()} to {current_end.date()}")
print(f"    Active Users: {current_users}")
print(f"    Reports: {current_reports}")
print(f"    Reports/User: {current_reports/current_users if current_users > 0 else 0:.1f}")

user_change = ((current_users - baseline_users) / baseline_users * 100) if baseline_users > 0 else 0
report_change = ((current_reports - baseline_reports) / baseline_reports * 100) if baseline_reports > 0 else 0

print(f"  Changes:")
print(f"    Users: {user_change:+.1f}%")
print(f"    Reports: {report_change:+.1f}%")

if abs(report_change) <= 20:
    print("  Status: ✅ STABLE")
elif report_change > 0:
    print("  Status: ✅ IMPROVED")
else:
    print("  Status: ⚠️ DECREASED - INVESTIGATE")
```

### Step 11.3: Create Final Validation Report

**Create** `reports/QUALITY_AUDIT_IMPACT_REPORT.md`:

```markdown
# Quality Audit Impact Report

**Audit Period**: [Start Date] to [End Date]
**Validation Period**: Last 7 days
**Server**: global-readingroom (64.225.17.0)

## Executive Summary

[2-3 sentences: Did quality audit achieve goals without regressions?]

## Metrics Comparison

| Metric Category | Baseline | Post-Audit | Change | Status | Notes |
|----------------|----------|------------|--------|--------|-------|
| **AI Feedback Quality** |
| Average Rating | X.XX | X.XX | ±X.XX | ✅/⚠️/❌ | [Notes] |
| Total Ratings | XX | XX | ±XX | ✅/⚠️/❌ | |
| Low-Rated (≤2) | X | X | ±X | ✅/⚠️/❌ | |
| **User Engagement** |
| Active Users | XX | XX | ±XX% | ✅/⚠️/❌ | |
| Reports Submitted | XX | XX | ±XX% | ✅/⚠️/❌ | |
| Reports/User | X.X | X.X | ±X.X | ✅/⚠️/❌ | |
| **System Performance** |
| API Response Time | XXXms | XXXms | ±XXms | ✅/⚠️/❌ | |
| Error Rate | X.X% | X.X% | ±X.X% | ✅/⚠️/❌ | |
| **Code Quality** |
| Flake8 Issues | XXX | XX | -XX | ✅ | Target: <10 |
| Pylint Score | X.X | X.X | +X.X | ✅ | Target: >8.0 |
| Test Coverage | 0% | XX% | +XX% | ✅/⚠️ | Target: >80% |

## Detailed Findings

### AI Feedback Quality
- [Analysis of rating changes]
- [Review of user comments]
- [Any patterns observed]

### User Engagement
- [Analysis of activity changes]
- [User behavior patterns]
- [Retention observations]

### System Performance
- [Performance improvements/regressions]
- [Database optimization results]
- [API response time analysis]

### Code Quality Achievements
- [Flake8/Pylint improvements]
- [Test coverage achieved]
- [Security vulnerabilities fixed]
- [Documentation improvements]

## Phases Completed

- ✅ Phase 0: Baseline Metrics Collection
- ✅ Phase 1: Python Code Quality Audit
- ✅ Phase 2: JavaScript Code Quality Audit
- ✅/❌ Phase 3: Testing Infrastructure (XX% coverage achieved)
- ✅/❌ Phase 4: Security Audit (X vulnerabilities fixed)
- [Continue for all phases...]

## Issues Identified

### Critical Issues (Must Fix Before Production)
1. [Issue description]
   - Impact: [Impact on users/system]
   - Mitigation: [How to fix]

### Non-Critical Issues (Address in Future Sprints)
1. [Issue description]

## Lessons Learned

### What Went Well
- [Success 1]
- [Success 2]

### Challenges Encountered
- [Challenge 1 and how it was resolved]
- [Challenge 2 and how it was resolved]

### Recommendations for Future Audits
- [Recommendation 1]
- [Recommendation 2]

## Go/No-Go Decision

### ✅ GO - Ready for Production IF:
- [ ] AI rating: No degradation (< 0.2 drop) ✅/❌
- [ ] User engagement: Stable or improved (within 20%) ✅/❌
- [ ] Error rate: No increase (< 2% change) ✅/❌
- [ ] All critical issues resolved ✅/❌
- [ ] Test coverage ≥ 50% (minimum) ✅/❌
- [ ] Security vulnerabilities fixed ✅/❌

### ❌ NO-GO - Additional Work Required IF:
- [ ] AI rating dropped > 0.2 points
- [ ] User activity dropped > 20%
- [ ] Critical security issues remain
- [ ] System unstable

## Final Decision

**Decision**: ✅ APPROVE FOR PRODUCTION / ⚠️ CONDITIONAL APPROVAL / ❌ NOT READY

**Conditions** (if conditional):
1. [Condition to be met]
2. [Condition to be met]

**Timeline to Production**: [Date] (if approved)

**Sign-off**:
- Technical Lead: ___________ Date: _______
- Project Manager: ___________ Date: _______

## Next Steps

### If Approved:
1. Merge `online_beta` to `main` branch
2. Schedule production deployment
3. Follow production deployment procedures
4. Monitor production for 7 days
5. Update project baseline metrics

### If Not Approved:
1. Address identified critical issues
2. Re-run affected phase validations
3. Repeat Phase 11 validation
4. Reassess Go/No-Go decision

## Appendices

- reports/BASELINE_REPORT.md
- reports/PHASE_1_VALIDATION.md
- reports/PHASE_3_test_coverage_report.html
- reports/SECURITY_AUDIT_REPORT.md
- ai_baseline_history.json
```

### Step 11.4: Go/No-Go Decision

**Decision Matrix**:

| Outcome | Criteria | Decision |
|---------|----------|----------|
| **All Green** | All metrics stable/improved, no critical issues | ✅ **APPROVE** - Proceed to production |
| **Mostly Green** | AI quality stable, minor issues identified | ⚠️ **CONDITIONAL** - Fix issues, then approve |
| **Mixed** | Some regressions but fixable | ⚠️ **ADDITIONAL WORK** - Address issues, re-validate |
| **Major Regressions** | AI quality degraded, user activity dropped | ❌ **NOT READY** - Rollback, investigate, redesign |

### Step 11.5: Production Deployment (If Approved)

**Only if Go decision**:

```bash
# 1. Merge to main
git checkout main
git merge online_beta
git push origin main

# 2. Tag release
git tag -a v1.0.0-quality-audit -m "Quality audit completed - production ready"
git push origin v1.0.0-quality-audit

# 3. Schedule production deployment
# Follow production deployment procedures
# (Outside scope of this beta-focused plan)

# 4. Update baselines
# Post-production baseline becomes new baseline for future improvements
```

### Phase 11 Deliverables

- [ ] `reports/QUALITY_AUDIT_IMPACT_REPORT.md` - Complete impact analysis
- [ ] Go/No-Go decision documented and approved
- [ ] All critical issues resolved (if conditional approval)
- [ ] Production deployment plan (if approved)
- [ ] Updated baseline metrics (for future audits)
- [ ] Lessons learned documented

**⚠️ CRITICAL**: This is the final gate before production. Do NOT proceed to production without completing Phase 11 validation and getting approval!

---

## 🚀 Execution Strategy

### **Option A: Quick Win** (1 week)

**Week 1**:
- Day 1-2: Phases 1-2 (Code quality audits - reports only)
- Day 3: Phase 4 (Security scan)
- Day 4: Phase 7 (Fix requirements.txt, validate configs)
- Day 5: Compile reports, prioritize critical fixes

**Deliverables**:
- All quality reports
- Critical security fixes
- Fixed requirements.txt
- Priority list for future work

**Best for**: Quick assessment before deployment

---

### **Option B: Foundation (RECOMMENDED)** (3 weeks with validation)

**Week 1: Assessment & Critical Fixes**:
- **Day 1**: Phase 0 - Baseline metrics collection ⚠️ MUST DO FIRST
- **Days 2-3**: Phases 1-2 - Code quality audits (reports only)
- **Day 4**: Phase 7 - Fix requirements.txt, validate configs
- **Day 5**: Deploy Phase 1-2 fixes to beta, begin monitoring

**Week 2: Security & Testing**:
- **Days 1-2**: Phase 4 - Security audit + critical fixes
- **Day 3**: Deploy security fixes to beta, validate (24-48h monitoring)
- **Days 4-5**: Phase 3 - Critical tests (models, auth, AI service)

**Week 3: Automation & Validation**:
- **Days 1-2**: Phase 10 - Pre-commit hooks, basic CI/CD
- **Day 3**: Deploy all improvements to beta
- **Days 4-7**: Phase 11 - Post-audit validation (data collection period)

**Deliverables**:
- ✅ Baseline and post-audit metrics documented
- ✅ Code quality improvements (Flake8/Pylint passing)
- ✅ Critical security vulnerabilities fixed
- ✅ Critical tests implemented (40-50% coverage)
- ✅ Pre-commit hooks automated
- ✅ All configuration validated
- ✅ **Data-driven Go/No-Go decision** for production

**Success Criteria**:
- AI quality: No degradation (< 0.2 drop)
- User engagement: Stable (within 20%)
- Error rate: No increase
- Test coverage: ≥ 40%

**Best for**: Data-driven preparation for production deployment with validation that improvements don't break anything

---

### **Option C: Comprehensive** (4 weeks with validation)

**Week 1**: Baseline & Audits
- **Day 1**: Phase 0 - Baseline metrics ⚠️ MUST DO FIRST
- **Days 2-3**: Phases 1-2 - Code quality audits
- **Day 4**: Phase 7 - Configuration validation
- **Day 5**: Phase 4 - Security audit

**Week 2**: Testing Infrastructure
- **Days 1-5**: Phase 3 - Complete test suite (80%+ coverage target)
- Deploy to beta, monitor 24h

**Week 3**: Performance & Deep Analysis
- **Days 1-2**: Phase 5 - Performance analysis
- **Day 3**: Phase 6 - Documentation quality
- **Days 4-5**: Phases 8-9 - Database integrity, dependency audit

**Week 4**: Automation & Final Validation
- **Days 1-2**: Phase 10 - Pre-commit hooks, full CI/CD
- **Day 3**: Final deployment to beta
- **Days 4-7**: Phase 11 - Post-audit validation & Go/No-Go decision

**Deliverables**:
- ✅ Complete baseline and post-audit metrics
- ✅ 80%+ test coverage achieved
- ✅ All quality issues resolved
- ✅ Full CI/CD pipeline operational
- ✅ Performance optimized
- ✅ Production-ready codebase with data-driven approval

**Success Criteria**:
- All metrics stable or improved
- Zero critical security issues
- Test coverage ≥ 80%
- AI quality maintained
- User engagement stable

**Best for**: Achieving production-grade quality with confidence through data validation

---

### **Option D: Phased** (Ongoing)

**Sprint 1** (Week 1):
- Code quality audit (Phases 1-2)
- Security scan (Phase 4)
- Fix critical issues

**Sprint 2** (Weeks 2-3):
- Testing infrastructure (Phase 3)
- Target: 50% coverage

**Sprint 3** (Week 4):
- Remaining tests (80% coverage)
- Pre-commit hooks (Phase 10)

**Sprint 4+** (Ongoing):
- Performance tuning (Phase 5)
- Documentation improvements (Phase 6)
- Continuous monitoring

**Best for**: Gradual improvement alongside feature development

---

## 📊 Success Metrics

### Code Quality
- [ ] **Flake8**: < 10 issues across codebase
- [ ] **Pylint**: Score > 8.0/10
- [ ] **ESLint**: 0 errors (warnings acceptable)
- [ ] **Black/Prettier**: All code formatted

### Testing
- [ ] **Backend Coverage**: > 80%
- [ ] **Critical Paths**: 100% coverage (auth, AI feedback, reports)
- [ ] **All Tests Passing**: Green build
- [ ] **Test Documentation**: Complete

### Security
- [ ] **High/Critical Vulnerabilities**: 0
- [ ] **Safety Check**: Pass
- [ ] **Bandit**: No high-severity issues
- [ ] **Secrets**: None exposed (git-secrets pass)
- [ ] **Security Checklist**: 100% complete

### Performance
- [ ] **API Response Times**: < 500ms average
- [ ] **N+1 Queries**: Eliminated
- [ ] **Database Indexes**: All critical paths indexed
- [ ] **LLM API**: Cost < $0.05 per feedback

### Configuration
- [ ] **requirements.txt**: Clean format
- [ ] **.env.example**: Complete
- [ ] **.gitignore**: Comprehensive
- [ ] **Settings**: Production-ready

### Automation
- [ ] **Pre-commit Hooks**: Installed
- [ ] **CI/CD**: Running on all commits
- [ ] **Quality Gates**: Enforced
- [ ] **Auto-formatting**: Enabled

---

## 📁 Report Structure

All reports will be saved to `reports/` directory:

```
reports/
├── python_quality_report.md
├── javascript_quality_report.md
├── SECURITY_AUDIT_REPORT.md
├── test_coverage_report.html
├── PERFORMANCE_REPORT.md
├── documentation_audit.md
├── configuration_audit.md
├── database_health_report.md
└── DEPENDENCY_AUDIT.md
```

---

## 🔄 Maintenance & Continuous Improvement

### Monthly
- [ ] Run dependency audit (Phase 9)
- [ ] Review test coverage
- [ ] Check for new security vulnerabilities

### Quarterly
- [ ] Full quality audit (all phases)
- [ ] Update tools and configurations
- [ ] Review and update quality metrics

### Before Production Deploy
- [ ] Run full test suite
- [ ] Security scan
- [ ] Performance benchmarks
- [ ] Configuration validation

---

## 📚 Related Documentation

- **BETA_TESTING_WORKFLOW.md** - Testing procedures for deployments
- **.claude/docs/TESTING.md** - Testing strategies and patterns
- **.claude/docs/SECURITY.md** - Security best practices
- **.claude/docs/PERFORMANCE.md** - Performance optimization
- **MONITORING_SETUP.md** - Production monitoring

---

## 🎯 Getting Started

### Pre-Requisites Checklist

**BEFORE starting any quality work**, ensure:

- [ ] Beta environment is stable and accessible
- [ ] Monitoring scripts installed (MONITORING_SETUP.md completed)
- [ ] AI baseline tracking configured (`scripts/track_ai_baseline.py` working)
- [ ] Can deploy to beta (BETA_DEPLOYMENT.md workflow understood)
- [ ] Team understands data-driven approach (read AI_ITERATION_WORKFLOW.md)
- [ ] Risk assessment framework reviewed (.claude/docs/RISK_ASSESSMENT.md)

### Recommended Approach

**We recommend Option B: Foundation** (3 weeks) because it:
- ✅ Balances thoroughness with pragmatism
- ✅ Includes full data-driven validation
- ✅ Provides Go/No-Go decision for production
- ✅ Addresses critical issues (security, testing, quality)
- ✅ Automated quality gates (pre-commit, CI/CD)

### Phase 0: Your First Day (MANDATORY)

**🚨 DO NOT SKIP Phase 0 - it is the foundation of data-driven quality improvement!**

```bash
# 1. SSH to beta droplet
ssh root@64.225.17.0
cd /home/deploy/global-peds-reading-room
source backend/venv/bin/activate

# 2. Collect AI quality baseline
python scripts/track_ai_baseline.py "Before quality audit - baseline"

# 3. Run comprehensive metrics
python scripts/monitor_metrics.py > reports/baseline_metrics_$(date +%Y%m%d).txt

# 4. View and document results
cat reports/baseline_metrics_*.txt
cat ai_baseline_history.json | jq '.'

# 5. Document baseline in reports/BASELINE_REPORT.md
# (See Phase 0 for template)
```

**Expected Output**:
```
BETA ENVIRONMENT METRICS
====================================================
📊 AI FEEDBACK QUALITY (Last 7 Days)
Average Rating: 4.20/5.00
Total Ratings: 45
...
```

**⚠️ STOP**: Do not proceed until you have documented baseline metrics!

### After Phase 0: Code Quality Audits

**Only after baseline is documented**:

```bash
# On local machine (not beta droplet)
cd /mnt/c/Users/strau/Desktop/gr4-gemini/backend

# 1. Install Python quality tools
pip install flake8 pylint black isort bandit pytest pytest-django pytest-cov

# 2. Create reports directory
mkdir -p ../reports

# 3. Run initial scans (Phase 1)
flake8 . --exclude=venv,migrations --max-line-length=120 > ../reports/flake8_initial.txt
pylint cases users api --ignore=migrations > ../reports/pylint_initial.txt
bandit -r . -x venv,migrations -f json > ../reports/bandit_initial.json

# 4. Review reports and categorize issues
cat ../reports/flake8_initial.txt | wc -l  # Count issues
cat ../reports/pylint_initial.txt | grep "rated at"  # See score

# 5. Create prioritized fix list
# (See Phase 1 for guidance)
```

### Implementation Workflow

For each phase:

1. **Plan**: Complete risk assessment
2. **Implement**: Make quality improvements
3. **Deploy to Beta**: Follow BETA_DEPLOYMENT.md
4. **Monitor**: 24-48h validation (AI quality, errors, engagement)
5. **Validate**: Compare to baseline, document results
6. **Decision**: Go/No-Go to next phase
7. **Repeat**: Move to next phase only after validation

### Phase 11: Final Decision

After all phases complete:

1. **Collect post-audit metrics** (same scripts as Phase 0)
2. **Compare before/after** (AI quality, engagement, performance)
3. **Create impact report** (QUALITY_AUDIT_IMPACT_REPORT.md)
4. **Make Go/No-Go decision** based on data
5. **If approved**: Merge to main, prepare production deployment
6. **If not approved**: Address issues, re-validate, repeat Phase 11

---

**Remember**: Quality is a journey, not a destination. Start with critical issues, build momentum, and continuously improve!

**Last Updated**: 2025-10-11
**Next Review**: After Phase 1 completion
