# Project Map - Global Peds Reading Room

This document outlines the key components and structure of the Global Peds Reading Room project.

## Backend Structure (`backend/`)

### Core Django Apps

#### `cases/` (Core Application for Case Management, Templates, Reports, DICOM UID, LLM)
- **`models.py`**: Defines the primary data models:
  - `Language`: Available languages for templates and content.
  - `MasterTemplate`: Reusable, structured report templates (admin-defined).
  - `MasterTemplateSection`: Individual sections within a `MasterTemplate`.
  - `Case`: Core teaching case information, including clinical data, expert findings, links to `MasterTemplate`, and **`orthanc_study_uid` for DICOM images**.
  - `CaseTemplate`: Expert-filled, language-specific versions of a `MasterTemplate` applied to a specific `Case`.
  - `CaseTemplateSectionContent`: The actual expert-written content for each section of a `CaseTemplate`.
  - `Report`: User-submitted reports, storing **`structured_content`** (JSON) based on `MasterTemplateSection`s.
  - `UserCaseView`: Tracks when a user views a case.
- **`views.py`**: Contains the API endpoint logic (ViewSets and APIViews):
  - `LanguageViewSet`: Manages languages.
  - `AdminMasterTemplateViewSet`: Admin CRUD for master templates.
  - `AdminCaseViewSet`: Admin CRUD for cases, including actions for managing expert `CaseTemplate`s.
  - `CaseTemplateViewSet`: Admin management for specific `CaseTemplate` content.
  - `UserCaseViewSet`: User-facing read-only access to published cases and expert templates.
  - `ReportCreateView`: Handles user submission of new reports.
  - `MyReportsListView`: Lists reports submitted by the current user.
  - **`AIReportFeedbackView`**: Handles requests to generate AI feedback for a user's report using Gemini.
- **`serializers.py`**: Defines how model data is converted to/from JSON for the API:
  - `LanguageSerializer`, `MasterTemplateSectionSerializer`, `MasterTemplateSerializer`
  - `CaseSerializer` (detailed view, includes `orthanc_study_uid`), `CaseListSerializer`, `AdminCaseListSerializer`
  - `ReportSectionDetailSerializer`, `ReportSerializer` (handles structured report content)
  - `CaseTemplateSectionContentSerializer`, `CaseTemplateSerializer`, `AdminCaseTemplateSetupSerializer`, `BulkCaseTemplateSectionContentUpdateSerializer`
- **`urls.py`**: Maps URLs to views within the `cases` app, including the AI feedback endpoint.
- **`llm_feedback_service.py`**: New service containing logic for interacting with the Google Gemini API to generate report feedback.
- **`admin.py`**: Configures how models are displayed and managed in the Django admin interface.
- **`utils.py`**: (Currently may have placeholder or limited utility functions).

#### `users/` (User Management and Authentication)
- **`models.py`**: Defines `UserProfile` (extends Django's `User` model with role, institution, country, approval_status).
- **`views.py`**: (User-specific actions not related to generic auth are primarily in `api/views.py`).
- **`serializers.py`**:
  - `UserProfileSerializer`, `UserSerializer` (for displaying user info, includes profile).
  - `UserRegistrationSerializer` (for new user sign-ups).
  - `CustomTokenObtainPairSerializer` (customizes JWT login to use email and include user details in token).
- **`backends.py`**: Implements `EmailBackend` to allow login with email.
- **`admin.py`**: Customizes Django admin for `User` and `UserProfile`.

#### `api/` (Main API App for Routing and Core Auth/User Views)
- **`views.py`**:
  - `UserRegisterView`: Handles new user registration.
  - `CustomTokenObtainPairView`: Handles user login (JWT token generation).
  - `LogoutView`: Placeholder for logout.
  - `CurrentUserView`: Endpoint to get details of the logged-in user (`/users/me/`).
  - `AdminUserViewSet`: Admin CRUD for users (list, retrieve, update, delete, approve).
- **`urls.py`**: Main API URL configuration, includes URLs from `cases.urls`. It defines the `/api/` prefix.

#### `globalpeds_project/` (Django Project Configuration)
- **`settings.py`**: Main Django project settings (database, installed apps, middleware, static files, REST Framework, SimpleJWT, CORS, `.env` loading for `GEMINI_API_KEY` etc.).
- **`urls.py`**: Root URL configuration for the Django project (routes to `admin/` and `api/`).
- `wsgi.py`, `asgi.py`: Deployment configuration files.

### Other Key Backend Files
- **`manage.py`**: Django's command-line utility.
- **`requirements.txt`**: List of Python dependencies (includes `google-generativeai`, `python-dotenv`).
- **`backend/.env`** (NOT COMMITTED): Stores secret keys, API keys (like `GEMINI_API_KEY`), database credentials.

## Frontend Structure (`frontend/`)

### Core HTML Files
- **`login.html`**: User login and registration page.
- **`index.html`**: Main application page for authenticated users (case listing, case viewing, reporting).
- **`admin/` directory**: Contains HTML pages for the admin interface:
  - `dashboard.html`
  - `manage_cases.html`, `add_case.html` (handles create & edit of cases, including `orthanc_study_uid` input)
  - `manage_users.html`
  - `manage_templates.html`
  - `settings.html`

### JavaScript (`js/`)
- **`api.js`**: Centralized API request handling function (`apiRequest`) used by all frontend JS.
- **`auth.js`**: Logic for login, registration, token management, and redirection (now corrected).
- **`main.js`**: Core logic for the user-facing application:
  - `checkLoginStatusAndInit()`: Initial page load and user auth check.
  - `loadCaseList()`: Fetches and renders the list of cases.
  - `viewCase()`: Fetches and renders detailed case view, including logic to embed **Orthanc OHIF DICOM viewer in an `<iframe>` using `orthanc_study_uid`**.
  - `handleReportSubmit()`: Handles submission of user reports (structured content).
  - `loadMyReports()`: Displays reports submitted by the user.
  - **`displayUserSubmittedReport()`**: Shows the user's own formatted report and a button to get AI feedback.
  - `populateExpertLanguageSelector()`: Handles language selection for expert reports.
- **`template.js`**: (Legacy placeholder for template data, likely superseded by backend templates).
- **`ui.js`**: UI helper components (Toast notifications, loading indicators).
- **`components.js`**: (Basic component initialization system, may have limited use).
- **Admin Scripts (`js/admin*.js`):**
  - `admin.js`: Core admin panel logic, auth check, common UI initializers (modals, tabs).
  - `admin-case-edit.js`: Logic for `add_case.html` (creating/editing cases, managing `orthanc_study_uid`, handling expert language templates for a case).
  - `admin-cases.js`: Logic for `manage_cases.html` (listing, filtering, searching cases).
  - `admin-templates.js`: Logic for `manage_templates.html` (CRUD for master templates and their sections).
  - `admin-users.js`: Logic for `manage_users.html` (listing, filtering, searching, approving users).

### CSS (`css/`) & Assets (`assets/`)
- **`styles.css`**: Global styles for the user-facing application.
- **`auth.css`**: Styles specific to the login/registration page.
- **`admin.css`**: Styles specific to the admin panel.
- **`assets/img/`**: Logo images, default user avatars.

## Key API Endpoints (Summary)

### Authentication (`/api/auth/`)
- `POST /login/`: User login.
- `POST /register/`: New user registration.
- `POST /login/refresh/`: Refresh JWT access token.
- `POST /logout/`: (Placeholder response).

### User Information (`/api/users/`)
- `GET /me/`: Get details of the currently authenticated user.

### Cases & Reports (User-Facing - under `/api/cases/`)
- `GET /cases/`: List published cases (includes `is_reported_by_user`, `is_viewed_by_user`).
- `GET /cases/<case_id>/`: Get details for a specific case (includes `orthanc_study_uid`, `master_template_details`, `applied_expert_templates`).
- `POST /cases/<case_id>/viewed/`: Mark a case as viewed.
- `GET /cases/<case_id>/expert-templates/<language_code>/`: Get a specific language version of the expert template.
- `POST /reports/`: Submit a new structured report.
- `GET /my-reports/`: List reports submitted by the current user (includes enriched `structured_content`).
- **`GET /reports/<report_id>/ai-feedback/`**: Get AI-generated feedback for a user's report.

### Admin - Users (`/api/admin/users/`)
- `GET, POST /`: List users or create one.
- `GET, PUT, PATCH, DELETE /<user_id>/`: Manage a specific user.
- `PATCH /<user_id>/approve/`: Approve a pending user.
- `PATCH /<user_id>/set-status/`: Set user active/inactive status.

### Admin - Cases (`/api/admin/cases/`)
- `GET, POST /`: List all cases or create a new case (payload includes `orthanc_study_uid`).
- `GET, PUT, PATCH, DELETE /<case_id>/`: Manage a specific case (payload includes `orthanc_study_uid`).
- `GET, POST /<case_id>/expert-templates/`: List or add an expert language template for a case.
- `DELETE /<case_id>/expert-templates/<case_template_pk>/`: Delete an expert language template.

### Admin - Master Templates (`/api/admin/templates/`)
- `GET, POST /`: List master templates or create new.
- `GET, PUT, PATCH, DELETE /<template_id>/`: Manage a specific master template.

### Admin - Case Template Content (`/api/admin/case-templates/`)
- `GET /<case_template_pk>/`: Retrieve a specific expert-filled `CaseTemplate`.
- `PUT /<case_template_pk>/update-sections/`: Bulk update section content for a `CaseTemplate`.

### Admin - Languages (`/api/admin/languages/`)
- `GET, POST /`: List languages or create new.
- `GET, PUT, PATCH, DELETE /<language_id>/`: Manage a specific language.

## Key Workflows (Updated)

1.  **User Registration & Login:**
    - Frontend (`login.html`, `auth.js`) -> Backend API (`/auth/register/`, `/auth/login/`). Admin approval (`manage-users.html`).
2.  **Admin Creates a Case:**
    - Admin uploads (anonymized) DICOM to a separate Orthanc server, notes `StudyInstanceUID`.
    - Frontend (`add_case.html`, `admin-case-edit.js`): Inputs case data, **`orthanc_study_uid`**, associates `MasterTemplate`.
    - Backend (`AdminCaseViewSet`): Saves `Case` model.
3.  **User Views Case & DICOM Images:**
    - Frontend (`index.html`, `main.js` -> `viewCase()`):
        - Fetches case data (including `orthanc_study_uid`).
        - If `orthanc_study_uid` exists, constructs URL for Orthanc OHIF viewer and embeds in `<iframe>`.
        - Displays case details, report form (if not yet reported).
4.  **User Submits Report:**
    - Frontend (`main.js` -> `handleReportSubmit()`): Sends structured report to `/cases/reports/`.
    - Backend (`ReportCreateView`): Saves `Report` with `structured_content`.
5.  **User Views Own Report, Expert Analysis, and AI Feedback:**
    - Frontend (`main.js` -> `viewCase()` calls `displayUserSubmittedReport()`):
        - Displays user's own report.
        - Shows "Get AI Feedback" button. On click, calls `/reports/<report_id>/ai-feedback/`.
        - Backend (`AIReportFeedbackView` -> `llm_feedback_service`) interacts with Gemini, returns feedback.
        - Frontend displays AI feedback.
        - Frontend also displays expert analysis (from `CaseTemplate`).