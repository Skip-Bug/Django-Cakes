from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from apps.orders.utils import make_order_number, make_payment_token


class PromoCode(models.Model):
    """Промокод для скидки при заказе."""

    DISCOUNT_PERCENT = "PERCENT"
    DISCOUNT_AMOUNT = "AMOUNT"

    code = models.CharField("Промокод", max_length=50, unique=True)
    discount_type = models.CharField(
        "Тип скидки",
        max_length=10,
        choices=[(DISCOUNT_PERCENT, "Процент"), (DISCOUNT_AMOUNT, "Сумма")],
        default=DISCOUNT_PERCENT,
    )
    percent_off = models.PositiveSmallIntegerField(
        "Процент", default=0, validators=[MinValueValidator(0)]
    )
    amount_off = models.PositiveIntegerField(
        "Сумма скидки, р.", default=0, validators=[MinValueValidator(0)]
    )
    min_order_sum = models.PositiveIntegerField(
        "Минимальная сумма заказа, р.", default=0, validators=[MinValueValidator(0)]
    )
    max_uses = models.PositiveIntegerField(
        "Максимум применений", blank=True, null=True, validators=[MinValueValidator(1)]
    )
    used_count = models.PositiveIntegerField("Применено раз", default=0)
    valid_from = models.DateTimeField("Действует с", null=True, blank=True)
    valid_until = models.DateTimeField("Действует до", null=True, blank=True)
    is_active = models.BooleanField("Активен", default=True)
    description = models.CharField("Описание", max_length=255, blank=True, default="")
    created_at = models.DateTimeField("Создан", auto_now_add=True)

    class Meta:
        verbose_name = "Промокод"
        verbose_name_plural = "Промокоды"
        ordering = ("-created_at",)

    def __str__(self):
        return self.code

    def clean(self):
        if self.discount_type == self.DISCOUNT_PERCENT:
            if not 1 <= self.percent_off <= 100:
                raise ValidationError(
                    {"percent_off": "Процент должен быть от 1 до 100"}
                )
        elif self.amount_off <= 0:
            raise ValidationError({"amount_off": "Укажите сумму скидки больше нуля"})

    @property
    def is_expired(self):
        return bool(self.valid_until and self.valid_until < timezone.now())

    @property
    def is_exhausted(self):
        return bool(self.max_uses and self.used_count >= self.max_uses)

    def is_usable_for(self, subtotal: int) -> bool:
        if not self.is_active or self.is_expired or self.is_exhausted:
            return False
        if self.valid_from and self.valid_from > timezone.now():
            return False
        return subtotal >= self.min_order_sum

    def discount_for(self, subtotal: int) -> int:
        if not self.is_usable_for(subtotal):
            return 0
        if self.discount_type == self.DISCOUNT_PERCENT:
            return int(round(subtotal * self.percent_off / 100))
        return min(self.amount_off, subtotal)

    def reject_reason(self, subtotal: int) -> str:
        if not self.is_active:
            return "Промокод отключён"
        if self.is_expired:
            return "Срок действия промокода истёк"
        if self.valid_from and self.valid_from > timezone.now():
            return "Промокод ещё не действует"
        if self.is_exhausted:
            return "Промокод исчерпал лимит применений"
        if subtotal < self.min_order_sum:
            return f"Промокод действует от {self.min_order_sum}р."
        return ""


class OrderQuerySet(models.QuerySet):
    def paid(self):
        return self.filter(payment_status=Order.PAYMENT_PAID)

    def not_cancelled(self):
        return self.exclude(status=Order.STATUS_CANCELLED)

    def delivered_on(self, day):
        return self.filter(delivery_date=day)


class Order(models.Model):
    """Заказ.

    Конфигурация торта и цена сохраняются снимком: если кондитер потом изменит
    цену топпинга в справочнике, уже принятый заказ не пересчитается.
    """

    STATUS_NEW = "NEW"
    STATUS_CONFIRMED = "CONFIRMED"
    STATUS_IN_PRODUCTION = "IN_PRODUCTION"
    STATUS_READY = "READY"
    STATUS_DELIVERING = "DELIVERING"
    STATUS_DELIVERED = "DELIVERED"
    STATUS_CANCELLED = "CANCELLED"
    STATUS_COMPLAINT = "COMPLAINT"

    STATUS_CHOICES = [
        (STATUS_NEW, "Новый"),
        (STATUS_CONFIRMED, "Подтверждён"),
        (STATUS_IN_PRODUCTION, "В работе"),
        (STATUS_READY, "Готов"),
        (STATUS_DELIVERING, "В доставке"),
        (STATUS_DELIVERED, "Доставлен"),
        (STATUS_CANCELLED, "Отменён"),
        (STATUS_COMPLAINT, "Жалоба"),
    ]

    STATUSES_IN_WORK = (
        STATUS_NEW,
        STATUS_CONFIRMED,
        STATUS_IN_PRODUCTION,
        STATUS_READY,
        STATUS_DELIVERING,
    )

    PAYMENT_PENDING = "PENDING"
    PAYMENT_PAID = "PAID"
    PAYMENT_REFUNDED = "REFUNDED"

    PAYMENT_STATUS_CHOICES = [
        (PAYMENT_PENDING, "Ожидает оплаты"),
        (PAYMENT_PAID, "Оплачен"),
        (PAYMENT_REFUNDED, "Возврат"),
    ]

    PAYMENT_METHOD_CARD = "CARD"
    PAYMENT_METHOD_CASH = "CASH"

    PAYMENT_METHOD_CHOICES = [
        (PAYMENT_METHOD_CARD, "Банковской картой онлайн"),
        (PAYMENT_METHOD_CASH, "Наличными ..."),
    ]

    number = models.CharField("Номер", max_length=20, unique=True)
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Клиент",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
    )

    # Гость без регистрации / пока под вопросом, будет ли такая опция
    guest_name = models.CharField("Имя", max_length=150, blank=True, default="")
    guest_phone = models.CharField("Телефон", max_length=20, db_index=True)
    guest_email = models.EmailField("Почта", blank=True, default="")

    status = models.CharField(
        "Статус",
        max_length=16,
        choices=STATUS_CHOICES,
        default=STATUS_NEW,
        db_index=True,
    )
    payment_status = models.CharField(
        "Оплата", max_length=12, choices=PAYMENT_STATUS_CHOICES, default=PAYMENT_PENDING
    )
    payment_method = models.CharField(
        "Способ оплаты",
        max_length=8,
        choices=PAYMENT_METHOD_CHOICES,
        default=PAYMENT_METHOD_CARD,
    )
    payment_token = models.CharField(
        "Токен оплаты", max_length=32, blank=True, default="", db_index=True
    )

    # --- конфигурация торта (снимок) ---
    options_snapshot = models.JSONField(
        "Опции на момент заказа", default=dict, blank=True
    )
    inscription = models.CharField("Надпись", max_length=200, blank=True, default="")

    base_price = models.PositiveIntegerField("Базовая цена, р.", default=0)
    options_total = models.PositiveIntegerField("Стоимость опций, р.", default=0)
    inscription_price = models.PositiveIntegerField("Надпись, р.", default=0)
    delivery_fee = models.PositiveIntegerField("Доставка, р.", default=0)
    promo_discount = models.PositiveIntegerField("Скидка, р.", default=0)
    urgency_surcharge = models.PositiveIntegerField(
        "Наценка за срочность, р.", default=0
    )
    total = models.PositiveIntegerField("Итого, р.", default=0)

    promo = models.ForeignKey(
        PromoCode,
        verbose_name="Промокод",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
    )
    promo_code = models.CharField(
        "Промокод (текстом)", max_length=50, blank=True, default=""
    )

    # --- доставка --- выносить отдельно?
    delivery_date = models.DateField("Дата доставки", db_index=True)
    delivery_time = models.TimeField("Время доставки")
    is_urgent = models.BooleanField("Срочный заказ", default=False)
    address_snapshot = models.JSONField("Адрес", default=dict, blank=True)
    comment = models.TextField("Комментарий к заказу", blank=True, default="")
    delivery_comment = models.TextField(
        "Комментарий для курьера", blank=True, default=""
    )
    estimated_delivery_at = models.DateTimeField(
        "Ожидаемая доставка", null=True, blank=True
    )
    paid_at = models.DateTimeField("Оплачен", null=True, blank=True)
    created_at = models.DateTimeField("Создан", auto_now_add=True)
    updated_at = models.DateTimeField("Изменён", auto_now=True)

    objects = OrderQuerySet.as_manager()

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.number} ({self.guest_phone})"

    def save(self, *args, **kwargs):
        if not self.number:
            self.number = make_order_number()
        if not self.payment_token:
            self.payment_token = make_payment_token()
        super().save(*args, **kwargs)

    # --- вычисляемое ---

    @property
    def subtotal(self) -> int:
        """Сумма без скидки, срочности и доставки — база для расчёта скидок."""
        return self.base_price + self.options_total + self.inscription_price

    @property
    def contact_name(self) -> str:
        if self.customer:
            return self.customer.name or self.customer.get_username()
        return self.guest_name or self.guest_phone

    @property
    def contact_phone(self) -> str:
        # Телефон в профиле хранится как username (см. apps.accounts.views.verify_code).
        if self.customer:
            return self.customer.get_username()
        return self.guest_phone

    @property
    def is_paid(self) -> bool:
        return self.payment_status == self.PAYMENT_PAID

    @property
    def is_active(self) -> bool:
        return self.status in self.STATUSES_IN_WORK

    @property
    def address_line(self) -> str:
        addr = self.address_snapshot or {}
        parts = [addr.get("city", ""), addr.get("street", "")]
        return ", ".join(p for p in parts if p)

    def _snapshot_items(self):
        """Пары (часть, опция) из снимка конфигурации."""
        for part_name, data in (self.options_snapshot or {}).items():
            for item in data if isinstance(data, list) else [data]:
                yield part_name, item

    @staticmethod
    def _text_option_ids() -> set:
        """id опций, для которых в заказе хранится надпись, а не название."""
        from apps.custom_cake.models import CakePartOption

        return set(
            CakePartOption.objects.filter(part__requires_text=True).values_list(
                "id", flat=True
            )
        )

    @property
    def options_lines(self) -> list:
        """Человекочитаемый состав торта для админки и печати."""
        text_option_ids = self._text_option_ids()
        lines = []
        for part_name, item in self._snapshot_items():
            value = item.get("name", "")
            if item.get("id") in text_option_ids and self.inscription:
                value = self.inscription
            lines.append(f"{part_name}: {value}")
        return lines

    @property
    def priced_lines(self) -> list:
        """Состав заказа с ценами для страницы оплаты.

        Возвращает [{"label": "Ягоды: Клубника", "price": 500}, ...],
        сумма цен равна subtotal.
        """
        text_option_ids = self._text_option_ids()
        lines = [{"label": "Торт", "price": self.base_price}]
        for part_name, item in self._snapshot_items():
            name = item.get("name", "")
            if item.get("id") in text_option_ids and self.inscription:
                name = self.inscription
            lines.append(
                {"label": f"{part_name}: {name}", "price": item.get("price", 0)}
            )
        return lines

    def mark_paid(self):
        if self.payment_status != self.PAYMENT_PAID:
            self.payment_status = self.PAYMENT_PAID
            self.paid_at = timezone.now()
            self.save(update_fields=["payment_status", "paid_at", "updated_at"])


class OrderEvent(models.Model):
    """История заказа: смена статуса, жалоба клиента, комментарий кондитера."""

    TYPE_STATUS = "STATUS"
    TYPE_COMPLAINT = "COMPLAINT"
    TYPE_COMMENT = "COMMENT"
    TYPE_PAYMENT = "PAYMENT"

    TYPE_CHOICES = [
        (TYPE_STATUS, "Смена статуса"),
        (TYPE_COMPLAINT, "Жалоба клиента"),
        (TYPE_COMMENT, "Комментарий"),
        (TYPE_PAYMENT, "Оплата"),
    ]

    order = models.ForeignKey(
        Order, verbose_name="Заказ", on_delete=models.CASCADE, related_name="events"
    )
    event_type = models.CharField(
        "Тип", max_length=12, choices=TYPE_CHOICES, default=TYPE_STATUS
    )
    from_status = models.CharField("Из статуса", max_length=16, blank=True, default="")
    to_status = models.CharField("В статус", max_length=16, blank=True, default="")
    message = models.TextField("Сообщение", blank=True, default="")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Автор",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order_events",
    )
    author_label = models.CharField(
        "Автор (текст)", max_length=150, blank=True, default=""
    )
    created_at = models.DateTimeField("Создано", auto_now_add=True)

    class Meta:
        verbose_name = "Событие заказа"
        verbose_name_plural = "События заказа"
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.order.number} — {self.get_event_type_display()}"
