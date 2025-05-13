# Global Peds Reading Room

Educational web platform for global pediatric radiology learning.

## Project Overview

The Global Peds Reading Room allows medical professionals to:
- View curated radiology cases
- Submit diagnostic reports for learning
- Compare reports against expert interpretations
- Practice with standardized report templates

## Quick Start

### Prerequisites
- Python 3.8+
- PostgreSQL
- Node.js (for any future frontend tooling)

### Backend Setup
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # On Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### Frontend Setup
```bash
cd frontend
# Currently using vanilla JS - no build step required
# Open index.html in browser or serve with:
python -m http.server 8080
```

## Project Structure
```
global-peds-reading-room/
├── backend/              # Django backend
│   ├── cases/           # Core case management app
│   ├── users/           # User authentication/profiles
│   └── globalpeds_project/  # Django settings
├── frontend/            # Vanilla JS frontend
│   ├── admin/          # Admin interface
│   ├── js/             # JavaScript files
│   └── css/            # Stylesheets
└── docs/               # Documentation
```

## Documentation
- [Architecture Overview](docs/ARCHITECTURE.md)
- [API Reference](docs/API.md)
- [Development Guide](docs/DEVELOPMENT.md)
- [Deployment Guide](docs/DEPLOYMENT.md)

## Recent Updates
Last updated: May 12, 2025

### Critical Bugs Fixed
- **API Data Handling**: Fixed loadMyReports to handle both paginated and direct array responses
- **Event Listeners**: Implemented single initialization pattern to prevent duplicate registrations
- **Django Admin**: Added proper admin configuration for User and UserProfile models  
- **Path Consistency**: Resolved navigation path issues between frontend and admin sections
- **User Management**: Fixed action handlers for edit, delete, and status toggle operations
- **Case Creation**: Improved draft saving and language version handling

### Infrastructure Improvements
- Added requirements.txt with all project dependencies
- Created consolidated .gitignore file at project root
- Added .env.example template for environment configuration

For a complete list of changes, see [CHANGELOG.md](docs/CHANGELOG.md)

## For AI Developers
When making changes:
1. Update this README with recent changes
2. Add comments to new functions
3. Update the project map in docs/PROJECT_MAP.md
4. Create a brief entry in docs/CHANGELOG.md
