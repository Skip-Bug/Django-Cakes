from django.db import transaction
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from apps.custom_cake.models import CakePartOption
from apps.custom_cake.views import build_cake_details
from apps.orders.forms import OrderForm
from apps.orders.models import Order, OrderEvent, PromoCode
from apps.orders.services import calculate_price


def resolve_options(option_ids):
    """Проверяет, что все id — активные опции, и возвращает их по частям."""
    options = list(
        CakePartOption.objects.filter(
            id__in=option_ids,
            is_active=True,
        ).select_related("part")
    )
    found = {option.id for option in options}
    missing = sorted(set(option_ids) - found)
    return options, missing


def missing_required_parts(options):
    """Возвращает названия обязательных частей, которых нет в выборе."""
    required = (
        CakePartOption.objects.filter(part__is_required=True)
        .values_list("part__name", flat=True)
        .distinct()
    )
    chosen = {option.part.name for option in options}
    return sorted({name for name in required} - chosen)


def apply_promo(order, subtotal, code):
    """Начисляет скидку, если промокод применим. Возвращает текст ошибки."""
    if not code:
        return ""
    promo = PromoCode.objects.filter(code=code).first()
    if promo is None:
        return "Промокод не найден"

    discount = promo.discount_for(subtotal)
    if discount <= 0:
        return promo.reject_reason(subtotal)

    order.promo = promo
    order.promo_code = promo.code
    order.promo_discount = discount
    return ""


@require_POST
def order_create(request):
    form = OrderForm(request.POST, user=request.user)
    customer = request.user if request.user.is_authenticated else None
    options = []

    if form.is_valid():
        options, missing = resolve_options(form.cleaned_data["options"])
        if missing:
            form.add_error("options", "Некоторые опции больше недоступны")
        elif not options:
            form.add_error("options", "Выберите комплектацию торта")
        else:
            for part_name in missing_required_parts(options):
                form.add_error("options", f"Выберите вариант: {part_name}")

    if form.is_valid() and options:
        priced = calculate_price(options, is_urgent=form.is_urgent())
        order = Order(
            **priced,
            customer=customer,
            guest_name=form.cleaned_data.get("guest_name", ""),
            guest_phone=form.cleaned_data["guest_phone"],
            guest_email=form.cleaned_data.get("guest_email", ""),
            inscription=form.cleaned_data.get("inscription", ""),
            delivery_date=form.cleaned_data["delivery_date"],
            delivery_time=form.cleaned_data["delivery_time"],
            address_snapshot={"street": form.cleaned_data["address"]},
            comment=form.cleaned_data.get("comment", ""),
            delivery_comment=form.cleaned_data.get("delivery_comment", ""),
            estimated_delivery_at=form.delivery_moment,
        )

        promo_error = apply_promo(order, order.subtotal, form.get_promo())
        if promo_error:
            form.add_error("promo", promo_error)
        else:
            order.total -= order.promo_discount

            with transaction.atomic():
                order.save()

                promo = order.promo
                if promo:
                    PromoCode.objects.filter(pk=promo.pk).update(
                        used_count=promo.used_count + 1
                    )

                OrderEvent.objects.create(
                    order=order,
                    event_type=OrderEvent.TYPE_STATUS,
                    from_status="",
                    to_status=Order.STATUS_NEW,
                    message="Заказ создан",
                    author=customer,
                    author_label="" if customer else order.guest_name,
                )

            if customer:
                return redirect("lk-order")
            return redirect(f"/?order={order.number}")

    messages = [
        message for field_errors in form.errors.values() for message in field_errors
    ]

    return render(
        request,
        "index.html",
        {
            "cake_details": build_cake_details(),
            "form": form,
            "order_errors": list(dict.fromkeys(messages)),
            "order_prefill": {
                key: value
                for key, value in form.data.items()
                if key not in ("csrfmiddlewaretoken", "options")
            },
        },
    )
