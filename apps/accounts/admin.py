from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import PhoneOTP, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    readonly_fields = ("last_login",)
    ordering = ("phone",)
    list_display = ("phone", "name", "email", "address", "is_staff", "is_active")
    search_fields = ("phone", "name", "email", "address")

    fieldsets = (
        (None, {"fields": ("phone", "password")}),
        ("Личные данные", {"fields": ("name", "email", "address")}),
        (
            "Права",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Даты", {"fields": ("last_login",)}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("phone", "password1", "password2"),
            },
        ),
    )


@admin.register(PhoneOTP)
class PhoneOTPAdmin(admin.ModelAdmin):
    list_display = ("phone", "code", "created_at", "expires_at", "is_used", "attempts")
    list_filter = ("is_used",)
    search_fields = ("phone",)
    readonly_fields = ("created_at",)
