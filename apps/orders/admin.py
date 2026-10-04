from django.contrib import admin

from apps.orders.models import Order, OrderEvent, PromoCode


class OrderEventInline(admin.TabularInline):
    model = OrderEvent
    extra = 0
    can_delete = False
    show_change_link = True
    fields = (
        "created_at",
        "event_type",
        "from_status",
        "to_status",
        "message",
        "author",
    )
    readonly_fields = fields
    ordering = ("-created_at",)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "number",
        "contact_name",
        "contact_phone",
        "address_display",
        "status",
        "payment_status",
        "total",
        "delivery_date",
        "delivery_time",
        "is_urgent",
    )
    list_filter = (
        "status",
        "payment_status",
        "payment_method",
        "is_urgent",
        "delivery_date",
    )
    search_fields = (
        "number",
        "guest_phone",
        "guest_email",
        "guest_name",
        "promo_code",
        "inscription",
    )
    date_hierarchy = "created_at"
    inlines = [OrderEventInline]
    actions = ["mark_as_paid", "cancel_selected"]

    readonly_fields = (
        "number",
        "payment_token",
        "options_display",
        "customer",
        "guest_name",
        "guest_phone",
        "guest_email",
        "options_snapshot",
        "base_price",
        "options_total",
        "inscription_price",
        "delivery_fee",
        "promo_discount",
        "urgency_surcharge",
        "total",
        "subtotal",
        "address_display",
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (
            "Заказ",
            {
                "fields": (
                    "number",
                    "status",
                    "payment_status",
                    "payment_method",
                    "payment_token",
                    "paid_at",
                ),
            },
        ),
        (
            "Клиент и доставка",
            {
                "fields": (
                    "customer",
                    "guest_name",
                    "guest_phone",
                    "guest_email",
                    "delivery_date",
                    "delivery_time",
                    "is_urgent",
                    "address_display",
                    "estimated_delivery_at",
                    "delivery_comment",
                    "comment",
                ),
            },
        ),
        (
            "Конфигурация и деньги",
            {
                "classes": ("collapse",),
                "fields": (
                    "options_display",
                    "options_snapshot",
                    "inscription",
                    "subtotal",
                    "base_price",
                    "options_total",
                    "inscription_price",
                    "delivery_fee",
                    "promo",
                    "promo_code",
                    "promo_discount",
                    "urgency_surcharge",
                    "total",
                    "created_at",
                    "updated_at",
                ),
            },
        ),
    )

    @admin.display(description="Состав торта")
    def options_display(self, obj):
        return "\n".join(obj.options_lines)

    @admin.display(description="Адрес")
    def address_display(self, obj):
        return obj.address_line or "—"

    @admin.action(description="Отметить оплаченными")
    def mark_as_paid(self, request, queryset):
        changed = 0
        for order in queryset.exclude(payment_status=Order.PAYMENT_PAID):
            old_status = order.payment_status
            order.mark_paid()
            OrderEvent.objects.create(
                order=order,
                event_type=OrderEvent.TYPE_PAYMENT,
                from_status=old_status,
                to_status=order.payment_status,
                message="Отмечен оплаченным в админке",
                author=request.user if request.user.is_authenticated else None,
            )
            changed += 1
        self.message_user(request, f"Оплаченными отмечено заказов: {changed}")

    @admin.action(description="Отменить выбранные заказы")
    def cancel_selected(self, request, queryset):
        changed = 0
        for order in queryset.exclude(status=Order.STATUS_CANCELLED):
            old_status = order.status
            order.status = Order.STATUS_CANCELLED
            order.save(update_fields=["status", "updated_at"])
            OrderEvent.objects.create(
                order=order,
                event_type=OrderEvent.TYPE_STATUS,
                from_status=old_status,
                to_status=order.status,
                message="Отменён в админке",
                author=request.user if request.user.is_authenticated else None,
            )
            changed += 1
        self.message_user(request, f"Отменено заказов: {changed}")


@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "discount_type",
        "discount_display",
        "min_order_sum",
        "used_count",
        "max_uses",
        "valid_until",
        "is_active",
    )
    list_filter = ("is_active", "discount_type")
    search_fields = ("code", "description")
    readonly_fields = ("used_count", "created_at")

    @admin.display(description="Скидка")
    def discount_display(self, obj):
        if obj.discount_type == PromoCode.DISCOUNT_PERCENT:
            return f"{obj.percent_off}%"
        return f"{obj.amount_off} ₽"


@admin.register(OrderEvent)
class OrderEventAdmin(admin.ModelAdmin):
    list_display = (
        "order",
        "event_type",
        "message",
        "author",
        "author_label",
        "created_at",
    )
    list_filter = ("event_type", "created_at")
    search_fields = ("order__number", "message")
    date_hierarchy = "created_at"
    readonly_fields = [f.name for f in OrderEvent._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_view_permission(self, request, obj=None):
        return True
