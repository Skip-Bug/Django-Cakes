from django.contrib import admin

from apps.custom_cake.models import CakePart, CakePartOption


class CakePartOptionInline(admin.TabularInline):
    model = CakePartOption
    extra = 0
    fields = ("name", "price", "is_active", "order")
    ordering = ("order", "name")
    show_change_link = True


@admin.register(CakePart)
class CakePartAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "is_required",
        "requires_text",
        "order",
    )
    list_editable = ("order",)
    ordering = ("order",)
    inlines = [CakePartOptionInline]
