# ⚠️ Risk Assessment Guidelines for Claude Code

## 🎯 Purpose

Before making ANY code changes, Claude Code MUST perform a thorough risk assessment to identify what could break, what data could be affected, and what systems could be impacted. This is a **MANDATORY** step for all modifications.

---

## 📋 When to Perform Risk Assessment

Perform risk assessment **BEFORE** making changes in these scenarios:

### 1. 🗄️ Database Schema Changes
- Adding/removing/modifying model fields
- Changing field types or constraints
- Modifying relationships (ForeignKey, ManyToMany)
- Adding/removing models
- Changing unique constraints

### 2. 🔌 API Modifications
- Changing API endpoints or response formats
- Modifying serializer fields
- Changing authentication/permission logic
- Adding/removing API parameters
- Changing status codes or error responses

### 3. 📊 Data-Driven System Changes
- Modifying analytics queries or metrics
- Changing logging/monitoring code
- Updating AI feedback processing logic
- Altering report comparison algorithms
- Changing data collection mechanisms

### 4. 🔐 Authentication & Security Changes
- Modifying JWT token handling
- Changing permission classes
- Updating CORS settings
- Altering rate limiting logic
- Modifying input sanitization

### 5. ⚡ Performance & Scalability Changes
- Modifying caching logic
- Changing database queries
- Updating rate limiting settings
- Altering LLM API call patterns
- Changing concurrency handling

---

## 🔍 Risk Assessment Framework

### Step 1️⃣: Identify Direct Impact

**Questions to Answer:**
- Which files will be directly modified?
- Which models/tables will be affected?
- Which API endpoints will change behavior?
- Which frontend components depend on this?

**Document:**
```
DIRECT IMPACT:
- Files to modify: [list all files]
- Models affected: [list models]
- API endpoints: [list endpoints]
- Frontend dependencies: [list JS files/components]
```

### Step 2️⃣: Analyze Cascading Effects

**Questions to Answer:**
- What other systems depend on this code?
- Will this require database migrations?
- Will existing data need transformation?
- Are there foreign key relationships that could cascade?
- Will cached data become stale?
- Could this affect AI feedback generation?

**Document:**
```
CASCADING EFFECTS:
- Dependent systems: [list systems]
- Migration required: [Yes/No - if yes, describe data transformation needed]
- Data integrity concerns: [describe potential issues]
- Cache invalidation needed: [Yes/No - what caches?]
- AI/Analytics impact: [describe how metrics/feedback could be affected]
```

### Step 3️⃣: Assess Data-Driven Implications

**Questions to Answer:**
- Will this change affect metrics collection?
- Could this impact AI feedback quality or content?
- Are analytics queries dependent on this structure?
- Will historical data remain queryable?
- Could this affect AIFeedbackRating analysis?
- Will report comparison logic still work?

**Document:**
```
DATA-DRIVEN IMPLICATIONS:
- Metrics affected: [list metrics that could change]
- AI feedback impact: [describe how feedback generation/quality could change]
- Analytics queries: [list queries that need updating]
- Historical data: [describe backward compatibility concerns]
- Report comparison: [describe impact on pre-analysis or LLM prompts]
```

### Step 4️⃣: Evaluate Scalability Impact

**Questions to Answer:**
- Will this increase database load?
- Could this affect API rate limits?
- Will this change query performance?
- Are there new N+1 query risks?
- Could this impact concurrent user handling?
- Will LLM API usage patterns change?

**Document:**
```
SCALABILITY IMPACT:
- Database performance: [describe query impact]
- Rate limiting: [will this affect API calls per minute?]
- Query optimization: [are select_related/prefetch_related needed?]
- Concurrency: [could this create race conditions?]
- LLM usage: [will this increase/decrease API calls?]
```

### Step 5️⃣: Check Breaking Changes

**Questions to Answer:**
- Will existing API consumers break?
- Will frontend JavaScript need updates?
- Are there migration dependencies?
- Will this break existing user workflows?
- Could this affect backward compatibility with existing reports?

**Document:**
```
BREAKING CHANGES:
- API breaking changes: [Yes/No - describe]
- Frontend updates required: [list files]
- Migration order dependencies: [describe sequence]
- User workflow impact: [describe changes users will notice]
- Backward compatibility: [can old data still be processed?]
```

### Step 6️⃣: Identify Testing Requirements

**Questions to Answer:**
- What new tests are needed?
- Which existing tests might break?
- Are migration tests needed?
- Should we test rollback scenarios?
- Do we need performance/load tests?

**Document:**
```
TESTING REQUIREMENTS:
- New tests needed: [list test cases]
- Existing tests to update: [list test files]
- Migration testing: [describe approach]
- Rollback testing: [Yes/No - how?]
- Performance testing: [what metrics to validate?]
```

---

## 📊 Risk Severity Levels

Assign a severity level to the overall change:

### 🟢 **LOW RISK**
- Cosmetic changes (comments, formatting)
- Adding optional fields with defaults
- Adding new endpoints without modifying existing ones
- Documentation updates
- Adding new non-required features

### 🟡 **MEDIUM RISK**
- Modifying existing API logic
- Adding fields that affect serialization
- Changing validation rules
- Modifying rate limiting
- Updating query logic

### 🔴 **HIGH RISK**
- Database schema changes affecting existing data
- Removing fields or models
- Changing authentication/authorization
- Modifying AI feedback prompt structure
- Altering report comparison logic
- Changing foreign key relationships
- Removing API endpoints

### 🔴⚫ **CRITICAL RISK**
- Changes that could cause data loss
- Breaking changes to production APIs
- Security vulnerabilities introduced
- Changes affecting payment/billing (if applicable)
- Modifications that could corrupt AI feedback data
- Changes to case identifier generation logic

---

## 🛠️ Risk Mitigation Strategies

### For Database Changes:
1. ✅ Create reversible migrations when possible
2. ✅ Use `default` or `null=True` for new fields
3. ✅ Test migration on copy of production data
4. ✅ Write data migration for transformations
5. ✅ Document rollback procedure

### For API Changes:
1. ✅ Version APIs if breaking changes are necessary
2. ✅ Update API documentation
3. ✅ Add deprecation warnings before removal
4. ✅ Test with actual frontend integration
5. ✅ Update serializers and validators together

### For Data-Driven Changes:
1. ✅ Ensure metrics remain comparable (or document changes)
2. ✅ Test AI feedback with sample reports before/after
3. ✅ Validate analytics queries against new structure
4. ✅ Consider impact on AIFeedbackRating analysis
5. ✅ Document changes to report comparison logic

### For Performance Changes:
1. ✅ Benchmark before and after
2. ✅ Test with realistic data volumes
3. ✅ Monitor query counts and execution time
4. ✅ Validate rate limiting behavior
5. ✅ Test under concurrent load

---

## 📝 Risk Assessment Template

Use this template for every significant change:

```markdown
## RISK ASSESSMENT: [Brief description of change]

### 🎯 Change Summary
[1-2 sentences describing what you're changing and why]

### 📍 Direct Impact
- Files to modify:
- Models affected:
- API endpoints:
- Frontend dependencies:

### 🔄 Cascading Effects
- Dependent systems:
- Migration required:
- Data integrity concerns:
- Cache invalidation needed:
- AI/Analytics impact:

### 📊 Data-Driven Implications
- Metrics affected:
- AI feedback impact:
- Analytics queries:
- Historical data:
- Report comparison:

### ⚡ Scalability Impact
- Database performance:
- Rate limiting:
- Query optimization:
- Concurrency:
- LLM usage:

### 💥 Breaking Changes
- API breaking changes:
- Frontend updates required:
- Migration order dependencies:
- User workflow impact:
- Backward compatibility:

### 🧪 Testing Requirements
- New tests needed:
- Existing tests to update:
- Migration testing:
- Rollback testing:
- Performance testing:

### 🚦 Overall Risk Level
[🟢 LOW / 🟡 MEDIUM / 🔴 HIGH / 🔴⚫ CRITICAL]

### 🛡️ Mitigation Plan
1. [First mitigation step]
2. [Second mitigation step]
...

### ✅ Pre-Implementation Checklist
- [ ] Risk assessment completed
- [ ] Affected files identified
- [ ] Tests planned
- [ ] Migration strategy defined (if needed)
- [ ] Rollback plan documented
- [ ] Team notified (if high/critical risk)
```

---

## 🎓 Example Risk Assessments

### Example 1: Adding Optional Field to Case Model

```markdown
## RISK ASSESSMENT: Add optional 'patient_weight' field to Case model

### 🎯 Change Summary
Adding optional patient_weight CharField to Case model for additional demographic data.

### 📍 Direct Impact
- Files to modify: backend/cases/models.py, backend/cases/serializers.py
- Models affected: Case
- API endpoints: /api/cases/ (GET/POST/PUT)
- Frontend dependencies: admin-case-edit.js (form)

### 🔄 Cascading Effects
- Dependent systems: None
- Migration required: Yes - simple AddField migration, no data transformation
- Data integrity concerns: None (field is optional)
- Cache invalidation needed: No
- AI/Analytics impact: None (not used in feedback or metrics currently)

### 📊 Data-Driven Implications
- Metrics affected: None
- AI feedback impact: Could be added to context in future, no current impact
- Analytics queries: None affected
- Historical data: Fully compatible (old records will have NULL/blank)
- Report comparison: No impact

### ⚡ Scalability Impact
- Database performance: Minimal (one additional nullable column)
- Rate limiting: No change
- Query optimization: No additional queries needed
- Concurrency: No concerns
- LLM usage: No change

### 💥 Breaking Changes
- API breaking changes: No (adding optional field to response)
- Frontend updates required: admin-case-edit.js (optional - to show field in form)
- Migration order dependencies: None
- User workflow impact: None (optional field)
- Backward compatibility: Full (existing cases continue to work)

### 🧪 Testing Requirements
- New tests needed: Test Case creation with/without patient_weight
- Existing tests to update: May need to update serializer tests
- Migration testing: Test migration on sample database
- Rollback testing: No (simple migration reversal)
- Performance testing: Not needed for single optional field

### 🚦 Overall Risk Level
🟢 LOW

### 🛡️ Mitigation Plan
1. Add field with blank=True, null=True for full backward compatibility
2. Update serializer to include new field
3. Test that existing cases without weight still serialize correctly
4. Update admin form to include field (optional)

### ✅ Pre-Implementation Checklist
- [x] Risk assessment completed
- [x] Affected files identified
- [x] Tests planned
- [x] Migration strategy defined
- [x] Rollback plan documented
- [ ] Team notified (low risk, not required)
```

### Example 2: Modifying AI Feedback Prompt Structure

```markdown
## RISK ASSESSMENT: Modify AI feedback prompt to include patient weight in context

### 🎯 Change Summary
Updating llm_feedback_service.py to include patient_weight in prompt context for more accurate AI feedback.

### 📍 Direct Impact
- Files to modify: backend/cases/llm_feedback_service.py, backend/cases/views.py
- Models affected: None (reading existing Case.patient_weight)
- API endpoints: /api/reports/{id}/ai-feedback/ (POST)
- Frontend dependencies: main.js (no changes, but AI feedback content may differ)

### 🔄 Cascading Effects
- Dependent systems: AI feedback generation, AIFeedbackRating analysis
- Migration required: No
- Data integrity concerns: None
- Cache invalidation needed: No (feedback generated on-demand)
- AI/Analytics impact: ⚠️ HIGH - Changes what information LLM receives

### 📊 Data-Driven Implications
- Metrics affected: ⚠️ AI feedback quality metrics may change
- AI feedback impact: ⚠️ Feedback content will differ when patient_weight is present
- Analytics queries: AIFeedbackRating ratings may trend differently
- Historical data: Old feedback won't have weight-based context (can't regenerate)
- Report comparison: Prompt change may affect consistency of feedback tone/content

### ⚡ Scalability Impact
- Database performance: No change (one additional field read)
- Rate limiting: No change (same number of LLM calls)
- Query optimization: No additional queries
- Concurrency: No concerns
- LLM usage: Token count increases slightly (~10-20 tokens)

### 💥 Breaking Changes
- API breaking changes: No (response structure unchanged)
- Frontend updates required: None
- Migration order dependencies: N/A
- User workflow impact: Users see different feedback style/content
- Backward compatibility: Cases without patient_weight will show "Not specified"

### 🧪 Testing Requirements
- New tests needed: Test feedback generation with/without patient_weight
- Existing tests to update: Update llm_feedback_service tests to mock patient_weight
- Migration testing: N/A
- Rollback testing: Yes - ensure reverting prompt doesn't break anything
- Performance testing: Validate LLM response time doesn't degrade significantly

### 🚦 Overall Risk Level
🟡 MEDIUM (due to data-driven impact on AI feedback consistency)

### 🛡️ Mitigation Plan
1. Use sanitize_text() for patient_weight input to prevent prompt injection
2. Add fallback "Not specified" for cases without patient_weight
3. Monitor AIFeedbackRating for 1-2 weeks post-deployment for quality changes
4. Document prompt change in changelog for future reference
5. Consider A/B testing with subset of users if critical
6. Keep old prompt in comments for easy rollback if feedback quality degrades

### ✅ Pre-Implementation Checklist
- [x] Risk assessment completed
- [x] Affected files identified
- [x] Tests planned
- [x] Migration strategy defined (N/A)
- [x] Rollback plan documented (revert prompt, monitor ratings)
- [x] Team notified (medium risk - review change with team before deployment)
```

---

## 💡 Best Practices

1. **🔄 Always Assess First**: Never make changes without completing a risk assessment
2. **📝 Document Everything**: Written risk assessments help team review and can be referenced later
3. **🧪 Test Thoroughly**: Risk level should determine test coverage requirements
4. **📊 Monitor After Changes**: Especially for data-driven changes, monitor metrics post-deployment
5. **🔙 Plan Rollbacks**: Know how to undo changes before making them
6. **👥 Communicate Risk**: Share high/critical risk assessments with team before implementing
7. **📈 Learn from Issues**: If something breaks, update this guide with lessons learned

---

## 🚨 Red Flags - Stop and Reassess

If you encounter these scenarios, STOP and seek additional guidance:

- ❌ Data migration affects > 10,000 records
- ❌ Change could cause data loss (even temporarily)
- ❌ Removing fields that contain user-generated content
- ❌ Modifying authentication/authorization without security review
- ❌ Changes to AI feedback that could leak sensitive information
- ❌ Breaking changes to public APIs without deprecation period
- ❌ Modifications that bypass rate limiting or security controls
- ❌ Changes to case identifier generation (affects uniqueness)
- ❌ Alterations to report comparison logic without validation against test cases

---

## 📚 Related Documentation

- @.claude/docs/DATA_MODELS.md - Understanding model relationships
- @.claude/docs/WORKFLOWS.md - Safe change workflows
- @.claude/docs/TESTING.md - Comprehensive testing strategies
- @.claude/docs/MONITORING.md - Post-deployment monitoring

---

**Remember**: Taking 10 minutes to assess risk can save hours of debugging and prevent data integrity issues. Always err on the side of caution.
