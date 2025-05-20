# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased] - MVP Features & Fixes (As of 2025-05-14)

### Added
- **DICOM Viewing MVP:**
    - Integrated Orthanc's OHIF viewer via an `<iframe>` in the user-facing case view page (`frontend/js/main.js`) to display DICOM images.
    - Added `orthanc_study_uid` field to the `Case` model (`backend/cases/models.py`) and relevant serializers (`backend/cases/serializers.py`) to link application cases to DICOM studies in an Orthanc server.
    - Updated the admin case creation/editing form (`frontend/admin/add-case.html`, `frontend/js/admin-case-edit.js`) to allow administrators to input the `orthanc_study_uid`.
    - Created necessary database migrations for the new DICOM linking field.
- **AI Report Feedback (Google Gemini) MVP:**
    - Implemented backend infrastructure for AI-powered feedback on user-submitted radiology reports.
    - Created `llm_feedback_service.py` in the `cases` app to handle interaction with the Google Gemini API.
    - Developed a new API endpoint (`/api/cases/reports/<report_id>/ai-feedback/`) and `AIReportFeedbackView` to trigger feedback generation.
    - Added `google-generativeai` and `python-dotenv` to Python dependencies (`backend/requirements.txt`).
    - Configured secure API key handling for Gemini using an `.env` file (`backend/.env`, loaded by `backend/globalpeds_project/settings.py`).
    - Developed an initial focused prompt for the Gemini LLM to provide concise, discrepancy-focused feedback comparing user reports to expert reports.
    - Added frontend UI elements (button and display area) in the user case view (`frontend/js/main.js`) to request and display AI-generated feedback.
- **User Experience Enhancements:**
    - Implemented display of a user's own submitted report on the case view page, allowing for direct comparison with expert analysis and AI feedback (`frontend/js/main.js`).

### Fixed
- **Authentication & Navigation:**
    - Corrected admin and user login redirection paths in `frontend/js/auth.js` to prevent "double frontend" URL errors.
- **Admin Case Management:**
    - Resolved issues in the "Add Language Version" flow on the "Add/Edit Case" page (`frontend/js/admin-case-edit.js`):
        - Ensured case draft save completes successfully (and `currentCaseId` is available) before attempting to add language versions for new cases.
        - Corrected display of language names in the "Available Languages" dropdown modal.
- **LLM Integration & Configuration:**
    - Ensured `python-dotenv` is correctly installed and configured to load the `GEMINI_API_KEY` from `backend/.env` at Django startup, resolving API key availability issues (`backend/globalpeds_project/settings.py`, `backend/cases/llm_feedback_service.py`).
    - Corrected a `NameError` in `backend/cases/llm_feedback_service.py` by properly defining `expert_key_findings_str` before its use in the LLM prompt.
    - Updated the Gemini model name used in `llm_feedback_service.py` to a generally available and supported version (`gemini-1.5-flash-latest`) to resolve API errors.
- **Miscellaneous Past Fixes (Consolidated from previous `[Unreleased]` sections):**
    - Addressed Patient Age and Key Findings saving issues in the admin interface.
    - Improved Modality and Subspecialty abbreviation handling.
    - Enhanced API data handling for `loadMyReports` to support both paginated and direct array responses.
    - Resolved potential multiple event listener registration issues.
    - General path consistency improvements across the application.
    - Fixed Manage Cases table action button alignment and display.
    - Corrected Admin Users action button handlers (edit, delete, status toggle).
    - Ensured backend allows DELETE operations for users via the API.

### Changed
- Refined the LLM prompt for AI feedback to be more concise and focused on discrepancies for the MVP.
- (Include other significant changes if any from previous `[Unreleased]` blocks that are now stable)

---
## Previous Development Notes (Pre-May 2025 MVP Focus)
*(This section can be used to archive older "Unreleased" items once a version/date is established above, or if you had older distinct versions)*

### Added
- Initial documentation structure.
- Consolidated project organization.
- `requirements.txt` file for Python dependencies.
- `.env.example` template for environment configuration.
- Proper Django admin configuration for User and UserProfile models.

### Changed
- Moved from separate frontend/backend git repos to unified structure.
- Consolidated multiple .gitignore files into single root file.

---
## [Initial Release Candidate] - May 2025 (Example, if you were tagging a release)

### Added
- Core Django backend with cases and users apps.
- Vanilla JavaScript frontend.
- Admin interface for case management.
- User report submission functionality.
- Master template system for reports.

# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased] - Next Steps (Frontend Focus)

### Pending
- **Frontend UI for Enhanced AI Feedback (Point 8 & others):**
    - Implement the new two-panel "View Case" page layout (DICOM viewer left, Info/Review right).
    - Right Panel - Top Strip: Display `case_identifier`, demographics, concise clinical history, and **prominently highlighted Expert Diagnosis (`Case.diagnosis`)**.
    - Right Panel - Middle (Two Columns):
        - *Left Column:* Display user's full report, with sections visually highlighted based on AI-assessed severity (Critical/Moderate).
        - *Right Column (Tab-Switchable):*
            - Default Tab "AI Feedback Summary": List sections flagged by AI, showing severity and brief LLM justification.
            - Tab "Full AI Detailed Feedback": Display complete LLM output.
            - Tab "Expert Report": Display full expert-filled `CaseTemplate` content.
    - Right Panel - Bottom Strip: Display `Case.references` and implement the "Feedback on AI Feedback" UI (1-5 stars, optional comment).
- **Frontend - Display Admin-Provided Learning Resources (Point 4 - Simplified):**
    - Ensure `Case.references` are clearly parsed and displayed as clickable links/formatted text on the "View Case" page.
- **Frontend - Case Identification (Point 7 Refinement):**
    - Ensure all user-facing case lists and detail views primarily display the new `case_identifier` (or `Case ID: ${case.id}` as fallback) instead of the internal `Case.title`.
- **Deferred (Future Considerations):**
    - Keyword highlighting within the AI's own output text (Original Point 5).
    - Advanced Learning Resources: AI-suggested topics linked to a separate, curated general library.
    - LLM ingestion of case-specific PDFs for feedback context.

---
## [Backend Enhancements] - 2025-05-17

### Added
- **Enhanced AI-Powered Feedback Backend (Points 1, 3, 7):**
    - `Case` model: Added `patient_sex` field.
    - `CaseTemplateSectionContent` model: Added `key_concepts_text` field for admins to define case-specific, section-linked key concepts for expert reports, used to guide AI.
    - `llm_feedback_service.py`:
        - `get_feedback_from_llm` signature updated to accept comprehensive case context (`case_identifier`, demographics, full expert summaries from `Case` model: `key_findings`, `diagnosis`, `discussion`, and `difficulty`).
        - LLM prompt significantly enhanced to utilize all new context, incorporate programmatic pre-analysis, request "Critical" or "Moderate" severity levels with justifications for discrepancies, and to ignore minor stylistic differences.
    - `cases/utils.py`: Added `generate_report_comparison_summary` function to programmatically compare user vs. expert reports (textual diff per section, check for admin-defined `key_concepts_text` in user sections, and compare user impression against `Case.diagnosis`).
    - `AIReportFeedbackView` (`cases/views.py`):
        - Now gathers all new case context.
        - Calls `generate_report_comparison_summary` and feeds its output into the LLM prompt.
        - Passes all comprehensive context to `get_feedback_from_llm`.
        - Includes a `_parse_llm_feedback_text` method to attempt structuring the LLM's text output into JSON (overall alignment, section-by-section feedback with severity/justification, key learning points).
        - API response for AI feedback (`/api/cases/reports/<report_id>/ai-feedback/`) now includes `raw_llm_feedback` and `structured_feedback`.
- **Case Identification & Admin Workflow (Point 7 Refinement):**
    - `Case` model: Added `case_identifier` field (e.g., `SUB-MOD-YYYY-NNNN`), auto-generated in `save()` method, unique, and human-readable. `Case.title` becomes primarily for admin internal organization.
    - Admin interfaces (`cases/admin.py`, `frontend/admin/add-case.html`, `frontend/js/admin-case-edit.js`) updated to support `patient_sex`, display `case_identifier`, and allow input of `key_concepts_text` for expert template sections. Help texts updated to guide AI-relevant input.
- **User Feedback on AI Feedback Backend (Point 6):**
    - `AIFeedbackRating` model created (`report_id`, `user_id`, `star_rating` 1-5, optional `comment`, `rated_at`).
    - `AIFeedbackRatingSerializer` and `AIFeedbackRatingCreateView` created.
    - API endpoint `POST /api/cases/ai-feedback-ratings/` added to save user ratings.
- **Standardized Section Naming/Order (Point 2 - Confirmation):**
    - Confirmed that `MasterTemplateSection.name` and `.order` are the source of truth.
    - Operational guideline: Avoid changing active `MasterTemplate` structures.
- **Learning Resources (Point 4 - Simplified Backend Support):**
    - Ensured `Case.references` field is available via `CaseSerializer` for frontend display. (No new backend models for a general resource library in this iteration).

### Changed
- **Admin Interface (`cases/admin.py`):** Updated `list_display`, filters, search fields, and inlines for `CaseAdmin`, `CaseTemplateAdmin`, `CaseTemplateSectionContentAdmin` to reflect new model fields and improve usability.
- **Serializers (`cases/serializers.py`):**
    - `CaseSerializer`, `CaseListSerializer`, `AdminCaseListSerializer` updated for `case_identifier` and `patient_sex`.
    - `CaseTemplateSectionContentSerializer` and `CaseTemplateSectionContentUpdateSerializer` (within `BulkCaseTemplateSectionContentUpdateSerializer`) updated to handle `key_concepts_text`.
- **LLM Prompt:** Major revisions to be more structured, accept more context, and request specific output formats (severity, justifications).

### Fixed
- Previous `NameError` issues in `admin.py`, `serializers.py`, and `views.py` related to missing `models` or `PatientSexChoices` imports.
- Database migration issues related to adding `unique=True` field `case_identifier` by setting `null=True` and relying on `save()` method for population.

---
## [MVP Features & Fixes] - 2025-05-14 (Consolidated from previous state)

### Added
- **DICOM Viewing MVP:**
    - Integrated Orthanc's OHIF viewer via `<iframe>`.
    - Added `orthanc_study_uid` to `Case` model, serializers, and admin forms.
- **Initial AI Report Feedback (Google Gemini) MVP:**
    - Basic backend infrastructure (`llm_feedback_service.py`, `AIReportFeedbackView`).
    - Initial focused prompt for discrepancy feedback.
    - Frontend button to request and display raw AI feedback text.
- **User Experience Enhancements:**
    - Display of user's own submitted report on the case view page.

### Fixed
- Authentication & Navigation redirection paths.
- Admin Case Management flow for "Add Language Version".
- Gemini API key loading and model name issues.
- Patient Age and Key Findings saving in admin.
- Modality/Subspecialty abbreviation handling.
- API data handling for `loadMyReports`.

### Changed
- Initial refinement of LLM prompt for conciseness.

---
## [Initial Release Candidate] - (Date of that phase)
*(Archive older items here)*
