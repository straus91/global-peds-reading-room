# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Global Peds Reading Room is an educational web platform for global pediatric radiology learning and practice. The platform allows medical professionals to view curated radiology cases, submit diagnostic reports, receive AI-powered feedback, and compare their interpretations against expert findings using standardized templates.

## Tech Stack

- **Backend**: Django 5.x with Django REST Framework, PostgreSQL
- **Frontend**: Vanilla JavaScript, HTML5, CSS3
- **AI Integration**: Google Gemini API for report feedback analysis
- **External Services**: Orthanc DICOM Server with OHIF Viewer integration

## Environment Setup

### Backend Setup Commands

```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment
python -m venv venv
# On Windows PowerShell:
.\venv\Scripts\Activate.ps1
# On Windows cmd:
venv\Scripts\activate.bat
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables (copy from .env.example or create new)
# Required variables in .env: 
# - SECRET_KEY, DEBUG, ALLOWED_HOSTS
# - DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT
# - GEMINI_API_KEY
# - CORS_ALLOWED_ORIGINS

# Run database migrations
python manage.py migrate

# Create superuser for admin access
python manage.py createsuperuser

# Run the development server
python manage.py runserver
```

### Frontend Setup Commands

```bash
# Navigate to frontend directory
cd frontend

# Serve the frontend files using Python's HTTP server
python -m http.server 5500
```

## Key Development Tasks

### Running the Backend Server

```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate.bat or .\venv\Scripts\Activate.ps1
python manage.py runserver
```

### Running Backend Tests

```bash
cd backend
python manage.py test
```

### Running Tests for a Specific App

```bash
cd backend
python manage.py test cases
```

### Running a Specific Test Case

```bash
cd backend
python manage.py test cases.tests.TestCaseName
```

### Running a Specific Test Method

```bash
cd backend
python manage.py test cases.tests.TestCaseName.test_method_name
```

### Creating Database Migrations

```bash
cd backend
python manage.py makemigrations
```

### Applying Database Migrations

```bash
cd backend
python manage.py migrate
```

## Architecture Overview

The application uses a client-server architecture with:

1. **Frontend** (Browser-based UI):
   - Vanilla JavaScript with ES6+ features
   - Communicates with backend via REST API
   - Embeds Orthanc OHIF Viewer for DICOM images
   - Structured into separate JS modules for different functionalities

2. **Backend** (Django REST API):
   - Django REST Framework for API endpoints
   - JWT authentication
   - PostgreSQL for data storage
   - Google Gemini API integration for AI feedback

3. **External Services**:
   - Orthanc DICOM Server for storing and viewing medical images
   - Google Gemini API for AI-powered report feedback

## Key Components

### Backend Architecture

- **cases/**: Core application with models and APIs for cases, reports, templates, and AI feedback
- **users/**: User authentication and profile management
- **api/**: Main API routing and authentication views
- **globalpeds_project/**: Django project settings

### Frontend Organization

- **js/api.js**: Centralized API client for all backend communication
- **js/main.js**: Core application logic including case viewing and report submission
- **js/admin-*.js**: Admin-specific functionalities
- **js/components.js**: Reusable UI components
- **js/ui.js**: UI utility functions

### AI Feedback System

The AI feedback system is a core feature that:
1. Collects user-submitted reports and compares them with expert templates
2. Performs programmatic pre-analysis to identify basic discrepancies
3. Sends this context along with the report to the Google Gemini API
4. Processes the AI response into structured feedback with severity levels
5. Displays feedback to users and allows them to rate its helpfulness

Key files for the AI system:
- **backend/cases/llm_feedback_service.py**: Service for interacting with Google Gemini API
- **backend/cases/utils.py**: Contains `generate_report_comparison_summary()` for pre-analysis
- **backend/cases/views.py**: `AIReportFeedbackView` orchestrates the feedback generation process