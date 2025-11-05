
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_user_model
from .models import SessionLog, User, Signin, Course



User = get_user_model()

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("email", "full_name", "phone_number", "is_staff", "is_active")
    list_filter = ("is_staff", "is_superuser", "is_active")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal Info", {"fields": ("full_name", "phone_number")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "full_name", "phone_number", "password1", "password2", "is_staff", "is_active"),
        }),
    )

    search_fields = ("email", "full_name", "phone_number")
    ordering = ("email",)

# Signin
@admin.register(Signin)
class SigninAdmin(admin.ModelAdmin):
    list_display = ("email",)
    search_fields = ("email",) 
# SessionLog 
@admin.register(SessionLog)
class SessionLogAdmin(admin.ModelAdmin):
    list_display = ("user", "ip_address", "user_agent", "login_time", "logout_time")
    list_filter = ("login_time", "logout_time")
    search_fields = ("user__email", "ip_address", "user_agent")


