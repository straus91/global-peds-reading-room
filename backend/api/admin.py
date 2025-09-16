# backend/api/admin.py
from django.contrib import admin
from django.contrib.auth.models import User

# API app doesn't have models, so this file can remain minimal
# If you add models to the API app later, register them here