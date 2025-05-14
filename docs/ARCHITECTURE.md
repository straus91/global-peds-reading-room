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
| - User Interface (Case lists, Case view, Reporting form)                         |
| - Admin Interface (User, Case, Template Management)                              |
| - DICOM Viewer (Embedded Orthanc OHIF via iframe)                                |
| - API Client (js/api.js for all backend communication)                           |
+------------------------+------------------------+--------------------------------+
| (HTTPS - REST API      | (HTTPS - REST API for AI Feedback)
|  for app data)         |
▼                        ▼
+------------------------+------------------------+      +--------------------------+
| Backend (Django & Django REST Framework)        |----->| Google Gemini API        |
| - API Endpoints (api/, cases/, users/)          |      | (LLM for Report Feedback)|
| - Business Logic (views.py, services)           |      +--------------------------+
| - Data Models (models.py for Case, Report, User)|
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

*Diagram Note: The Django backend communicates with PostgreSQL for application data and with Orthanc for DICOM study information. The Frontend fetches data from Django and embeds the Orthanc OHIF viewer.*

## Technology Stack

### Backend
- **Framework:** Django 5.x with Django REST Framework (DRF) for building robust APIs.
- **Database:** PostgreSQL for relational data storage (cases, users, reports, templates).
- **Authentication:** JWT (JSON Web Tokens) using `djangorestframework-simplejwt` for stateless API authentication. Custom `EmailBackend` allows login with email.
- **CORS Handling:** `django-cors-headers` to manage cross-origin requests from the frontend.
- **Environment Variables:** `python-dotenv` for managing configuration and sensitive keys (e.g., `GEMINI_API_KEY`, `SECRET_KEY`, database credentials).
- **LLM Integration:** `google-generativeai` Python SDK for interacting with Google Gemini models to provide report feedback.

### Frontend
- **Core Technologies:** Vanilla JavaScript (ES6+), HTML5, CSS3.
- **API Communication:** Native Fetch API, abstracted via a utility function in `js/api.js`.
- **DICOM Viewing:** Embedding Orthanc's OHIF (Open Health Imaging Foundation) Viewer via an `<iframe>`. The `StudyInstanceUID` stored with each case is used to construct the direct viewer URL.
- **Development Serving:** Python's built-in `http.server` or similar for serving static files during development. No complex frontend build process is currently required.

### External Services / Key Integrations
- **Orthanc DICOM Server:** An external or locally hosted Orthanc instance is required for storing, managing, and serving DICOM images. The application embeds its OHIF web viewer. The Django backend stores references (e.g., `orthanc_study_uid`) to link application cases to studies in Orthanc.
- **Google Gemini API:** Used by the backend to provide AI-powered feedback on user-submitted radiology reports by comparing them against expert interpretations.

## Data Flow Highlights

1.  **Authentication:** User logs in via the frontend (`login.html`); credentials are sent to the Django backend (`/api/auth/login/`). Upon success, JWT tokens (access & refresh) are returned and stored in the frontend's localStorage. Subsequent API requests to protected endpoints include the access token in the Authorization header.
2.  **Case Data & DICOM Linking (Admin):**
    * Administrators create/edit cases via the admin frontend (`add_case.html`).
    * They input case metadata and an `orthanc_study_uid` (obtained from their Orthanc server where the DICOM study is stored).
    * This data is saved to the PostgreSQL database via the Django backend API (`/api/admin/cases/`).
3.  **Case Viewing & DICOM Display (User):**
    * Users browse cases listed on `index.html` (data fetched from `/api/cases/cases/`).
    * When a user views a specific case, `frontend/js/main.js` fetches detailed case data (including `orthanc_study_uid`) from `/api/cases/cases/<case_id>/`.
    * If `orthanc_study_uid` is present, JavaScript constructs the appropriate URL for the Orthanc OHIF viewer (e.g., `http://ORTHANC_IP:PORT/ohif/viewer?StudyInstanceUIDs=<UID>`) and sets this as the `src` for an `<iframe>`, displaying the DICOM images.
4.  **Report Submission:**
    * Users submit structured reports for a case via a form on the case view page.
    * The report content (structured by master template sections) is sent to `/api/cases/reports/`.
    * The Django backend saves this `structured_content` (as JSON) in the `Report` model in PostgreSQL.
5.  **AI Feedback Generation:**
    * After submitting a report, the user can click a "Get AI Feedback" button.
    * The frontend calls a backend API endpoint: `/api/cases/reports/<report_id>/ai-feedback/`.
    * The Django backend (`AIReportFeedbackView` and `llm_feedback_service.py`) retrieves the user's report and the relevant expert `CaseTemplate` content.
    * It formats a detailed prompt including both reports and the case context.
    * This prompt is sent to the Google Gemini API.
    * The LLM's textual feedback is returned to the Django backend, which then relays it to the frontend for display.

## Security Considerations

- **API Keys:** The `GEMINI_API_KEY` is stored as an environment variable on the backend (loaded from `backend/.env`, which is gitignored) and is not exposed to the frontend. Orthanc server access credentials (if any) should also be managed securely.
- **Authentication & Authorization:**
    - API endpoints are protected using JWT authentication (`IsAuthenticated` for users, `IsAdminUser` for admin-specific actions).
    - User-specific data (like "My Reports") is filtered by the authenticated user.
- **CORS (Cross-Origin Resource Sharing):**
    - `django-cors-headers` is configured on the Django backend to allow requests from the frontend's development server origin (e.g., `http://127.0.0.1:5500`).
    - The Orthanc server must also be configured with appropriate CORS headers and potentially `X-Frame-Options` or `Content-Security-Policy` to allow its OHIF viewer to be embedded in an `<iframe>` by the main application's domain.
- **Data Privacy (DICOM):** For an educational platform, it is critical that all DICOM data uploaded to Orthanc and used in cases is thoroughly **anonymized** according to relevant standards (e.g., HIPAA de-identification rules if applicable, or general best practices for educational data) before being made accessible.
- **Input Validation:** Standard Django/DRF mechanisms are used for validating incoming API data on the backend. Frontend input validation is also present for a better user experience.
- **HTTPS:** Should be enforced in any production deployment for all communication