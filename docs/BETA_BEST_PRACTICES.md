# 🌟 Beta Environment Best Practices

**For**: Global Peds Reading Room Beta Environment
**Server**: global-readingroom (64.225.17.0)
**Last Updated**: 2025-10-11

> Principles and best practices for safe, sustainable development using the beta environment as a testing ground before production.

---

## 🎯 Beta Environment Philosophy

### What Beta IS

✅ **A Safe Testing Ground**
- Place to discover bugs before users do
- Environment to validate improvements
- Space to experiment with new features
- Staging area that mirrors production

✅ **A Learning Laboratory**
- Test AI prompt changes with real data
- Measure actual user impact
- Iterate based on metrics
- Validate assumptions

✅ **A Safety Net**
- Catch issues before production
- Practice deployment procedures
- Test rollback mechanisms
- Build confidence

### What Beta IS NOT

❌ **NOT Production**
- It's okay if things break
- Data can be reset if needed
- Downtime is acceptable
- Experiments are encouraged

❌ **NOT Permanent**
- Changes that work → promote to production
- Changes that fail → rollback and learn
- Data might be refreshed from production periodically
- Treat it as transient

---

## 📋 Core Principles

### 1. 🔒 Safety First

**Always Have a Rollback Plan**

Before ANY deployment:
- [ ] Know exactly how to undo the change
- [ ] Have database backup (if data changes)
- [ ] Document rollback steps
- [ ] Test rollback procedure periodically

**Example**:
```markdown
Deploying: New AI prompt v2.1

Rollback Plan:
1. SSH: ssh root@64.225.17.0
2. Code: git reset --hard HEAD~1
3. Service: sudo systemctl restart gunicorn
4. Verify: curl http://localhost:8001/api/
5. Time required: 2 minutes
```

---

### 2. 📊 Data-Driven Decisions

**Measure Before and After**

Never make changes based on gut feeling:

```bash
# Before deploying prompt change
python scripts/track_ai_baseline.py "Before prompt v2.1"

# Deploy change

# Wait 7 days, then measure again
python scripts/monitor_metrics.py

# Compare results → Decide to keep or rollback
```

**Key Metrics to Track**:
- AI feedback quality (star ratings)
- User engagement (reports/day)
- System performance (response times)
- Error rates (logs)
- Costs (API usage)

See: **MONITORING_SETUP.md** for tracking setup

---

### 3. 🧪 Test Systematically

**Follow the Testing Workflow**

Don't skip steps to save time - it backfires:

1. ✅ **Local Testing** - Catch obvious bugs
2. ✅ **Unit Tests** - Verify code correctness
3. ✅ **Beta Deployment** - Test in production-like environment
4. ✅ **Monitoring** - Watch for 24-48 hours
5. ✅ **Production** - Only after beta proves stable

See: **BETA_TESTING_WORKFLOW.md** for complete procedures

**Shortcuts Lead to Problems**:
```
❌ "Just a small change, skip testing"
   → Breaks production
   → Emergency rollback
   → Lost user trust

✅ "Small change, quick test"
   → Find issue in beta
   → Fix before production
   → Users never affected
```

---

### 4. 📝 Document Everything

**Your Future Self Will Thank You**

Document:
- **What** you changed
- **Why** you changed it
- **How** to rollback if needed
- **Results** (metrics before/after)

**Keep a Change Log**:

```markdown
# Beta Change Log

## 2025-10-11 - AI Prompt v2.1
**What**: Updated prompt to provide more specific discrepancy descriptions
**Why**: Users complained feedback was too vague
**Baseline**: 4.2/5.0 average rating, 45 ratings
**Rollback**: git reset --hard abc123
**Results** (after 7 days):
- Rating: 4.4/5.0 (+0.2) ✅
- User comments: 8 mentioned "more specific"
- Decision: Keep, promote to production
```

---

### 5. 🔄 Iterate, Don't Revolutionize

**Small Changes Are Safer**

```
❌ BAD: Change 5 things at once
   → Something breaks
   → Don't know which change caused it
   → Hard to fix

✅ GOOD: Change one thing, test, measure, decide
   → Clear cause and effect
   → Easy to rollback if needed
   → Learn from each iteration
```

**AI Improvement Example**:
```
Iteration 1: Make discrepancy descriptions more specific
  → Measure → Improvement → Keep

Iteration 2: Add pedagogical scaffolding
  → Measure → Improvement → Keep

Iteration 3: Adjust severity thresholds
  → Measure → No improvement → Rollback

Total: 2/3 improvements kept (66% success rate)
```

See: **AI_ITERATION_WORKFLOW.md** for systematic AI testing

---

## 🛡️ Safety Best Practices

### Database Operations

**ALWAYS Backup Before Schema Changes**

```bash
# GOOD: Backup first
ssh root@64.225.17.0
sudo -u postgres pg_dump globalpeds_db > ~/backups/globalpeds_$(date +%Y%m%d_%H%M%S).sql
ls -lh ~/backups/  # Verify backup exists

# Then deploy
python manage.py migrate

# BAD: Migrate without backup
python manage.py migrate  # ❌ NO! What if migration fails?
```

**Keep 7 Days of Backups**

```bash
# Delete backups older than 7 days
find ~/backups -name "globalpeds_*.sql" -mtime +7 -delete
```

---

### Code Changes

**Use Git Properly**

```bash
# GOOD: Clear, descriptive commits
git add backend/cases/llm_feedback_service.py
git commit -m "Update AI prompt to v2.1 - more specific discrepancy descriptions"
git push origin online_beta

# BAD: Vague commits
git add -A
git commit -m "changes"  # ❌ Unclear what changed
git push
```

**Never Force Push to Beta**

```bash
# GOOD: Regular push
git push origin online_beta

# BAD: Force push
git push --force origin online_beta  # ❌ Destroys history!
```

---

### Deployment Timing

**Deploy During Low-Traffic Periods**

**Best Times**:
- Early morning (6-8 AM) - Few active users
- Late evening (10 PM - midnight) - Users likely done for day
- Weekends - Generally lower traffic

**Avoid**:
- Peak hours (lunchtime, evenings)
- Before weekends (want to monitor post-deploy)
- Before holidays (you might not be available to fix issues)

**Monitor Immediately After Deploy**

```bash
# Deploy
sudo systemctl restart gunicorn

# THEN WATCH FOR 5-10 MINUTES
tail -f /var/log/gunicorn/gunicorn.log

# Look for:
# - Startup messages (should see "Listening at...")
# - No errors
# - Requests being handled

# Press Ctrl+C when satisfied
```

---

## 📊 Monitoring Best Practices

### Daily Routine (5 minutes)

**Morning Check**:

```bash
ssh root@64.225.17.0

# 1. Services healthy?
sudo systemctl status gunicorn nginx postgresql

# 2. Any errors overnight?
tail -50 /var/log/gunicorn/gunicorn.log | grep -i error

# 3. Disk space okay?
df -h  # Should be < 80%

# Exit if all good
exit
```

---

### Weekly Review (30 minutes)

**Metrics Analysis**:

```bash
ssh root@64.225.17.0
source /home/deploy/global-peds-reading-room/backend/venv/bin/activate

# 1. Generate metrics
python /home/deploy/global-peds-reading-room/scripts/monitor_metrics.py > ~/weekly_metrics_$(date +%Y%m%d).txt

# 2. Review AI quality trend
cat /home/deploy/global-peds-reading-room/ai_baseline_history.json | jq '.'

# 3. Check for patterns
grep -i error /var/log/gunicorn/gunicorn.log | tail -100
```

**Action Items**:
- AI rating dropping? → Review prompt changes
- Errors increasing? → Investigate cause
- Disk filling up? → Clean old logs/backups
- Performance degrading? → Check slow queries

---

## 🔧 Development Workflow Best Practices

### Feature Development Cycle

```
1. LOCAL DEVELOPMENT
   ├─ Write code
   ├─ Write tests
   ├─ Run tests (must pass)
   └─ Manual testing

2. CODE REVIEW (if team)
   ├─ Commit to feature branch
   ├─ Create pull request
   └─ Review before merging

3. MERGE TO ONLINE_BETA
   ├─ Merge feature branch
   └─ Resolve conflicts

4. BETA DEPLOYMENT
   ├─ Follow BETA_DEPLOYMENT.md
   ├─ Create database backup
   ├─ Deploy to droplet
   └─ Monitor immediately

5. BETA TESTING
   ├─ Follow BETA_TESTING_WORKFLOW.md
   ├─ Test all features
   └─ Monitor for 24-48 hours

6. METRICS VALIDATION
   ├─ Compare before/after metrics
   ├─ Check for regressions
   └─ Collect user feedback

7. DECISION
   ├─ Success? → Plan production deploy
   ├─ Issues? → Fix and redeploy
   └─ Failed? → Rollback and analyze
```

---

### AI Improvement Cycle

**For AI Prompt/Model Changes**:

See: **AI_ITERATION_WORKFLOW.md** for complete methodology

```
1. HYPOTHESIS
   "Adding patient age context will improve feedback accuracy"

2. BASELINE
   python scripts/track_ai_baseline.py "Before age context"
   Current: 4.2/5.0 average

3. IMPLEMENT
   Update prompt to include age context
   Test with 5 sample reports

4. DEPLOY TO BETA
   Follow deployment procedure
   Track which reports use new prompt

5. COLLECT DATA (7 days)
   Monitor ratings
   Review low-rated feedback
   Check false positive rate

6. ANALYZE
   New: 4.5/5.0 average (+0.3)
   Statistical significance: p < 0.05
   User comments: Positive

7. DECIDE
   ✅ Significant improvement → Keep, promote to production
   ❌ No improvement → Rollback, try different approach
```

---

## 🚨 What To Do When Things Go Wrong

### Something Broke After Deployment

**Stay Calm, Act Methodically**:

1. **Assess Severity**:
   - Can users login? → Critical
   - AI feedback broken? → High
   - Cosmetic issue? → Low

2. **If Critical**: **ROLLBACK IMMEDIATELY**
   ```bash
   ssh root@64.225.17.0
   cd /home/deploy/global-peds-reading-room
   git reset --hard HEAD~1
   sudo systemctl restart gunicorn
   curl http://localhost:8001/api/  # Verify working
   ```

3. **If Not Critical**: Investigate
   ```bash
   # Check recent errors
   tail -100 /var/log/gunicorn/gunicorn.log | grep -i error

   # Check what changed
   git log -1 --stat

   # Try to identify cause
   ```

4. **Fix** (if quick) **or Rollback** (if complex)

5. **Document** what happened and how you fixed it

---

### Database Migration Failed

```bash
# 1. Don't panic - migrations are usually reversible

# 2. Check error message
python manage.py migrate
# Read error carefully

# 3. Common issues:
#    - Conflicting migrations → python manage.py migrate --fake
#    - Data incompatibility → May need data migration
#    - Syntax error → Fix migration file

# 4. If stuck, rollback migration
python manage.py migrate cases 00XX_previous_migration

# 5. Restore from backup if data corrupted
sudo -u postgres psql globalpeds_db < ~/backups/latest.sql
```

---

## 💡 Communication Best Practices

### When to Notify Users

**Before Deployment** (if downtime expected):
- Email/announce: "Beta will be briefly unavailable tomorrow 8-9 AM for updates"

**After Deployment** (if user-facing changes):
- Announce new features
- Ask for feedback on changes
- Set expectations

**If Issues Occur**:
- Notify immediately
- Explain what happened
- Timeline for fix
- Apologize for inconvenience

---

### Change Communication Template

```markdown
Subject: Beta Update - [Feature Name]

Hi Beta Testers,

We've just deployed a new update to the beta environment:

CHANGES:
- [What changed]
- [What's new]
- [What's improved]

WHAT TO TEST:
- [Specific features to try]
- [Known issues to watch for]

FEEDBACK:
Please report any issues or feedback to: [contact]

THANKS:
Your testing helps us improve the platform!

[Your Name]
```

---

## 📚 Documentation Practices

### Keep Documentation Current

**When You Change Code**, **Update Docs**:

```
Changed AI prompt?
  → Update AI_GUIDE.md or AI_FEATURES_ROADMAP.md

Changed database model?
  → Update .claude/docs/DATA_MODELS.md

Changed deployment process?
  → Update BETA_DEPLOYMENT.md

Added new feature?
  → Update README.md and PROJECT_MAP.md
```

**Update "Last Updated" Dates**:
```markdown
**Last Updated**: 2025-10-11  # ← Keep this current!
```

---

### Document Lessons Learned

**After Issues/Incidents**:

Create `docs/lessons_learned/YYYY-MM-DD-incident.md`:

```markdown
# Incident: AI Feedback Stopped Working

**Date**: 2025-10-11
**Duration**: 2 hours
**Severity**: High (no AI feedback generating)

## What Happened
Gemini API key expired, all feedback requests failing

## Root Cause
Didn't set calendar reminder for key rotation

## How We Fixed It
1. Generated new API key in Google AI Studio
2. Updated .env file
3. Restarted gunicorn
4. Tested feedback generation

## How We Prevent This
- [ ] Set calendar reminder 30 days before key expiration
- [ ] Add monitoring alert for consecutive API failures
- [ ] Document key rotation in QUICK_REFERENCE.md

## Related
- SECURITY.md#secret-rotation
- SERVER_CHEATSHEET.md#troubleshooting
```

---

## ✅ Pre-Deployment Checklist

**Print This and Check Before EVERY Deployment**:

### Before Deploying

- [ ] All tests pass locally
- [ ] Database backup created (if schema changes)
- [ ] Baseline metrics documented (if AI changes)
- [ ] Rollback plan written down
- [ ] Deployment steps reviewed
- [ ] Deploying during low-traffic time
- [ ] Can monitor for 30+ minutes after deploy

### During Deployment

- [ ] Follow BETA_DEPLOYMENT.md steps exactly
- [ ] Verify each command completes successfully
- [ ] Check for errors in output
- [ ] Services restart without errors

### After Deployment

- [ ] Monitor logs for 10+ minutes
- [ ] Test critical features manually
- [ ] Check metrics dashboard
- [ ] No errors in browser console (frontend)
- [ ] API endpoints responding correctly

### First 24 Hours

- [ ] Check metrics daily
- [ ] Review error logs
- [ ] Collect user feedback (if applicable)
- [ ] Compare to baseline (if AI changes)

### First Week (for AI changes)

- [ ] Daily metrics check
- [ ] Review low-rated feedback
- [ ] Statistical analysis (compare to baseline)
- [ ] Decision: keep, iterate, or rollback

---

## 🎯 Success Metrics

**You're Following Best Practices If**:

- [ ] Beta has caught at least 1 bug before production (per month)
- [ ] You can rollback any change in < 5 minutes
- [ ] Deployments have < 5% failure rate
- [ ] All AI changes have baseline metrics tracked
- [ ] Database has daily backups with tested restore procedure
- [ ] Documentation updated within 1 day of changes
- [ ] No production deployments without beta testing first
- [ ] Team knows how to access all documentation

---

## 🔗 Related Documentation

### Essential Workflows
- **BETA_DEPLOYMENT.md** - How to deploy changes
- **BETA_TESTING_WORKFLOW.md** - How to test systematically
- **QUICK_REFERENCE.md** - Emergency procedures
- **SERVER_CHEATSHEET.md** - Quick copy-paste commands

### Specialized Guides
- **AI_ITERATION_WORKFLOW.md** - Data-driven AI testing
- **MONITORING_SETUP.md** - Metrics collection
- **AI_FEATURES_ROADMAP.md** - Strategic AI improvements

### Reference
- **DOCUMENTATION_INDEX.md** - Master navigation
- **.claude/docs/RISK_ASSESSMENT.md** - Assess changes before deploying

---

## 💭 Beta Environment Mindset

### Remember

✅ **Beta is FOR breaking things** - Better here than production
✅ **Measure everything** - Data beats opinions
✅ **Iterate quickly** - Small changes, fast feedback
✅ **Document learnings** - Build institutional knowledge
✅ **Safety first** - Always have rollback plan

### Quotes to Live By

> "Beta is not a place to be perfect, it's a place to get better."

> "If you're not occasionally breaking beta, you're not innovating enough."

> "Every beta issue is a production bug prevented."

> "Data-driven decisions over gut feelings, always."

> "The best time to practice rollback is before you need it."

---

## 🏁 Getting Started with These Practices

### Week 1: Foundation

- [ ] Read BETA_DEPLOYMENT.md and BETA_TESTING_WORKFLOW.md
- [ ] Set up monitoring (MONITORING_SETUP.md)
- [ ] Practice one rollback (even though nothing broke)
- [ ] Create baseline metrics for current state

### Week 2: First Real Deploy

- [ ] Plan a small change
- [ ] Follow complete workflow (local → beta → test → monitor)
- [ ] Document results
- [ ] Reflect on what went well/poorly

### Week 3: Continuous Improvement

- [ ] Establish daily monitoring routine (5 min)
- [ ] Set up weekly metrics review (30 min)
- [ ] Start tracking changes in change log
- [ ] Share learnings with team (if applicable)

---

**Remember**: The best practices are the ones you actually follow. Start with the basics, build habits, then add more sophisticated practices over time.

**Last Updated**: 2025-10-11
**Server**: global-readingroom (64.225.17.0)
