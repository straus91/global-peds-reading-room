Global Peds Reading RoomAn educational web platform designed for global pediatric radiology learning and practice. This platform allows medical professionals to view curated radiology cases, submit diagnostic reports, receive AI-powered feedback, and compare their interpretations against expert findings using standardized templates.Project OverviewThe Global Peds Reading Room aims to provide an interactive learning environment where users can:Browse and select radiology cases across various subspecialties and modalities, identified by non-spoiling, human-readable Case IDs.View DICOM images for selected cases using an embedded OHIF viewer connected to an Orthanc DICOM server.Submit structured diagnostic reports based on provided master templates.Receive automated, AI-generated feedback on their submitted reports, enhanced by comprehensive case context, programmatic pre-analysis, and severity indications for discrepancies.Compare their reports against expert-filled language-specific templates.Provide ratings and comments on the AI-generated feedback to help improve the system.Track their progress and learning.Administrators can:Manage users, including registration approvals.Create, edit, and manage teaching cases, including linking them to DICOM studies in Orthanc and defining case-specific key concepts to guide AI feedback.Manage master report templates and expert-filled language versions of these templates.Configure system settings.Key FeaturesThe platform includes the following core features:User registration and authentication with admin approval.Comprehensive admin panel for managing users, cases, and report templates.DICOM image viewing via an embedded Orthanc OHIF viewer.Structured report submission and display of user reports.Enhanced AI-Powered Feedback System: Backend infrastructure significantly updated for more insightful AI feedback using Google Gemini, incorporating case context, programmatic pre-analysis, and severity levels.Non-Spoiling Case Identification: Auto-generated, human-readable case_identifier for user-facing views.User Feedback on AI Feedback: Backend infrastructure for users to submit ratings and comments on AI critiques.For a complete and detailed list of all changes and features, please refer to the Changelog.Quick StartThis guide will help you get the Global Peds Reading Room application up and running on your local machine for development.PrerequisitesPython 3.8+PostgreSQLAn Orthanc DICOM server instance (for DICOM image hosting).A Google Gemini API Key (for AI feedback feature).Backend Setup (backend/ directory)Create a Python virtual environment:python -m venv venv
Activate the virtual environment:Windows PowerShell: .\venv\Scripts\Activate.ps1Windows cmd: venv\Scripts\activate.batmacOS/Linux: source venv/bin/activateInstall dependencies:pip install -r requirements.txt
Create a .env file: In the backend/ directory, create a .env file (you can copy from .env.example if provided, or create new). Add your SECRET_KEY, PostgreSQL database credentials (DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT), and your GEMINI_API_KEY.Example backend/.env:SECRET_KEY="your_strong_secret_key_here"
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
CORS_ALLOWED_ORIGINS="http://127.0.0.1:5500,http://localhost:5500" 
Run database migrations: This will set up your database schema, including all necessary tables for cases, users, templates, and AI feedback.python manage.py migrate
Create a superuser (admin account):python manage.py createsuperuser
Run the Django development server:python manage.py runserver
The backend API will typically be accessible at http://127.0.0.1:8000/.Frontend Setup (frontend/ directory)The frontend is built with Vanilla JavaScript, HTML, and CSS. No complex build step is currently required.Configure API Base URL: Ensure API_CONFIG.BASE_URL in frontend/js/api.js points to your running backend (default http://127.0.0.1:8000/api).Configure Orthanc Viewer URL: Ensure your local Orthanc server (with OHIF plugin) is running and accessible (default http://localhost:8042). The orthancOhifViewerBaseUrl in frontend/js/main.js (within the setupDicomViewer function) may need adjustment if your Orthanc OHIF path is different.Serve the frontend directory: You can use a simple Python HTTP server:cd frontend
python -m http.server 5500
Then, access the application by navigating to http://127.0.0.1:5500/login.html in your web browser.Project Structureglobal-peds-reading-room/
├── backend/                  # Django backend application and API
│   ├── cases/                # Core application logic for cases, reports, templates, and AI feedback
│   ├── users/                # User authentication and profiles
│   ├── globalpeds_project/   # Django project settings and main URL configurations
│   ├── api/                  # Main API routing and common authentication views
│   ├── .env                  # Environment variables (NOT COMMITTED)
│   ├── manage.py             # Django management utility
│   └── requirements.txt      # Python dependencies
├── frontend/                 # Vanilla JavaScript, HTML, and CSS for the user interface
│   ├── admin/                # HTML pages for the admin interface
│   ├── assets/               # Images, icons, and other static assets
│   ├── css/                  # Stylesheets
│   ├── js/                   # JavaScript files for frontend logic
│   └── login.html            # User login page
│   └── index.html            # Main user application page
├── docs/                     # Detailed project documentation
├── .gitignore                # Git ignore rules
└── README.md                 # This file
DocumentationFor more in-depth information about the project, please refer to the following documentation files located in the docs/ directory:Architecture Overview: Details the system's architecture, technology stack, data flow, and security.Development Guide: Instructions for setting up the development environment, code style, and common development tasks.Project Map: A detailed breakdown of the backend and frontend file structure, including models, views, and API endpoints.AI Assistant Guide: Specific documentation on the AI-powered feedback system, its implementation, and how to work with it.Deployment Guide: Checklist and steps for deploying the application to a production environment.Changelog: A comprehensive record of all notable changes, features, and fixes across different versions.