# AI Assistant Guide

## Quick Context

This is the Global Peds Reading Room - a medical education platform for pediatric radiology.

## Key Files to Know

### Backend (Django)
- `cases/models.py` - Core data models
- `cases/views.py` - API endpoints
- `cases/serializers.py` - Data serialization

### Frontend (Vanilla JS)
- `js/main.js` - User interface logic
- `js/api.js` - API communication
- `js/admin.js` - Admin panel

## Common Tasks

### Adding a Feature
1. Check PROJECT_MAP.md for structure
2. Implement backend first (if needed)
3. Update frontend to use new backend
4. Test thoroughly
5. Update documentation

### Fixing a Bug
1. Identify affected files
2. Check git history if needed
3. Fix issue
4. Test related functionality
5. Update CHANGELOG.md

## Important Patterns

- JWT auth tokens in localStorage
- API calls use `apiRequest()` function
- Admin pages check authentication first
- Reports use structured content (JSON)

## Recent Issues Fixed
- Patient Age saving
- Modality abbreviations
- Dynamic report sections
