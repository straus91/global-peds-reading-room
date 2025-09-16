# Project Map - Global Peds Reading Room

This document outlines the key components and structure of the Global Peds Reading Room project.

## Backend Structure (backend/)

### Core Django Apps

#### cases/ (Core Application for Case Management, Templates, Reports, DICOM UID, LLM)

- **models.py**: Defines the primary data models:
  - Language: Available languages for templates and content.
  - MasterTemplate: Reusable, structured report templates (admin-defined).
  - MasterTemplateSection: Individual sections within a MasterTemplate.
  - Case: Core teaching case information.
    - Includes clinical data, expert findings, links to MasterTemplate.
    - orthanc_study_uid: For DICOM images.
    - case_identifier: Human-readable, non-spoiling, unique ID for user-facing display (e.g., NR-MRI-2025-0001), auto-generated. Original title field is now primarily for admin internal organization.
    - patient_sex: Patient's sex for clinical context.
    - Expert-defined fields (key_findings, diagnosis, discussion) now serve as critical context for AI feedback.
  - CaseTemplate: Expert-filled, language-specific versions of a MasterTemplate applied to a specific Case.
  - CaseTemplateSectionContent: The actual expert-written content for each section of a CaseTemplate.
    - key_concepts_text: Admin-defined, case-specific key concepts for this section of the expert template, used to guide AI feedback.
  - Report: User-submitted reports, storing structured_content (JSON) based on MasterTemplateSections.
  - UserCaseView: Tracks when a user views a case.
  - AIFeedbackRating: Stores user-submitted ratings (1-5 stars) and optional comments on the AI-generated feedback for a Report.

- **views.py**: Contains the API endpoint logic (ViewSets and APIViews):
  - LanguageViewSet, AdminMasterTemplateViewSet, AdminCaseViewSet, CaseTemplateViewSet, UserCaseViewSet, ReportCreateView, MyReportsListView.
  - AIReportFeedbackView: Gathers comprehensive case context, calls programmatic pre-analysis, passes all context to LLM, and structures the LLM's text output into JSON.
    - Enhanced with atomic transactions for database operations.
    - Improved error handling with specific error responses.
    - Detailed logging for debugging and monitoring.
  - AIFeedbackRatingCreateView: Handles submission of user ratings for AI feedback.

- **serializers.py**: Defines how model data is converted to/from JSON for the API:
  - LanguageSerializer, MasterTemplateSectionSerializer, MasterTemplateSerializer.
  - CaseSerializer, CaseListSerializer, AdminCaseListSerializer: Updated to include case_identifier and patient_sex.
  - ReportSerializer: Updated to include case_identifier_display.
  - CaseTemplateSectionContentSerializer, CaseTemplateSectionContentUpdateSerializer (within BulkCaseTemplateSectionContentUpdateSerializer): Updated to handle key_concepts_text.
  - CaseTemplateSerializer, AdminCaseTemplateSetupSerializer.
  - AIFeedbackRatingSerializer: For validating and saving AI feedback ratings.

- **urls.py**: Maps URLs to views within the cases app.
  - Includes new URL for AIFeedbackRatingCreateView.
  - AI feedback endpoint: /api/cases/reports/<report_id>/ai-feedback/.

- **llm_feedback_service.py**:
  - get_feedback_from_llm function signature updated to accept comprehensive case context and the programmatic pre-analysis summary.
  - LLM prompt significantly enhanced to utilize all new context, incorporate pre-analysis, request "Critical" or "Moderate" severity levels with justifications, and to ignore minor stylistic differences.
  - Input sanitization with sanitize_text() to prevent prompt injection attacks.
  - Rate limiting with check_rate_limit() to prevent API abuse.
  - Model caching with @lru_cache for performance optimization.
  - Enhanced error handling for Google API errors.
  - Replaced print statements with structured logging.
  - Safety settings for medical content.

- **utils.py**:
  - Contains the new generate_report_comparison_summary function for programmatic pre-analysis of user vs. expert reports and checking for key concepts.

- **admin.py**: Configures how models are displayed and managed in the Django admin interface.
  - Updated for new fields in Case (case_identifier, patient_sex) and CaseTemplateSectionContent (key_concepts_text).
  - Registered the new AIFeedbackRating model.

#### users/ (User Management and Authentication)
- **models.py**: Defines UserProfile (extends Django's User model).
- **serializers.py**: UserProfileSerializer, UserSerializer, UserRegistrationSerializer, CustomTokenObtainPairSerializer.
- **backends.py**: EmailBackend for login with email.

#### api/ (Main API App for Routing and Core Auth/User Views)
- **views.py**: UserRegisterView, CustomTokenObtainPairView, LogoutView, CurrentUserView, AdminUserViewSet.
- **urls.py**: Main API URL configuration, includes URLs from cases.urls.

#### globalpeds_project/ (Django Project Configuration)
- **settings.py**: Main Django project settings.
- **urls.py**: Root URL configuration.

### Other Key Backend Files
- manage.py
- requirements.txt (includes google-generativeai, python-dotenv).
- backend/.env (NOT COMMITTED): Stores GEMINI_API_KEY, etc.

## Frontend Structure (frontend/)

### Core HTML Files
- login.html
- index.html: Main user application. Footer simplified.
- admin/ directory:
  - dashboard.html, manage_cases.html, manage_users.html, manage_templates.html, settings.html.
  - add_case.html: Updated to include input for patient_sex, display case_identifier (read-only after save), and provide updated help text for AI context fields. Admins can also input key_concepts_text when editing expert template sections via this page's JS. All admin pages updated with simplified footer.

### JavaScript (js/)
- **api.js**: Centralized API request handling.
- **auth.js**: Login, registration, token management.
- **main.js**: Core logic for user-facing application.
  - loadCaseList(): Implements a side-by-side (two-column) layout for "Case Grid View" and "Case List View" (table).
  - viewCase(): Implements a side-by-side (two-column) layout for "Imaging" and "Case Information".
    - The "Case Information" column features a top strip (case ID, demographics, history, expert diagnosis), a tabbed interface for "Your Submitted Report", "AI Feedback", and "Expert Report", and a bottom strip for references.
    - Stray HTML comments removed.
  - setupInfoTabs(): Handles tab switching logic for the Case Information column.
  - displayUserSubmittedReport(): Populates the "Your Submitted Report" tab.
  - requestAIFeedback(): Populates the "AI Feedback" tab.
  - handleReportSubmit(): Handles submission of user reports.
- **Admin Scripts (js/admin*.js)**:
  - admin.js: Core admin panel logic.
  - admin-case-edit.js: Updated to handle patient_sex field, display case_identifier. Includes logic to add/edit key_concepts_text for expert template sections and save it via API.
  - admin-cases.js: Updated to display case_identifier in the cases table.
  - admin-templates.js, admin-users.js.

### CSS (css/) & Assets (assets/)
- **styles.css**: Major updates for:
  - Side-by-side column layouts on Case List and Case Viewer pages.
  - Scrollbar management to ensure only specific content areas scroll (e.g., right info column on Case Viewer), preventing global page scrollbars and content elongation.
  - Tabbed interface styling for the Case Viewer page.
  - Simplified and more compact footer styling.
- auth.css, admin.css.

## Documentation (docs/)

The project includes comprehensive documentation to guide developers, administrators, and users:

- **ARCHITECTURE.md**: Provides an overview of the system architecture and design patterns.
- **CHANGELOG.md**: Documents all notable changes to the project in a chronological order.
- **DEPLOYMENT.md**: Instructions for deploying the application to production environments.
- **DEVELOPMENT.md**: Guide for setting up development environment and contributing to the project.
  - Includes sections on code style, making changes, and common development tasks.
  - Updated with security best practices section.
- **PROJECT_MAP.md**: This document, providing a map of the project structure and components.
- **AI_GUIDE.md**: Detailed documentation of the AI feedback system.
  - Context and goals
  - Key files and roles
  - Implementation patterns
  - Recent enhancements including security improvements
- **SECURITY.md**: New document outlining security practices and features.
  - Input validation and sanitization
  - Rate limiting and resource protection
  - Error handling and recovery
  - Transaction safety
  - Logging and monitoring
  - API key and secret management
  - Best practices for developers

## Key API Endpoints (Summary)

### Cases & Reports (User-Facing - under /api/cases/)
- GET /cases/cases/: Lists published cases (response includes case_identifier).
- GET /cases/cases/<case_id>/: Get details for a specific case (response includes case_identifier, patient_sex).
- GET /reports/<report_id>/ai-feedback/: Get AI-generated feedback. Response now includes raw_llm_feedback and structured_feedback (with overall alignment, section-by-section analysis including severity/justification, and key learning points).

### AI Feedback Rating (NEW - under /api/cases/)
- POST /ai-feedback-ratings/: Submit a user's rating (1-5 stars) and optional comment for AI feedback on a specific report.

### Admin - Cases (/api/admin/cases/)
- GET, POST /: List all cases or create a new case (payload/response includes case_identifier, patient_sex).
- GET, PUT, PATCH, DELETE /<case_id>/: Manage a specific case (payload/response includes case_identifier, patient_sex).

### Admin - Case Template Content (/api/admin/case-templates/)
- PUT /<case_template_pk>/update-sections/: Bulk update section content for a CaseTemplate. Payload for each section can now include key_concepts_text. Response includes updated CaseTemplate with key_concepts_text in its section contents.

## Key Workflows

### Admin Creates/Edits Case & Expert Template:
1. Admin uses add_case.html to input case details, including patient_sex, and internal title. case_identifier is auto-generated.
2. Admin defines expert summaries (key_findings, diagnosis, discussion) for the specific case.
3. Admin creates/edits an expert-filled CaseTemplate (e.g., English version). For relevant sections, admin optionally adds key_concepts_text (case-specific, section-linked key phrases).

### User Submits Report.

### User Requests AI Feedback:
1. Frontend (main.js) calls /api/cases/reports/<report_id>/ai-feedback/.
2. Backend (AIReportFeedbackView):
   - Retrieves user report, expert CaseTemplate (with its section_contents including key_concepts_text), and full Case details (demographics, expert summaries, case_identifier).
   - Calls generate_report_comparison_summary to perform programmatic text diffs and check for key_concepts_text from the expert template against the user's sections, and user's impression against Case.diagnosis.
   - Calls get_feedback_from_llm with all this context and the pre-analysis summary.
   - llm_feedback_service.py uses an enhanced prompt (with all context, pre-analysis, and instructions for severity) to query Gemini.
   - AIReportFeedbackView receives LLM text, parses it into structured JSON (overall, per-section with severity/justification, learning points), and returns this to frontend.

### User Views AI Feedback:
- User sees color-coded feedback with critical and non-critical discrepancies clearly separated.
- Sections are colored based on severity (red/yellow/green).

### User Rates AI Feedback:
1. User submits a 1-5 star rating and optional comment.
2. Frontend calls POST /api/cases/ai-feedback-ratings/.
3. Backend (AIFeedbackRatingCreateView) saves the rating.