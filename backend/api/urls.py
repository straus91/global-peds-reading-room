# api/urls.py
from django.urls import path, include # Ensure include is imported
from rest_framework.routers import DefaultRouter # Import the router
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    UserRegisterView,
    CustomTokenObtainPairView,
    LogoutView,
    CurrentUserView,
    AdminUserViewSet # Import the new ViewSet
)

# --- Router Setup ---
router = DefaultRouter()
router.register(r'admin/users', AdminUserViewSet, basename='admin-user')
# Register other viewsets here later (e.g., for cases)

# --- URL Patterns ---
urlpatterns = [
    # --- Authentication Endpoints ---
    path('auth/register/', UserRegisterView.as_view(), name='register'),
    path('auth/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/login/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('cases/', include('cases.urls')),

    # --- User Profile Endpoint ---
    path('users/me/', CurrentUserView.as_view(), name='current_user'),

    # --- Include Router URLs ---
    # This adds /api/admin/users/, /api/admin/users/{pk}/, etc.
    path('', include(router.urls)),

    # --- Case & Report Endpoints (To be added in Phase 2) ---

    # REMOVED: path('admin/', admin.site.urls), # This line does NOT belong here
]
