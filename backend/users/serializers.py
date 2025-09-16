# users/serializers.py

from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import authenticate # <<< *** ENSURE THIS IMPORT IS PRESENT ***
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import UserProfile, RoleChoices, StatusChoices # Import your UserProfile model and choices

class UserProfileSerializer(serializers.ModelSerializer):
    role = serializers.CharField(source='get_role_display', read_only=True)
    # FIX: Remove source='get_approval_status_display' to send the raw value
    approval_status = serializers.CharField(read_only=True) # Or simply serializers.CharField() if you might write to it elsewhere

    class Meta:
        model = UserProfile
        fields = ['role', 'institution', 'country', 'approval_status']

class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for the built-in User model, including the nested profile.
    Used for displaying user information (e.g., in /users/me/ endpoint).
    """
    # Nest the profile serializer for reading profile details alongside user details
    profile = UserProfileSerializer(read_only=True)
    # Include the calculated 'is_admin' property from the profile model
    is_admin = serializers.BooleanField(source='profile.is_admin_role', read_only=True)

    class Meta:
        model = User
        # Fields included when reading user data
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_active', 'profile', 'is_admin']
        # Make certain fields read-only as they shouldn't be directly updated via this serializer
        read_only_fields = ['is_active', 'id', 'is_admin', 'username', 'profile']

class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer specifically for handling new user registration via the API.
    Validates input and creates both the User and UserProfile records.
    """
    # Define fields required for registration, including profile fields
    role = serializers.ChoiceField(choices=RoleChoices.choices, write_only=True) # Write-only for creation
    institution = serializers.CharField(max_length=255, required=False, allow_blank=True, write_only=True)
    country = serializers.CharField(max_length=100, required=False, allow_blank=True, write_only=True)
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True, label="Confirm password")
    email = serializers.EmailField(required=True)
    first_name = serializers.CharField(required=True, max_length=150)
    last_name = serializers.CharField(required=True, max_length=150)

    class Meta:
        model = User # Based on the User model for core fields
        # Fields expected in the registration request payload
        fields = ('email', 'first_name', 'last_name', 'password', 'password2',
                  'role', 'institution', 'country')

    def validate(self, attrs):
        """
        Custom validation to check if passwords match and if email is unique.
        """
        # Check if the two password fields match
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})

        # Check if a user with the given email already exists (as username or email)
        # Use case-insensitive check for email
        if User.objects.filter(email__iexact=attrs['email']).exists() or \
           User.objects.filter(username__iexact=attrs['email']).exists():
             raise serializers.ValidationError({"email": "A user with this email already exists."})

        return attrs # Return validated attributes

    def create(self, validated_data):
        """
        Handles the creation of the new User and associated UserProfile.
        """
        # Separate profile data from user data
        profile_data = {
            'role': validated_data.pop('role'),
            'institution': validated_data.pop('institution', ''), # Use default if not provided
            'country': validated_data.pop('country', '')       # Use default if not provided
        }
        # Remove the confirmation password as it's not stored
        validated_data.pop('password2')
        # Use the email address as the username for the User model
        username = validated_data['email']

        # Create the User instance using create_user to handle password hashing
        user = User.objects.create_user(
            username=username,
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            is_active=False # New users are inactive until approved
        )

        # Create the associated UserProfile instance
        UserProfile.objects.create(
            user=user,
            role=profile_data['role'],
            institution=profile_data['institution'],
            country=profile_data['country'],
            approval_status=StatusChoices.PENDING # New users start as pending
        )

        return user # Return the created User instance

# --- Custom Token Serializer (Login) ---
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Customizes the JWT token claim generation to include user role,
    and uses email as the username field for login.
    Calls authenticate directly for clarity.
    """
    username_field = User.EMAIL_FIELD # Use email field for login

    @classmethod
    def get_token(cls, user):
        """
        Generates the token and adds custom claims.
        """
        # Generate the standard token
        token = super().get_token(user)

        # Add custom claims (role, admin status) from the user's profile
        try:
            profile = user.profile # Assumes related_name='profile' on UserProfile.user
            token['role'] = profile.role
            token['is_admin'] = profile.is_admin_role
        except UserProfile.DoesNotExist:
            # Handle cases where profile might not exist (shouldn't happen with current setup)
            token['role'] = None
            token['is_admin'] = False

        # Add other user details to the token payload if needed
        token['email'] = user.email
        token['name'] = f"{user.first_name} {user.last_name}".strip()

        return token

    def validate(self, attrs):
        """
        Validates the login credentials by calling authenticate directly
        using the configured EmailBackend.
        """
        # Get email and password from incoming attributes using the defined username_field
        email = attrs.get(self.username_field)
        password = attrs.get('password')

        # --- Optional: Remove or comment out debug prints for production ---
        print(f"--- [DEBUG] CustomSerializer validate received email: {email}, password: {'******' if password else None} ---")

        user = None
        if email and password:
            # Explicitly call authenticate. Pass the email into the 'username' parameter,
            # as this is what our EmailBackend expects.
            # Pass the request context which might be needed by some backends.
            user = authenticate(request=self.context.get('request'), username=email, password=password)
            # --- Optional: Remove or comment out debug prints for production ---
            print(f"--- [DEBUG] CustomSerializer authenticate call result: {'User object returned' if user else 'None returned'} ---")
        else:
            # --- Optional: Remove or comment out debug prints for production ---
            print(f"--- [DEBUG] CustomSerializer missing email or password in attrs ---")
            # Raise validation error if email or password are missing
            raise serializers.ValidationError('Must include "email" and "password".', code='authorization')

        # Check if authenticate was successful (returned a user object)
        # Note: Our EmailBackend's user_can_authenticate method already checks if user.is_active
        if not user:
            # --- Optional: Remove or comment out debug prints for production ---
            print(f"--- [DEBUG] CustomSerializer raising validation error: No active account found... ---")
            # Raise the specific error message expected by the frontend on login failure
            raise serializers.ValidationError('No active account found with the given credentials', code='authorization')

        # If authenticate succeeded, set self.user for get_token
        # --- Optional: Remove or comment out debug prints for production ---
        print(f"--- [DEBUG] CustomSerializer authentication successful for user: {user.username} ---")
        self.user = user

        # Generate refresh token (which includes custom claims via get_token)
        refresh = self.get_token(self.user)

        # Prepare response data dictionary including tokens and custom claims
        data = {}
        data['refresh'] = str(refresh)
        data['access'] = str(refresh.access_token) # Generate access token from refresh token
        # Add custom claims directly to the response payload for frontend convenience
        data['role'] = refresh.get('role')
        data['is_admin'] = refresh.get('is_admin')
        data['name'] = refresh.get('name')
        data['email'] = refresh.get('email')

        # --- Optional: Remove or comment out debug prints for production ---
        print(f"--- [DEBUG] CustomSerializer returning data keys: {list(data.keys())} ---")
        return data
