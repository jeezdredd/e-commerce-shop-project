from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from common.admin import SoftDeleteAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(SoftDeleteAdmin, UserAdmin):
    list_display = ("username", "email", "phone", "full_name", "is_staff", "is_deleted")
    list_filter = ("is_staff", "is_superuser", "is_active", "is_deleted", "groups")
    search_fields = ("username", "email", "phone", "full_name")
    fieldsets = UserAdmin.fieldsets + (
        ("Profile", {"fields": ("full_name", "phone", "avatar")}),
    )
