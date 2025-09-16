# backend/users/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile, RoleChoices, StatusChoices

# Inline for UserProfile to show it in User admin
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fields = ('role', 'institution', 'country', 'approval_status')

# Extend the User admin to include UserProfile
class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_active', 'get_approval_status', 'get_role')
    list_filter = BaseUserAdmin.list_filter + ('profile__approval_status', 'profile__role')
    search_fields = BaseUserAdmin.search_fields + ('profile__institution', 'profile__country')
    
    def get_approval_status(self, obj):
        return obj.profile.get_approval_status_display() if hasattr(obj, 'profile') else '-'
    get_approval_status.short_description = 'Approval Status'
    get_approval_status.admin_order_field = 'profile__approval_status'
    
    def get_role(self, obj):
        return obj.profile.get_role_display() if hasattr(obj, 'profile') else '-'
    get_role.short_description = 'Role'
    get_role.admin_order_field = 'profile__role'

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

# Standalone UserProfile admin for direct access
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'institution', 'country', 'approval_status', 'created_at')
    list_filter = ('role', 'approval_status', 'country')
    search_fields = ('user__username', 'user__email', 'institution', 'country')
    readonly_fields = ('created_at', 'updated_at')
    
    actions = ['approve_users', 'reject_users']
    
    def approve_users(self, request, queryset):
        count = queryset.filter(approval_status=StatusChoices.PENDING).update(
            approval_status=StatusChoices.ACTIVE
        )
        # Also activate the associated users
        for profile in queryset.filter(approval_status=StatusChoices.ACTIVE):
            profile.user.is_active = True
            profile.user.save()
        self.message_user(request, f'{count} users approved.')
    approve_users.short_description = "Approve selected users"
    
    def reject_users(self, request, queryset):
        count = queryset.update(approval_status=StatusChoices.INACTIVE)
        # Also deactivate the associated users
        for profile in queryset:
            profile.user.is_active = False
            profile.user.save()
        self.message_user(request, f'{count} users rejected.')
    reject_users.short_description = "Reject selected users"