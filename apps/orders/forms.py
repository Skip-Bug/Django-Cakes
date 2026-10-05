from datetime import timedelta

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.accounts.utils import normalize_phone
from apps.orders.models import Order
from apps.orders.services import URGENCY_LEAD_HOURS


class OrderForm(forms.ModelForm):
    options = forms.JSONField(
        label="Комплектация",
        required=False,
        error_messages={
            "invalid_json": "Не удалось прочитать выбранные опции",
            "required": "Выберите комплектацию торта",
        },
    )
    promo = forms.CharField(label="Промокод", required=False, max_length=50)
    base_cake = forms.IntegerField(label="Base cake", required=False)
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
        value = self.cleaned_data["options"] or []
        if not isinstance(value, list):
            raise ValidationError("Ожидался список выбранных опций")
        ids = []
        for item in value:
            if not isinstance(item, int) or isinstance(item, bool):
                raise ValidationError("Некорректный идентификатор опции")
            ids.append(item)
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


class PaymentForm(forms.Form):
    """Выбор способа оплаты на странице оплаты заказа."""

    payment_method = forms.ChoiceField(
        label="Способ оплаты",
        choices=Order.PAYMENT_METHOD_CHOICES,
        error_messages={"invalid_choice": "Выберите способ оплаты"},
    )
