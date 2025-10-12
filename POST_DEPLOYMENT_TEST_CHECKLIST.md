# Post-Deployment Testing Checklist

## 🎯 Purpose

Quick checklist to verify the `/app/` prefix architecture is working correctly after applying `nginx_app_prefix.conf`.

**Estimated Time**: 10-15 minutes

---

## Pre-Test: Verify Nginx Configuration Applied

```bash
# SSH to droplet
ssh deploy@64.225.17.0

# Verify config has /app/ location block
sudo grep -n "location /app/" /etc/nginx/sites-available/globalpeds

# If you see line numbers, config is applied ✅
# If you see nothing, config NOT applied ❌ (see EMERGENCY_FIX_NGINX.md)

# Check Nginx is running
systemctl is-active nginx
```

---

## Test 1: Root URL Redirect ✅

**Test**: Root URL redirects to `/app/`

**Command Line Test**:
```bash
curl -I http://64.225.17.0/
```

**Expected Output**:
```
HTTP/1.1 301 Moved Permanently
Location: /app/
```

**Browser Test**:
1. Open: http://64.225.17.0/
2. Should redirect to: http://64.225.17.0/app/

**Status**: [ ] PASS [ ] FAIL

---

## Test 2: Frontend Pages Load Without 404 Errors ✅

**Test**: All HTML pages load with correct assets

### 2.1 Main Landing Page

**URL**: http://64.225.17.0/app/

**Checks**:
- [ ] Page loads (not blank/white screen)
- [ ] Page has styling (CSS loaded)
- [ ] Logo visible
- [ ] Navigation visible
- [ ] No errors in browser console (F12)

**Browser Console Check**:
```
Open DevTools (F12) → Console tab
Look for errors (red text)
Expected: No 404 errors
```

**Status**: [ ] PASS [ ] FAIL

---

### 2.2 Login Page

**URL**: http://64.225.17.0/app/login.html

**Checks**:
- [ ] Page loads with styling
- [ ] Logo visible
- [ ] Login form visible
- [ ] No 404 errors in console

**Status**: [ ] PASS [ ] FAIL

---

### 2.3 Admin Dashboard (After Login)

**URL**: http://64.225.17.0/app/admin/dashboard.html

**Prerequisites**: Log in first (may redirect to login if not authenticated)

**Checks**:
- [ ] Dashboard loads
- [ ] Sidebar navigation visible
- [ ] Welcome toast appears
- [ ] No 404 errors in console
- [ ] CSS and JS files loaded (check Network tab)

**Status**: [ ] PASS [ ] FAIL

---

### 2.4 Other Admin Pages

Test each admin page (click links or visit directly):

| Page | URL | Status |
|------|-----|--------|
| Manage Cases | http://64.225.17.0/app/admin/manage-cases.html | [ ] PASS [ ] FAIL |
| Manage Users | http://64.225.17.0/app/admin/manage-users.html | [ ] PASS [ ] FAIL |
| Add Case | http://64.225.17.0/app/admin/add-case.html | [ ] PASS [ ] FAIL |
| Manage Templates | http://64.225.17.0/app/admin/manage-templates.html | [ ] PASS [ ] FAIL |
| Settings | http://64.225.17.0/app/admin/settings.html | [ ] PASS [ ] FAIL |

**Expected**: All pages load without 404 errors

---

## Test 3: Asset Paths Correct ✅

**Test**: CSS, JS, and image files load from `/app/` prefix

**Browser DevTools Test**:
1. Open any page: http://64.225.17.0/app/
2. Open DevTools (F12) → Network tab
3. Filter by "CSS", "JS", "Img"
4. Refresh page (Ctrl+Shift+R for hard refresh)

**Expected URL Format**:
```
✅ http://64.225.17.0/app/css/styles.css
✅ http://64.225.17.0/app/js/api.js
✅ http://64.225.17.0/app/assets/img/logo.png

❌ http://64.225.17.0/css/styles.css (missing /app/)
❌ http://64.225.17.0/app/app/css/styles.css (double /app/)
```

**Status**: [ ] PASS [ ] FAIL

---

## Test 4: Navigation Works ✅

**Test**: All navigation links use correct paths

### 4.1 Login → Dashboard
1. Go to: http://64.225.17.0/app/login.html
2. Log in with valid credentials
3. Should redirect to: http://64.225.17.0/app/index.html OR dashboard

**Status**: [ ] PASS [ ] FAIL

---

### 4.2 Admin Sidebar Navigation
1. Go to admin dashboard: http://64.225.17.0/app/admin/dashboard.html
2. Click each sidebar link:
   - Dashboard
   - Manage Cases
   - Manage Users
   - Manage Templates
   - Add Case
   - Settings

**Expected**: Each link navigates to `/app/admin/[page].html`

**Status**: [ ] PASS [ ] FAIL

---

### 4.3 Edit Case Redirect
1. Go to: http://64.225.17.0/app/admin/manage-cases.html
2. Click "Edit" button on any case
3. Should redirect to: http://64.225.17.0/app/admin/add-case.html?edit_id=[number]

**Status**: [ ] PASS [ ] FAIL

---

## Test 5: Logout Works (Critical Bug Fix) 🔴

**Test**: The CRITICAL production bug fix (admin.js:97-106)

### 5.1 Admin Logout
1. Log in to admin dashboard
2. Click profile dropdown in header
3. Click "Logout"

**Expected**:
- Redirects to: http://64.225.17.0/app/login.html
- No errors in console
- No infinite redirect loop
- Can log in again successfully

**Status**: [ ] PASS [ ] FAIL

**⚠️ If this fails**: The critical bug fix didn't work. Check admin.js lines 97-106.

---

## Test 6: API Endpoints Still Work ✅

**Test**: Django REST API unaffected by Nginx changes

### 6.1 API Root
**URL**: http://64.225.17.0/api/

**Expected**: JSON response (not 404)

**Command Line Test**:
```bash
curl http://64.225.17.0/api/
```

**Expected Output**: JSON response (may be empty array or list of endpoints)

**Status**: [ ] PASS [ ] FAIL

---

### 6.2 Login API (If Not Authenticated)
**URL**: http://64.225.17.0/api/auth/login/ (or similar)

**Test**: API accepts POST requests

**Status**: [ ] PASS [ ] FAIL

---

### 6.3 Authenticated API Request
**Prerequisites**: Get access token by logging in

**Test**: Make authenticated request to protected endpoint

**Expected**: Returns data (not 401 Unauthorized)

**Status**: [ ] PASS [ ] FAIL

---

## Test 7: Django Admin Unaffected ✅

**Test**: Django admin interface at `/admin/` still works

**URL**: http://64.225.17.0/admin/

**Expected**:
- Redirects to: http://64.225.17.0/admin/login/
- Admin login page loads
- Can log in with Django admin credentials
- Django admin interface fully functional

**Status**: [ ] PASS [ ] FAIL

**⚠️ Important**: `/admin/` is Django admin, `/app/admin/` is your custom frontend admin dashboard. Both should work independently.

---

## Test 8: Complete User Workflow ✅

**Test**: End-to-end user experience

### 8.1 New User Registration (If Applicable)
**Status**: [ ] PASS [ ] FAIL [ ] N/A

---

### 8.2 User Login → View Cases → Submit Report
1. Log in as regular user
2. Browse cases: http://64.225.17.0/app/
3. Click on a case
4. View case details
5. Submit a report
6. Request AI feedback
7. Rate AI feedback

**Expected**: Entire workflow completes without errors

**Status**: [ ] PASS [ ] FAIL

---

### 8.3 Admin Workflow
1. Log in as admin
2. Navigate to: http://64.225.17.0/app/admin/dashboard.html
3. Create a new case
4. Edit existing case
5. Manage users
6. Manage templates

**Expected**: All admin operations work without errors

**Status**: [ ] PASS [ ] FAIL

---

## Test 9: Error Logs Clean ✅

**Test**: No unexpected errors in server logs

```bash
# SSH to droplet
ssh deploy@64.225.17.0

# Check Nginx error log (last 50 lines)
sudo tail -50 /var/log/nginx/globalpeds_error.log

# Check Gunicorn log (last 50 lines)
tail -50 /var/log/gunicorn/gunicorn.log
```

**Expected**:
- No 404 errors for /app/css/... or /app/js/...
- No "file not found" errors
- No permission denied errors
- Only normal operational logs

**Status**: [ ] PASS [ ] FAIL

---

## Test 10: Service Status ✅

**Test**: All services running correctly

```bash
# SSH to droplet
ssh deploy@64.225.17.0

# Check service status
echo "Service Status:"
echo "  Gunicorn: $(systemctl is-active gunicorn)"
echo "  Nginx: $(systemctl is-active nginx)"
echo "  PostgreSQL: $(systemctl is-active postgresql)"

# Expected output: all should show "active"
```

**Status**: [ ] PASS [ ] FAIL

---

## Issues Found 🐛

**Document any issues here:**

### Issue 1:
- **Description**:
- **Test Failed**:
- **Error Message**:
- **Screenshot/Log**:

### Issue 2:
- **Description**:
- **Test Failed**:
- **Error Message**:
- **Screenshot/Log**:

---

## Overall Result

**Total Tests**: 10 categories (with multiple sub-tests)

**Passed**: [ ___ ] / 10

**Failed**: [ ___ ] / 10

**Overall Status**: [ ] ✅ ALL PASS [ ] ⚠️ PARTIAL [ ] ❌ FAILED

---

## Next Steps Based on Results

### If ALL Tests Pass ✅

**Congratulations!** Deployment successful.

**Next steps**:
1. Monitor site for 24 hours
2. Check error logs daily for first week
3. Document deployment date and commit hash
4. Update team/stakeholders
5. Consider additional testing (performance, load, security)

---

### If Some Tests Fail ⚠️

**Identify failure category**:

1. **404 Errors on Assets**:
   - See EMERGENCY_FIX_NGINX.md → Troubleshooting → Issue 4
   - Verify Nginx config applied correctly
   - Check frontend directory permissions

2. **API Issues**:
   - Check Gunicorn is running: `systemctl status gunicorn`
   - Check backend logs: `tail -100 /var/log/gunicorn/gunicorn.log`
   - Verify Django settings correct

3. **Navigation/Redirect Issues**:
   - Check JavaScript files deployed correctly
   - Verify pathname checks updated (see COMMIT_MESSAGE.md Phase 4)
   - Clear browser cache and retry

4. **Service Not Running**:
   - Restart services: `sudo systemctl restart gunicorn nginx`
   - Check logs for errors
   - Verify no port conflicts

---

### If Most Tests Fail ❌

**Consider rollback**:

See EMERGENCY_FIX_NGINX.md → Rollback Procedure

**Steps**:
1. Restore previous Nginx configuration
2. Reload Nginx
3. Verify site works with old configuration
4. Investigate issues before retrying

---

## Testing Timestamp

**Tester**: _______________

**Date**: _______________

**Time**: _______________

**Commit Hash**: 6a1e947 (or current)

**Branch**: online_beta

---

## Additional Notes

[Add any observations, concerns, or recommendations here]

---

**📊 Save this checklist for future deployments!**
