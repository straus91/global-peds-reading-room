# 🚨 EMERGENCY FIX: 401 API & 404 Frontend Errors

**Date**: 2025-10-13
**Status**: ⚠️ **URGENT - SITE BROKEN**
**Estimated Fix Time**: 15-20 minutes
**Risk Level**: 🟢 **LOW** (configuration fix only, no code changes)

---

## 🔍 Problem Summary

After deploying Phase 1 analytics (commit `a0ad2de`), the Beta Droplet site is experiencing:
- ❌ **404 errors** on all pages (frontend and API)
- ❌ **401 errors** on API requests from frontend

**Root Cause**: Production server **missing `.env` file** with proper `ALLOWED_HOSTS` and `CORS_ALLOWED_ORIGINS` configuration.

---

## 📋 What Went Wrong

### Issue 1: Missing Production Environment Variables

The GitHub Actions deployment workflow **deploys code** but **does NOT deploy `.env` file** (by design - `.env` is in `.gitignore` for security).

**What This Means**:
- Django is using **default settings** from `settings.py`
- `ALLOWED_HOSTS` defaults to `localhost,127.0.0.1` → **doesn't include `64.225.17.0`**
- `CORS_ALLOWED_ORIGINS` defaults to `http://127.0.0.1:5500,http://localhost:5500` → **doesn't include production URL**
- Django **rejects all requests** from `http://64.225.17.0` as untrusted

### Issue 2: Possible Migration Not Applied

New migration `0009_phase1_foundation.py` adds 4 tables:
- `PromptVersion`
- `FeedbackCache`
- `TokenUsageLog`
- `AIFeedbackDetailedRating`

If migration didn't run during deployment → **API endpoints will crash**.

---

## ✅ Solution: Deploy Production `.env` File

**File Location**: `/mnt/c/Users/strau/Desktop/gr4-gemini/backend/.env.production`

This file contains correct settings for Beta Droplet:
- `ALLOWED_HOSTS=64.225.17.0,localhost,127.0.0.1`
- `CORS_ALLOWED_ORIGINS=http://64.225.17.0`
- `DEBUG=False`
- Strong `SECRET_KEY`
- All other required settings

---

## 🚀 Step-by-Step Fix Instructions

### Step 1: Access the Droplet

**Option A: DigitalOcean Console** (Easiest - Always Works)
1. Log in to [DigitalOcean](https://cloud.digitalocean.com/)
2. Navigate to **Droplets** → **global-readingroom**
3. Click **Access** tab → **Launch Droplet Console**
4. Log in as `root` (or `deploy` if you have password)

**Option B: SSH** (If Key Configured)
```bash
ssh root@64.225.17.0
```

---

### Step 2: Backup Existing Configuration (If Any)

```bash
# Navigate to project
cd /home/deploy/global-peds-reading-room/backend

# Check if .env exists
ls -la .env

# If exists, create backup
cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
```

---

### Step 3: Create New `.env` File

**Method A: Copy from Local Machine** (Recommended if you have SSH access)

On your **local Windows/WSL terminal**:
```bash
# Copy .env.production to droplet
scp backend/.env.production root@64.225.17.0:/tmp/env_production

# SSH to droplet
ssh root@64.225.17.0

# Move to correct location
sudo mv /tmp/env_production /home/deploy/global-peds-reading-room/backend/.env

# Set correct ownership and permissions
sudo chown deploy:deploy /home/deploy/global-peds-reading-room/backend/.env
sudo chmod 600 /home/deploy/global-peds-reading-room/backend/.env
```

**Method B: Manually Create via Console** (If no SSH key)

On the **droplet** (via console):
```bash
# Navigate to project
cd /home/deploy/global-peds-reading-room/backend

# Create .env file
nano .env
```

**Paste this content** (copy from `.env.production` file):
```env
SECRET_KEY=fov8yh0cj=j%%x#pwk8r6fbuh4jjg&=#+5p5l^%=te!q3-k36@
DEBUG=False
ALLOWED_HOSTS=64.225.17.0,localhost,127.0.0.1

DB_NAME=globalpeds_db
DB_USER=postgres
DB_PASSWORD=password
DB_HOST=localhost
DB_PORT=5432

CORS_ALLOWED_ORIGINS=http://64.225.17.0

ACCESS_TOKEN_LIFETIME=60
REFRESH_TOKEN_LIFETIME=7

GEMINI_API_KEY=AIzaSyBozAbFqUCWws_dpkGIK4-sA91lOny0404
GEMINI_API_RATE_LIMIT=10
```

**Save and exit**:
- Press `Ctrl+X`
- Press `Y` to confirm
- Press `Enter` to save

**Set correct permissions**:
```bash
chown deploy:deploy .env
chmod 600 .env
```

---

### Step 4: Verify Migration Applied

```bash
# Switch to deploy user context
cd /home/deploy/global-peds-reading-room/backend

# Activate virtual environment
source venv/bin/activate

# Check migrations status
python manage.py showmigrations cases | tail -5
```

**Expected Output** (should show `[X]` marks):
```
cases
 [X] 0007_alter_report_unique_together_report_is_archived
 [X] 0008_add_tutoring_models
 [X] 0009_phase1_foundation
```

**If `0009_phase1_foundation` is NOT checked `[X]`**, run:
```bash
python manage.py migrate
```

---

### Step 5: Verify `.env` File Loaded

```bash
# Still in activated venv
python manage.py shell
```

In the Python shell:
```python
import os
print("ALLOWED_HOSTS:", os.environ.get('ALLOWED_HOSTS'))
print("CORS_ALLOWED_ORIGINS:", os.environ.get('CORS_ALLOWED_ORIGINS'))
print("DEBUG:", os.environ.get('DEBUG'))
exit()
```

**Expected Output**:
```
ALLOWED_HOSTS: 64.225.17.0,localhost,127.0.0.1
CORS_ALLOWED_ORIGINS: http://64.225.17.0
DEBUG: False
```

**If variables are NOT loaded** (showing `None`), check:
- File location: `/home/deploy/global-peds-reading-room/backend/.env`
- File permissions: `ls -la .env` (should be owned by deploy)

---

### Step 6: Restart Services

```bash
# Restart Gunicorn to pick up new environment variables
sudo systemctl restart gunicorn

# Restart Nginx (just to be safe)
sudo systemctl restart nginx

# Wait for services to stabilize
sleep 5

# Check services are running
systemctl status gunicorn nginx postgresql
```

**Expected Output**:
- All services should show `active (running)` in green

---

### Step 7: Test API Endpoints

```bash
# Test API is accessible
curl -I http://64.225.17.0/api/

# Test API returns something (not 404)
curl http://64.225.17.0/api/cases/ | head -20
```

**Expected Results**:
- **Before fix**: `HTTP/1.1 404 Not Found` or no response
- **After fix**: `HTTP/1.1 401 Unauthorized` (means API is working, just needs authentication)
  - OR `HTTP/1.1 200 OK` with JSON data

**⚠️ If still getting 404**: Check Nginx logs (Step 9)

---

### Step 8: Test Frontend

**Open browser** and navigate to:
```
http://64.225.17.0/app/
```

**Check browser console** (F12 → Console tab):
- **Before fix**: CORS errors like `Access to XMLHttpRequest at 'http://64.225.17.0/api/...' has been blocked by CORS policy`
- **After fix**: No CORS errors (may have 401 errors if not logged in - that's OK!)

**Test pages**:
- ✅ Main page loads: `http://64.225.17.0/app/`
- ✅ Login page loads: `http://64.225.17.0/app/login.html`
- ✅ Admin dashboard loads: `http://64.225.17.0/app/admin/dashboard.html`

---

### Step 9: Check Logs for Errors

```bash
# Check Gunicorn logs (last 50 lines)
sudo tail -50 /var/log/gunicorn/gunicorn.log

# Check Nginx error log
sudo tail -50 /var/log/nginx/globalpeds_error.log

# Check Nginx access log (recent requests)
sudo tail -20 /var/log/nginx/globalpeds_access.log
```

**Look for**:
- ❌ `Invalid HTTP_HOST header` → ALLOWED_HOSTS issue (repeat Step 5-6)
- ❌ `CORS policy` → CORS_ALLOWED_ORIGINS issue (repeat Step 5-6)
- ❌ `relation "cases_promptversion" does not exist` → Migration not applied (repeat Step 4)

---

## ✅ Success Criteria

Deployment is fixed when:
- [x] API returns 401 or 200 (not 404): `curl -I http://64.225.17.0/api/`
- [x] Frontend pages load without errors: `http://64.225.17.0/app/`
- [x] No CORS errors in browser console
- [x] All services running: `systemctl status gunicorn nginx postgresql`
- [x] Gunicorn logs show no `Invalid HTTP_HOST` errors
- [x] Migration `0009_phase1_foundation` applied (checked `[X]`)

---

## 🐛 Troubleshooting

### Problem: Still Getting 404 Errors

**Possible Causes**:
1. `.env` file not in correct location
2. Gunicorn not restarted after `.env` created
3. `.env` file not readable by deploy user

**Solutions**:
```bash
# Verify file location
ls -la /home/deploy/global-peds-reading-room/backend/.env

# Verify permissions
# Should show: -rw------- 1 deploy deploy ... .env
# If not, fix with:
sudo chown deploy:deploy /home/deploy/global-peds-reading-room/backend/.env
sudo chmod 600 /home/deploy/global-peds-reading-room/backend/.env

# Restart Gunicorn again
sudo systemctl restart gunicorn

# Check if Gunicorn loaded .env
sudo journalctl -u gunicorn -n 50 | grep -i "ALLOWED_HOSTS\|error"
```

---

### Problem: Still Getting CORS Errors

**Possible Causes**:
1. `CORS_ALLOWED_ORIGINS` has trailing slash (should NOT have)
2. `CORS_ALLOWED_ORIGINS` has wrong protocol (should be `http://`)
3. Django CORS middleware not enabled

**Solutions**:
```bash
# Verify CORS setting (should be exactly: http://64.225.17.0)
cd /home/deploy/global-peds-reading-room/backend
source venv/bin/activate
python manage.py shell -c "import os; print('CORS:', os.environ.get('CORS_ALLOWED_ORIGINS'))"

# Check for trailing slash - if present, edit .env:
nano .env
# Change: CORS_ALLOWED_ORIGINS=http://64.225.17.0/
# To:     CORS_ALLOWED_ORIGINS=http://64.225.17.0
# (No trailing slash!)

# Restart Gunicorn
sudo systemctl restart gunicorn
```

---

### Problem: API Returns 500 Errors

**Possible Causes**:
1. Database migration not applied
2. Database connection error
3. GEMINI_API_KEY invalid or missing

**Solutions**:
```bash
# Check migration status
cd /home/deploy/global-peds-reading-room/backend
source venv/bin/activate
python manage.py showmigrations | grep -A 5 "0009_phase1_foundation"

# If not applied, run migration
python manage.py migrate

# Check database connection
python manage.py dbshell
# If connects successfully, type: \q to exit

# Check Gunicorn logs for specific error
sudo tail -100 /var/log/gunicorn/gunicorn.log | grep -i error
```

---

## 🔄 Rollback Procedure (If Needed)

If fix causes issues and you need to rollback:

```bash
# Restore previous .env (if you created backup in Step 2)
cd /home/deploy/global-peds-reading-room/backend
cp .env.backup.YYYYMMDD_HHMMSS .env

# Restart services
sudo systemctl restart gunicorn

# Verify
curl -I http://64.225.17.0/api/
```

**Note**: Rolling back `.env` will NOT rollback database migrations. Migrations are safe and should remain applied.

---

## 📚 Related Documentation

- **DEPLOYMENT_LOG.md** - Previous deployment history
- **DEPLOYMENT.md** - General deployment procedures
- **.claude/docs/ENVIRONMENT.md** - Environment variable details
- **.claude/docs/DEPLOYMENT.md** - Server configuration guide

---

## 💡 Preventing This In The Future

### For Future Deployments:

1. **Always verify `.env` exists on production** before deploying code changes
2. **Document required environment variables** for each feature
3. **Consider**: Add `.env.example.production` to repository (without secrets)
4. **Consider**: Automated deployment checklist that verifies `.env` presence

### For This Specific Issue:

**The `.env` file should have been deployed when the droplet was first set up.** This is a one-time setup that was missed.

**Going forward**: The `.env` file should remain on the server and NOT need redeployment unless:
- Adding new environment variables (e.g., new API keys)
- Changing ALLOWED_HOSTS (e.g., adding new domain)
- Rotating secrets (recommended every 90 days)

---

## ✅ Post-Fix Actions

After site is working:
- [ ] Update DEPLOYMENT_LOG.md with this fix
- [ ] Update DEPLOYMENT_STATUS.md to mark site as operational
- [ ] Monitor site for 24 hours to ensure stability
- [ ] Consider creating `.env.example.production` for future reference

---

**Last Updated**: 2025-10-13
**Environment**: Beta Droplet (64.225.17.0)
**Status After Fix**: ✅ **OPERATIONAL** (expected)
