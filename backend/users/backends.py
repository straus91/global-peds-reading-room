# users/backends.py (WITH DEBUG PRINT STATEMENTS)
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.core.exceptions import MultipleObjectsReturned

UserModel = get_user_model()

class EmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        email = username # Email comes in as 'username' arg
        print(f"--- [DEBUG] EmailBackend attempting authentication for email: {email} ---")

        if email is None:
            print("--- [DEBUG] EmailBackend received email=None ---")
            return None

        try:
            # Use case-insensitive lookup for email
            user = UserModel.objects.get(email__iexact=email)
            print(f"--- [DEBUG] EmailBackend found user: {user.username} (ID: {user.id}) ---")
        except UserModel.DoesNotExist:
            print(f"--- [DEBUG] EmailBackend User.DoesNotExist for email: {email} ---")
            # Run the default password hasher once to reduce timing attacks
            UserModel().set_password(password)
            return None
        except MultipleObjectsReturned:
            print(f"--- [DEBUG] EmailBackend MultipleObjectsReturned for email: {email} ---")
            return None
        else:
            password_check_result = user.check_password(password)
            print(f"--- [DEBUG] EmailBackend check_password result: {password_check_result} ---")
            # self.user_can_authenticate checks is_active
            can_authenticate_result = self.user_can_authenticate(user)
            print(f"--- [DEBUG] EmailBackend user_can_authenticate (is_active) result: {can_authenticate_result} ---")

            if password_check_result and can_authenticate_result:
                print(f"--- [DEBUG] EmailBackend authentication SUCCESSFUL for user: {user.username} ---")
                return user
            else:
                print(f"--- [DEBUG] EmailBackend authentication FAILED for user: {user.username} (password check: {password_check_result}, active check: {can_authenticate_result}) ---")
                # Return None here explicitly if checks fail
                return None

        # This line should ideally not be reached if logic above is correct
        print(f"--- [DEBUG] EmailBackend returning None unexpectedly at the end for email: {email} ---")
        return None

    # Optional but recommended: Handle retrieving user by ID
    def get_user(self, user_id):
        print(f"--- [DEBUG] EmailBackend get_user called for ID: {user_id} ---")
        try:
            user = UserModel.objects.get(pk=user_id)
            print(f"--- [DEBUG] EmailBackend get_user found user: {user.username} ---")
            return user
        except UserModel.DoesNotExist:
            print(f"--- [DEBUG] EmailBackend get_user User.DoesNotExist for ID: {user_id} ---")
            return None