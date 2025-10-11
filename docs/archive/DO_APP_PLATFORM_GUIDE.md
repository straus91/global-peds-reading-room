# 🔵 DigitalOcean App Platform - Complete Deployment Guide

**Created**: 2025-01-11
**Platform**: DigitalOcean App Platform
**Time Required**: 30-45 minutes
**Difficulty**: Beginner-friendly

---

## 📋 Prerequisites

### What You Need:
- [ ] DigitalOcean account (or will create new one)
- [ ] GitHub account with your project repository
- [ ] Google Gemini API key
- [ ] Credit card (for DigitalOcean billing)

### What You DON'T Need:
- ❌ SSH keys or terminal access
- ❌ Server administration knowledge
- ❌ Manual nginx/database configuration

---

## 🎯 Deployment Overview

Your app will have:
1. **Web Service**: Django backend on DigitalOcean App Platform
2. **Database**: Managed PostgreSQL with automatic backups
3. **Static Files**: Served via App Platform
4. **Frontend**: Vanilla JS served alongside backend
5. **SSL Certificate**: Automatic and free
6. **Custom Domain**: Optional (can add later)

---

## 📝 Step 1: Prepare Your Repository

### 1.1 Commit Current Changes

```bash
cd /mnt/c/Users/strau/Desktop/gr4-gemini

# Check what needs to be committed
git status

# Add all changes (including new deployment docs)
git add -A

# Commit
git commit -m "Add deployment documentation and prepare for DO App Platform"

# Push to GitHub
git push origin online_beta
```

### 1.2 Create Required Configuration Files

Create these files in your project root:

#### `runtime.txt`
```
python-3.8
```

#### `build.sh` (App Platform build script)
```bash
#!/bin/bash
# Build script for DigitalOcean App Platform

# Install Python dependencies
pip install -r backend/requirements.txt

# Collect static files
cd backend
python manage.py collectstatic --noinput --clear

# Run migrations (DO will run this automatically)
python manage.py migrate --noinput
```

#### `gunicorn_config.py` (in backend/)
```python
# Gunicorn configuration for production
bind = "0.0.0.0:8000"
workers = 2
threads = 4
timeout = 120
keepalive = 5
errorlog = "-"
accesslog = "-"
loglevel = "info"
```

#### Update `.gitignore` (if not already there)
```
# Environment files
.env
.env.production
*.env.local

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
ENV/

# Django
*.log
local_settings.py
db.sqlite3
staticfiles/
media/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
```

---

## 🔵 Step 2: DigitalOcean Account Setup

### 2.1 Option A: Existing Account (You Have One!)

1. Go to https://cloud.digitalocean.com/login
2. Try to login with your email
3. **If you forgot password**:
   - Click "Forgot password?"
   - Check your email
   - Reset password
   - **Set up 2FA** (so you don't lose access again!)
   - Consider using a password manager (1Password, Bitwarden, etc.)

4. **If you can't access email or 2FA**:
   - Contact DO support: https://www.digitalocean.com/support
   - They can help reset your account
   - Have your billing info ready for verification

### 2.2 Option B: New Account

1. Go to https://cloud.digitalocean.com/registrations/new
2. Sign up with email or GitHub
3. Verify your email
4. Add payment method
5. **Set up 2FA immediately**: Account → Settings → Security → Two-Factor Authentication

### 2.3 Enable Billing

- Add credit card or PayPal
- No charges until you deploy (except free tier)
- Set up billing alerts: Billing → Settings → Billing Alerts
  - Recommended: Alert at $20, $40, $60

---

## 🔗 Step 3: Connect GitHub Repository

### 3.1 Authorize DigitalOcean on GitHub

1. In DigitalOcean dashboard, click **Create** → **Apps**
2. Click **GitHub** as source
3. Click **Authorize DigitalOcean**
4. You'll be redirected to GitHub
5. Select repositories to allow:
   - **Recommended**: Select only "global-peds-reading-room"
   - Or select "All repositories" if you prefer
6. Click **Install & Authorize**

### 3.2 Select Repository

1. Back in DO dashboard, you'll see your repositories
2. Select **straus91/global-peds-reading-room**
3. Select branch: **online_beta**
4. Click **Next**

---

## ⚙️ Step 4: Configure Your App

### 4.1 App Settings

**App Name**: `globalpeds-beta` (or your preferred name)
- This will be part of your URL: `globalpeds-beta.ondigitalocean.app`

**Region**:
- Choose closest to your users
- Recommended: `New York` or `San Francisco`

### 4.2 Configure Web Service

DO should auto-detect Django. If not, configure manually:

**Name**: `web`

**Environment**:
- **Type**: Python
- **Python Version**: 3.8

**Build Command**:
```bash
pip install -r backend/requirements.txt && python backend/manage.py collectstatic --noinput
```

**Run Command**:
```bash
cd backend && gunicorn globalpeds_project.wsgi:application --bind 0.0.0.0:8000
```

**HTTP Port**: `8000`

**Source Directory**: `/` (root of repository)

**Instance Size**:
- **Testing**: Basic ($5/month) - 512MB RAM
- **Production**: Professional ($12/month) - 1GB RAM

**Instance Count**: `1` (can scale later)

### 4.3 Add Static Site (Frontend)

Click **Add Component** → **Static Site**

**Name**: `frontend`

**Source Directory**: `/frontend`

**Output Directory**: `/` (same as source)

**Routes**: Leave default (will be accessible at `/`)

---

## 🗄️ Step 5: Add Database

### 5.1 Create PostgreSQL Database

Click **Add Resource** → **Database**

**Database Engine**: PostgreSQL

**Version**: 14 (or latest)

**Database Name**: `globalpeds_db`

**Plan**:
- **Testing**: Development ($7/month) - 1GB RAM, 10GB storage
- **Production**: Basic ($15/month) - 1GB RAM, 10GB storage, daily backups

**Region**: Same as your app

Click **Add Database**

### 5.2 Database Connection

DO will automatically:
- Create database
- Set up user/password
- Add connection string to environment variables
- Configure connection pooling

**Environment variable created**: `${db.DATABASE_URL}`

---

## 🔐 Step 6: Configure Environment Variables

Click on your **web** service → **Environment Variables**

### 6.1 Add Required Variables

Click **Edit** and add these variables:

```
# Django Configuration
SECRET_KEY=<generate-new-50-char-key>
DEBUG=False
ALLOWED_HOSTS=globalpeds-beta.ondigitalocean.app

# Database (automatically added by DO)
DATABASE_URL=${db.DATABASE_URL}

# Alternative: Manual database config (if not using DATABASE_URL)
DB_NAME=${db.DATABASE}
DB_USER=${db.USERNAME}
DB_PASSWORD=${db.PASSWORD}
DB_HOST=${db.HOSTNAME}
DB_PORT=${db.PORT}

# Google Gemini API
GEMINI_API_KEY=<your-gemini-api-key>
GEMINI_API_RATE_LIMIT=10

# CORS Configuration
CORS_ALLOWED_ORIGINS=https://globalpeds-beta.ondigitalocean.app

# JWT Settings
ACCESS_TOKEN_LIFETIME=30
REFRESH_TOKEN_LIFETIME=7

# Email (optional - configure later)
# EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
# EMAIL_HOST=smtp.gmail.com
# EMAIL_PORT=587
# EMAIL_USE_TLS=True
# EMAIL_HOST_USER=your-email@gmail.com
# EMAIL_HOST_PASSWORD=your-app-password
```

### 6.2 Generate SECRET_KEY

Run locally:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Copy the output and paste as `SECRET_KEY` value.

### 6.3 Mark Secrets as Encrypted

- Click the eye icon next to sensitive values (SECRET_KEY, GEMINI_API_KEY, etc.)
- This encrypts them in DO's system

---

## 🎯 Step 7: Update Django Settings for App Platform

### 7.1 Modify `settings.py` for DATABASE_URL Support

Add to `backend/globalpeds_project/settings.py`:

```python
import os
import dj_database_url  # Add this to requirements.txt
from pathlib import Path
from dotenv import load_dotenv

# ... existing code ...

# Database Configuration - Support both DATABASE_URL and individual vars
if os.environ.get('DATABASE_URL'):
    # DigitalOcean App Platform provides DATABASE_URL
    DATABASES = {
        'default': dj_database_url.config(
            default=os.environ.get('DATABASE_URL'),
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
else:
    # Fallback to individual environment variables (local development)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('DB_NAME', 'globalpeds_db'),
            'USER': os.environ.get('DB_USER', 'postgres'),
            'PASSWORD': os.environ.get('DB_PASSWORD', 'password'),
            'HOST': os.environ.get('DB_HOST', 'localhost'),
            'PORT': os.environ.get('DB_PORT', '5432'),
        }
    }

# ... rest of settings ...
```

### 7.2 Add `dj-database-url` to requirements.txt

```bash
cd backend
echo "dj-database-url==2.1.0" >> requirements.txt
```

### 7.3 Update STATIC files configuration

```python
# backend/globalpeds_project/settings.py

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Additional locations of static files
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# Whitenoise for static files (add to requirements.txt)
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

### 7.4 Add whitenoise to requirements.txt

```bash
echo "whitenoise==6.6.0" >> requirements.txt
```

### 7.5 Commit These Changes

```bash
git add -A
git commit -m "Configure for DigitalOcean App Platform deployment"
git push origin online_beta
```

---

## 🚀 Step 8: Launch Your App

### 8.1 Review Configuration

Back in DO dashboard:
- Review all settings
- Verify environment variables
- Check database connection
- Review pricing estimate

### 8.2 Create App

Click **Create Resources** button

DO will now:
1. ✅ Clone your repository
2. ✅ Build your application
3. ✅ Create database
4. ✅ Run migrations
5. ✅ Collect static files
6. ✅ Deploy application
7. ✅ Set up SSL certificate
8. ✅ Configure health checks

**This takes 5-10 minutes** ⏱️

### 8.3 Monitor Build

You'll see real-time build logs:
- Installing dependencies
- Running collectstatic
- Running migrations
- Deploying containers

**Common issues during first build**:
- Missing dependencies → Add to requirements.txt
- Migration errors → Check database connection
- Static files issues → Verify STATIC_ROOT setting

---

## ✅ Step 9: Verify Deployment

### 9.1 Access Your App

Once deployment completes:
1. Click on your app name
2. Copy the URL: `https://globalpeds-beta.ondigitalocean.app`
3. Open in browser

### 9.2 Create Superuser

You need to run this via DO's console:

1. In DO dashboard, click **Console** (terminal icon)
2. Select **web** component
3. Run:
```bash
python manage.py createsuperuser
```
4. Follow prompts to create admin account

### 9.3 Test Functionality

- [ ] Frontend loads correctly
- [ ] Can access login page
- [ ] Can login with superuser
- [ ] Admin panel accessible (`/admin`)
- [ ] API endpoints working (`/api/`)
- [ ] DICOM viewer loads (if Orthanc configured)

---

## 🌐 Step 10: Custom Domain (Optional)

### 10.1 Add Domain to App

1. In app settings, click **Domains**
2. Click **Add Domain**
3. Enter your domain: `globalpeds.yourdomain.com`
4. DO will provide DNS records

### 10.2 Configure DNS

In your domain registrar (Namecheap, GoDaddy, etc.):

```
Type: CNAME
Name: globalpeds
Value: globalpeds-beta.ondigitalocean.app
TTL: 3600
```

### 10.3 Wait for Propagation

- DNS changes take 5-60 minutes
- SSL certificate issued automatically
- DO will show "Active" when ready

### 10.4 Update Environment Variables

```
ALLOWED_HOSTS=globalpeds.yourdomain.com,globalpeds-beta.ondigitalocean.app
CORS_ALLOWED_ORIGINS=https://globalpeds.yourdomain.com
```

Redeploy for changes to take effect.

---

## 📊 Step 11: Set Up Monitoring

### 11.1 Enable App Insights

1. Go to app → **Insights** tab
2. View metrics:
   - Request rate
   - Response times
   - Error rates
   - Resource usage

### 11.2 Configure Alerts

1. Go to **Settings** → **Alerts**
2. Add alerts for:
   - High error rate (> 5%)
   - High response time (> 2 seconds)
   - High memory usage (> 80%)
   - Down/unhealthy status

### 11.3 Set Up Billing Alerts

1. Go to **Billing** → **Settings**
2. Add alerts at:
   - $20 (unexpected usage)
   - $40 (approaching budget)
   - $60 (budget limit)

---

## 🔄 Step 12: Set Up Auto-Deploy

### 12.1 Enable Auto-Deploy

1. In app settings → **Settings**
2. Find "Auto-Deploy" section
3. **Enable** auto-deploy for `online_beta` branch

Now, every push to `online_beta` automatically deploys!

### 12.2 Deployment Workflow

```bash
# Make changes locally
git add -A
git commit -m "Add new feature"
git push origin online_beta

# DO automatically:
# - Detects push
# - Builds app
# - Runs tests (if configured)
# - Deploys new version
# - Zero-downtime rollover
```

---

## 🎉 Success! Your App is Live

### What You Have Now:
- ✅ Django backend running on DO App Platform
- ✅ Managed PostgreSQL database with backups
- ✅ Automatic SSL certificate
- ✅ Git-based deployment (push to deploy)
- ✅ Zero-downtime deployments
- ✅ Automatic health checks and restarts
- ✅ Centralized logging
- ✅ Metrics and monitoring

### Your URLs:
- **App**: https://globalpeds-beta.ondigitalocean.app
- **Admin**: https://globalpeds-beta.ondigitalocean.app/admin
- **API**: https://globalpeds-beta.ondigitalocean.app/api

### Monthly Cost:
```
Web Service (Professional): $12/month
PostgreSQL (Basic):         $15/month
──────────────────────────────────
Total:                      $27/month
```

---

## 🔧 Common Tasks

### View Logs
1. Go to app → **Runtime Logs**
2. Filter by component (web, database)
3. Search for errors or specific messages

### Restart App
1. Go to app dashboard
2. Click **Actions** → **Restart All Components**
3. Restarts without downtime

### Scale Resources
1. Go to **web** component → **Settings**
2. Change **Instance Size** or **Instance Count**
3. Click **Save**
4. Redeploys with new resources

### Rollback Deployment
1. Go to **Deployments** tab
2. Find previous working deployment
3. Click **Rollback to this Deployment**
4. Confirm rollback
5. Takes ~2 minutes

### Access Database
1. Go to database → **Connection Details**
2. Use provided credentials
3. Connect via:
   - `psql` command line
   - pgAdmin
   - DBeaver
   - Any PostgreSQL client

---

## 🚨 Troubleshooting Quick Reference

### Build Fails
- Check build logs for specific error
- Verify requirements.txt is complete
- Ensure Python version matches

### Database Connection Error
- Verify DATABASE_URL is set
- Check database is created
- Ensure app and DB in same region

### Static Files Not Loading
- Run `collectstatic` in build command
- Verify STATIC_ROOT setting
- Check whitenoise is installed

### Environment Variables Not Working
- Redeploy after changing variables
- Verify variable names (case-sensitive)
- Check for typos

See **TROUBLESHOOTING.md** for detailed solutions.

---

## 📚 Next Steps

Now that you're deployed:

1. **Read DEPLOYMENT_WORKFLOW.md** - Learn day-to-day operations
2. **Set up preview environments** - Test features before production
3. **Configure backups** - Already automatic, but verify
4. **Plan AI upgrades** - Read AI_FEATURES_INFRASTRUCTURE.md
5. **Monitor costs** - Check dashboard weekly

---

## 📖 Related Documentation

- **DEPLOYMENT_COMPARISON.md** - Why we chose DO App Platform
- **DEPLOYMENT_WORKFLOW.md** - Day-to-day operations
- **AI_FEATURES_INFRASTRUCTURE.md** - Adding Redis, Celery later
- **DATABASE_MIGRATION.md** - Safe database updates
- **TROUBLESHOOTING.md** - Common problems and solutions

---

**Congratulations!** 🎉 You've successfully deployed Global Peds Reading Room to DigitalOcean App Platform!

**Last Updated**: 2025-01-11
**Deployment Time**: ~45 minutes
**Next Document**: DEPLOYMENT_WORKFLOW.md