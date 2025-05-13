@echo off
REM Project Organization Script for Global Peds Reading Room (Windows)
REM This script will help reorganize your project structure

echo === Global Peds Reading Room - Project Organization ===
echo This script will help organize your project structure
echo.

REM 1. Clean up Git issues
echo Step 1: Cleaning up Git files...
if exist "backend\.git" (
    echo Found stray .git directory in backend
    set /p confirm="Remove backend\.git directory? (y/n): "
    if /i "%confirm%"=="y" (
        rmdir /s /q "backend\.git"
        echo Removed backend\.git
    )
)

REM 2. Create unified repository structure
echo.
echo Step 2: Creating unified repository structure...

REM Create docs directory
if not exist "docs" mkdir docs
echo Created docs directory

REM 3. Create main .gitignore file
echo.
echo Step 3: Creating consolidated .gitignore...
(
echo # Python
echo *.pyc
echo __pycache__/
echo *.py[cod]
echo *$py.class
echo *.so
echo venv/
echo env/
echo ENV/
echo .Python
echo pip-log.txt
echo pip-delete-this-directory.txt
echo .tox/
echo .coverage
echo .coverage.*
echo .cache
echo .pytest_cache/
echo nosetests.xml
echo coverage.xml
echo *.cover
echo .hypothesis/
echo.
echo # Django
echo *.log
echo local_settings.py
echo db.sqlite3
echo db.sqlite3-journal
echo media/
echo staticfiles/
echo .env
echo *.env.*
echo.
echo # Frontend
echo node_modules/
echo npm-debug.log*
echo yarn-debug.log*
echo yarn-error.log*
echo .npm
echo .eslintcache
echo.
echo # IDE
echo .vscode/
echo .idea/
echo *.swp
echo *.swo
echo *~
echo.
echo # OS
echo .DS_Store
echo Thumbs.db
echo.
echo # Project specific
echo backend/venv/
echo *.docx
echo project_analysis_*.json
) > .gitignore

echo Created consolidated .gitignore

REM 4. Create README.md
echo.
echo Step 4: Creating README.md...
(
echo # Global Peds Reading Room
echo.
echo Educational web platform for global pediatric radiology learning.
echo.
echo ## Project Overview
echo.
echo The Global Peds Reading Room allows medical professionals to:
echo - View curated radiology cases
echo - Submit diagnostic reports for learning
echo - Compare reports against expert interpretations
echo - Practice with standardized report templates
echo.
echo ## Quick Start
echo.
echo ### Prerequisites
echo - Python 3.8+
echo - PostgreSQL
echo - Node.js ^(for any future frontend tooling^)
echo.
echo ### Backend Setup
echo ```bash
echo cd backend
echo python -m venv venv
echo venv\Scripts\activate  # On Windows
echo pip install -r requirements.txt
echo python manage.py migrate
echo python manage.py createsuperuser
echo python manage.py runserver
echo ```
echo.
echo ### Frontend Setup
echo ```bash
echo cd frontend
echo # Currently using vanilla JS - no build step required
echo # Open index.html in browser or serve with:
echo python -m http.server 8080
echo ```
echo.
echo ## Project Structure
echo ```
echo global-peds-reading-room/
echo ├── backend/              # Django backend
echo │   ├── cases/           # Core case management app
echo │   ├── users/           # User authentication/profiles
echo │   └── globalpeds_project/  # Django settings
echo ├── frontend/            # Vanilla JS frontend
echo │   ├── admin/          # Admin interface
echo │   ├── js/             # JavaScript files
echo │   └── css/            # Stylesheets
echo └── docs/               # Documentation
echo ```
echo.
echo ## Documentation
echo - [Architecture Overview](docs/ARCHITECTURE.md^)
echo - [API Reference](docs/API.md^)
echo - [Development Guide](docs/DEVELOPMENT.md^)
echo - [Deployment Guide](docs/DEPLOYMENT.md^)
echo.
echo ## Recent Updates
echo Last updated: May 12, 2025
echo - [List recent changes here]
echo.
echo ## For AI Developers
echo When making changes:
echo 1. Update this README with recent changes
echo 2. Add comments to new functions
echo 3. Update the project map in docs/PROJECT_MAP.md
echo 4. Create a brief entry in docs/CHANGELOG.md
) > README.md

echo Created README.md

REM 5. Create project documentation structure
echo.
echo Step 5: Creating documentation structure...

REM Create PROJECT_MAP.md
(
echo # Project Map - Global Peds Reading Room
echo.
echo ## Backend Structure
echo.
echo ### Core Django Apps
echo.
echo #### cases/ ^(Core Application^)
echo - **models.py**: Data models
echo   - `Language`: Available languages for templates
echo   - `MasterTemplate`: Reusable report templates
echo   - `Case`: Teaching case information
echo   - `Report`: User-submitted reports
echo   - `CaseTemplate`: Expert-filled templates
echo.
echo - **views.py**: API endpoints
echo   - `AdminCaseViewSet`: Admin case management
echo   - `UserCaseViewSet`: User-facing case viewing
echo   - `ReportCreateView`: Report submission
echo.
echo - **serializers.py**: API serialization
echo   - `CaseSerializer`: Case data serialization
echo   - `ReportSerializer`: Report handling
echo   - `MasterTemplateSerializer`: Template management
echo.
echo #### users/ ^(Authentication^)
echo - **models.py**: User profile extension
echo - **views.py**: Authentication endpoints
echo - **backends.py**: Custom auth backend
echo.
echo ### Configuration
echo - **globalpeds_project/settings.py**: Django settings
echo - **requirements.txt**: Python dependencies
echo.
echo ## Frontend Structure
echo.
echo ### User Interface ^(js/^)
echo - **main.js**: Main user interface
echo   - `loadCaseList^(^)`: Display case list
echo   - `viewCase^(^)`: Show case details
echo   - `handleReportSubmit^(^)`: Submit reports
echo.
echo - **api.js**: API communication layer
echo   - `apiRequest^(^)`: HTTP request handler
echo.
echo - **auth.js**: Authentication logic
echo.
echo ### Admin Interface ^(admin/^)
echo - **admin.js**: Core admin functionality
echo - **admin-cases.js**: Case management
echo - **admin-templates.js**: Template management
echo - **admin-users.js**: User management
echo.
echo ### Styles ^(css/^)
echo - **styles.css**: Global styles
echo - **admin.css**: Admin panel styles
echo - **auth.css**: Login page styles
echo.
echo ## API Endpoints
echo.
echo ### Authentication
echo - POST `/api/users/login/`
echo - POST `/api/users/register/`
echo - GET `/api/users/me/`
echo.
echo ### Cases
echo - GET `/api/cases/cases/` - List cases
echo - GET `/api/cases/cases/{id}/` - Case detail
echo - POST `/api/cases/reports/` - Submit report
echo.
echo ### Admin
echo - GET/POST `/api/cases/admin/cases/`
echo - GET/POST `/api/cases/master-templates/`
echo.
echo ## Key Workflows
echo.
echo 1. **User Views Case**
echo    - Frontend: `main.js` → `loadCaseList^(^)` → `viewCase^(^)`
echo    - Backend: `UserCaseViewSet` → `CaseSerializer`
echo.
echo 2. **User Submits Report**
echo    - Frontend: `handleReportSubmit^(^)` → `apiRequest^(^)`
echo    - Backend: `ReportCreateView` → `ReportSerializer`
echo.
echo 3. **Admin Creates Template**
echo    - Frontend: `admin-templates.js`
echo    - Backend: `AdminMasterTemplateViewSet`
) > docs\PROJECT_MAP.md

echo Created docs\PROJECT_MAP.md

REM Create remaining documentation files
echo Creating additional documentation files...

REM ARCHITECTURE.md
(
echo # Architecture Overview
echo.
echo ## System Architecture
echo.
echo ```
echo ┌─────────────────┐     ┌─────────────────┐
echo │   Frontend      │     │   Backend       │
echo │  ^(Vanilla JS^)   │────▶│  ^(Django DRF^)   │
echo └─────────────────┘     └─────────────────┘
echo                               │
echo                               ▼
echo                        ┌─────────────────┐
echo                        │   PostgreSQL    │
echo                        └─────────────────┘
echo ```
echo.
echo ## Technology Stack
echo.
echo ### Backend
echo - Django 4.x with Django REST Framework
echo - PostgreSQL database
echo - JWT authentication ^(Simple JWT^)
echo - django-cors-headers for CORS
echo.
echo ### Frontend
echo - Vanilla JavaScript ^(ES6+^)
echo - Native Fetch API for HTTP requests
echo - CSS3 for styling
echo - No build process required
echo.
echo ## Data Flow
echo.
echo 1. User authentication via JWT tokens
echo 2. API requests include auth token in headers
echo 3. Backend validates and processes requests
echo 4. JSON responses sent to frontend
echo 5. Frontend updates UI dynamically
echo.
echo ## Security
echo.
echo - JWT tokens stored in localStorage
echo - CORS configured for frontend origin
echo - User roles: Admin, Medical Professional
echo - Protected endpoints require authentication
) > docs\ARCHITECTURE.md

REM Create remaining files...
echo Creating DEVELOPMENT.md...
(
echo # Development Guide
echo.
echo ## Setting Up Development Environment
echo.
echo ### Backend Setup
echo 1. Create virtual environment
echo 2. Install dependencies: `pip install -r requirements.txt`
echo 3. Configure database in settings.py
echo 4. Run migrations: `python manage.py migrate`
echo 5. Create superuser: `python manage.py createsuperuser`
echo.
echo ### Frontend Setup
echo 1. No build process required
echo 2. Serve files locally or open directly in browser
echo 3. Update `API_CONFIG.BASE_URL` in js/api.js if needed
echo.
echo ## Code Style Guidelines
echo.
echo ### Python ^(Backend^)
echo - Follow PEP 8
echo - Use meaningful variable names
echo - Add docstrings to functions
echo - Keep views focused and simple
echo.
echo ### JavaScript ^(Frontend^)
echo - Use const/let instead of var
echo - Async/await for API calls
echo - Meaningful function names
echo - Comment complex logic
echo.
echo ## Making Changes
echo.
echo ### Before Starting
echo 1. Pull latest changes
echo 2. Create feature branch
echo 3. Update from main regularly
echo.
echo ### After Changes
echo 1. Test thoroughly
echo 2. Update documentation
echo 3. Add comments to code
echo 4. Update PROJECT_MAP.md
echo 5. Create changelog entry
echo.
echo ## Common Tasks
echo.
echo ### Adding a New API Endpoint
echo 1. Create view in views.py
echo 2. Add serializer if needed
echo 3. Register URL in urls.py
echo 4. Update frontend API calls
echo 5. Document in PROJECT_MAP.md
echo.
echo ### Adding Frontend Feature
echo 1. Create/modify JS file
echo 2. Update HTML if needed
echo 3. Add styles to CSS
echo 4. Test across browsers
echo 5. Update documentation
) > docs\DEVELOPMENT.md

echo Creating CHANGELOG.md...
(
echo # Changelog
echo.
echo All notable changes to this project will be documented in this file.
echo.
echo The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/^).
echo.
echo ## [Unreleased]
echo.
echo ### Added
echo - Initial documentation structure
echo - Consolidated project organization
echo.
echo ### Changed
echo - Moved from separate frontend/backend git repos to unified structure
echo - Consolidated multiple .gitignore files
echo.
echo ### Fixed
echo - Patient Age and Key Findings saving issues in admin interface
echo - Modality and Subspecialty abbreviation handling
echo.
echo ## [Initial] - May 2025
echo.
echo ### Added
echo - Core Django backend with cases and users apps
echo - Vanilla JavaScript frontend
echo - Admin interface for case management
echo - User report submission functionality
echo - Master template system for reports
) > docs\CHANGELOG.md

echo Creating AI_GUIDE.md...
(
echo # AI Assistant Guide
echo.
echo ## Quick Context
echo.
echo This is the Global Peds Reading Room - a medical education platform for pediatric radiology.
echo.
echo ## Key Files to Know
echo.
echo ### Backend ^(Django^)
echo - `cases/models.py` - Core data models
echo - `cases/views.py` - API endpoints
echo - `cases/serializers.py` - Data serialization
echo.
echo ### Frontend ^(Vanilla JS^)
echo - `js/main.js` - User interface logic
echo - `js/api.js` - API communication
echo - `js/admin.js` - Admin panel
echo.
echo ## Common Tasks
echo.
echo ### Adding a Feature
echo 1. Check PROJECT_MAP.md for structure
echo 2. Implement backend first ^(if needed^)
echo 3. Update frontend to use new backend
echo 4. Test thoroughly
echo 5. Update documentation
echo.
echo ### Fixing a Bug
echo 1. Identify affected files
echo 2. Check git history if needed
echo 3. Fix issue
echo 4. Test related functionality
echo 5. Update CHANGELOG.md
echo.
echo ## Important Patterns
echo.
echo - JWT auth tokens in localStorage
echo - API calls use `apiRequest^(^)` function
echo - Admin pages check authentication first
echo - Reports use structured content ^(JSON^)
echo.
echo ## Recent Issues Fixed
echo - Patient Age saving
echo - Modality abbreviations
echo - Dynamic report sections
) > docs\AI_GUIDE.md

echo Creating DEPLOYMENT.md...
(
echo # Deployment Guide
echo.
echo ## Production Checklist
echo.
echo ### Security
echo - [ ] Set DEBUG = False
echo - [ ] Update SECRET_KEY
echo - [ ] Configure ALLOWED_HOSTS
echo - [ ] Set up HTTPS
echo - [ ] Configure CORS properly
echo.
echo ### Database
echo - [ ] Set up production PostgreSQL
echo - [ ] Run migrations
echo - [ ] Create admin user
echo - [ ] Backup strategy
echo.
echo ### Static Files
echo - [ ] Configure static file serving
echo - [ ] Set up CDN if needed
echo - [ ] Minify CSS/JS
echo.
echo ### Environment
echo - [ ] Create .env file
echo - [ ] Set environment variables
echo - [ ] Configure logging
echo.
echo ## Basic Deployment Steps
echo.
echo 1. Clone repository
echo 2. Set up virtual environment
echo 3. Install dependencies
echo 4. Configure environment variables
echo 5. Run migrations
echo 6. Collect static files
echo 7. Set up web server ^(Nginx/Apache^)
echo 8. Configure WSGI server ^(Gunicorn^)
echo 9. Set up SSL certificate
echo 10. Start services
) > docs\DEPLOYMENT.md

echo.
echo === Organization Complete! ===
echo.
echo Next steps:
echo 1. Review the created files
echo 2. Commit everything to git
echo 3. Remove old .gitignore files in subdirectories
echo 4. Update the documentation as you work
echo.
echo Created documentation in docs/:
echo - PROJECT_MAP.md ^(file reference^)
echo - ARCHITECTURE.md ^(system overview^)
echo - DEVELOPMENT.md ^(dev guide^)
echo - DEPLOYMENT.md ^(deployment guide^)
echo - CHANGELOG.md ^(change tracking^)
echo - AI_GUIDE.md ^(AI assistant reference^)

pause