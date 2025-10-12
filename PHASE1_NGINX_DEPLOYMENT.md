# Phase 1: Nginx Configuration Deployment Guide

## 📋 Overview

This guide covers deploying the Nginx configuration to implement the `/app/` prefix architecture on the beta server.

**Server Details:**
- IP: 64.225.17.0
- User: deploy
- Project Path: `/home/deploy/global-peds-reading-room`
- Services: Gunicorn (port 8001), Nginx, PostgreSQL

---

## ⚠️ Pre-Deployment Checklist

Before deploying, ensure:

- [ ] All frontend code changes committed and pushed to `online_beta` branch
- [ ] Current Nginx config backed up
- [ ] SSH access to server confirmed
- [ ] Services are currently running (check with deployment script)

---

## 🚀 Deployment Steps

### Step 1: Backup Current Configuration

```bash
# SSH into the server
ssh deploy@64.225.17.0

# Backup current Nginx config
sudo cp /etc/nginx/sites-available/globalpeds /etc/nginx/sites-available/globalpeds.backup.$(date +%Y%m%d_%H%M%S)

# Confirm backup created
ls -lh /etc/nginx/sites-available/globalpeds.backup*
```

### Step 2: Upload New Configuration

**From your local machine:**

```bash
# Navigate to project directory
cd /mnt/c/Users/strau/Desktop/gr4-gemini

# Copy configuration to server
scp nginx_app_prefix.conf deploy@64.225.17.0:/tmp/
```

**On the server:**

```bash
# Move to Nginx sites-available
sudo mv /tmp/nginx_app_prefix.conf /etc/nginx/sites-available/globalpeds

# Set correct permissions
sudo chown root:root /etc/nginx/sites-available/globalpeds
sudo chmod 644 /etc/nginx/sites-available/globalpeds
```

### Step 3: Test Configuration

```bash
# Test Nginx configuration syntax
sudo nginx -t
```

**Expected output:**
```
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful
```

**If errors occur:**
- Read error message carefully
- Common issues:
  - Path typos (check `/home/deploy/global-peds-reading-room/frontend/`)
  - Missing semicolons
  - Incorrect upstream server address

### Step 4: Deploy Frontend Code

```bash
# Navigate to project
cd /home/deploy/global-peds-reading-room

# Pull latest changes with /app/ prefix updates
git pull origin online_beta

# Verify frontend files exist
ls -la frontend/
ls -la frontend/admin/
```

### Step 5: Reload Nginx

```bash
# Reload Nginx (graceful reload, no downtime)
sudo systemctl reload nginx

# Check status
sudo systemctl status nginx

# View recent logs
sudo tail -50 /var/log/nginx/globalpeds_error.log
```

### Step 6: Verify Deployment

**Test frontend access:**
```bash
# Test root redirect
curl -I http://64.225.17.0/

# Should return: HTTP/1.1 301 Moved Permanently
# Location: /app/

# Test frontend serving
curl -I http://64.225.17.0/app/

# Should return: HTTP/1.1 200 OK

# Test admin page
curl -I http://64.225.17.0/app/admin/dashboard.html

# Should return: HTTP/1.1 200 OK
```

**Test API access:**
```bash
# Test API endpoint
curl http://64.225.17.0/api/

# Should return JSON response

# Test Django admin (will redirect to login)
curl -I http://64.225.17.0/admin/

# Should return: HTTP/1.1 302 Found (redirect to login)
```

---

## 🧪 Post-Deployment Testing

### Test 1: Frontend Loads

**Open in browser:**
1. Navigate to: http://64.225.17.0/app/
2. Should see the main landing page
3. Check browser console for errors (F12)

**Expected behavior:**
- Page loads without 404 errors
- CSS and JavaScript load correctly
- No console errors about missing files

### Test 2: Login Flow

1. Click "Login" button
2. Should navigate to: http://64.225.17.0/app/login.html
3. Enter credentials and login
4. Should redirect to: http://64.225.17.0/app/index.html (logged in)

**Watch for:**
- No redirect loops
- Tokens stored correctly
- API calls succeed

### Test 3: Admin Dashboard

1. Login as admin user
2. Navigate to: http://64.225.17.0/app/admin/dashboard.html
3. Should see admin dashboard
4. Click navigation links (Manage Cases, Manage Users, etc.)

**Verify:**
- All admin pages load
- Navigation works
- No 404 errors

### Test 4: API Endpoints

```bash
# Test authenticated endpoint (use actual token)
curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" http://64.225.17.0/api/users/me/

# Should return user data JSON
```

---

## 🔧 Troubleshooting

### Issue: 404 on /app/

**Symptoms:**
- Accessing http://64.225.17.0/app/ returns 404

**Diagnosis:**
```bash
# Check if frontend files exist
ls -la /home/deploy/global-peds-reading-room/frontend/

# Check Nginx error log
sudo tail -50 /var/log/nginx/globalpeds_error.log
```

**Solutions:**
- Verify `alias` path in Nginx config is correct
- Check file permissions: `sudo chmod -R 755 /home/deploy/global-peds-reading-room/frontend/`
- Ensure files were pulled from git

### Issue: 502 Bad Gateway on /api/

**Symptoms:**
- API requests return 502 error

**Diagnosis:**
```bash
# Check if Gunicorn is running
sudo systemctl status gunicorn

# Check Gunicorn logs
sudo tail -50 /var/log/gunicorn/gunicorn.log
```

**Solutions:**
- Restart Gunicorn: `sudo systemctl restart gunicorn`
- Check Gunicorn is listening on port 8001: `sudo netstat -tlnp | grep 8001`

### Issue: CORS Errors in Browser Console

**Symptoms:**
- Browser console shows: "CORS policy blocked..."

**Diagnosis:**
```bash
# Check Django CORS settings
cd /home/deploy/global-peds-reading-room/backend
source venv/bin/activate
python manage.py shell
```

```python
from django.conf import settings
print(settings.CORS_ALLOWED_ORIGINS)
# Should include: http://64.225.17.0 or http://64.225.17.0/app
```

**Solutions:**
- Update backend/.env:
  ```
  CORS_ALLOWED_ORIGINS=http://64.225.17.0
  ```
- Restart Gunicorn: `sudo systemctl restart gunicorn`

### Issue: Static Files (CSS/JS) Not Loading

**Symptoms:**
- Pages load but have no styling
- Browser console shows 404 for .css/.js files

**Diagnosis:**
- Open browser DevTools (F12) → Network tab
- Look at failed requests for CSS/JS
- Note the requested path

**Solutions:**
- Verify paths in HTML use `/app/` prefix
- Check browser is requesting correct URLs
- Hard refresh browser: Ctrl+Shift+R

---

## 🔄 Rollback Procedure

If issues occur and you need to rollback:

```bash
# Restore previous Nginx config
sudo cp /etc/nginx/sites-available/globalpeds.backup.YYYYMMDD_HHMMSS /etc/nginx/sites-available/globalpeds

# Test configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx

# Verify services
sudo systemctl status nginx
sudo systemctl status gunicorn

# Revert git changes
cd /home/deploy/global-peds-reading-room
git reset --hard HEAD~1  # Or specific commit hash
git pull origin online_beta  # Pull previous version
```

---

## ✅ Success Criteria

Phase 1 deployment is successful when:

- [ ] Root URL (http://64.225.17.0/) redirects to /app/
- [ ] Frontend loads at /app/ without errors
- [ ] All admin pages load at /app/admin/*
- [ ] API responds at /api/*
- [ ] Django admin accessible at /admin/
- [ ] No 404 errors in browser console
- [ ] No CORS errors in browser console
- [ ] Login flow works end-to-end
- [ ] Admin dashboard navigation works

---

## 📊 Monitoring After Deployment

**For the first 24 hours, monitor:**

1. **Nginx Access Logs**
   ```bash
   sudo tail -f /var/log/nginx/globalpeds_access.log
   ```

2. **Nginx Error Logs**
   ```bash
   sudo tail -f /var/log/nginx/globalpeds_error.log
   ```

3. **Gunicorn Logs**
   ```bash
   tail -f /var/log/gunicorn/gunicorn.log
   ```

4. **Service Status**
   ```bash
   watch -n 60 'systemctl is-active nginx gunicorn postgresql'
   ```

**Watch for:**
- Unusual 404 patterns (might indicate missed path updates)
- 502 errors (Gunicorn issues)
- High error rates

---

## 📞 Support

If issues persist after troubleshooting:

1. Collect logs:
   ```bash
   sudo tail -200 /var/log/nginx/globalpeds_error.log > /tmp/nginx_errors.log
   tail -200 /var/log/gunicorn/gunicorn.log > /tmp/gunicorn_errors.log
   ```

2. Document:
   - What you were testing
   - Expected vs actual behavior
   - Error messages
   - Steps already attempted

3. Review CLAUDE.md risk assessment guidelines
4. Check .claude/docs/TROUBLESHOOTING.md (if exists)

---

**Next Steps After Phase 1:**
- Phase 5: Local Testing (3-stage test strategy)
- Phase 6: Commit all changes with comprehensive message
