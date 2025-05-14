# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Added
- Initial documentation structure
- Consolidated project organization

### Changed
- Moved from separate frontend/backend git repos to unified structure
- Consolidated multiple .gitignore files

### Fixed
- Patient Age and Key Findings saving issues in admin interface
- Modality and Subspecialty abbreviation handling

## [Initial] - May 2025

### Added
- Core Django backend with cases and users apps
- Vanilla JavaScript frontend
- Admin interface for case management
- User report submission functionality
- Master template system for reports



# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Added
- Initial documentation structure
- Consolidated project organization
- requirements.txt file for Python dependencies
- .env.example template for environment configuration
- Proper Django admin configuration for User and UserProfile models
- Basic DICOM integration:
    - Cases can now be linked to DICOM studies in Orthanc via `StudyInstanceUID`.
    - User-facing case view embeds Orthanc's OHIF viewer in an `<iframe>` to display linked DICOM studies.
- AI Report Feedback (Gemini) - Backend MVP:
    - Created `llm_feedback_service.py` in the `cases` app to interact with the Google Gemini API.
    - Added `AIReportFeedbackView` and a new API endpoint (`/api/cases/reports/<report_id>/ai-feedback/`) to trigger and return AI-generated feedback on user reports.
    - Added `google-generativeai` to Python dependencies and configured API key handling via `.env`.
    - Implemented a more focused prompt for the LLM to provide concise, discrepancy-focused feedback for the MVP.
- (You might have other "Added" items from previous commits here)

### Changed
- Moved from separate frontend/backend git repos to unified structure
- Consolidated multiple .gitignore files into single root file
- Updated login redirect paths to proper frontend structure
- Language version handling now auto-saves case as draft first

### Fixed
- Patient Age and Key Findings saving issues in admin interface
- Modality and Subspecialty abbreviation handling
- API data handling for loadMyReports (supports both paginated and direct array responses)
- Multiple event listener registration issue with single initialization pattern
- Path consistency issues across the application
- Manage Cases table action button alignment and display
- Admin Users action button handlers (edit, delete, status toggle)
- Backend now allows DELETE operations for users
- Case creation form submission to handle draft saving properly
- Frontend case view button functionality
- Corrected admin and user login redirection paths to prevent "double frontend" error (`frontend/js/auth.js`).
- Implemented display of user's own submitted report on the case view page, allowing users to compare with expert analysis (`frontend/js/main.js`).
- Resolved issues in "Add Language Version" flow on the new case page (`frontend/js/admin-case-edit.js`):
    - Ensured case draft save completes before attempting to add language versions.
    - Corrected display of language names in the "Available Languages" dropdown modal.
    - Corrected admin and user login redirection paths to prevent "double frontend" error (`frontend/js/auth.js`).
- Implemented display of user's own submitted report on the case view page, allowing users to compare with expert analysis (`frontend/js/main.js`).
- Resolved issues in "Add Language Version" flow on the new case page (`frontend/js/admin-case-edit.js`):
    - Ensured case draft save completes before attempting to add language versions.
    - Corrected display of language names in the "Available Languages" dropdown modal.
- **Ensured `python-dotenv` is installed and correctly loads `GEMINI_API_KEY` from `backend/.env` at Django startup (`backend/globalpeds_project/settings.py`).**
- **Corrected `NameError` in `llm_feedback_service.py` by properly defining `expert_key_findings_str` before use in the prompt.**
- (You might have other "Fixed" items from previous commits here)
