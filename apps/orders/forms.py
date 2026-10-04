from datetime import timedelta

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.accounts.utils import normalize_phone
from apps.orders.models import Order
from apps.orders.services import URGENCY_LEAD_HOURS
from apps.ready_cake.models import Cake

# Ограничения на заказ готовых тортов.
MAX_CAKES_PER_ORDER = 10
MAX_CAKE_QTY = 20


class OrderForm(forms.ModelForm):
    options = forms.JSONField(
        label="Комплектация",
        error_messages={
            "invalid_json": "Не удалось прочитать выбранные опции",
            "required": "Выберите комплектацию торта",
        },
    )
    promo = forms.CharField(label="Промокод", required=False, max_length=50)
    address = forms.CharField(
        label="Адрес",
        max_length=300,
        error_messages={"required": "Укажите адрес доставки"},
    )

    class Meta:
        model = Order
        fields = (
            "guest_name",
            "guest_phone",
            "guest_email",
            "inscription",
            "comment",
            "delivery_date",
            "delivery_time",
            "delivery_comment",
        )
        error_messages = {
            "guest_name": {"required": "Укажите имя"},
            "guest_phone": {"required": "Укажите телефон"},
            "delivery_date": {"required": "Укажите дату доставки"},
            "delivery_time": {"required": "Укажите время доставки"},
        }
        widgets = {
            "guest_name": forms.TextInput(attrs={"class": "form-control"}),
            "guest_phone": forms.TextInput(
                attrs={"class": "form-control", "type": "tel"}
            ),
            "guest_email": forms.EmailInput(attrs={"class": "form-control"}),
            "inscription": forms.TextInput(attrs={"class": "form-control"}),
            "comment": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "delivery_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "delivery_time": forms.TimeInput(
                attrs={"class": "form-control", "type": "time"}
            ),
            "delivery_comment": forms.Textarea(
                attrs={"class": "form-control", "rows": 2}
            ),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        if user is not None and user.is_authenticated:
            for name in ("guest_name", "guest_email"):
                self.fields[name].required = False
            self.fields["guest_phone"].required = False

    def clean_delivery_date(self):
        value = self.cleaned_data["delivery_date"]
        if value < timezone.localdate():
            raise ValidationError("Дата доставки не может быть в прошлом")
        return value

    def clean_options(self):
        """Ожидаем список id выбранных опций: [12, 14, 31]."""
        value = self.cleaned_data["options"]
        if not isinstance(value, list):
            raise ValidationError("Ожидался список выбранных опций")
        ids = []
        for item in value:
            if not isinstance(item, int) or isinstance(item, bool):
                raise ValidationError("Некорректный идентификатор опции")
            ids.append(item)
        if not ids:
            raise ValidationError("Выберите комплектацию торта")
        return ids

    def clean_guest_phone(self):
        value = (self.cleaned_data.get("guest_phone") or "").strip()
        if not value and self.user is not None and self.user.is_authenticated:
            return str(self.user.phone or "")
        if not value:
            raise ValidationError("Укажите телефон")
        normalized = normalize_phone(value)
        if normalized is None:
            raise ValidationError("Некорректный номер телефона")
        return normalized

    def clean(self):
        cleaned = super().clean()
        user = self.user
        if user is not None and user.is_authenticated:
            phone = cleaned.get("guest_phone") or str(user.phone or "")
            cleaned["guest_phone"] = phone
            if not cleaned.get("guest_name"):
                cleaned["guest_name"] = user.name or ""
            if not cleaned.get("guest_email"):
                cleaned["guest_email"] = user.email or ""
        return cleaned

    @property
    def delivery_moment(self):
        date = self.cleaned_data.get("delivery_date")
        time = self.cleaned_data.get("delivery_time")
        if not date or not time:
            return None
        return timezone.make_aware(
            timezone.datetime.combine(date, time),
            timezone.get_current_timezone(),
        )

    def is_urgent(self) -> bool:
        moment = self.delivery_moment
        if moment is None:
            return False
        return moment < timezone.now() + timedelta(hours=URGENCY_LEAD_HOURS)

    def get_promo(self):
        code = (self.cleaned_data.get("promo") or "").strip()
        return code.upper()


class ReadyCakeOrderForm(OrderForm):
    """Готовые торты из каталога: доставка и промокод, без комплектации.

    Наследует валидацию телефона, даты доставки и префилл из профиля —
    убираются только комплектация и надпись. Торты выбираются полем cakes:
    [{"id": 3, "qty": 2}, {"id": 7, "qty": 1}], где qty — целое >= 1.
    """

    cakes = forms.JSONField(
        label="Торты",
        error_messages={
            "invalid_json": "Не удалось прочитать список тортов",
            "required": "Выберите хотя бы один торт",
        },
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        del self.fields["options"]
        del self.fields["inscription"]
        # cakes — невидимое поле: список тортов собирает JS из формы ниже.
        self.fields["cakes"].widget = forms.HiddenInput()
        for field in self.fields.values():
            if field is self.fields["cakes"]:
                continue
            css = field.widget.attrs.get("class") or "form-control"
            field.widget.attrs["class"] = f"{css} cake__textinput"

    @property
    def contact_fields(self):
        return [self[name] for name in ("guest_name", "guest_phone", "guest_email")]

    @property
    def delivery_fields(self):
        return [self[name] for name in ("address", "delivery_date", "delivery_time")]

    def clean_cakes(self):
        """Проверяет список тортов и возвращает [(Cake, qty), ...].

        Цены берутся из справочника на сервере: значения из поля не доверяем.
        """
        value = self.cleaned_data["cakes"]
        if not isinstance(value, list):
            raise ValidationError("Ожидался список тортов")

        chosen = {}
        for item in value:
            if not isinstance(item, dict):
                raise ValidationError("Некорректный формат позиции")
            cake_id = item.get("id")
            qty = item.get("qty", 1)
            if not isinstance(cake_id, int) or isinstance(cake_id, bool):
                raise ValidationError("Некорректный идентификатор торта")
            if not isinstance(qty, int) or isinstance(qty, bool):
                raise ValidationError("Количество должно быть целым числом")
            if not 1 <= qty <= MAX_CAKE_QTY:
                raise ValidationError(
                    f"Количество одного торта — от 1 до {MAX_CAKE_QTY}"
                )
            if cake_id in chosen:
                raise ValidationError("Один торт указан дважды")
            chosen[cake_id] = qty

        if not chosen:
            raise ValidationError("Выберите хотя бы один торт")
        if len(chosen) > MAX_CAKES_PER_ORDER:
            raise ValidationError(f"Не больше {MAX_CAKES_PER_ORDER} позиций в заказе")

        cakes = {
            cake.id: cake for cake in Cake.objects.filter(id__in=chosen, is_active=True)
        }
        missing = sorted(set(chosen) - set(cakes))
        if missing:
            raise ValidationError("Некоторые торты больше недоступны")

        return [(cakes[cake_id], qty) for cake_id, qty in chosen.items()]


class PaymentForm(forms.Form):
    """Выбор способа оплаты на странице оплаты заказа."""

    payment_method = forms.ChoiceField(
        label="Способ оплаты",
        choices=Order.PAYMENT_METHOD_CHOICES,
        error_messages={"invalid_choice": "Выберите способ оплаты"},
    )
