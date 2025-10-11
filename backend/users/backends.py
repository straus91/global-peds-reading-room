# users/backends.py
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.core.exceptions import MultipleObjectsReturned

UserModel = get_user_model()

class EmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        email = username # Email comes in as 'username' arg

        if email is None:
            return None

        try:
            # Use case-insensitive lookup for email
            user = UserModel.objects.get(email__iexact=email)
        except UserModel.DoesNotExist:
            # Run the default password hasher once to reduce timing attacks
            UserModel().set_password(password)
            return None
        except MultipleObjectsReturned:
            return None
        else:
            password_check_result = user.check_password(password)
            # self.user_can_authenticate checks is_active
            can_authenticate_result = self.user_can_authenticate(user)

            if password_check_result and can_authenticate_result:
                return user
            else:
                # Return None here explicitly if checks fail
                return None

        # This line should ideally not be reached if logic above is correct
        return None

    # Optional but recommended: Handle retrieving user by ID
    def get_user(self, user_id):
        try:
            user = UserModel.objects.get(pk=user_id)
            return user
        except UserModel.DoesNotExist:
            return None