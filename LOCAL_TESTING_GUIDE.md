# Local Testing Guide - /app/ Prefix Implementation

## 📋 Overview

This guide provides a comprehensive testing strategy to validate the `/app/` prefix implementation before deploying to production.

**What Changed:**
- All HTML files now use absolute paths with `/app/` prefix
- All JavaScript pathname checks updated to match new URL structure
- Nginx configured to serve frontend under `/app/`
- Root URL (/) redirects to `/app/`

**Testing Goals:**
1. Verify all pages load without 404 errors
2. Confirm navigation works correctly
3. Validate login/authentication flow
4. Test admin dashboard functionality

---

## 🛠️ Setup: Local Testing Environment

### Option A: Using Python HTTP Server (Simple)

**Limitations:**
- Cannot test the full `/app/` prefix (serves from current directory)
- Best for checking individual page loads
- Cannot test Nginx redirect from `/` to `/app/`

```bash
# Navigate to frontend directory
cd /mnt/c/Users/strau/Desktop/gr4-gemini/frontend

# Start HTTP server on port 5500
python -m http.server 5500

# Access in browser:
# http://localhost:5500/index.html
# http://localhost:5500/admin/dashboard.html
```

**What to Test:**
- Check browser console for JavaScript errors
- Verify all CSS/JS files load
- Confirm pathname checks don't block page initialization

### Option B: Using Nginx Locally (Recommended)

**If you have Nginx installed on WSL:**

1. **Install Nginx (if not installed):**
   ```bash
   sudo apt update
   sudo apt install nginx
   ```

2. **Create local Nginx config:**
   ```bash
   sudo nano /etc/nginx/sites-available/globalpeds-local
   ```

3. **Add this configuration:**
   ```nginx
   server {
       listen 8080;
       server_name localhost;

       location /app/ {
           alias /mnt/c/Users/strau/Desktop/gr4-gemini/frontend/;
           try_files $uri $uri/ =404;
       }

       location = / {
           return 301 /app/;
       }

       # Proxy to Django backend (if running locally)
       location /api/ {
           proxy_pass http://localhost:8000;
           proxy_set_header Host $http_host;
       }

       location /admin/ {
           proxy_pass http://localhost:8000;
           proxy_set_header Host $http_host;
       }
   }
   ```

4. **Enable and test:**
   ```bash
   sudo ln -s /etc/nginx/sites-available/globalpeds-local /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   ```

5. **Access:** http://localhost:8080/

### Option C: Testing on Beta Server

**Most reliable method** - tests the actual production environment:

```bash
# SSH into beta server
ssh deploy@64.225.17.0

# Follow PHASE1_NGINX_DEPLOYMENT.md to deploy configuration

# Test directly on server
curl http://64.225.17.0/app/
```

---

## 🧪 3-Stage Testing Strategy

### Stage 1: Static File Serving ✅

**Goal:** Verify all HTML pages load and static assets resolve correctly.

#### Test 1.1: Root Redirect
```bash
# Test root URL redirects to /app/
curl -I http://localhost:8080/

# Expected: HTTP/1.1 301 Moved Permanently
# Location: /app/
```

#### Test 1.2: Main Pages Load
**In Browser:**
1. Navigate to: http://localhost:8080/app/
2. Open DevTools (F12) → Console tab
3. Verify no 404 errors
4. Check Network tab → All resources loaded (200 status)

**Pages to Test:**
- [ ] /app/ or /app/index.html
- [ ] /app/login.html
- [ ] /app/admin/dashboard.html
- [ ] /app/admin/manage-cases.html
- [ ] /app/admin/manage-users.html
- [ ] /app/admin/manage-templates.html
- [ ] /app/admin/add-case.html
- [ ] /app/admin/settings.html

**For Each Page:**
- [ ] Page loads without white screen
- [ ] No 404 errors in console
- [ ] All CSS loaded (page has styling)
- [ ] All JavaScript loaded (no script errors)

#### Test 1.3: Asset Paths
**In Browser DevTools → Network tab:**

Filter by type and verify paths:
- **CSS files:** Should load from `/app/css/...`
- **JS files:** Should load from `/app/js/...`
- **Images:** Should load from `/app/assets/img/...`

**Expected URL format:**
```
✅ http://localhost:8080/app/css/styles.css
✅ http://localhost:8080/app/js/api.js
✅ http://localhost:8080/app/assets/img/logo.png

❌ http://localhost:8080/css/styles.css (missing /app/)
❌ http://localhost:8080/app/app/css/styles.css (double /app/)
```

---

### Stage 2: Navigation & JavaScript ✅

**Goal:** Verify all JavaScript pathname checks work and navigation functions correctly.

#### Test 2.1: Pathname Check Initialization

**admin.js Line 327:**
```javascript
if (window.location.pathname.includes('/app/admin/manage-templates.html'))
```

**Test:**
1. Open: http://localhost:8080/app/admin/manage-templates.html
2. Open Console (F12)
3. Verify no warning: "Not on manage-templates.html page, skipping initialization"
4. Verify page initializes (tabs work, buttons clickable)

**Repeat for:**
- [ ] /app/admin/manage-users.html (admin-users.js line 19)
- [ ] /app/admin/manage-cases.html (admin-cases.js line 12)
- [ ] /app/admin/add-case.html (admin-cases.js line 15)

#### Test 2.2: Internal Navigation

**Test redirects and navigation links:**

1. **From index.html to login.html:**
   - Open: http://localhost:8080/app/
   - Click "Login" button
   - Verify URL: http://localhost:8080/app/login.html ✅

2. **Admin Dashboard Links:**
   - Open: http://localhost:8080/app/admin/dashboard.html
   - Click "Manage Cases" in sidebar
   - Verify URL: http://localhost:8080/app/admin/manage-cases.html ✅
   - Repeat for all sidebar links

3. **Manage Cases → Add Case:**
   - Open: http://localhost:8080/app/admin/manage-cases.html
   - Click "Edit" button on a case (admin-cases.js line 67)
   - Verify URL: http://localhost:8080/app/admin/add-case.html?edit_id=... ✅

4. **Add Case → Manage Templates:**
   - Open: http://localhost:8080/app/admin/add-case.html
   - Click "Create New Master Template" button (admin-case-edit.js line 100)
   - Verify URL: http://localhost:8080/app/admin/manage-templates.html?... ✅

#### Test 2.3: Conditional Logic

**main.js Login Redirects:**
```javascript
// Line 69, 109, 154, 184 - All redirect to '/app/login.html'
```

**Test Scenario: Unauthenticated Access**
1. Clear localStorage (DevTools → Application → Local Storage → Clear)
2. Try to access: http://localhost:8080/app/admin/dashboard.html
3. **Expected:** Redirects to http://localhost:8080/app/login.html

**admin.js Logout Functions:**
```javascript
// Lines 97-106 and 211-227 - Both redirect to '/app/login.html'
```

**Test Scenario: Logout**
1. Login to admin dashboard
2. Click "Logout" in header dropdown
3. **Expected:** Redirects to http://localhost:8080/app/login.html

**api.js Line 102-106: logoutUser() Pathname Checks**
```javascript
if (window.location.pathname !== '/app/login.html' &&
    window.location.pathname !== '/app/' &&
    window.location.pathname !== '/app/index.html')
```

**Test:** Token expiration should redirect, but NOT if already on login page

---

### Stage 3: Full Integration Testing ✅

**Goal:** Test complete user flows end-to-end with backend API.

**Prerequisites:**
- Django backend running (python manage.py runserver)
- Database populated with test data
- User accounts created (admin + regular user)

#### Test 3.1: Authentication Flow

**User Login:**
1. Navigate to http://localhost:8080/app/login.html
2. Enter valid credentials
3. Click "Login"
4. **Verify:**
   - [ ] Redirects to /app/index.html
   - [ ] Token stored in localStorage
   - [ ] No console errors
   - [ ] Username appears in header

**Admin Login:**
1. Navigate to http://localhost:8080/app/login.html
2. Login with admin credentials
3. Click "Admin Dashboard" (or navigate to /app/admin/dashboard.html)
4. **Verify:**
   - [ ] Dashboard loads
   - [ ] "Welcome back, [name]" toast appears
   - [ ] Sidebar navigation visible

**Logout:**
1. From admin dashboard, click "Logout"
2. **Verify:**
   - [ ] Redirects to /app/login.html
   - [ ] Tokens cleared from localStorage
   - [ ] Can't access admin pages without re-login

#### Test 3.2: Admin Dashboard Workflows

**Manage Users:**
1. Navigate to /app/admin/manage-users.html
2. **Verify:**
   - [ ] Users table loads
   - [ ] Tabs work (All Users, Pending Approvals, Administrators)
   - [ ] Filters work (role, status, search)
   - [ ] Action buttons appear (Approve, Edit, Delete)

**Manage Cases:**
1. Navigate to /app/admin/manage-cases.html
2. Click "Edit" on a case
3. **Verify:**
   - [ ] Redirects to /app/admin/add-case.html?edit_id=[id]
   - [ ] Case data populates form
   - [ ] "Update Case" button shows (not "Create Case")

**Add New Case:**
1. Navigate to /app/admin/add-case.html (no edit_id)
2. Fill in form
3. Click "Create Case"
4. **Verify:**
   - [ ] Case saved
   - [ ] URL updates to /app/admin/add-case.html?edit_id=[new_id]
   - [ ] Button text changes to "Update Case"
   - [ ] Success toast appears

**Manage Templates:**
1. Navigate to /app/admin/manage-templates.html
2. Switch tabs (Template List, Create Template)
3. **Verify:**
   - [ ] Tabs switch correctly
   - [ ] No console errors about pathname
   - [ ] Template form initializes

#### Test 3.3: Case Viewing (User Flow)

1. Login as regular user
2. Navigate to /app/index.html
3. Click on a case
4. **Verify:**
   - [ ] Case details load
   - [ ] Images display
   - [ ] Report form appears
5. Submit a report
6. **Verify:**
   - [ ] Report saved
   - [ ] AI feedback requested
   - [ ] No redirect loops

---

## 🐛 Common Issues & Solutions

### Issue: 404 on /app/

**Symptom:** Accessing /app/ shows 404 Not Found

**Diagnosis:**
- Check Nginx config: `location /app/` should use `alias`, not `root`
- Verify path: `/mnt/c/Users/strau/Desktop/gr4-gemini/frontend/`
- Check permissions: Files should be readable

**Solution:**
```bash
# Verify files exist
ls -la /mnt/c/Users/strau/Desktop/gr4-gemini/frontend/

# Fix permissions (if needed)
chmod -R 755 /mnt/c/Users/strau/Desktop/gr4-gemini/frontend/
```

### Issue: Double /app/app/ in URLs

**Symptom:** URLs show /app/app/css/styles.css

**Diagnosis:**
- HTML files have `/app/` prefix AND Nginx alias adds another
- Check HTML: `<link href="/app/css/styles.css">` with `alias /path/`

**Solution:**
- HTML should use: `href="/app/css/styles.css"`
- Nginx should use: `alias /mnt/c/.../frontend/;` (ends with /)
- Result: /app/css/styles.css → /mnt/c/.../frontend/css/styles.css

### Issue: Pathname Check Blocks Initialization

**Symptom:** Console shows "Not on manage-users.html page, skipping initialization"

**Diagnosis:**
- JavaScript checks for 'manage-users.html' but URL is '/app/admin/manage-users.html'
- Old code didn't include full path

**Solution:**
- Already fixed in Phase 4 ✅
- Verify pathname checks include '/app/admin/...'

### Issue: Redirect Loop on Login

**Symptom:** Logging in causes infinite redirects

**Diagnosis:**
- api.js logoutUser() checks pathname
- If check is wrong, might redirect even when on login page

**Solution:**
- Verify api.js line 102-106 checks for:
  - `/app/login.html`
  - `/app/`
  - `/app/index.html`

### Issue: CORS Errors in Console

**Symptom:** "CORS policy: No 'Access-Control-Allow-Origin' header"

**Diagnosis:**
- Django backend not allowing http://localhost:8080

**Solution:**
```bash
# Update backend/.env
CORS_ALLOWED_ORIGINS=http://localhost:8080,http://127.0.0.1:5500

# Restart Django
python backend/manage.py runserver
```

---

## ✅ Testing Checklist

### Stage 1: Static Files ✅
- [ ] Root redirects to /app/
- [ ] All 8 HTML pages load (index, login, 6 admin)
- [ ] No 404 errors in console
- [ ] All CSS loaded (pages styled)
- [ ] All JavaScript loaded (no script errors)
- [ ] Asset paths correct (/app/css/, /app/js/, /app/assets/)

### Stage 2: Navigation ✅
- [ ] Pathname checks work (pages initialize)
- [ ] Login button navigates to /app/login.html
- [ ] Admin sidebar links work
- [ ] Edit case button redirects correctly
- [ ] Create template button redirects correctly
- [ ] Logout redirects to /app/login.html
- [ ] No redirect loops

### Stage 3: Integration ✅
- [ ] User login flow works
- [ ] Admin login flow works
- [ ] Logout works
- [ ] Tokens stored/cleared correctly
- [ ] Admin dashboard loads
- [ ] Manage Users page works
- [ ] Manage Cases page works
- [ ] Add/Edit Case page works
- [ ] Manage Templates page works
- [ ] Case viewing works
- [ ] Report submission works

---

## 📊 Test Results Template

Use this template to document your test results:

```
=== LOCAL TESTING RESULTS ===
Date: [YYYY-MM-DD]
Tester: [Your Name]
Environment: [Local Nginx / Python Server / Beta Server]

STAGE 1: Static Files
- Root redirect: [PASS/FAIL]
- All pages load: [PASS/FAIL] - [X/8 pages]
- Console errors: [NONE / List errors]
- CSS loaded: [PASS/FAIL]
- JS loaded: [PASS/FAIL]
- Asset paths: [PASS/FAIL]

STAGE 2: Navigation
- Pathname checks: [PASS/FAIL]
- Login navigation: [PASS/FAIL]
- Admin navigation: [PASS/FAIL]
- Edit case redirect: [PASS/FAIL]
- Create template redirect: [PASS/FAIL]
- Logout redirect: [PASS/FAIL]

STAGE 3: Integration
- User login: [PASS/FAIL]
- Admin login: [PASS/FAIL]
- Logout: [PASS/FAIL]
- Admin dashboard: [PASS/FAIL]
- Manage Users: [PASS/FAIL]
- Manage Cases: [PASS/FAIL]
- Add/Edit Case: [PASS/FAIL]
- Manage Templates: [PASS/FAIL]

Issues Found:
1. [Description]
2. [Description]

Overall Result: [PASS / FAIL / PARTIAL]

Notes:
[Any additional observations]
```

---

## 🚀 Next Steps After Testing

**If all tests PASS:**
1. Document test results
2. Commit changes (see commit guide)
3. Deploy to beta server (PHASE1_NGINX_DEPLOYMENT.md)
4. Monitor for 24 hours
5. Deploy to production (if beta stable)

**If tests FAIL:**
1. Document specific failures
2. Review error messages
3. Check relevant code sections
4. Fix issues
5. Re-test
6. Repeat until all tests pass

---

**Testing is critical** - these changes affect every page. Don't skip any stage!
