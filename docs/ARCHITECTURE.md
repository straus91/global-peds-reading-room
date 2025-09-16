# Architecture Overview

## System Architecture

The Global Peds Reading Room application employs a modern client-server architecture, integrating distinct backend and frontend components with specialized external services for DICOM image management and advanced AI-powered feedback.

```mermaid
graph TD
    A[User's Web Browser] -->|HTTPS: HTML, CSS, JS| B(Frontend Application)
    B -->|HTTPS: REST API for Application Data| C(Django Backend)
    B -->|HTTPS: Embedded OHIF Viewer| D(Orthanc DICOM Server)

    C -->|SQL Database Connection| E(PostgreSQL Database)
    C -->|HTTPS: LLM API Calls| F(Google Gemini API)
    C -->|DICOMweb/HTTP API Calls| D

    subgraph Frontend (Vanilla JavaScript, HTML, CSS)
        B
        B -- UI for Case Browsing & Viewing --> B1[Case Lists, Detail Views]
        B -- UI for Report Submission --> B2[Dynamic Report Forms]
        B -- UI for AI Feedback Display --> B3[Structured Feedback Presentation]
        B -- UI for AI Feedback Rating --> B4[Rating & Commenting Interface]
        B -- Handles User & Admin Interfaces --> B5[Login, Admin Dashboards]
        B -- Manages API Communication --> B6[js/api.js]
    end

    subgraph Backend (Django & Django REST Framework)
        C
        C -- Manages User Authentication & Authorization --> C1[User & Admin APIs]
        C -- Provides Case & Template Management APIs --> C2[Cases, Master Templates, Expert Templates]
        C -- Processes User Report Submissions --> C3[Reports API]
        C -- Orchestrates AI Feedback Generation --> C4[AI Feedback Logic]
        C -- Stores AI Feedback Ratings --> C5[AIFeedbackRating Model]
        C -- Integrates with External Services --> C6[LLM & DICOM APIs]
    end

    subgraph External Services
        D
        E
        F
    end

    style A fill:#f9f,stroke:#333,stroke-width:2px
    style B fill:#bbf,stroke:#333,stroke-width:2px
    style C fill:#ccf,stroke:#333,stroke-width:2px
    style D fill:#fcf,stroke:#333,stroke-width:2px
    style E fill:#cfc,stroke:#333,stroke-width:2px
    style F fill:#ffc,stroke:#333,stroke-width:2px
```

**Diagram Note:** The frontend application, running in the user's web browser, communicates with the Django backend for all application data and logic. The backend, in turn, interacts with a PostgreSQL database for persistent storage, the Google Gemini API for AI feedback generation, and the Orthanc DICOM server for DICOM study information. The frontend also directly embeds the Orthanc OHIF viewer via an iframe for DICOM image display.

## Technology Stack

### Backend

- **Framework:** Django 5.x with Django REST Framework (DRF) for robust API development.
- **Database:** PostgreSQL, chosen for its reliability, scalability, and rich feature set, suitable for structured application data.
- **Authentication:** JWT (JSON Web Tokens) via djangorestframework-simplejwt, providing secure, stateless authentication.
- **CORS Handling:** django-cors-headers to manage cross-origin resource sharing.
- **Environment Variables:** python-dotenv for secure management of sensitive configuration.
- **LLM Integration:** google-generativeai Python SDK for seamless interaction with the Google Gemini API, enabling advanced AI capabilities.

### Frontend

- **Core Technologies:** Vanilla JavaScript (ES6+), HTML5, and CSS3, ensuring high performance and flexibility without heavy framework dependencies.
- **API Communication:** Native Fetch API, managed centrally through js/api.js for consistent and efficient data exchange with the backend.
- **DICOM Viewing:** Embedded Orthanc OHIF Viewer, providing a powerful and interactive interface for radiology image review directly within the application.

### External Services / Key Integrations

- **Orthanc DICOM Server:** A lightweight, RESTful DICOM server used for storing, managing, and serving DICOM images, including providing the integrated OHIF viewer.
- **Google Gemini API:** A powerful large language model (LLM) that forms the core of the AI-powered feedback system, providing intelligent analysis and critique of user-submitted reports.

## Data Flow Highlights

### User Authentication:
Users register and log in via the frontend. Credentials are sent to the Django backend, which authenticates the user and issues JWT tokens. These tokens are stored client-side and sent with subsequent API requests for authorization.

### Case & Template Management (Admin):
- Administrators use the frontend admin interface to create and manage cases, master report templates, and expert-filled language-specific templates.
- Case creation includes linking to a StudyInstanceUID in Orthanc and defining expert content (key_findings, diagnosis, discussion). A unique case_identifier is auto-generated for user-facing display.
- Expert templates can have key_concepts_text defined per section, serving as specific guidance for AI feedback.

### Case Browsing & DICOM Display (User):
- Users browse available cases, identified by their case_identifier, fetched from the Django backend.
- Upon selecting a case, the frontend fetches detailed case information, including the orthanc_study_uid.
- The orthanc_study_uid is used to construct a URL for the embedded Orthanc OHIF viewer, which then directly streams DICOM images to the user's browser.

### Report Submission:
Users fill out structured reports based on the associated master template. The report content is sent as JSON to the Django backend, where it is stored, linked to the user and case.

### AI Feedback Generation (Core Workflow):
- When a user requests AI feedback for their submitted report, the frontend triggers an API call to the Django backend.
- The backend gathers comprehensive context: the user's report, the expert-filled template (including key_concepts_text), and the full case details (demographics, clinical history, expert findings, diagnosis, discussion).
- A programmatic pre-analysis is performed to identify initial discrepancies between the user's report and the expert content/key concepts.
- All this information is then sent to the Google Gemini API via a carefully constructed prompt.
- Gemini processes the input and generates a detailed critique, including identified discrepancies, assigned severity levels (Critical/Moderate), justifications, and key learning points.
- The backend parses Gemini's response into a structured JSON format and returns it to the frontend for display.

### User Feedback on AI Feedback:
Users can rate the AI-generated feedback (1-5 stars) and provide optional comments via the frontend. This feedback is sent to a dedicated API endpoint on the Django backend and stored in the database, contributing to future system improvements.

## Security Considerations

- **Authentication & Authorization:** JWTs are used for secure user sessions. Django REST Framework permissions ensure only authorized users can access specific API endpoints and perform actions (e.g., only admins can manage cases/users).
- **API Key Management:** Sensitive API keys (e.g., GEMINI_API_KEY) are stored in environment variables (.env file) and not committed to version control.
- **CORS Configuration:** django-cors-headers is configured to allow requests only from trusted frontend origins, preventing unauthorized cross-origin access.
- **DICOM Data Handling:** While Orthanc manages DICOM data, the application itself primarily stores StudyInstanceUIDs (identifiers) rather than raw DICOM files, minimizing direct exposure of sensitive image data within the application database. Anonymization of DICOM studies within Orthanc is crucial for patient privacy.
- **Input Sanitization:** All user inputs and data exchanged via APIs are handled with care to prevent common web vulnerabilities (e.g., XSS, SQL injection).
- **HTTPS:** It is critical to deploy the application with HTTPS in production to encrypt all communication between the client and server.