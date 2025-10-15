# Frontend API Call Patterns - MANDATORY REFERENCE

## 🎯 Purpose

This document explains how the `apiRequest()` function works and provides the CORRECT pattern for making API calls in the frontend. **Read this BEFORE making any frontend API changes!**

---

## ⚠️ CRITICAL: How apiRequest() Works

The `apiRequest()` function in `frontend/js/api.js` (line 119-212) automatically prepends the base URL to your endpoint.

### Base URL Construction (from config.js)

**In Production/Beta (64.225.17.0)**:
```javascript
APP_CONFIG.api.getBaseUrl() // Returns: "/api"
```

**In Local Development (localhost)**:
```javascript
APP_CONFIG.api.getBaseUrl() // Returns: "http://127.0.0.1:8000/api"
```

### How apiRequest() Constructs URLs

**From api.js line 120**:
```javascript
const url = endpoint.startsWith('/')
    ? `${APP_CONFIG.api.getBaseUrl()}${endpoint}`
    : `${APP_CONFIG.api.getBaseUrl()}/${endpoint}`;
```

**Example**:
```javascript
// Production:
apiRequest('/cases/reports/')
// Becomes: "/api" + "/cases/reports/" = "/api/cases/reports/" ✅

// Development:
apiRequest('/cases/reports/')
// Becomes: "http://127.0.0.1:8000/api" + "/cases/reports/"
//        = "http://127.0.0.1:8000/api/cases/reports/" ✅
```

---

## ✅ CORRECT Pattern (Always Use This)

**Rule**: Always use relative paths WITHOUT the `/api/` prefix.

The `apiRequest()` function adds `/api/` automatically!

### Examples from Working Code

```javascript
// From main.js line 131 - User details
apiRequest('/users/me/')
// ✅ Becomes: /api/users/me/

// From main.js line 485 - My reports
apiRequest('/cases/my-reports/')
// ✅ Becomes: /api/cases/my-reports/

// From main.js line 1575 - Create report
apiRequest('/cases/reports/', { method: 'POST', ... })
// ✅ Becomes: /api/cases/reports/

// AI feedback retrieval (CORRECT)
apiRequest(`/cases/reports/${reportId}/ai-feedback/`, { method: 'GET' })
// ✅ Becomes: /api/cases/reports/6/ai-feedback/

// AI feedback generation (CORRECT)
apiRequest(`/cases/reports/${reportId}/ai-feedback/`, { method: 'POST' })
// ✅ Becomes: /api/cases/reports/6/ai-feedback/

// Rating submission (CORRECT)
apiRequest('/cases/ai-feedback-ratings/', { method: 'POST', ... })
// ✅ Becomes: /api/cases/ai-feedback-ratings/
```

---

## ❌ INCORRECT Pattern (Never Do This)

**Rule**: Never include `/api/` in your endpoint string.

If you add `/api/`, it gets doubled!

### Examples of WRONG Code

```javascript
// ❌ WRONG - Double prefix!
apiRequest('/api/users/me/')
// Becomes: /api/api/users/me/ ❌ 404 ERROR

// ❌ WRONG - Double prefix!
apiRequest('/api/cases/my-reports/')
// Becomes: /api/api/cases/my-reports/ ❌ 404 ERROR

// ❌ WRONG - Double prefix!
apiRequest('/api/cases/reports/6/ai-feedback/')
// Becomes: /api/api/cases/reports/6/ai-feedback/ ❌ 404 ERROR
```

**Error in Console**:
```
/api/api/cases/reports/6/ai-feedback/:1 Failed to load resource: the server responded with a status of 404 (Not Found)
```

---

## 🔍 How to Verify Backend Endpoints

### Step 1: Check backend/cases/urls.py

The backend URL patterns are defined WITHOUT the `/api/cases/` prefix:

```python
# backend/cases/urls.py (lines 46-84)

urlpatterns = [
    path("", include(router.urls)),
    path("reports/", views.ReportCreateView.as_view(), name="report-create"),
    path("my-reports/", views.MyReportsListView.as_view(), name="my-reports-list"),
    path(
        "reports/<int:report_id>/ai-feedback/",
        AIReportFeedbackView.as_view(),
        name="report-ai-feedback",
    ),
    path(
        "ai-feedback-ratings/",
        AIFeedbackRatingCreateView.as_view(),
        name="ai-feedback-rating-create",
    ),
    # ... more patterns
]
```

### Step 2: Understand Django URL Routing

Django adds prefixes through `include()` statements:

**From backend/api/urls.py**:
```python
urlpatterns = [
    path('api/cases/', include('cases.urls')),  # Adds /api/cases/ prefix
    path('api/users/', include('users.urls')),  # Adds /api/users/ prefix
]
```

**Full URL Construction**:
1. Django prefix: `/api/cases/`
2. cases/urls.py pattern: `reports/<int:report_id>/ai-feedback/`
3. **Final URL**: `/api/cases/reports/6/ai-feedback/`

### Step 3: Frontend Must Match Final URL

**Backend Final URL**: `/api/cases/reports/6/ai-feedback/`

**Frontend Call**:
```javascript
// ✅ CORRECT - apiRequest adds /api/ automatically
apiRequest('/cases/reports/6/ai-feedback/')
// Result: /api + /cases/reports/6/ai-feedback/ = /api/cases/reports/6/ai-feedback/ ✅
```

---

## 📋 Quick Reference Table

| Backend URL Pattern (in cases/urls.py) | Frontend apiRequest() Call | Final Production URL |
|----------------------------------------|----------------------------|---------------------|
| `path("reports/", ...)` | `apiRequest('/cases/reports/')` | `/api/cases/reports/` |
| `path("my-reports/", ...)` | `apiRequest('/cases/my-reports/')` | `/api/cases/my-reports/` |
| `path("reports/<int:report_id>/ai-feedback/", ...)` | `apiRequest('/cases/reports/6/ai-feedback/')` | `/api/cases/reports/6/ai-feedback/` |
| `path("ai-feedback-ratings/", ...)` | `apiRequest('/cases/ai-feedback-ratings/')` | `/api/cases/ai-feedback-ratings/` |

**Pattern to Remember**:
```
Backend: path("X", ...)
Frontend: apiRequest('/cases/X')
Result: /api/cases/X
```

---

## 🛠️ Debugging API Calls

### 1. Check Base URL in Browser Console

```javascript
console.log(APP_CONFIG.api.getBaseUrl());
// Production: "/api"
// Development: "http://127.0.0.1:8000/api"
```

### 2. Check Network Tab

1. Open Chrome DevTools → Network tab
2. Submit your API request
3. Look at the actual URL called
4. **Correct**: `/api/cases/reports/6/ai-feedback/` (single `/api/`)
5. **Wrong**: `/api/api/cases/reports/6/ai-feedback/` (double `/api/`)

### 3. Check for 404 Errors

If you see 404 errors with `/api/api/...`, you have a double-prefix issue.

**Fix**: Remove `/api/` from your `apiRequest()` call.

---

## ⚠️ Before Making ANY API Call Changes

### Pre-Flight Checklist

1. ✅ **Search for existing similar API calls**:
   ```bash
   grep -n "apiRequest.*cases" frontend/js/main.js
   grep -n "apiRequest.*users" frontend/js/main.js
   ```

2. ✅ **Copy the exact pattern** from working code:
   - If existing calls use `/cases/...`, use `/cases/...`
   - If existing calls use `/users/...`, use `/users/...`
   - **NEVER add `/api/` prefix!**

3. ✅ **Verify backend endpoint** exists in `backend/cases/urls.py`:
   ```python
   path("reports/<int:report_id>/ai-feedback/", ..., name="report-ai-feedback"),
   ```

4. ✅ **Test in browser console** before deploying:
   ```javascript
   console.log(APP_CONFIG.api.getBaseUrl()); // Should show "/api" in production
   ```

5. ✅ **Check Network tab** for correct URL (single `/api/` prefix)

---

## 📚 Related Files

### Key Files to Reference

1. **frontend/js/api.js** (lines 119-212) - apiRequest() implementation
2. **frontend/js/config.js** (lines 22-29) - Base URL configuration
3. **backend/cases/urls.py** - Backend URL patterns
4. **backend/api/urls.py** - Django URL prefix routing

### Documentation

- `.claude/docs/WORKFLOWS.md` - Section 6: Modifying Frontend API Calls
- `.claude/FRONTEND_CHECKLIST.md` - Pre-commit checklist
- `CLAUDE.md` - Frontend development reminders

---

## 🎓 Lessons Learned (Historical Context)

### Issue: AI Feedback 404 Errors (2025-01-14)

**Problem**: Added `/api/` prefix to endpoints, causing double-prefix:
```javascript
// ❌ WRONG
apiRequest('/api/cases/reports/6/ai-feedback/')
// Became: /api/api/cases/reports/6/ai-feedback/ → 404 ERROR
```

**Solution**: Removed `/api/` prefix:
```javascript
// ✅ CORRECT
apiRequest('/cases/reports/6/ai-feedback/')
// Becomes: /api/cases/reports/6/ai-feedback/ → SUCCESS
```

**Root Cause**: Misunderstanding how `apiRequest()` constructs URLs.

**Prevention**: Created this documentation to prevent recurrence.

---

## 💡 Best Practices Summary

1. **Never add `/api/` prefix** to `apiRequest()` calls
2. **Always search for existing patterns** before writing new API calls
3. **Copy exact patterns** from working code
4. **Verify backend URLs** in urls.py before implementing frontend
5. **Test in browser** before committing (check Network tab)
6. **Read this doc** before making ANY frontend API changes

---

**Last Updated**: 2025-01-14
**Maintainer**: straus91
**For Questions**: Refer to `.claude/docs/WORKFLOWS.md` Section 6
