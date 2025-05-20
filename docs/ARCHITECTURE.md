# Architecture Overview

## System Architecture

The Global Peds Reading Room application follows a client-server architecture with distinct backend and frontend components, and integration with external services for DICOM handling and AI-powered feedback.

                           +---------------------+
                           | User's Web Browser  |
                           +--------+------------+
                                    | (HTTPS - HTML, CSS, JS)
                                    ▼
+---------------------------------------+------------------------------------------+
| Frontend (Vanilla JavaScript, HTML, CSS) - Served Statically or via Dev Server   |
| - User Interface (Case lists, Case view using `case_identifier`, Reporting form) |
| - Admin Interface (User, Case, Template Management - including new Case fields)  |
| - DICOM Viewer (Embedded Orthanc OHIF via iframe)                                |
| - API Client (js/api.js for all backend communication)                           |
| - UI for submitting AI Feedback Ratings (Pending full implementation)            |
+------------------------+------------------------+--------------------------------+
| (HTTPS - REST API      | (HTTPS - REST API for AI Feedback & Ratings)
|  for app data)         |
▼                        ▼
+------------------------+------------------------+      +--------------------------+
| Backend (Django & Django REST Framework)        |----->| Google Gemini API        |
| - API Endpoints (api/, cases/, users/)          |      | (LLM for Report Feedback)|
|   - Enhanced AI Feedback Endpoint (structured JSON) |      +--------------------------+
|   - New AI Feedback Rating Endpoint             |
| - Business Logic (views.py, services, utils.py) |
|   - Programmatic report pre-analysis            |
| - Data Models (models.py for Case with new fields,|
|   Report, User, Template, AIFeedbackRating)     |
| - Authentication (SimpleJWT)                    |
| - PostgreSQL Interface                          |
| - Orthanc Integration (Stores/retrieves UIDs)   |
+------------------------+------------------------+
| (SQL)                  | (DICOMweb/HTTP to Orthanc)
▼                        ▼
+-----------------+     +--------------------------------------+
|   PostgreSQL    |     | Orthanc DICOM Server                 |
| (Application    |     | - Stores/Manages DICOM files         |
|  Data Storage)  |     | - Provides OHIF Viewer (embedded)    |
+-----------------+     | - DICOMweb services (WADO-RS, etc.)  |
                        +--------------------------------------+

*Diagram Note: The Django backend communicates with PostgreSQL for application data and with Orthanc for DICOM study information. The Frontend fetches data from Django and embeds the Orthanc OHIF viewer. The AI Feedback workflow is now more sophisticated.*

## Technology Stack

### Backend
- **Framework:** Django 5.x with Django REST Framework (DRF).
- **Database:** PostgreSQL.
- **Authentication:** JWT (JSON Web Tokens) via `djangorestframework-simplejwt`.
- **CORS Handling:** `django-cors-headers`.
- **Environment Variables:** `python-dotenv`.
- **LLM Integration:** `google-generativeai` Python SDK for Google Gemini.
- **Core Logic:**
    - `cases/models.py`: Defines `Case` (now with `case_identifier`, `patient_sex`), `CaseTemplateSectionContent` (with `key_concepts_text`), and new `AIFeedbackRating` model.
    - `cases/llm_feedback_service.py`: Contains `get_feedback_from_llm` with an enhanced prompt that accepts more context (case details, expert summaries, programmatic pre-analysis) and instructs the LLM on severity assignment.
    - `cases/utils.py`: Includes `generate_report_comparison_summary` for programmatic pre-analysis of user vs. expert reports and checking for admin-defined key concepts.
    - `cases/views.py`: `AIReportFeedbackView` orchestrates data gathering, pre-analysis, LLM call, and structuring of the AI feedback into JSON. New `AIFeedbackRatingCreateView` handles user ratings.

### Frontend
- **Core Technologies:** Vanilla JavaScript (ES6+), HTML5, CSS3.
- **API Communication:** Native Fetch API via `js/api.js`.
- **DICOM Viewing:** Embedded Orthanc OHIF Viewer.
- **Case Identification:** Users primarily see and interact with a non-spoiling, human-readable `case_identifier`. The internal `Case.title` is for admin organization.

### External Services / Key Integrations
- **Orthanc DICOM Server:** As before.
- **Google Gemini API:** Used by the backend for AI-powered feedback. The interaction is now more context-rich.

## Data Flow Highlights

1.  **Authentication:** Unchanged.
2.  **Case Data & DICOM Linking (Admin):**
    * Admins create/edit cases, inputting metadata including `patient_sex`, `orthanc_study_uid`, and an internal `title`. A unique, human-readable `case_identifier` is auto-generated.
    * Admins define expert summaries (`key_findings`, `diagnosis`, `discussion`) directly on the `Case` model.
    * When creating/editing expert-filled `CaseTemplate`s, admins can optionally add `key_concepts_text` to individual `CaseTemplateSectionContent` items (these are case-specific, section-linked key phrases).
3.  **Case Viewing & DICOM Display (User):**
    * Users browse cases identified by `case_identifier`.
    * `viewCase()` in `frontend/js/main.js` fetches case data (including `case_identifier`, `patient_sex`, `orthanc_study_uid`, expert summaries from `Case` model).
    * DICOM display via Orthanc OHIF iframe remains the same.
4.  **Report Submission:** Unchanged at the core (structured report sent to backend).
5.  **AI Feedback Generation (Enhanced):**
    * User requests AI feedback via frontend.
    * Frontend calls `/api/cases/reports/<report_id>/ai-feedback/`.
    * Django backend (`AIReportFeedbackView`):
        a. Retrieves user's report, the relevant expert `CaseTemplate` (including its `section_contents` with `key_concepts_text`), and the full `Case` object (with `case_identifier`, `patient_sex`, `clinical_history`, expert `key_findings`, `diagnosis`, `discussion`, `difficulty`).
        b. Calls `utils.generate_report_comparison_summary` to perform programmatic text diffs (user section vs. expert section) and check if user addressed the admin-defined `key_concepts_text` for each section and the overall `Case.diagnosis`.
        c. Calls `llm_feedback_service.get_feedback_from_llm`, passing the user report text, expert report text, the comprehensive case context, and the programmatic pre-analysis summary.
        d. The LLM prompt now instructs Gemini to use all this context, identify discrepancies, assign severity ("Critical" or "Moderate") with justification, and provide key learning points.
        e. `AIReportFeedbackView` receives the LLM's text response and uses its `_parse_llm_feedback_text` method to attempt to structure it into JSON (overall alignment, section-by-section feedback with severity/justification, learning points).
        f. Returns this structured JSON (along with raw LLM text) to the frontend.
6.  **User Rates AI Feedback (New Workflow):**
    * Frontend (pending full UI implementation) will display a 1-5 star rating and optional comment box.
    * On submission, frontend calls `POST /api/cases/ai-feedback-ratings/`.
    * Backend (`AIFeedbackRatingCreateView`) saves the rating to the `AIFeedbackRating` model.

## Security Considerations
- Unchanged from previous, with continued emphasis on anonymized DICOM data and secure API key management.
- The new `AIFeedbackRating` endpoint should ensure users can only submit ratings for feedback on reports they have permission to access (typically their own). The current serializer logic implies this by linking to a `Report` which is user-associated.
