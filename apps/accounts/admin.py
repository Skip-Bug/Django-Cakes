from django.contrib import admin

from .models import PhoneOTP


@admin.register(PhoneOTP)
class PhoneOTPAdmin(admin.ModelAdmin):
    list_display = ("phone", "code", "created_at", "expires_at", "is_used", "attempts")
    list_filter = ("is_used",)
    search_fields = ("phone",)
    readonly_fields = ("created_at",)
