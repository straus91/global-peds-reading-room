# Migration Instructions

We've added a new field to the Report model and modified the model's uniqueness constraints. Before deploying these changes, you'll need to create and apply migrations:

```bash
# Navigate to the backend directory
cd backend

# Activate your virtual environment
# On Windows PowerShell:
.\venv\Scripts\Activate.ps1
# On Windows cmd:
venv\Scripts\activate.bat
# On macOS/Linux:
source venv/bin/activate

# Create the migration
python manage.py makemigrations cases

# Apply the migration
python manage.py migrate
```

## Changes Made

1. Added `is_archived` boolean field to the Report model to track archived/previous reports
2. Removed the unique constraint on (case, user) in the Report model to allow multiple reports per user/case
3. Added a new 'reset' endpoint to UserCaseViewSet to allow users to reset a case and submit a new report
4. Updated the frontend to provide both "Reset Case" and "Get AI Feedback" buttons

## About the Reset Feature

The reset feature allows users to submit a new report for a case they've already completed. When a case is reset:

1. The user's existing report is archived (not deleted)
2. The user's view status for the case is cleared
3. The case appears as not-yet-reported in the case list
4. The user can submit a new report for the case

This is ideal for:
- Practicing on the same case multiple times
- Correcting mistakes in a previous submission
- Testing different approaches to the same case

The previous report is preserved for reference and could be viewed in a "History" section in the future.