# Global Peds Reading Room

An educational web platform designed for global pediatric radiology learning and practice. This platform allows medical professionals to view curated radiology cases, submit diagnostic reports, receive AI-powered feedback, and compare their interpretations against expert findings using standardized templates.

## Project Overview

The Global Peds Reading Room aims to provide an interactive learning environment where users can:
- Browse and select radiology cases across various subspecialties and modalities, identified by non-spoiling, human-readable Case IDs.
- View DICOM images for selected cases using an embedded OHIF viewer connected to an Orthanc DICOM server.
- Submit structured diagnostic reports based on provided master templates.
- Receive automated, AI-generated feedback on their submitted reports. This feedback is enhanced by:
    - Comprehensive case context (demographics, clinical history, expert summaries).
    - Programmatic pre-analysis comparing user reports to expert templates and checking for case-specific key concepts.
    - Indication of severity (Critical/Moderate) for identified discrepancies.
    - Structured output for better presentation.
- Compare their reports against expert-filled language-specific templates.
- Provide ratings and comments on the AI-generated feedback to help improve the system.
- Track their progress and learning.

Administrators can:
- Manage users, including registration approvals.
- Create, edit, and manage teaching cases, including linking them to DICOM studies in Orthanc and defining case-specific key concepts to guide AI feedback.
- Manage master report templates and expert-filled language versions of these templates, including defining section-specific key concepts for expert reports.
- Configure system settings.

## Key Features Implemented (Focus on Backend for AI Feedback Enhancement)
- User registration and authentication (with admin approval workflow).
- Admin panel for managing users, cases, and report templates.
- User-facing interface to list and view case details (frontend UI for new AI feedback display is pending).
- DICOM image viewing via an embedded Orthanc OHIF viewer.
- Structured report submission by users based on master templates.
- Display of user's own submitted report alongside expert analysis (frontend UI for new AI feedback display is pending).
- **Enhanced AI-Powered Feedback Backend:**
    - Backend infrastructure significantly updated for more insightful AI feedback using Google Gemini.
    - AI now receives comprehensive case context including patient demographics (age, sex), clinical history, expert-defined key findings, diagnosis, and discussion for the specific case.
    - Programmatic pre-analysis of user reports against expert templates and case-specific key concepts (defined by admins per expert report section) is performed to guide the LLM.
    - LLM is prompted to provide severity levels (Critical/Moderate) with justifications for discrepancies.
    - API endpoint for AI feedback now aims to return structured JSON for richer frontend presentation (frontend display of this structured feedback is pending).
- **Case Identification:** Implemented non-spoiling, human-readable, auto-generated `case_identifier` for user-facing views, replacing potentially revealing titles.
- **User Feedback on AI Feedback:** Backend infrastructure (model, API endpoint) created to allow users to submit 1-5 star ratings and optional comments on the AI-generated critiques. (Frontend UI for this is pending).

## Quick Start

### Prerequisites
- Python 3.8+
- PostgreSQL
- Node.js (currently no frontend build step, but good for potential future tooling)
- An Orthanc DICOM server instance (for DICOM image hosting).
- A Google Gemini API Key (for AI feedback feature).

### Backend Setup (`backend/` directory)
1. Create a Python virtual environment: `python -m venv venv`
2. Activate the virtual environment:
   - Windows PowerShell: `.\venv\Scripts\Activate.ps1`
   - Windows cmd: `venv\Scripts\activate.bat`
   - macOS/Linux: `source venv/bin/activate`
3. Install dependencies: `pip install -r requirements.txt`
4. Create a `.env` file in the `backend/` directory (from `.env.example` if provided, or create new). Add your `DATABASE_URL`, `SECRET_KEY`, and `GEMINI_API_KEY`.
   Example `backend/.env`:
   ```env
   SECRET_KEY="your_strong_secret_key_here"
   DEBUG="True"
   ALLOWED_HOSTS="localhost,127.0.0.1"
   # Database Example (PostgreSQL)
   DB_NAME="globalpeds_db"
   DB_USER="your_db_user"
   DB_PASSWORD="your_db_password"
   DB_HOST="localhost"
   DB_PORT="5432"
   # Gemini API Key
   GEMINI_API_KEY="your_google_gemini_api_key"
   # CORS Origins for frontend dev server
   CORS_ALLOWED_ORIGINS="[http://127.0.0.1:5500](http://127.0.0.1:5500),http://localhost:5500" 
   # Note: If using a different port for frontend, add it here.
Configure database connection details in backend/globalpeds_project/settings.py if not fully covered by .env.Run database migrations: python manage.py migrate (this will include migrations for new fields like case_identifier, patient_sex, key_concepts_text, and the AIFeedbackRating model).Create a superuser (admin account): python manage.py createsuperuserRun the Django development server: python manage.py runserver (Usually at http://127.0.0.1:8000/)Frontend Setup (frontend/ directory)Vanilla JavaScript, HTML, and CSS. No build step is currently required.Ensure API_CONFIG.BASE_URL in frontend/js/api.js points to your running backend (default http://127.0.0.1:8000/api).Ensure your local Orthanc server (with OHIF plugin) is running and accessible (default http://localhost:8042). The orthancOhifViewerBaseUrl in frontend/js/main.js (within viewCase function) may need adjustment if your Orthanc OHIF path is different.Serve the frontend directory using a simple HTTP server:cd frontend
python -m http.server 5500 
Then access the application, typically starting at http://127.0.0.1:5500/login.html.(Note: The frontend UI for displaying the newly structured AI feedback and the redesigned case view page is pending further development).Project Structureglobal-peds-reading-room/
├── backend/                  # Django backend
│   ├── cases/                # Core app: Case mgt, Templates, Reports, DICOM UID, LLM service, AI Feedback Ratings
│   │   ├── models.py         # Defines Case (with case_identifier, patient_sex), CaseTemplateSectionContent (with key_concepts_text), AIFeedbackRating, etc.
│   │   ├── views.py          # Includes AIReportFeedbackView (updated), AIFeedbackRatingCreateView
│   │   ├── serializers.py    # Updated for new fields and AIFeedbackRating
│   │   ├── llm_feedback_service.py # Updated prompt and signature
│   │   └── utils.py          # Contains generate_report_comparison_summary
│   ├── users/                # User authentication & profiles
│   ├── globalpeds_project/   # Django project settings & main URLs
│   ├── api/                  # Main API routing & some auth views
│   ├── .env                  # (NOT COMMITTED) Environment variables
│   ├── manage.py
│   └── requirements.txt
├── frontend/                 # Vanilla JS frontend
│   ├── admin/                # HTML & JS for admin interface pages (add-case.html updated for new fields)
│   ├── assets/               # Images, icons
│   ├── css/                  # CSS stylesheets
│   ├── js/                   # JavaScript files (main.js - user-facing case ID changes implemented; AI feedback display and rating UI pending)
│   └── login.html            
│   └── index.html            
├── docs/                     # Project documentation
└── .gitignore
└── README.md                 # This file
DocumentationArchitecture OverviewProject Map (File & API Structure)Development GuideDeployment GuideChangelogAI Assistant Guide (for collaborators interacting with AI dev assistants)Recent Key Updates (Reflecting Backend Enhancements - May 17, 2025)Core Features Implemented (Backend Focus):Enhanced AI-Powered Feedback Backend:AI (Google Gemini) now receives comprehensive case context: non-spoiling case_identifier, patient demographics (age, sex), clinical history, expert-defined key_findings, diagnosis, and discussion for the specific case.Programmatic pre-analysis of user reports against expert templates and admin-defined, case-specific, section-linked "Key Concepts" (from CaseTemplateSectionContent.key_concepts_text) guides the LLM.LLM prompted to provide "Critical" or "Moderate" severity levels with justifications for discrepancies.API endpoint for AI feedback (/api/cases/reports/<report_id>/ai-feedback/) now returns structured JSON (including raw_llm_feedback and structured_feedback with overall alignment, section-by-section analysis, and key learning points).Case Identification: Implemented non-spoiling, human-readable, auto-generated case_identifier (e.g., NR-MRI-2025-0001) for Case model. This is used in user-facing views and for LLM context. Case.title is now primarily for admin internal organization.Patient Demographics: Added patient_sex to the Case model and admin forms.User Feedback on AI Feedback: Backend model (AIFeedbackRating), serializer, view, and API endpoint (/api/cases/ai-feedback-ratings/) created to allow users to submit 1-5 star ratings and optional comments on AI critiques.DICOM Viewing MVP: Remains functional (Orthanc OHIF viewer integration).User registration (admin approval) & JWT authentication.Admin panel for management of Users, Cases (including DICOM linking, new context fields), and Master Report Templates.User ability to view cases and submit structured reports.Pending Frontend Development:Display of the new structured AI feedback (with severity, justifications, learning points).UI for submitting "Feedback on AI Feedback" (star rating, comments).The full "View Case" page UI/UX overhaul as per visual mockups.For a complete list of detailed changes, see

## Recent Updates
Last updated: May 20, 2025

### Critical Bugs Fixed
- **API Data Handling**: Fixed loadMyReports to handle both paginated and direct array responses
- **Event Listeners**: Implemented single initialization pattern to prevent duplicate registrations
- **Django Admin**: Added proper admin configuration for User and UserProfile models  
- **Path Consistency**: Resolved navigation path issues between frontend and admin sections
- **User Management**: Fixed action handlers for edit, delete, and status toggle operations
- **Case Creation**: Improved draft saving and language version handling
- **Fixed frontend navigation**: Resolved path duplication in URL redirects

### Infrastructure Improvements
- Added requirements.txt with all project dependencies
- Created consolidated .gitignore file at project root
- Added .env.example template for environment configuration

For a complete list of changes, see [CHANGELOG.md](docs/CHANGELOG.md)