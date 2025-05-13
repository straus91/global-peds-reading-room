# Development Guide

## Setting Up Development Environment

### Backend Setup
1. Create virtual environment
2. Install dependencies: `pip install -r requirements.txt`
3. Configure database in settings.py
4. Run migrations: `python manage.py migrate`
5. Create superuser: `python manage.py createsuperuser`

### Frontend Setup
1. No build process required
2. Serve files locally or open directly in browser
3. Update `API_CONFIG.BASE_URL` in js/api.js if needed

## Code Style Guidelines

### Python (Backend)
- Follow PEP 8
- Use meaningful variable names
- Add docstrings to functions
- Keep views focused and simple

### JavaScript (Frontend)
- Use const/let instead of var
- Async/await for API calls
- Meaningful function names
- Comment complex logic

## Making Changes

### Before Starting
1. Pull latest changes
2. Create feature branch
3. Update from main regularly

### After Changes
1. Test thoroughly
2. Update documentation
3. Add comments to code
4. Update PROJECT_MAP.md
5. Create changelog entry

## Common Tasks

### Adding a New API Endpoint
1. Create view in views.py
2. Add serializer if needed
3. Register URL in urls.py
4. Update frontend API calls
5. Document in PROJECT_MAP.md

### Adding Frontend Feature
1. Create/modify JS file
2. Update HTML if needed
3. Add styles to CSS
4. Test across browsers
5. Update documentation
