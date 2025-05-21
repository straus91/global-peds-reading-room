# Project Map - Global Peds Reading Room

This document outlines the key components and structure of the Global Peds Reading Room project.
**Last Updated: 2025-05-17** (Reflects backend enhancements for AI feedback and case context)

## Backend Structure (`backend/`)

### Core Django Apps

#### `cases/` (Core Application for Case Management, Templates, Reports, DICOM UID, LLM)
- **`models.py`**: Defines the primary data models:
  - `Language`: Available languages for templates and content.
  - `MasterTemplate`: Reusable, structured report templates (admin-defined).
  - `MasterTemplateSection`: Individual sections within a `MasterTemplate`.
  - `Case`: Core teaching case information.
    - Includes clinical data, expert findings, links to `MasterTemplate`.
    - **`orthanc_study_uid`**: For DICOM images.
    - **`case_identifier`**: NEW - Human-readable, non-spoiling, unique ID for user-facing display (e.g., `NR-MRI-2025-0001`), auto-generated. Original `title` field is now primarily for admin internal organization.
    - **`patient_sex`**: NEW - Patient's sex for clinical context.
    - Expert-defined fields (`key_findings`, `diagnosis`, `discussion`) now serve as critical context for AI feedback.
  - `CaseTemplate`: Expert-filled, language-specific versions of a `MasterTemplate` applied to a specific `Case`.
  - `CaseTemplateSectionContent`: The actual expert-written content for each section of a `CaseTemplate`.
    - **`key_concepts_text`**: NEW - Admin-defined, case-specific key concepts for this section of the expert template, used to guide AI feedback.
  - `Report`: User-submitted reports, storing `structured_content` (JSON) based on `MasterTemplateSection`s.
  - `UserCaseView`: Tracks when a user views a case.
  - **`AIFeedbackRating`**: NEW - Stores user-submitted ratings (1-5 stars) and optional comments on the AI-generated feedback for a `Report`.
- **`views.py`**: Contains the API endpoint logic (ViewSets and APIViews):
  - `LanguageViewSet`, `AdminMasterTemplateViewSet`, `AdminCaseViewSet`, `CaseTemplateViewSet`, `UserCaseViewSet`, `ReportCreateView`, `MyReportsListView`.
  - **`AIReportFeedbackView`**: Significantly enhanced.
    - Gathers comprehensive case context (demographics, history, expert summaries from `Case` model).
    - Calls `generate_report_comparison_summary` (from `utils.py`) for programmatic pre-analysis.
    - Passes all context and pre-analysis to `get_feedback_from_llm`.
    - Includes a `_parse_llm_feedback_text` helper method to attempt structuring the LLM's text output into JSON (including overall alignment, section-by-section feedback with severity/justification, and key learning points).
    - API response now includes `raw_llm_feedback` and `structured_feedback`.
  - **`AIFeedbackRatingCreateView`**: NEW - Handles submission of user ratings for AI feedback.
- **`serializers.py`**: Defines how model data is converted to/from JSON for the API:
  - `LanguageSerializer`, `MasterTemplateSectionSerializer`, `MasterTemplateSerializer`.
  - `CaseSerializer`, `CaseListSerializer`, `AdminCaseListSerializer`: Updated to include `case_identifier` and `patient_sex`.
  - `ReportSerializer`: Updated to include `case_identifier_display`.
  - `CaseTemplateSectionContentSerializer`, `CaseTemplateSectionContentUpdateSerializer` (within `BulkCaseTemplateSectionContentUpdateSerializer`): Updated to handle `key_concepts_text`.
  - `CaseTemplateSerializer`, `AdminCaseTemplateSetupSerializer`.
  - **`AIFeedbackRatingSerializer`**: NEW - For validating and saving AI feedback ratings.
- **`urls.py`**: Maps URLs to views within the `cases` app.
  - Includes new URL for `AIFeedbackRatingCreateView`.
  - AI feedback endpoint: `/api/cases/reports/<report_id>/ai-feedback/`.
- **`llm_feedback_service.py`**:
    - `get_feedback_from_llm` function signature updated to accept comprehensive case context and the programmatic pre-analysis summary.
    - LLM prompt significantly enhanced to utilize all new context, incorporate pre-analysis, request "Critical" or "Moderate" severity levels with justifications, and to ignore minor stylistic differences.
- **`utils.py`**:
    - Contains the new `generate_report_comparison_summary` function for programmatic pre-analysis of user vs. expert reports and checking for key concepts.
- **`admin.py`**: Configures how models are displayed and managed in the Django admin interface.
    - Updated for new fields in `Case` (`case_identifier`, `patient_sex`) and `CaseTemplateSectionContent` (`key_concepts_text`).
    - Registered the new `AIFeedbackRating` model.

#### `users/` (User Management and Authentication)
- **`models.py`**: Defines `UserProfile` (extends Django's `User` model).
- **`serializers.py`**: `UserProfileSerializer`, `UserSerializer`, `UserRegistrationSerializer`, `CustomTokenObtainPairSerializer`.
- **`backends.py`**: `EmailBackend` for login with email.

#### `api/` (Main API App for Routing and Core Auth/User Views)
- **`views.py`**: `UserRegisterView`, `CustomTokenObtainPairView`, `LogoutView`, `CurrentUserView`, `AdminUserViewSet`.
- **`urls.py`**: Main API URL configuration, includes URLs from `cases.urls`.

#### `globalpeds_project/` (Django Project Configuration)
- **`settings.py`**: Main Django project settings.
- **`urls.py`**: Root URL configuration.

### Other Key Backend Files
- **`manage.py`**
- **`requirements.txt`** (includes `google-generativeai`, `python-dotenv`).
- **`backend/.env`** (NOT COMMITTED): Stores `GEMINI_API_KEY`, etc.

## Frontend Structure (`frontend/`)

### Core HTML Files
- **`login.html`**
- **`index.html`**: Main user application.
- **`admin/` directory**:
  - `dashboard.html`, `manage_cases.html`, `manage_users.html`, `manage_templates.html`, `settings.html`.
  - **`add_case.html`**: Updated to include input for `patient_sex`, display `case_identifier` (read-only after save), and provide updated help text for AI context fields. Admins can also input `key_concepts_text` when editing expert template sections via this page's JS.

### JavaScript (`js/`)
- **`api.js`**: Centralized API request handling.
- **`auth.js`**: Login, registration, token management.
- **`main.js`**: Core logic for user-facing application.
  - `loadCaseList()`: Updated to display `case_identifier`.
  - `viewCase()`: Updated to display `case_identifier` and `patient_sex`. Logic for displaying new structured AI feedback and feedback rating UI is pending (Phase 2/3 of frontend updates). Hides `Case.discussion` by default. Displays `Case.references`.
  - `displayUserSubmittedReport()`: Fetches AI feedback (now structured JSON from backend). Current display of AI feedback is simplified (shows `raw_llm_feedback`); full structured display pending. Placeholder for `addFeedbackRatingUI` function.
  - `handleReportSubmit()`: Handles submission of user reports.
- **Admin Scripts (`js/admin*.js`):**
  - `admin.js`: Core admin panel logic.
  - **`admin-case-edit.js`**: Updated to handle `patient_sex` field, display `case_identifier`. Includes logic to add/edit `key_concepts_text` for expert template sections and save it via API.
  - `admin-cases.js`: Updated to display `case_identifier` in the cases table.
  - `admin-templates.js`, `admin-users.js`.

### CSS (`css/`) & Assets (`assets/`)
- **`styles.css`**, **`auth.css`**, **`admin.css`**.
- (CSS for new feedback rating UI and overhauled case view page is pending).

## Key API Endpoints (Summary - Relevant Updates)

### Cases & Reports (User-Facing - under `/api/cases/`)
- `GET /cases/cases/`: Lists published cases (response includes `case_identifier`).
- `GET /cases/cases/<case_id>/`: Get details for a specific case (response includes `case_identifier`, `patient_sex`).
- **`GET /reports/<report_id>/ai-feedback/`**: Get AI-generated feedback. Response now includes `raw_llm_feedback` and `structured_feedback` (with overall alignment, section-by-section analysis including severity/justification, and key learning points).

### AI Feedback Rating (NEW - under `/api/cases/`)
- **`POST /ai-feedback-ratings/`**: Submit a user's rating (1-5 stars) and optional comment for AI feedback on a specific report.

### Admin - Cases (`/api/admin/cases/`)
- `GET, POST /`: List all cases or create a new case (payload/response includes `case_identifier`, `patient_sex`).
- `GET, PUT, PATCH, DELETE /<case_id>/`: Manage a specific case (payload/response includes `case_identifier`, `patient_sex`).

### Admin - Case Template Content (`/api/admin/case-templates/`)
- `PUT /<case_template_pk>/update-sections/`: Bulk update section content for a `CaseTemplate`. Payload for each section can now include `key_concepts_text`. Response includes updated `CaseTemplate` with `key_concepts_text` in its section contents.

## Key Workflows (Updated for AI Feedback)

1.  **Admin Creates/Edits Case & Expert Template:**
    - Admin uses `add_case.html` to input case details, including `patient_sex`, and internal `title`. `case_identifier` is auto-generated.
    - Admin defines expert summaries (`key_findings`, `diagnosis`, `discussion`) for the specific case.
    - Admin creates/edits an expert-filled `CaseTemplate` (e.g., English version). For relevant sections, admin *optionally* adds `key_concepts_text` (case-specific, section-linked key phrases).
2.  **User Submits Report.**
3.  **User Requests AI Feedback:**
    - Frontend (`main.js`) calls `/api/cases/reports/<report_id>/ai-feedback/`.
    - Backend (`AIReportFeedbackView`):
        - Retrieves user report, expert `CaseTemplate` (with its `section_contents` including `key_concepts_text`), and full `Case` details (demographics, expert summaries, `case_identifier`).
        - Calls `generate_report_comparison_summary` to perform programmatic text diffs and check for `key_concepts_text` from the expert template against the user's sections, and user's impression against `Case.diagnosis`.
        - Calls `get_feedback_from_llm` with all this context and the pre-analysis summary.
        - `llm_feedback_service.py` uses an enhanced prompt (with all context, pre-analysis, and instructions for severity) to query Gemini.
        - `AIReportFeedbackView` receives LLM text, parses it into structured JSON (overall, per-section with severity/justification, learning points), and returns this to frontend.
4.  **User Views AI Feedback (Frontend - Pending Full UI):**
    - Frontend currently displays `raw_llm_feedback`. (Full structured display and UI overhaul is Point 8).
5.  **User Rates AI Feedback (Frontend - Pending Full UI):**
    - User submits a 1-5 star rating and optional comment.
    - Frontend calls `POST /api/cases/ai-feedback-ratings/`.
    - Backend (`AIFeedbackRatingCreateView`) saves the rating.

Project Map - Global Peds Reading RoomThis document outlines the key components and structure of the Global Peds Reading Room project.Last Updated: 2025-05-20 (Reflects frontend UI layout and AI feedback integration)Backend Structure (backend/)Core Django Appscases/ (Core Application for Case Management, Templates, Reports, DICOM UID, LLM)models.py: Defines the primary data models:Language: Available languages for templates and content.MasterTemplate: Reusable, structured report templates (admin-defined).MasterTemplateSection: Individual sections within a MasterTemplate.Case: Core teaching case information.Includes clinical data, expert findings, links to MasterTemplate.orthanc_study_uid: For DICOM images.case_identifier: Human-readable, non-spoiling, unique ID for user-facing display.patient_sex: Patient's sex for clinical context.Expert-defined fields (key_findings, diagnosis, discussion) serve as critical context for AI feedback.CaseTemplate: Expert-filled, language-specific versions of a MasterTemplate applied to a specific Case.CaseTemplateSectionContent: The actual expert-written content for each section of a CaseTemplate.key_concepts_text: Admin-defined, case-specific key concepts for this section of the expert template, used to guide AI feedback.Report: User-submitted reports, storing structured_content (JSON) based on MasterTemplateSections.UserCaseView: Tracks when a user views a case.AIFeedbackRating: Stores user-submitted ratings (1-5 stars) and optional comments on the AI-generated feedback for a Report.views.py: Contains the API endpoint logic:LanguageViewSet, AdminMasterTemplateViewSet, AdminCaseViewSet, CaseTemplateViewSet, UserCaseViewSet, ReportCreateView, MyReportsListView.AIReportFeedbackView: Gathers comprehensive case context, calls programmatic pre-analysis, passes all context to LLM, and structures the LLM's text output into JSON.AIFeedbackRatingCreateView: Handles submission of user ratings for AI feedback.serializers.py: Defines how model data is converted to/from JSON. Updated for new fields and AIFeedbackRating.urls.py: Maps URLs to views. Includes new URL for AIFeedbackRatingCreateView.llm_feedback_service.py: Handles interaction with Google Gemini API. Prompt enhanced for more context and structured output.utils.py: Contains generate_report_comparison_summary for programmatic pre-analysis of user vs. expert reports.admin.py: Configures Django admin interface. Updated for new model fields.users/ (User Management and Authentication)models.py: Defines UserProfile (extends Django's User model).serializers.py: UserProfileSerializer, UserSerializer, UserRegistrationSerializer, CustomTokenObtainPairSerializer.backends.py: EmailBackend for login with email.api/ (Main API App for Routing and Core Auth/User Views)views.py: UserRegisterView, CustomTokenObtainPairView, LogoutView, CurrentUserView, AdminUserViewSet.urls.py: Main API URL configuration.globalpeds_project/ (Django Project Configuration)settings.py: Main Django project settings.urls.py: Root URL configuration.Other Key Backend Filesmanage.pyrequirements.txt (includes google-generativeai, python-dotenv).backend/.env (NOT COMMITTED): Stores GEMINI_API_KEY, etc.Frontend Structure (frontend/)Core HTML Fileslogin.htmlindex.html: Main user application. Footer simplified.admin/ directory:dashboard.html, manage_cases.html, manage_users.html, manage_templates.html, settings.html, add_case.html. All admin pages updated with simplified footer.JavaScript (js/)api.js: Centralized API request handling.auth.js: Login, registration, token management.main.js: Core logic for user-facing application.loadCaseList(): Implements a side-by-side (two-column) layout for "Case Grid View" and "Case List View" (table).renderCaseDetail():Implements a side-by-side (two-column) layout for "Imaging" and "Case Information".The "Case Information" column features a top strip (case ID, demographics, history, expert diagnosis), a tabbed interface for "Your Submitted Report", "AI Feedback", and "Expert Report", and a bottom strip for references.Stray HTML comments removed.setupInfoTabs(): Handles tab switching logic for the Case Information column.displayUserSubmittedReport(): Populates the "Your Submitted Report" tab.requestAIFeedback(): Populates the "AI Feedback" tab.Admin Scripts (js/admin*.js):admin.js: Core admin panel logic.admin-case-edit.js, admin-cases.js, admin-templates.js, admin-users.js.CSS (css/) & Assets (assets/)styles.css: Major updates for:Side-by-side column layouts on Case List and Case Viewer pages.Scrollbar management to ensure only specific content areas scroll (e.g., right info column on Case Viewer), preventing global page scrollbars and content elongation.Tabbed interface styling for the Case Viewer page.Simplified and more compact footer styling.auth.css, admin.css.Key API Endpoints (Summary - Relevant Updates)No changes to API endpoints themselves from the previous documentation, but the frontend now consumes and presents data differently.AI Feedback endpoint (/api/cases/reports/<report_id>/ai-feedback/) returns structured JSON.Key Workflows (Updated for Frontend Layout)Case Listing: Users see a side-by-side view of case cards and a case table.Case Viewing:DICOM images are displayed in a left column.Case information, user report submission/review, AI feedback, and expert report are displayed in a right column.The right column uses tabs to organize "Your Submitted Report", "AI Feedback", and "Expert Report" after the user has submitted their report.The right column's content (specifically the active tab's content) scrolls independently if it's too long, without affecting the DICOM viewer's height.AI Feedback Interaction: Unchanged from backend perspective; frontend now has a dedicated tab.Admin Footer: All admin pages now use the simplified footer.