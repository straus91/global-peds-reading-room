# 🔧 Environment Configuration Guide

## 🎯 Overview

This guide provides step-by-step instructions for configuring your development environment using environment variables. Proper configuration is critical for security, scalability, and connecting to external services.

---

## 📋 Quick Start Checklist

Before running the application, ensure you have:

- ✅ Python 3.8+ installed
- ✅ PostgreSQL database created
- ✅ Orthanc DICOM Server running (optional for development)
- ✅ Google Gemini API key obtained
- ✅ `.env` file created in `backend/` directory

---

## 🚀 Step-by-Step Setup

### Step 1️⃣: Create Your Environment File

Navigate to the backend directory and create a `.env` file:

```bash
cd backend
touch .env  # On Windows: type nul > .env
```

⚠️ **Important**: The `.env` file is in `.gitignore` and should NEVER be committed to version control!

### Step 2️⃣: Copy Template

Copy the contents from `backend/.env.example` (or use the template below) into your `.env` file.

### Step 3️⃣: Configure Each Variable

Follow the detailed explanations below to configure each variable appropriately.

---

## 🔑 Environment Variables Reference

### 1️⃣ Core Django Settings

#### `SECRET_KEY` (Required)
**Purpose**: Cryptographic signing key for Django session management, CSRF protection, and password hashing.

**Security Level**: 🔴 **CRITICAL** - Never share or commit this!

**How to Generate**:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

**Example**:
```env
SECRET_KEY=django-insecure-x+ewof#94net5w(rk8j)w6c0%2sr=+gm60@tsqj578vo5!-%l_
```

**Best Practices**:
- 🔒 Use a unique key for each environment (dev, staging, prod)
- 📏 Minimum 50 characters
- 🔄 Rotate periodically in production
- 🚫 Never reuse across projects

---

#### `DEBUG` (Optional, default: `True`)
**Purpose**: Enables detailed error pages and debug information.

**Security Level**: ⚠️ **WARNING** - Must be `False` in production!

**Valid Values**: `True` or `False` (case-sensitive)

**Example**:
```env
# Development
DEBUG=True

# Production
DEBUG=False
```

**⚠️ Production Impact**:
- `DEBUG=True` exposes sensitive information (SQL queries, settings, stack traces)
- Never deploy to production with DEBUG=True
- Performance overhead when enabled

**Best Practices**:
- ✅ `True` in development for easier debugging
- ❌ `False` in staging and production
- 📊 Use proper logging instead of DEBUG mode

---

#### `ALLOWED_HOSTS` (Optional, default: `localhost,127.0.0.1`)
**Purpose**: Whitelist of hostnames/IPs that can serve the application (prevents Host header attacks).

**Security Level**: 🔴 **CRITICAL** for production

**Format**: Comma-separated list (no spaces)

**Examples**:
```env
# Development
ALLOWED_HOSTS=localhost,127.0.0.1

# Production
ALLOWED_HOSTS=globalpeds.example.com,www.globalpeds.example.com

# With IP addresses
ALLOWED_HOSTS=globalpeds.example.com,203.0.113.42
```

**Best Practices**:
- 🔒 Be as restrictive as possible in production
- 🚫 Never use `*` (allows any host)
- 🌐 Include all domains the app will be accessed from
- 📱 Include mobile/API subdomains if applicable

---

### 2️⃣ Database Configuration

#### `DB_NAME` (Optional, default: `globalpeds_db`)
**Purpose**: PostgreSQL database name.

**Example**:
```env
# Development
DB_NAME=globalpeds_db

# Production
DB_NAME=globalpeds_production
```

**Best Practices**:
- 📋 Use descriptive names including environment
- 🔄 Different databases for dev/staging/prod

---

#### `DB_USER` (Optional, default: `postgres`)
**Purpose**: PostgreSQL username.

**Security Level**: 🟡 **MODERATE** - Don't use superuser in production

**Example**:
```env
# Development
DB_USER=postgres

# Production (dedicated user)
DB_USER=globalpeds_app
```

**Best Practices**:
- 👤 Create dedicated database user for the application
- 🔐 Grant only necessary permissions (not superuser)
- 🚫 Don't use `postgres` superuser in production

---

#### `DB_PASSWORD` (Optional, default: `password`)
**Purpose**: PostgreSQL password.

**Security Level**: 🔴 **CRITICAL** - Must be strong in production!

**Example**:
```env
# Development (weak is OK)
DB_PASSWORD=password

# Production (strong password required)
DB_PASSWORD=8Xk#mP9$nQ2@vL7&wR4^tY6!
```

**Best Practices**:
- 🔒 Minimum 16 characters in production
- 🎲 Use password manager to generate
- 🔄 Rotate regularly (every 90 days)
- 🚫 Never reuse across environments

---

#### `DB_HOST` (Optional, default: `localhost`)
**Purpose**: PostgreSQL server hostname or IP.

**Example**:
```env
# Local development
DB_HOST=localhost

# Docker container
DB_HOST=postgres

# Production (cloud)
DB_HOST=prod-db.example.com
```

**Scalability Considerations**:
- 📊 Use connection pooling (PgBouncer) in production
- 🔄 Consider read replicas for analytics queries
- 🌐 Use private networking for database connections

---

#### `DB_PORT` (Optional, default: `5432`)
**Purpose**: PostgreSQL server port.

**Example**:
```env
DB_PORT=5432  # Default PostgreSQL port
```

**Best Practices**:
- 🔒 Change default port in production for security obscurity
- 🔥 Ensure firewall rules allow only app servers

---

### 3️⃣ AI Integration

#### `GEMINI_API_KEY` (Required)
**Purpose**: Google Gemini API key for AI-powered feedback generation.

**Security Level**: 🔴 **CRITICAL** - API usage costs money!

**Where to Get It**:
1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with Google account
3. Click "Get API Key"
4. Copy and paste into `.env`

**Example**:
```env
GEMINI_API_KEY=AIzaSyD1234567890abcdefghijklmnopqrstuvwxyz
```

**⚠️ Cost & Rate Limiting**:
- Free tier: 60 requests per minute
- Paid tier: Higher limits
- See @.claude/docs/PERFORMANCE.md for rate limiting configuration

**Best Practices**:
- 🔒 Never commit to version control
- 💰 Monitor usage in Google Cloud Console
- 🚦 Implement rate limiting (see PERFORMANCE.md)
- 🔄 Rotate if accidentally exposed
- 📊 Track API costs as data-driven metric

**Scalability Considerations**:
- 📈 Monitor requests per minute (see llm_feedback_service.py:23-24)
- 💲 Track costs per report generated
- 🔄 Consider caching AI feedback for identical reports

---

### 4️⃣ CORS & API Configuration

#### `CORS_ALLOWED_ORIGINS` (Optional, default: `http://127.0.0.1:5500,http://localhost:5500`)
**Purpose**: Whitelist of frontend URLs allowed to make API requests (Cross-Origin Resource Sharing).

**Security Level**: 🔴 **CRITICAL** - Prevents unauthorized API access

**Format**: Comma-separated list (no spaces), full URLs with protocol

**Examples**:
```env
# Development
CORS_ALLOWED_ORIGINS=http://127.0.0.1:5500,http://localhost:5500

# Production
CORS_ALLOWED_ORIGINS=https://globalpeds.example.com,https://www.globalpeds.example.com

# Multiple environments
CORS_ALLOWED_ORIGINS=https://globalpeds.example.com,https://staging.globalpeds.example.com
```

**⚠️ Common Mistakes**:
- ❌ `http://localhost:5500/` - No trailing slash
- ❌ `localhost:5500` - Must include `http://` or `https://`
- ❌ `*` - Never use wildcard in production

**Best Practices**:
- 🔒 Be as restrictive as possible
- 🔐 Use HTTPS in production
- 🚫 Never use `*` wildcard
- 🌐 Include all frontend domains/subdomains

**Debugging CORS Issues**:
```python
# Check current CORS settings in Django shell
python manage.py shell
>>> from django.conf import settings
>>> print(settings.CORS_ALLOWED_ORIGINS)
```

---

### 5️⃣ JWT Authentication

#### `ACCESS_TOKEN_LIFETIME` (Optional, default: `60`)
**Purpose**: JWT access token expiration time in minutes.

**Security Level**: 🟡 **MODERATE** - Balance security vs user experience

**Example**:
```env
# Short-lived (more secure)
ACCESS_TOKEN_LIFETIME=15

# Development (convenience)
ACCESS_TOKEN_LIFETIME=60

# Production (balanced)
ACCESS_TOKEN_LIFETIME=30
```

**Best Practices**:
- ⏱️ Shorter is more secure (15-30 minutes)
- 🔄 Use refresh tokens for longer sessions
- 📊 Monitor token expiration impact on user experience

**Scalability Considerations**:
- 🔄 Shorter lifetime = more refresh requests
- 📈 Monitor refresh token endpoint load

---

#### `REFRESH_TOKEN_LIFETIME` (Optional, default: `1`)
**Purpose**: JWT refresh token expiration time in days.

**Security Level**: 🟡 **MODERATE**

**Example**:
```env
# Production (security-focused)
REFRESH_TOKEN_LIFETIME=7

# Development
REFRESH_TOKEN_LIFETIME=1

# Long-lived sessions
REFRESH_TOKEN_LIFETIME=30
```

**Best Practices**:
- 🔒 Balance between security and UX
- 🚫 Don't exceed 30 days
- 🔄 Force re-login for sensitive operations

---

## 📊 Configuration by Environment

### 🧪 Development Environment

```env
# Development .env
SECRET_KEY=django-insecure-dev-only-not-for-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

DB_NAME=globalpeds_dev
DB_USER=postgres
DB_PASSWORD=password
DB_HOST=localhost
DB_PORT=5432

GEMINI_API_KEY=AIzaSy_your_dev_key_here

CORS_ALLOWED_ORIGINS=http://127.0.0.1:5500,http://localhost:5500

ACCESS_TOKEN_LIFETIME=60
REFRESH_TOKEN_LIFETIME=1
```

**📝 Notes**:
- ✅ Weak passwords are acceptable
- ✅ DEBUG=True for easier troubleshooting
- ✅ Longer token lifetimes for convenience

---

### 🚀 Production Environment

```env
# Production .env
SECRET_KEY=<generate-strong-unique-secret-key>
DEBUG=False
ALLOWED_HOSTS=globalpeds.example.com,www.globalpeds.example.com

DB_NAME=globalpeds_production
DB_USER=globalpeds_app
DB_PASSWORD=<strong-16+-char-password>
DB_HOST=prod-db.internal.example.com
DB_PORT=5432

GEMINI_API_KEY=<production-api-key-with-monitoring>

CORS_ALLOWED_ORIGINS=https://globalpeds.example.com

ACCESS_TOKEN_LIFETIME=30
REFRESH_TOKEN_LIFETIME=7
```

**⚠️ Critical Checks**:
- ✅ DEBUG=False
- ✅ Strong passwords (16+ characters)
- ✅ HTTPS only for CORS
- ✅ Restricted ALLOWED_HOSTS
- ✅ Dedicated database user
- ✅ API key monitoring enabled

---

## 🔍 Verification & Testing

### Step 1️⃣: Verify Environment Loading

```bash
cd backend
python manage.py shell
```

```python
import os
from django.conf import settings

# Check if .env loaded
print("DEBUG:", settings.DEBUG)
print("ALLOWED_HOSTS:", settings.ALLOWED_HOSTS)
print("DATABASE NAME:", settings.DATABASES['default']['NAME'])

# Check Gemini API key (don't print full key!)
gemini_key = os.environ.get('GEMINI_API_KEY')
if gemini_key:
    print(f"GEMINI_API_KEY loaded: Yes (length: {len(gemini_key)})")
else:
    print("GEMINI_API_KEY loaded: No")
```

### Step 2️⃣: Test Database Connection

```bash
python manage.py check --database default
```

### Step 3️⃣: Test Migrations

```bash
python manage.py migrate --plan
```

### Step 4️⃣: Test Gemini API

```bash
python manage.py shell
```

```python
import os
os.environ.get('GEMINI_API_KEY')  # Should print your key
exit()

# Test AI feedback service
cd backend/cases
python llm_feedback_service.py
# Should see "Testing LLM feedback service directly..." in output
```

---

## 🛠️ Troubleshooting

### Issue 1: "Environment variable not found"

**Symptom**: Application can't find `GEMINI_API_KEY` or other variables.

**Solutions**:
1. ✅ Check `.env` file is in `backend/` directory (not project root)
2. ✅ Verify no spaces around `=` sign: `KEY=value` not `KEY = value`
3. ✅ Restart Django server after `.env` changes
4. ✅ Check `load_dotenv()` in settings.py (line 11-14)

### Issue 2: "CORS errors in browser console"

**Symptom**: API requests fail with CORS error.

**Solutions**:
1. ✅ Check `CORS_ALLOWED_ORIGINS` includes full URL with protocol
2. ✅ No trailing slashes in URLs
3. ✅ Restart Django server after changes
4. ✅ Clear browser cache
5. ✅ Verify `django-cors-headers` installed (see requirements.txt)

### Issue 3: "Database connection failed"

**Symptom**: Can't connect to PostgreSQL.

**Solutions**:
1. ✅ Verify PostgreSQL is running: `sudo service postgresql status`
2. ✅ Check credentials: `psql -U postgres -d globalpeds_db`
3. ✅ Verify `DB_HOST` is correct (localhost vs 127.0.0.1)
4. ✅ Check PostgreSQL accepts connections on `DB_PORT`
5. ✅ Create database: `createdb globalpeds_db`

### Issue 4: "Invalid Gemini API key"

**Symptom**: AI feedback fails with authentication error.

**Solutions**:
1. ✅ Verify key is correct (copy-paste error?)
2. ✅ Check API enabled in Google Cloud Console
3. ✅ Verify billing enabled (free tier has limits)
4. ✅ Check quotas not exceeded
5. ✅ Test key in Google AI Studio

### Issue 5: "JWT tokens expire too quickly"

**Symptom**: Users logged out frequently.

**Solutions**:
1. ✅ Increase `ACCESS_TOKEN_LIFETIME` (careful: security trade-off)
2. ✅ Implement automatic token refresh in frontend
3. ✅ Check `REFRESH_TOKEN_LIFETIME` is long enough

---

## 📊 Monitoring Environment Configuration

### Log Environment Status on Startup

Your settings.py already logs on startup (lines 13-22):
```python
env_path = BASE_DIR / '.env'
if os.path.exists(env_path):
    print(f"Found .env file at: {env_path}")
    load_dotenv(dotenv_path=env_path, verbose=True)
    GEMINI_API_KEY_CHECK = os.environ.get('GEMINI_API_KEY')
    if GEMINI_API_KEY_CHECK:
        print(f"GEMINI_API_KEY loaded: Present (length: {len(GEMINI_API_KEY_CHECK)})")
    else:
        print("GEMINI_API_KEY NOT loaded immediately after load_dotenv.")
else:
    print(f"WARNING: .env file not found at {env_path}")
```

**Best Practices**:
- 📊 Monitor these logs on application startup
- 🚨 Alert if `.env` not found in production
- 📈 Track when keys are rotated (via logs)

---

## 🔒 Security Best Practices Summary

1. **🚫 Never Commit `.env`**: Already in `.gitignore`, but double-check
2. **🔑 Rotate Secrets**: Change keys every 90 days in production
3. **🔒 Strong Passwords**: 16+ characters for production
4. **🔐 Least Privilege**: Database user should have minimal permissions
5. **📊 Monitor API Usage**: Track Gemini API costs and quotas
6. **🚦 Rate Limiting**: Configure in `PERFORMANCE.md`
7. **🔄 Separate Environments**: Different secrets for dev/staging/prod
8. **🔥 Firewall Rules**: Only allow necessary connections to database

---

## 📚 Related Documentation

- @.claude/docs/SECURITY.md - Comprehensive security guidelines
- @.claude/docs/PERFORMANCE.md - Rate limiting and API optimization
- @.claude/docs/RISK_ASSESSMENT.md - Assess risks before config changes
- @.claude/docs/MONITORING.md - Track environment health metrics

---

**💡 Next Steps**:
1. Create your `.env` file using the template
2. Generate secure `SECRET_KEY`
3. Configure database credentials
4. Obtain `GEMINI_API_KEY`
5. Verify configuration with tests above
6. Run `python manage.py migrate`
7. Start development server: `python manage.py runserver`
