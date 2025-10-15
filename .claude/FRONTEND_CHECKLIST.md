# Frontend Changes Pre-Commit Checklist

## 🎯 Purpose

This checklist ensures you follow best practices when making frontend changes, especially API-related modifications. **Complete this checklist BEFORE every commit that touches frontend JavaScript!**

---

## ✅ Before Committing Frontend API Changes

### 1. Documentation Review
- [ ] **Read** `.claude/docs/FRONTEND_API_PATTERNS.md` (MANDATORY for API changes)
- [ ] **Understand** how `apiRequest()` automatically prepends `/api/`
- [ ] **Know** the difference between correct and incorrect patterns

### 2. Pattern Research
- [ ] **Searched** for existing similar API calls in main.js:
  ```bash
  grep -n "apiRequest.*cases" frontend/js/main.js
  grep -n "apiRequest.*users" frontend/js/main.js
  ```
- [ ] **Found** at least one working example to copy from
- [ ] **Copied** exact pattern from working code (not guessing)

### 3. Backend Verification
- [ ] **Checked** `backend/cases/urls.py` for endpoint pattern
- [ ] **Verified** endpoint exists in backend
- [ ] **Confirmed** endpoint does NOT include `/api/` prefix in urls.py
- [ ] **Understood** how Django routing adds `/api/cases/` prefix

### 4. Code Review
- [ ] **Did NOT add** `/api/` prefix to `apiRequest()` calls
- [ ] **Used** relative paths like `/cases/...` or `/users/...`
- [ ] **Checked** endpoint string matches working examples
- [ ] **Verified** no typos in endpoint path

### 5. Browser Testing
- [ ] **Tested** in browser console (F12 → Console)
- [ ] **Checked** `APP_CONFIG.api.getBaseUrl()` returns correct value
  - Production: `/api`
  - Development: `http://127.0.0.1:8000/api`
- [ ] **Verified** no console errors
- [ ] **Confirmed** no 404 errors in Network tab

### 6. Network Tab Verification
- [ ] **Opened** Chrome DevTools → Network tab
- [ ] **Triggered** the API call in the UI
- [ ] **Inspected** the actual URL called
- [ ] **Confirmed** URL has SINGLE `/api/` prefix (not `/api/api/`)
- [ ] **Example**: `/api/cases/reports/6/ai-feedback/` ✅ (not `/api/api/cases/...`)

### 7. Git Diff Review
- [ ] **Ran** `git diff frontend/js/main.js` before staging
- [ ] **Verified** only intended changes are present
- [ ] **Checked** no accidental edits or deletions
- [ ] **Confirmed** no debug `console.log()` statements left behind

### 8. Functional Testing
- [ ] **Tested** the feature end-to-end in browser
- [ ] **Verified** API response is correct
- [ ] **Checked** UI updates properly with data
- [ ] **Tested** error handling (e.g., network failure)

---

## 🔍 Common Mistakes to Avoid

### ❌ Mistake 1: Adding `/api/` Prefix
**Wrong**:
```javascript
apiRequest('/api/cases/reports/6/ai-feedback/')  // ❌ Double prefix!
```

**Correct**:
```javascript
apiRequest('/cases/reports/6/ai-feedback/')  // ✅ Single prefix
```

### ❌ Mistake 2: Guessing Endpoint Patterns
**Wrong Approach**:
> "I think the endpoint should be `/api/cases/feedback/`, let me try that..."

**Correct Approach**:
> 1. Search: `grep "apiRequest.*feedback" frontend/js/main.js`
> 2. Find: `apiRequest('/cases/reports/6/ai-feedback/')`
> 3. Copy: Use exact same pattern

### ❌ Mistake 3: Not Testing in Browser
**Wrong**:
> Commit → Push → Hope it works in production

**Correct**:
> Code → Test in browser → Verify Network tab → Then commit

### ❌ Mistake 4: Ignoring Backend URLs
**Wrong**:
> Frontend guesses `/cases/ai-feedback/` but backend has `/cases/reports/<id>/ai-feedback/`

**Correct**:
> Check `backend/cases/urls.py` FIRST, then match pattern in frontend

---

## 🛡️ Safety Checks

### Before Staging Changes

```bash
# 1. Check your changes
git diff frontend/js/main.js

# 2. Search for accidental /api/ prefix
git diff frontend/js/main.js | grep "apiRequest.*'/api/"
# Should return NOTHING (empty result)

# 3. Verify only intended files modified
git status

# 4. Review all changes one more time
git diff
```

### After Staging, Before Committing

```bash
# Verify staged changes
git diff --cached frontend/js/main.js

# Check for debug code
git diff --cached | grep -i "console.log\|debugger\|TODO"
# Remove any debug code found
```

---

## 📊 Testing Scenarios

### Test Case 1: API Call Success
- [ ] Submit request via UI
- [ ] Check Network tab: 200 OK status
- [ ] Verify URL: `/api/cases/...` (single `/api/`)
- [ ] Confirm response data is correct

### Test Case 2: API Call Failure (Network Error)
- [ ] Disconnect internet or block request
- [ ] Verify error handling works
- [ ] Check user sees error message
- [ ] Confirm no console errors crash the app

### Test Case 3: API Call Failure (404)
- [ ] If 404 occurs → **STOP AND FIX!**
- [ ] Check URL in Network tab
- [ ] If `/api/api/...` → Remove `/api/` from `apiRequest()` call
- [ ] If single `/api/...` → Check backend endpoint exists

---

## 🚨 Red Flags - Stop and Reassess

**If you see any of these, DO NOT COMMIT**:

1. ❌ `/api/api/...` in Network tab → Double prefix error
2. ❌ 404 errors on API calls that should exist
3. ❌ Console errors about "Invalid response format"
4. ❌ `git diff` shows changes you didn't intend
5. ❌ You can't find a working example to copy from
6. ❌ Backend endpoint doesn't exist in urls.py
7. ❌ You're guessing instead of searching for patterns

**Action**: If any red flag appears, pause and:
1. Read `.claude/docs/FRONTEND_API_PATTERNS.md` again
2. Search for working examples more carefully
3. Verify backend endpoints exist
4. Test more thoroughly in browser
5. Ask for review if still uncertain

---

## ✅ Final Pre-Commit Checklist Summary

**Quick checklist before running `git commit`**:

- [ ] Read FRONTEND_API_PATTERNS.md
- [ ] Searched for existing patterns
- [ ] Copied exact pattern from working code
- [ ] Verified backend endpoint exists
- [ ] Did NOT add `/api/` prefix to apiRequest
- [ ] Tested in browser (no 404 errors)
- [ ] Checked Network tab (single `/api/` prefix)
- [ ] Reviewed `git diff` (only intended changes)
- [ ] All tests passed (success and error cases)
- [ ] No debug code or console.logs left

**If ALL boxes checked** → ✅ Safe to commit!

**If ANY box unchecked** → ⚠️ Review and fix before committing!

---

## 📚 Resources

### Documentation to Reference
- **API Patterns**: `.claude/docs/FRONTEND_API_PATTERNS.md`
- **Workflows**: `.claude/docs/WORKFLOWS.md` (Section 6)
- **Backend URLs**: `backend/cases/urls.py`
- **API Client**: `frontend/js/api.js` (line 119-212)
- **Config**: `frontend/js/config.js` (line 22-29)

### Useful Commands

```bash
# Search for API patterns
grep -n "apiRequest.*cases" frontend/js/main.js
grep -n "apiRequest.*users" frontend/js/main.js

# Check backend endpoints
cat backend/cases/urls.py | grep -A 3 "path("

# Review changes before commit
git diff frontend/js/main.js

# Check for accidental /api/ prefix
git diff | grep "apiRequest.*'/api/"
```

---

## 🎓 Learning from Past Issues

### 2025-01-14: AI Feedback 404 Errors

**Problem**: Added `/api/` prefix causing double-prefix error

**Symptoms**:
```
/api/api/cases/reports/6/ai-feedback/:1 Failed to load resource: 404 Not Found
```

**Root Cause**: Didn't understand `apiRequest()` prepends `/api/` automatically

**Solution**: Removed `/api/` prefix from all three calls

**Prevention**: Created this checklist and FRONTEND_API_PATTERNS.md

**Lesson**: Always search for existing patterns before guessing!

---

**Remember**: Taking 5 minutes to complete this checklist prevents hours of debugging production issues!

**Last Updated**: 2025-01-14
**Maintainer**: straus91
