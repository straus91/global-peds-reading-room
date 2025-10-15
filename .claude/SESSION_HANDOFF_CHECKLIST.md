# ✅ SESSION HANDOFF CHECKLIST

**Purpose**: Ensure seamless context transfer between Claude Code sessions

**When to Use**: **BEFORE ending ANY Claude Code session** (mandatory for all sessions)

---

## 🎯 CRITICAL IMPORTANCE

**Why This Matters**:
- Claude Code sessions don't retain memory across conversations
- Next session relies 100% on written documentation
- Incomplete handoff = wasted time rediscovering context
- Good handoff = next session continues seamlessly

**Time Investment**: 5-10 minutes to complete checklist
**Time Saved**: 30-60 minutes for next session

---

## ✅ PRE-HANDOFF CHECKLIST

### Section 1: Document What You Accomplished

- [ ] **List all files created**:
  ```
  Example:
  - Created: SESSION_ENTRY_POINT.md
  - Created: PROGRESS_TRACKER.md
  - Created: INTEGRATION_MAP.md
  ```

- [ ] **List all files modified**:
  ```
  Example:
  - Modified: frontend/js/api.js (line 61 - fixed double /api/ bug)
  - Modified: backend/cases/models.py (added new field)
  ```

- [ ] **List all tests written**:
  ```
  Example:
  - Wrote 6 new tests in test_cache_utils.py
  - All tests passing ✅
  - Coverage increased from 75% to 82%
  ```

- [ ] **List bugs fixed**:
  ```
  Example:
  - Fixed: api.js line 61 double /api/ prefix in token refresh
  - Impact: Would have caused 404 when tokens expire
  - Status: Fixed and verified
  ```

- [ ] **List bugs discovered** (but not fixed):
  ```
  Example:
  - Discovered: Potential race condition in cache writes
  - Impact: Low probability, affects <1% of requests
  - Status: Added to PROGRESS_TRACKER.md for future fix
  ```

### Section 2: Update Core Documentation

- [ ] **Updated SESSION_ENTRY_POINT.md**:
  - [ ] "Last Session Summary" → "What Was Accomplished"
  - [ ] "Last Session Summary" → "What Was Discovered"
  - [ ] "Last Session Summary" → "Next Action"
  - [ ] "Current Phase Details" → Progress percentage
  - [ ] "Project Health Metrics" (if collected)

- [ ] **Updated PROGRESS_TRACKER.md**:
  - [ ] Checked off **ALL** completed tasks (don't batch!)
  - [ ] Updated "Last Updated" header with date + note
  - [ ] Updated progress percentages (e.g., "Day 2: 50% complete")
  - [ ] Verified next unchecked task is accurate

- [ ] **Updated DEPLOYMENT_LOG.md** (if deployed):
  - [ ] Added new entry with date and summary
  - [ ] Documented what was deployed
  - [ ] Documented verification steps taken
  - [ ] Documented any issues encountered
  - [ ] Documented lessons learned

### Section 3: Verify Next Action is Clear

- [ ] **SESSION_ENTRY_POINT.md "Next Action" is**:
  - [ ] Specific (not vague like "continue work")
  - [ ] Actionable (clear what to do)
  - [ ] Complete (includes file paths if relevant)

  ```
  Example of GOOD next action:
  "Create cache_utils.py in backend/cases/ with generate_cache_key() function.
   See NEXT_STEPS.md Day 2 Task 1 for implementation details."

  Example of BAD next action:
  "Continue Phase 1 work."
  ```

- [ ] **PROGRESS_TRACKER.md next unchecked task**:
  - [ ] Is the same as SESSION_ENTRY_POINT.md "Next Action"
  - [ ] Has clear checkbox that's unchecked
  - [ ] Has estimated time if available

### Section 4: Check for Undocumented Knowledge

- [ ] **No temporary notes left in comments**:
  ```bash
  # Search for TODO/FIXME comments you added
  git diff | grep -i "TODO\|FIXME\|XXX\|HACK"
  # If found, move to proper docs or PROGRESS_TRACKER.md
  ```

- [ ] **No decisions left undocumented**:
  - [ ] If you made architectural decisions → documented in SESSION_ENTRY_POINT.md
  - [ ] If you discovered edge cases → documented in relevant .claude/docs/
  - [ ] If you changed approach → documented why in PROGRESS_TRACKER.md

- [ ] **No "I'll remember this" assumptions**:
  - Future Claude session **WON'T** remember!
  - Write it down or it's lost

### Section 5: Test Context Survival (5-Minute Simulation)

- [ ] **Pretend you're a new Claude session**:
  1. Close all files
  2. Open only SESSION_ENTRY_POINT.md
  3. Can you answer these questions WITHOUT other files?
     - [ ] What phase is the project in?
     - [ ] What was just completed?
     - [ ] What should I do next?
     - [ ] Where do I find details for next task?
  4. If you can't answer ALL questions → **IMPROVE SESSION_ENTRY_POINT.md**

- [ ] **Verify PROGRESS_TRACKER.md is up-to-date**:
  1. Open PROGRESS_TRACKER.md
  2. Find "Current Phase" section
  3. Does checkbox status match what you actually completed?
  4. If not → **UPDATE PROGRESS_TRACKER.md**

---

## 🚨 RED FLAGS - Don't End Session If...

### Critical Blockers (Must Fix Before Handoff)

- ❌ **"Last Updated" dates are old**
  - Both SESSION_ENTRY_POINT.md and PROGRESS_TRACKER.md must show today's date

- ❌ **Progress percentages don't match reality**
  - If you completed 3/10 tasks, should show 30%, not 0%

- ❌ **Next action is vague**
  - "Continue work" is NOT acceptable
  - Must be specific and actionable

- ❌ **Checkboxes don't match completed work**
  - If you finished a task, it MUST be checked off
  - Don't leave completed tasks unchecked

- ❌ **New discoveries not documented**
  - Found a bug? → Added to PROGRESS_TRACKER.md?
  - Made a decision? → Documented in SESSION_ENTRY_POINT.md?
  - Changed approach? → Explained why in docs?

### Warning Signs (Improve Before Handoff)

- ⚠️ **Git commits without corresponding doc updates**
  - Every commit should have matching checkbox in PROGRESS_TRACKER.md

- ⚠️ **Modified files not listed**
  - SESSION_ENTRY_POINT.md "What Was Accomplished" should list ALL modified files

- ⚠️ **Tests written but not documented**
  - How many tests? All passing? Coverage change? → Document it!

- ⚠️ **Deployment without DEPLOYMENT_LOG.md entry**
  - EVERY deployment must have a log entry

---

## 📝 HANDOFF TEMPLATE

**Copy this template into SESSION_ENTRY_POINT.md "Last Session Summary"**:

```markdown
**Session Date**: 2025-XX-XX
**Session Focus**: [One sentence describing session focus]

**What Was Accomplished**:
1. [Specific accomplishment with file references]
2. [Another specific accomplishment]
3. [Another...]

**What Was Discovered**:
- [Key finding or insight]
- [Bug discovered]
- [Decision made and why]

**What Was Modified**:
- Files Created: [list]
- Files Modified: [list with line numbers if relevant]
- Tests Added: [count and status]

**Next Action**:
[Specific, actionable next step with file paths and reference docs]
```

---

## ✅ FINAL VERIFICATION CHECKLIST

**Before ending session, verify ALL of these**:

- [ ] ✅ SESSION_ENTRY_POINT.md updated (3 sections)
- [ ] ✅ PROGRESS_TRACKER.md updated (checkboxes + header)
- [ ] ✅ DEPLOYMENT_LOG.md updated (if deployed)
- [ ] ✅ Next action is clear and specific
- [ ] ✅ All completed tasks checked off
- [ ] ✅ No undocumented decisions
- [ ] ✅ No TODO comments left without docs
- [ ] ✅ Context survival test passed
- [ ] ✅ Progress percentages accurate
- [ ] ✅ "Last Updated" dates are today

**If ALL boxes checked** → ✅ Safe to end session!

**If ANY box unchecked** → ⚠️ Fix before ending!

---

## 🎓 EXAMPLES

### Example 1: Good Handoff

**SESSION_ENTRY_POINT.md "Last Session Summary"**:
```markdown
**Session Date**: 2025-10-14
**Session Focus**: Fix critical API bug and create documentation system

**What Was Accomplished**:
1. ✅ Fixed api.js line 61 double /api/ prefix bug
   - File: frontend/js/api.js
   - Changed: `${APP_CONFIG.api.getBaseUrl()}/api/auth/login/refresh/`
   - To: `${APP_CONFIG.api.getBaseUrl()}/auth/login/refresh/`
   - Verified: Backend endpoint exists at api/urls.py line 24

2. ✅ Created SESSION_ENTRY_POINT.md (comprehensive entry point)
   - Purpose: Single source of truth for new sessions
   - Content: Status, docs map, next action, pitfalls

3. ✅ Created PROGRESS_TRACKER.md (checkbox tracking)
   - Tracks: Phase 1, Quality Audit, System Validation
   - Progress: 40% complete (4/10 tasks)

**What Was Discovered**:
- "Fixing-breaking" cycle was already SOLVED (Jan 14, 2025)
- 100% of API calls now use correct pattern (verified)
- One critical bug found and fixed (token refresh)
- No single entry point existed (now created)

**Next Action**:
Run system validation to collect baseline metrics. Start with:
`cd backend && venv/bin/python manage.py test --dry-run`
See PROGRESS_TRACKER.md "System Validation" section for complete checklist.
```

**Why This is Good**:
- ✅ Specific file names and line numbers
- ✅ Clear next action with exact command
- ✅ Documented discoveries with context
- ✅ Lists what was created vs modified

### Example 2: Bad Handoff (DON'T DO THIS)

**SESSION_ENTRY_POINT.md "Last Session Summary"**:
```markdown
**Session Date**: 2025-10-14
**Session Focus**: Worked on stuff

**What Was Accomplished**:
1. Fixed some bugs
2. Updated some docs

**What Was Discovered**:
- Nothing major

**Next Action**:
Continue working on the project.
```

**Why This is Bad**:
- ❌ No specific files mentioned
- ❌ "Some bugs" - which bugs?
- ❌ "Some docs" - which docs?
- ❌ "Continue working" - on what?
- ❌ No details for next session to continue

---

## 💡 TIPS FOR EFFECTIVE HANDOFFS

### Tip 1: Be Specific, Not General
```
❌ BAD: "Fixed API issue"
✅ GOOD: "Fixed api.js line 61 double /api/ prefix causing 404 in token refresh"
```

### Tip 2: Always Include File Paths
```
❌ BAD: "Updated the cache utility"
✅ GOOD: "Updated backend/cases/cache_utils.py - added get_cached_feedback() function"
```

### Tip 3: Document Why, Not Just What
```
❌ BAD: "Changed approach"
✅ GOOD: "Changed from raw fetch() to apiRequest() because apiRequest handles auth automatically"
```

### Tip 4: List Files Explicitly
```
❌ BAD: "Created some new documentation"
✅ GOOD: "Created: SESSION_ENTRY_POINT.md, PROGRESS_TRACKER.md, INTEGRATION_MAP.md"
```

### Tip 5: Provide Continuity Breadcrumbs
```
❌ BAD: "Next: Do more work"
✅ GOOD: "Next: Create cache_utils.py. See NEXT_STEPS.md Day 2 Task 1 lines 23-114 for detailed implementation spec."
```

---

## 🔄 CONTINUOUS IMPROVEMENT

**After Using This Checklist 5 Times**:
- Review: Did it help continuity?
- Identify: What's still unclear in handoffs?
- Update: Add new checklist items
- Refine: Improve examples

**Common Additions Needed**:
- Deployment-specific handoff items
- Test coverage change documentation
- Performance metric changes
- Database migration handoff notes

---

**Remember**: 10 minutes documenting now saves 1 hour discovering next session!

**Last Updated**: 2025-10-14
**Next Review**: After 5 handoffs completed
**Maintained By**: Claude Code + Human Developer
