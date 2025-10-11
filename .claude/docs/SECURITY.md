# 🔒 Security Best Practices

## 🎯 Overview

Security is critical for protecting user data, preventing unauthorized access, and maintaining system integrity. This guide covers security best practices for Global Peds Reading Room with focus on Django, API security, and data protection.

---

## 🔑 Authentication & Authorization

### JWT Token Security

**Current Implementation**: `djangorestframework-simplejwt`

**Location**: `backend/globalpeds_project/settings.py:147-153`

#### Token Lifetime Configuration

```python
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),  # ⚠️ Reduce to 15-30 in production
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'AUTH_HEADER_TYPES': ('Bearer',),
}
```

**Best Practices**:
- ✅ **Short-lived access tokens**: 15-30 minutes in production
- ✅ **Refresh tokens for long sessions**: 7-30 days
- ✅ **Secure storage**: Never store tokens in localStorage (XSS vulnerable)
- ✅ **HttpOnly cookies** (preferred) or sessionStorage for tokens

#### Password Requirements

**Current**: Django default password validators (settings.py:101-114)

**Enforced Rules**:
1. Not too similar to user attributes
2. Minimum 8 characters
3. Not a common password
4. Not entirely numeric

**Recommendations for Production**:
```python
# Add to settings.py
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 12,  # Increase to 12
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]
```

### Permission Classes

**Always specify permissions for views**:

```python
# ✅ GOOD: Explicit permissions
from rest_framework.permissions import IsAuthenticated

class CaseViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

# ❌ BAD: No permission class (uses default)
class UnsecureViewSet(viewsets.ModelViewSet):
    pass  # Potentially allows unauthenticated access!
```

### User Role Management

**Best Practices**:
1. Use Django's built-in permission system
2. Never check `user.is_superuser` for business logic
3. Create custom permissions for specific actions

**Example**:
```python
# In models.py
class Case(models.Model):
    class Meta:
        permissions = [
            ("can_publish_case", "Can publish case"),
            ("can_archive_case", "Can archive case"),
        ]

# In views.py
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import User

class CaseViewSet(viewsets.ModelViewSet):
    @action(detail=True, methods=['post'],
            permission_classes=[IsAuthenticated])
    def publish(self, request, pk=None):
        if not request.user.has_perm('cases.can_publish_case'):
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        # ... publish logic ...
```

---

## 🛡️ Input Validation & Sanitization

### Preventing Prompt Injection

**Location**: `backend/cases/llm_feedback_service.py:38-58`

**Implementation**:
```python
PROMPT_INJECTION_PATTERN = re.compile(
    r'(ignore previous instructions|ignore above instructions|stop using template|exit role)',
    re.IGNORECASE
)

def sanitize_text(text):
    """Remove potential prompt injection patterns"""
    if not isinstance(text, str):
        return "" if text is None else str(text)

    # Remove injection patterns
    sanitized = PROMPT_INJECTION_PATTERN.sub('', text)

    # Limit length
    if len(sanitized) > 10000:
        sanitized = sanitized[:10000] + "... [truncated]"

    return sanitized
```

**⚠️ Critical**: ALL user input sent to LLM must be sanitized!

### SQL Injection Prevention

**Django ORM protects against SQL injection automatically**:

```python
# ✅ SAFE: Uses parameterized query
Case.objects.filter(case_identifier=user_input)

# ❌ DANGEROUS: Raw SQL with string formatting
cursor.execute(f"SELECT * FROM cases_case WHERE case_identifier = '{user_input}'")

# ✅ SAFE: Raw SQL with parameters
cursor.execute("SELECT * FROM cases_case WHERE case_identifier = %s", [user_input])
```

**Best Practice**: Always use ORM. If raw SQL needed, always use parameterized queries.

### Cross-Site Scripting (XSS) Prevention

**Django automatically escapes HTML in templates**.

**Frontend Protection**:
```javascript
// ❌ DANGEROUS: Inserts raw HTML
element.innerHTML = userInput;

// ✅ SAFE: Escapes HTML
element.textContent = userInput;

// ✅ SAFE: Using a sanitization library
import DOMPurify from 'dompurify';
element.innerHTML = DOMPurify.sanitize(userInput);
```

**API Response**: Never include unsanitized user content in responses without escaping.

---

## 🌐 CORS & API Security

### CORS Configuration

**Location**: `backend/globalpeds_project/settings.py:156-160`

```python
CORS_ALLOWED_ORIGINS = os.environ.get(
    'CORS_ALLOWED_ORIGINS',
    'http://127.0.0.1:5500,http://localhost:5500'
).split(',')

CORS_ALLOW_CREDENTIALS = True
```

**Security Rules**:
1. **🔴 NEVER** use `CORS_ALLOW_ALL_ORIGINS = True` in production
2. **🔴 NEVER** include wildcard (`*`) in `CORS_ALLOWED_ORIGINS`
3. ✅ Use HTTPS URLs in production
4. ✅ Be as restrictive as possible

**Production Example**:
```env
CORS_ALLOWED_ORIGINS=https://globalpeds.example.com
```

### CSRF Protection

**Django's CSRF protection enabled by default** (settings.py:63).

**For API endpoints using JWT**: CSRF not needed (stateless authentication).

**For cookie-based sessions**: CSRF tokens required.

```python
# If you need CSRF exemption for specific API views (use cautiously!)
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

@method_decorator(csrf_exempt, name='dispatch')
class WebhookView(View):
    pass  # Only for webhooks from trusted sources
```

---

## 🔐 Secret Management

### Environment Variables

**✅ DO**:
- Store secrets in `.env` file (never committed)
- Use different secrets for each environment
- Rotate secrets regularly (90 days)

**❌ DON'T**:
- Hardcode secrets in code
- Commit `.env` to version control
- Share secrets via email/chat
- Reuse secrets across projects

### Secret Rotation Procedure

**When to Rotate**:
1. Every 90 days (routine)
2. Employee departure
3. Suspected compromise
4. After security incident

**How to Rotate SECRET_KEY**:
```bash
# 1. Generate new key
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# 2. Update .env with new key
SECRET_KEY=new-secret-key-here

# 3. Restart application
# All existing sessions will be invalidated (users must re-login)

# 4. Store old key securely for 30 days (for rollback if needed)
```

**How to Rotate GEMINI_API_KEY**:
```bash
# 1. Generate new key in Google AI Studio
# 2. Update .env
GEMINI_API_KEY=new-key-here

# 3. Test AI feedback generation
python manage.py shell
>>> from cases.llm_feedback_service import get_feedback_from_llm
>>> # Test with sample data...

# 4. Restart application
# 5. Disable old key in Google Cloud Console after 24 hours
```

### Checking for Exposed Secrets

**Use git-secrets or similar tools**:
```bash
# Install git-secrets
brew install git-secrets  # macOS
# or download from: https://github.com/awslabs/git-secrets

# Setup for repository
cd /path/to/gr4-gemini
git secrets --install
git secrets --register-aws

# Add custom patterns
git secrets --add 'GEMINI_API_KEY.*'
git secrets --add 'SECRET_KEY.*'

# Scan repository
git secrets --scan
```

---

## 🗄️ Database Security

### Connection Security

**Production Configuration**:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),  # ⚠️ NOT 'postgres' superuser!
        'PASSWORD': os.environ.get('DB_PASSWORD'),  # ⚠️ Strong password!
        'HOST': os.environ.get('DB_HOST'),  # ⚠️ Private network!
        'PORT': os.environ.get('DB_PORT', '5432'),
        'OPTIONS': {
            'sslmode': 'require',  # ✅ Enforce SSL in production
        },
    }
}
```

### Database User Permissions

**Create dedicated database user** (not superuser):
```sql
-- As postgres superuser
CREATE USER globalpeds_app WITH PASSWORD 'strong_password_here';
CREATE DATABASE globalpeds_production OWNER globalpeds_app;

-- Grant only necessary permissions
GRANT CONNECT ON DATABASE globalpeds_production TO globalpeds_app;
GRANT USAGE ON SCHEMA public TO globalpeds_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO globalpeds_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO globalpeds_app;
```

### Backup Encryption

**Encrypt database backups**:
```bash
# Backup with encryption
pg_dump globalpeds_production | gzip | openssl enc -aes-256-cbc -salt -out backup.sql.gz.enc

# Restore
openssl enc -aes-256-cbc -d -in backup.sql.gz.enc | gunzip | psql globalpeds_production
```

---

## 📡 HTTPS & Transport Security

### Force HTTPS in Production

**In settings.py** (production only):
```python
if not DEBUG:
    # Force HTTPS
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

    # HSTS (HTTP Strict Transport Security)
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

    # Prevent MIME sniffing
    SECURE_CONTENT_TYPE_NOSNIFF = True

    # XSS protection
    SECURE_BROWSER_XSS_FILTER = True
```

### Certificate Management

- Use Let's Encrypt for free SSL certificates
- Automate renewal (certbot)
- Monitor expiration dates

---

## 🔍 Logging & Monitoring

### Security Event Logging

**Log these events**:
1. Failed login attempts
2. Password changes
3. Permission changes
4. Data access/modifications by admins
5. API authentication failures

**Example**:
```python
import logging

security_logger = logging.getLogger('security')

class CustomLoginView(APIView):
    def post(self, request):
        username = request.data.get('username')

        # ... authentication logic ...

        if authentication_failed:
            security_logger.warning(
                f"Failed login attempt for user: {username} "
                f"from IP: {request.META.get('REMOTE_ADDR')}"
            )
            return Response({'error': 'Invalid credentials'}, status=401)

        security_logger.info(
            f"Successful login for user: {username} "
            f"from IP: {request.META.get('REMOTE_ADDR')}"
        )
```

### Monitoring for Attacks

**Signs of attack**:
1. High volume of 401/403 responses
2. Unusual API request patterns
3. Multiple failed logins from same IP
4. SQL injection attempts in logs
5. Abnormal AI API usage

---

## 🚨 Incident Response

### Security Incident Checklist

**If breach suspected**:

1. **Immediate Response** (within 1 hour):
   - [ ] Identify affected systems
   - [ ] Contain breach (disable accounts, block IPs)
   - [ ] Preserve evidence (logs, database snapshots)

2. **Assessment** (within 24 hours):
   - [ ] Determine what data was accessed
   - [ ] Identify attack vector
   - [ ] Assess scope of compromise

3. **Remediation**:
   - [ ] Patch vulnerabilities
   - [ ] Rotate all secrets
   - [ ] Force password resets for affected users
   - [ ] Review and update security policies

4. **Communication**:
   - [ ] Notify affected users
   - [ ] Report to authorities if required
   - [ ] Document incident

5. **Post-Incident**:
   - [ ] Conduct post-mortem
   - [ ] Update security practices
   - [ ] Implement additional monitoring

---

## ✅ Security Checklist

### Development
- [ ] `.env` file in `.gitignore`
- [ ] No hardcoded secrets in code
- [ ] All user input sanitized before LLM
- [ ] SQL queries use ORM or parameterized
- [ ] XSS protection on frontend
- [ ] CSRF protection enabled
- [ ] Authentication required for all API endpoints

### Staging/Production
- [ ] DEBUG = False
- [ ] ALLOWED_HOSTS restrictive
- [ ] CORS_ALLOWED_ORIGINS HTTPS only
- [ ] Strong SECRET_KEY (50+ chars)
- [ ] Strong database password (16+ chars)
- [ ] Database user not superuser
- [ ] SSL/TLS enabled for database
- [ ] HTTPS enforced (SECURE_SSL_REDIRECT)
- [ ] HSTS enabled
- [ ] Security headers configured
- [ ] Regular security updates
- [ ] Logging configured
- [ ] Monitoring active
- [ ] Backup encryption enabled

### Regular Maintenance
- [ ] Rotate secrets every 90 days
- [ ] Review user permissions quarterly
- [ ] Update dependencies monthly
- [ ] Review security logs weekly
- [ ] Test incident response plan annually
- [ ] Security audit annually

---

## 🛠️ Security Tools

### Recommended Tools

1. **Bandit**: Python security linter
```bash
pip install bandit
bandit -r backend/
```

2. **Safety**: Check for vulnerable dependencies
```bash
pip install safety
safety check
```

3. **OWASP ZAP**: Web application security scanner
```bash
# Download from: https://www.zaproxy.org/
# Run against staging environment
```

4. **Git-secrets**: Prevent committing secrets
```bash
# See "Checking for Exposed Secrets" section above
```

---

## 📚 Related Documentation

- @.claude/docs/ENVIRONMENT.md - Secure environment configuration
- @.claude/docs/RISK_ASSESSMENT.md - Security risk assessment
- @.claude/docs/MONITORING.md - Security event monitoring
- @.claude/docs/WORKFLOWS.md - Secure development workflows

---

## 📖 External Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Django Security](https://docs.djangoproject.com/en/5.0/topics/security/)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)
- [NIST Password Guidelines](https://pages.nist.gov/800-63-3/)

---

**💡 Remember**: Security is not a one-time effort. It requires ongoing vigilance, regular updates, and continuous improvement. When in doubt, err on the side of caution!
