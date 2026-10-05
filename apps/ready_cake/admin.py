from django.contrib import admin

from .models import Cake


@admin.register(Cake)
class CakeAdmin(admin.ModelAdmin):
    list_display = ("title", "price", "weight", "is_active")
    list_filter = ("is_active",)
    search_fields = ("title", "description")
    list_editable = ("is_active",)
