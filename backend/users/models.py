# users/models.py
from django.db import models
from django.contrib.auth.models import User # Import Django's built-in User model

# Define choices for role and status fields for consistency
class RoleChoices(models.TextChoices):
    STUDENT = 'student', 'Student'
    RESIDENT = 'resident', 'Resident'
    FELLOW = 'fellow', 'Fellow'
    ATTENDING = 'attending', 'Attending'
    ADMIN = 'admin', 'Administrator'
    OTHER = 'other', 'Other'

class StatusChoices(models.TextChoices):
    PENDING = 'pending', 'Pending Approval'
    ACTIVE = 'active', 'Active'
    INACTIVE = 'inactive', 'Inactive'

class UserProfile(models.Model):
    """
    Stores additional information related to the built-in Django User model.
    """
    # Link to the built-in User model.
    # OneToOneField ensures each User has exactly one UserProfile.
    # on_delete=models.CASCADE means if a User is deleted, their profile is also deleted.
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')

    # Custom fields based on requirements
    role = models.CharField(
        max_length=20,
        choices=RoleChoices.choices,
        default=RoleChoices.OTHER, # Sensible default
        help_text="User's role in the institution"
    )
    institution = models.CharField(
        max_length=255,
        blank=True, # Allow blank for now, maybe make required later
        help_text="User's institution or hospital affiliation"
    )
    country = models.CharField(
        max_length=100,
        blank=True, # Allow blank
        help_text="User's country"
    )
    approval_status = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.PENDING, # New users start as pending
        help_text="Approval status of the user account"
    )

    # Timestamps (optional but good practice)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        """
        String representation of the UserProfile object, useful in Django admin.
        """
        return f"{self.user.username}'s Profile ({self.get_role_display()})"

    # Optional: Property to easily check if user is admin based on profile role
    @property
    def is_admin_role(self):
        return self.role == RoleChoices.ADMIN

    # Optional: Property to check if user account is fully active
    @property
    def is_approved_and_active(self):
        return self.approval_status == StatusChoices.ACTIVE and self.user.is_active

