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