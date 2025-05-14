# Project Map - Global Peds Reading Room

## Backend Structure

### Core Django Apps

#### cases/ (Core Application)
- **models.py**: Data models
  - `Language`: Available languages for templates
  - `MasterTemplate`: Reusable report templates
  - `Case`: Teaching case information
  - `Report`: User-submitted reports
  - `CaseTemplate`: Expert-filled templates

- **views.py**: API endpoints
  - `AdminCaseViewSet`: Admin case management
  - `UserCaseViewSet`: User-facing case viewing
  - `ReportCreateView`: Report submission

- **serializers.py**: API serialization
  - `CaseSerializer`: Case data serialization
  - `ReportSerializer`: Report handling
  - `MasterTemplateSerializer`: Template management

#### users/ (Authentication)
- **models.py**: User profile extension
- **views.py**: Authentication endpoints
- **backends.py**: Custom auth backend

### Configuration
- **globalpeds_project/settings.py**: Django settings
- **requirements.txt**: Python dependencies

## Frontend Structure

### User Interface (js/)
- **main.js**: Main user interface
  - `loadCaseList()`: Display case list
  - `viewCase()`: Show case details
  - `handleReportSubmit()`: Submit reports

- **api.js**: API communication layer
  - `apiRequest()`: HTTP request handler

- **auth.js**: Authentication logic

### Admin Interface (admin/)
- **admin.js**: Core admin functionality
- **admin-cases.js**: Case management
- **admin-templates.js**: Template management
- **admin-users.js**: User management

### Styles (css/)
- **styles.css**: Global styles
- **admin.css**: Admin panel styles
- **auth.css**: Login page styles

## API Endpoints

### Authentication
- POST `/api/users/login/`
- POST `/api/users/register/`
- GET `/api/users/me/`

### Cases
- GET `/api/cases/cases/` - List cases
- GET `/api/cases/cases/{id}/` - Case detail
- POST `/api/cases/reports/` - Submit report

### Admin
- GET/POST `/api/cases/admin/cases/`
- GET/POST `/api/cases/master-templates/`

## Key Workflows

1. **User Views Case**
   - Frontend: main.js → loadCaseList() → viewCase() (now includes iframe to Orthanc for DICOM)
   - Backend: `UserCaseViewSet` → `CaseSerializer`

2. **User Submits Report**
   - Frontend: `handleReportSubmit()` → `apiRequest()`
   - Backend: `ReportCreateView` → `ReportSerializer`

3. **Admin Creates Template**
   - Frontend: `admin-templates.js`
   - Backend: `AdminMasterTemplateViewSet`
