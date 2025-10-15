# 🏥 CLAUDE.md - Global Peds Reading Room

This file provides essential guidance for Claude Code when working with this repository. Detailed documentation is modularized in `.claude/docs/`.

---

## 📋 Project Overview

**Global Peds Reading Room** is an AI-powered educational web platform for global pediatric radiology learning. Medical professionals view curated cases, submit diagnostic reports, receive AI-powered feedback, and compare interpretations against expert findings using standardized templates.

**Key Features**:
- 🔍 Interactive DICOM viewing with Orthanc/OHIF integration
- 🤖 AI-powered feedback using Google Gemini 2.5 Flash
- 📋 Structured multi-language reporting templates
- 📊 Data-driven analytics and progress tracking

---

## 🛠️ Tech Stack

- **Backend**: Django 5.2, Django REST Framework, PostgreSQL
- **Frontend**: Vanilla JavaScript (ES6+), HTML5, CSS3
- **AI**: Google Gemini API with rate limiting & caching
- **External**: Orthanc DICOM Server with OHIF Viewer

---

## ⚠️ CRITICAL: Risk Assessment Requirement

**Before making ANY code changes**, you MUST complete a risk assessment:

1. 📖 Read: @.claude/docs/RISK_ASSESSMENT.md
2. 📝 Document: Direct impact, cascading effects, data implications
3. 🔍 Assess: Breaking changes, scalability, security
4. 🛡️ Plan: Mitigation strategies and rollback procedures

**This is mandatory** - prevents data loss, performance issues, and user-facing bugs.

---

## 🚨 CRITICAL: Frontend API Development

**Before making ANY frontend API changes**, you MUST:

1. 📖 **Read**: @.claude/docs/FRONTEND_API_PATTERNS.md (MANDATORY)
2. 🔍 **Search**: Find existing similar API calls - DO NOT GUESS!
3. ✅ **Copy**: Use exact pattern from working code
4. ❌ **NEVER**: Add `/api/` prefix to `apiRequest()` calls
5. ✓ **Verify**: Test in browser, check Network tab for single `/api/` prefix

**Why This Matters**:
- `apiRequest()` automatically prepends `/api/` to all endpoints
- Adding `/api/` in your call causes double-prefix: `/api/api/...` → 404 ERROR
- This is the #1 cause of recurring "fixing-breaking" issues

**Example**:
```javascript
// ❌ WRONG - Double prefix
apiRequest('/api/cases/reports/6/ai-feedback/')
// Becomes: /api/api/cases/reports/6/ai-feedback/ → 404

// ✅ CORRECT - Single prefix
apiRequest('/cases/reports/6/ai-feedback/')
// Becomes: /api/cases/reports/6/ai-feedback/ → SUCCESS
```

**Checklist**: @.claude/FRONTEND_CHECKLIST.md

---

## 🚀 Quick Start Commands

### 1️⃣ Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Configure environment (see @.claude/docs/ENVIRONMENT.md)
cp .env.example .env
# Edit .env with your configuration

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start server
python manage.py runserver
```

### 2️⃣ Frontend Setup

```bash
cd frontend
python -m http.server 5500
```

### 3️⃣ Running Tests

```bash
cd backend
python manage.py test                                      # All tests
python manage.py test cases                                # Specific app
python manage.py test cases.tests.TestClassName           # Specific class
python manage.py test cases.tests.TestClass.test_method   # Specific method
```

---

## 📚 Detailed Documentation

### Core Documentation (Import with @)

**@.claude/docs/RISK_ASSESSMENT.md** ⚠️
- Mandatory risk assessment framework
- Step-by-step evaluation process
- Risk severity levels and mitigation strategies
- Template for all code changes

**@.claude/docs/DATA_MODELS.md** 🗄️
- Complete documentation of 9 models
- Relationships and cascading behaviors
- Query optimization patterns
- Case identifier auto-generation logic
- Report versioning system

**@.claude/docs/ENVIRONMENT.md** 🔧
- Tutorial-style environment setup
- All environment variables explained
- Security best practices for secrets
- Development vs production configuration

**@.claude/docs/TESTING.md** 🧪
- Data-driven testing strategy
- Coverage expectations (90%+ for models)
- Testing analytics queries
- Performance testing with assertNumQueries

**@.claude/docs/PERFORMANCE.md** ⚡
- API rate limiting (10 calls/min default)
- Database query optimization
- Caching strategies
- Scalability roadmap

**@.claude/docs/MONITORING.md** 📊
- Key metrics: user engagement, AI quality, performance
- Analytics query examples
- Data-driven decision-making
- Alerting thresholds

**@.claude/docs/WORKFLOWS.md** 🔄
- Step-by-step workflows with risk assessment
- Adding database fields safely
- Modifying AI prompts
- Creating teaching cases
- Database migration procedures

**@.claude/docs/SECURITY.md** 🔒
- Authentication & authorization best practices
- Input validation & sanitization
- CORS configuration
- Secret management & rotation
- Incident response procedures

**@.claude/docs/DEPLOYMENT.md** 🚀
- Beta Droplet server configuration (IP, users, paths)
- GitHub Actions automated deployment workflow
- Manual verification procedures
- root vs deploy user guidance
- Common deployment issues & solutions
- Quick command reference for troubleshooting

**@.claude/docs/FRONTEND_API_PATTERNS.md** 🌐 **[MANDATORY FOR FRONTEND]**
- How `apiRequest()` automatically prepends `/api/`
- Correct vs incorrect API call patterns
- Backend URL verification guide
- Quick reference table for all endpoints
- Debugging 404 errors (double-prefix issues)
- Historical context and lessons learned

**@.claude/FRONTEND_CHECKLIST.md** ✅ **[PRE-COMMIT REQUIRED]**
- Pre-commit checklist for frontend changes
- Pattern research steps
- Browser testing procedures
- Common mistakes to avoid
- Red flags that indicate problems
- Git diff verification

---

## 🏗️ Architecture Overview

### Backend Structure

```
backend/
├── cases/                      # Core: Cases, Reports, Templates, AI Feedback
│   ├── models.py              # 9 models with complex relationships
│   ├── llm_feedback_service.py # Gemini API with rate limiting
│   ├── utils.py               # Report comparison pre-analysis
│   ├── views.py               # API endpoints
│   └── serializers.py         # DRF serializers
├── users/                      # Authentication & profiles
├── api/                        # API routing
└── globalpeds_project/         # Django settings
```

### Frontend Structure

```
frontend/
├── js/
│   ├── api.js                 # Centralized API client with JWT
│   ├── main.js                # Case viewing & report submission
│   ├── auth.js                # Login/logout flows
│   ├── admin-*.js             # Admin interfaces (cases, users, templates)
│   └── config.js              # Frontend configuration
└── admin/                      # Admin HTML pages
```

---

## 🎯 Development Guidelines

### 1️⃣ Data-Driven Approach

**Always Consider**:
- 📊 How changes affect analytics queries
- 🤖 Impact on AI feedback quality (track ratings)
- 📈 Performance with realistic data volumes
- 🔍 Historical data compatibility

**Example**: Before changing AI prompt, record baseline AIFeedbackRating average, deploy, monitor for 7 days, compare.

### 2️⃣ Scalability First

**Query Optimization**:
- Always use `select_related()` for ForeignKeys
- Always use `prefetch_related()` for reverse relations
- Test with 100+ records, not just 5
- Use `assertNumQueries()` in tests

**Rate Limiting**:
- Gemini API: 10 calls/min (configurable via `GEMINI_API_RATE_LIMIT`)
- Monitor via `llm_feedback_service.API_CALL_HISTORY`

### 3️⃣ Best Practices

**Code Style**:
- Python: PEP 8, type hints for complex functions
- JavaScript: ES6+, async/await for API calls
- Django: Use ORM (never raw SQL without parameterization)

**Before Committing**:
- [ ] Risk assessment completed
- [ ] Tests written and passing
- [ ] Query optimization verified
- [ ] Documentation updated if needed

---

## 🔑 Key System Behaviors

### Case Identifier Auto-Generation
- **Format**: `{SUBSPECIALTY}-{MODALITY}-{YEAR}-{SEQUENCE}`
- **Example**: `NR-MR-2025-0001`
- **Location**: backend/cases/models.py:213-273
- **Note**: Handles collisions with retry + UUID fallback

### Report Versioning
- Multiple reports per user/case allowed
- `is_archived=True` for old versions
- Query non-archived for "current" report

### AI Feedback Pipeline
1. User submits report
2. Programmatic pre-analysis (utils.py)
3. Gemini API call with rate limiting (llm_feedback_service.py)
4. Parse response into structured feedback
5. Store in Report.ai_feedback_content (JSON)
6. User rates quality (AIFeedbackRating)

---

## 📝 Common Commands Reference

```bash
# Database
python manage.py makemigrations
python manage.py migrate
python manage.py migrate --plan  # Preview migration

# Testing
python manage.py test
python manage.py test --keepdb  # Reuse test database
python manage.py test --parallel  # Faster on multi-core

# Shell
python manage.py shell  # Django shell for queries

# Static files (production)
python manage.py collectstatic
```

---

## 🚨 Critical Files & Locations

**AI System**:
- `backend/cases/llm_feedback_service.py` - Gemini API integration
- `backend/cases/utils.py` - Report comparison logic
- `backend/cases/views.py:AIReportFeedbackView` - Feedback endpoint

**Configuration**:
- `backend/globalpeds_project/settings.py` - All Django settings
- `backend/.env` - Environment variables (NEVER commit!)
- `backend/.env.example` - Template for .env

**Models**:
- `backend/cases/models.py` - All 9 models (Case, Report, etc.)
- See @.claude/docs/DATA_MODELS.md for relationships

---

## 💡 Remember

1. **⚠️ Risk Assessment First** - No exceptions, ever
2. **📊 Data-Driven** - Track metrics, measure impact
3. **⚡ Scalability** - Test with realistic data volumes
4. **🔒 Security** - Sanitize inputs, protect secrets
5. **🧪 Test Everything** - Especially data integrity

---

## 📖 Additional Resources

- **Project README**: `/README.md` - User-facing documentation
- **Environment Template**: `/backend/.env.example`
- **Git Status**: Check current branch before changes
- **Claude Code Docs**: [docs.claude.com/claude-code](https://docs.claude.com/claude-code)

---

**Generated for Claude Code** - Last Updated: 2025-01-11
