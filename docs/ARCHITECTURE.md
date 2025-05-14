# Architecture Overview

## System Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Frontend      │───▶│   Backend       │     │     Orthanc     │
│  (Vanilla JS)   │     │  (Django DRF)   │◀────│ (DICOM Server & │
└─────────────────┘     └─────────────────┘     │  OHIF Viewer)   │
                              │                 └─────────────────┘
                              ▼
                       ┌─────────────────┐
                       │   PostgreSQL    │
                       └─────────────────┘
```

## Technology Stack

### Backend
- Django 4.x with Django REST Framework
- PostgreSQL database
- JWT authentication (Simple JWT)
- django-cors-headers for CORS

### Frontend
- Vanilla JavaScript (ES6+)
- Native Fetch API for HTTP requests
- CSS3 for styling
- No build process required

## Data Flow

1. User authentication via JWT tokens
2. API requests include auth token in headers
3. Backend validates and processes requests
4. JSON responses sent to frontend
5. Frontend updates UI dynamically

## Security

- JWT tokens stored in localStorage
- CORS configured for frontend origin
- User roles: Admin, Medical Professional
- Protected endpoints require authentication
