# api/views.py
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404 # For custom actions
from rest_framework import generics, permissions, status, viewsets, filters # Added viewsets, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import action # For custom actions like approve
from rest_framework_simplejwt.views import TokenObtainPairView # Keep existing imports

# Import filters backend
from django_filters.rest_framework import DjangoFilterBackend

# Import serializers and models from the users app
from users.serializers import UserRegistrationSerializer, UserSerializer, CustomTokenObtainPairSerializer 
from users.models import UserProfile, StatusChoices, RoleChoices # Import UserProfile and Choices

# --- Authentication Views ---

class UserRegisterView(generics.CreateAPIView):
    """
    API endpoint for user registration.
    Uses the UserRegistrationSerializer to handle creation.
    Allows any user (even unauthenticated) to access it.
    """
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,) # Anyone can register
    serializer_class = UserRegistrationSerializer

    # --- MODIFIED create method ---
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # The serializer's create method now handles User and UserProfile creation
        user = serializer.save()
        # Instead of returning serializer.data (which causes the error),
        # return a simple success message.
        return Response(
            {"message": "User registered successfully. Awaiting admin approval."},
            status=status.HTTP_201_CREATED
            # No headers needed for this simple response
        )
    # --- End MODIFIED create method ---

# Use Simple JWT's built-in view for obtaining token pairs (login)
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer 
    # You can customize the serializer here if needed:
    # serializer_class = YourCustomTokenObtainPairSerializer
    pass

# Simple JWT's refresh view is usually sufficient as is
# class CustomTokenRefreshView(TokenRefreshView):
#     pass

class LogoutView(APIView):
    """
    Placeholder for logout logic. Frontend should discard tokens.
    If using simplejwt blacklist app, implement token blacklisting here.
    """
    permission_classes = (permissions.IsAuthenticated,) # Must be logged in to log out

    def post(self, request):
        # Simple confirmation assuming frontend handles token removal
        return Response({"message": "Logout successful. Please discard your tokens."}, status=status.HTTP_200_OK)


# --- User Profile View ---

class CurrentUserView(generics.RetrieveAPIView):
    """
    API endpoint to retrieve the details of the currently authenticated user.
    """
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticated,) # Must be logged in

    def get_object(self):
        """
        Override get_object to return the currently authenticated user (request.user).
        The serializer will handle fetching the related profile.
        """
        return self.request.user

# --- Admin User Management ViewSet ---

class AdminUserViewSet(viewsets.ModelViewSet):  # Changed from ReadOnlyModelViewSet
    """
    API endpoint for admins to manage users.
    Provides full CRUD operations.
    """
    queryset = User.objects.select_related('profile').all().order_by('id')
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]

    # Configure filtering
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        'profile__approval_status': ['exact'],
        'profile__role': ['exact'],
        'is_active': ['exact'],
    }
    search_fields = ['username', 'email', 'first_name', 'last_name', 'profile__institution', 'profile__country']
    ordering_fields = ['id', 'email', 'first_name', 'last_name', 'date_joined', 'profile__role', 'profile__approval_status']
    ordering = ['id']

    def destroy(self, request, *args, **kwargs):
        """Override destroy to add custom logic if needed"""
        user = self.get_object()
        user_id = user.id
        self.perform_destroy(user)
        return Response({'detail': f'User {user_id} deleted successfully.'}, status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['patch'], permission_classes=[permissions.IsAdminUser], url_path='approve')
    def approve_user(self, request, pk=None):
        """Custom action to approve a pending user."""
        user = self.get_object()
        profile = getattr(user, 'profile', None)

        if not profile:
             return Response({'detail': 'User profile not found.'}, status=status.HTTP_404_NOT_FOUND)

        if profile.approval_status != StatusChoices.PENDING:
            return Response({'detail': f'User status is already {profile.get_approval_status_display()}. Cannot approve.'}, status=status.HTTP_400_BAD_REQUEST)

        # Update status and activate user
        profile.approval_status = StatusChoices.ACTIVE
        user.is_active = True
        profile.save()
        user.save()

        # Return updated user data
        serializer = self.get_serializer(user)
        return Response(serializer.data)

    @action(detail=True, methods=['patch'], permission_classes=[permissions.IsAdminUser], url_path='set-status')
    def set_user_status(self, request, pk=None):
        """Custom action to set user profile status and sync User.is_active."""
        user = self.get_object()
        profile = getattr(user, 'profile', None)
        new_status = request.data.get('status')

        if not profile:
            return Response({'detail': 'User profile not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Validate the provided status
        valid_statuses = [StatusChoices.ACTIVE, StatusChoices.INACTIVE]
        if new_status not in valid_statuses:
            return Response({'detail': f'Invalid status provided. Use "{StatusChoices.ACTIVE}" or "{StatusChoices.INACTIVE}".'}, status=status.HTTP_400_BAD_REQUEST)

        # Update status and sync is_active flag
        profile.approval_status = new_status
        user.is_active = (new_status == StatusChoices.ACTIVE)
        profile.save()
        user.save()

        serializer = self.get_serializer(user)
        return Response(serializer.data)