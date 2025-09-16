# Development Guide

This guide provides comprehensive instructions for setting up your development environment, understanding code style, contributing to the project, and performing common development tasks for the Global Peds Reading Room application.

## 1. Setting Up Your Development Environment

To start developing, you'll need to set up both the backend (Django) and frontend (Vanilla JS) components.

### 1.1 Backend Setup (backend/ directory)

The backend is built with Python and Django.

1. **Navigate to the Backend Directory**:
   ```
   cd backend
   ```

2. **Create a Python Virtual Environment**: It's highly recommended to use a virtual environment to manage project dependencies.
   ```
   python -m venv venv
   ```

3. **Activate the Virtual Environment**:
   - Windows PowerShell:
     ```
     .\venv\Scripts\Activate.ps1
     ```
   - Windows Command Prompt:
     ```
     venv\Scripts\activate.bat
     ```
   - macOS/Linux:
     ```
     source venv/bin/activate
     ```
   (You'll know it's active when `(venv)` appears at the start of your terminal prompt.)

4. **Install Dependencies**: Install all required Python packages.
   ```
   pip install -r requirements.txt
   ```

5. **Configure Environment Variables**:
   - Create a `.env` file in the backend/ directory if it doesn't exist (you can use backend/.env.example as a template).
   - Populate it with your SECRET_KEY, PostgreSQL database credentials, and your GEMINI_API_KEY.
   - Important: Ensure DEBUG="True" for development.

6. **Run Database Migrations**: Apply all database schema changes.
   ```
   python manage.py migrate
   ```

7. **Create a Superuser** (Admin Account): This account will allow you to access the Django admin panel.
   ```
   python manage.py createsuperuser
   ```

8. **Run the Django Development Server**:
   ```
   python manage.py runserver
   ```
   The backend API will typically be accessible at http://127.0.0.1:8000/.

### 1.2 Frontend Setup (frontend/ directory)

The frontend is a static web application built with Vanilla JavaScript, HTML, and CSS.

1. **Navigate to the Frontend Directory**:
   ```
   cd frontend
   ```

2. **Configure API Base URL**: Open `frontend/js/api.js` and ensure that `API_CONFIG.BASE_URL` is set to your backend's API URL (e.g., 'http://127.0.0.1:8000/api').

3. **Configure Orthanc Viewer URL**: If you're using a local Orthanc DICOM server, open `frontend/js/main.js`. Locate the `setupDicomViewer` function and verify `orthancOhifViewerBaseUrl` points to your Orthanc OHIF viewer (default http://localhost:8042/ohif/viewer).

4. **Serve the Frontend Files**: You can use Python's built-in HTTP server for local development:
   ```
   python -m http.server 5500
   ```
   This will serve the frontend files at http://127.0.0.1:5500/. Open http://127.0.0.1:5500/login.html in your web browser to start the application.

## 2. Code Style Guidelines

Maintaining consistent code style is crucial for collaboration and readability.

### 2.1 Python (Backend)

- **PEP 8 Compliance**: Adhere to the PEP 8 style guide for Python code. Use linters like flake8 or pylint.
- **Meaningful Naming**: Use descriptive variable, function, and class names (e.g., `calculate_average_score` instead of `calc_avg`).
- **Docstrings**: All functions, methods, and classes should have clear docstrings explaining their purpose, arguments, and return values.
- **Django Best Practices**:
  - Keep Django views (especially APIView and ViewSet methods) focused on handling HTTP requests and responses, delegating complex business logic to services or utility functions.
  - Use Django's ORM effectively for database interactions.
  - Write clear and concise serializers.
  - Use transactions for operations that modify multiple database records.

### 2.2 JavaScript (Frontend)

- **Modern JavaScript**: Use `const` and `let` instead of `var`. Prefer arrow functions.
- **Asynchronous Operations**: Use async/await for all API calls and other asynchronous operations to ensure readability and proper error handling.
- **Meaningful Naming**: Use camelCase for variable and function names (e.g., `loadCaseList`, `handleReportSubmit`).
- **Modularity**: Organize JavaScript into logical files (e.g., `api.js` for API calls, `main.js` for core app logic, `admin-*.js` for admin-specific features).
- **Comments**: Add comments for complex logic, non-obvious solutions, or any areas that might be confusing.
- **DOM Manipulation**: Minimize direct DOM manipulation; prefer generating HTML strings or using template literals for larger UI components.

### 2.3 CSS

- **BEM Methodology** (Optional but Recommended): Consider using BEM (Block, Element, Modifier) for class naming to create modular and scalable CSS.
- **Variables**: Utilize CSS custom properties (`--primary`, `--dark`, etc.) for colors, fonts, and spacing to maintain consistency and ease of theming.
- **Responsiveness**: Design with a mobile-first approach. Use media queries (`@media`) to adapt layouts for different screen sizes.
- **Readability**: Organize CSS rules logically (e.g., by component, by page, or alphabetically within a block).

## 3. Making Changes and Contributing

Follow these steps when making modifications or adding new features to the project.

### 3.1 Before You Start Coding

1. **Pull Latest Changes**: Always start by pulling the latest changes from the main branch to ensure your local repository is up-to-date.
   ```
   git pull origin main
   ```

2. **Create a Feature Branch**: Create a new branch for your work. Use descriptive names (e.g., `feature/ai-feedback-ratings`, `fix/login-redirect`).
   ```
   git checkout -b feature/your-feature-name
   ```

3. **Keep Your Branch Updated**: Regularly rebase or merge main into your feature branch to avoid large merge conflicts later.
   ```
   git fetch origin
   git rebase origin/main # or git merge origin/main
   ```

### 3.2 After Implementing Your Changes

1. **Test Thoroughly**:
   - **Backend**: Run Django unit tests (`python manage.py test`). Manually test API endpoints using tools like Postman or by interacting with the frontend.
   - **Frontend**: Test your changes across different browsers and screen sizes (desktop, tablet, mobile).

2. **Update Documentation**:
   - **Code Comments**: Add or update comments within the code to explain new or modified logic.
   - **PROJECT_MAP.md**: Update the relevant sections in PROJECT_MAP.md to reflect any new files, models, views, serializers, or API endpoints you've added or significantly modified.
   - **AI_GUIDE.md**: If your changes relate to the AI feedback system, update AI_GUIDE.md with details on new features, prompt changes, or workflow modifications.
   - **SECURITY.md**: If your changes impact security features, input validation, or error handling, update SECURITY.md accordingly.
   - **Other Docs**: If your changes impact architecture, deployment, or general development practices, update ARCHITECTURE.md or DEPLOYMENT.md accordingly.

3. **Create a Changelog Entry**: Add a new entry to CHANGELOG.md under the [Unreleased] section. Describe your changes clearly using the "Added", "Changed", "Fixed" categories. Be concise but informative.

## 4. Common Development Tasks

This section outlines common tasks you might perform during development.

### 4.1 Adding a New API Endpoint (Backend)

1. **Define Model** (if new data): If your endpoint involves new data, define or update models in `cases/models.py` or `users/models.py`. Run `python manage.py makemigrations` and `python manage.py migrate`.

2. **Create/Update Serializer**: Define how your data will be serialized/deserialized in `cases/serializers.py` or `users/serializers.py`.

3. **Create View**: Implement the logic for your API endpoint in a views.py file (e.g., `cases/views.py`, `api/views.py`). Use Django REST Framework's APIView, generics, or viewsets as appropriate.

4. **Register URL**: Add a URL pattern in the relevant urls.py file (e.g., `cases/urls.py`, `api/urls.py`) to map your view to an accessible endpoint.

5. **Update Frontend API Calls**: Modify `frontend/js/api.js` or other frontend JavaScript files to make requests to your new endpoint and handle its responses.

6. **Document**: Update PROJECT_MAP.md with details of the new endpoint, its purpose, and expected payload/response.

### 4.2 Adding a New Frontend Feature

1. **Identify/Create HTML Structure**: Modify existing HTML files (e.g., `index.html`, `admin/*.html`) or create new ones to support the feature's UI.

2. **Create/Modify JavaScript Logic**: Implement the interactive logic in a new or existing .js file (e.g., `main.js`, `admin-case-edit.js`). Break down complex logic into smaller, reusable functions.

3. **Apply Styles**: Add or update CSS rules in the appropriate stylesheet (`styles.css`, `admin.css`, `auth.css`) to ensure the feature looks good and is responsive.

4. **Test Across Browsers**: Verify the feature's functionality and appearance across different web browsers (Chrome, Firefox, Safari, Edge) and device types.

5. **Document**: Update PROJECT_MAP.md to describe the new frontend components and their associated files.

## 5. Security Best Practices

Always follow these security best practices when developing:

1. **Input Validation**: Sanitize and validate all user inputs, both on the frontend and backend.

2. **Transactional Safety**: Use `@transaction.atomic` for operations that modify multiple database records.

3. **Error Handling**: Implement comprehensive error handling with appropriate user-friendly messages.

4. **Rate Limiting**: Apply rate limiting to prevent abuse of external APIs and internal resources.

5. **Logging**: Use Python's logging module instead of print statements for better error tracking.

6. **API Security**: Follow the principles in SECURITY.md for all API endpoints and LLM interactions.

7. **Secure Coding**: Avoid common security pitfalls like SQL injection, XSS, CSRF, etc.

For more details on security practices, refer to the SECURITY.md document.