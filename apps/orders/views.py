import json

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.custom_cake.models import CakePartOption
from apps.custom_cake.views import build_cake_details, build_order_prefill
from apps.orders.forms import (
    MAX_CAKE_QTY,
    OrderForm,
    PaymentForm,
    ReadyCakeOrderForm,
)
from apps.orders.models import Order, OrderEvent, PromoCode
from apps.orders.services import calculate_price, price_ready_cakes
from apps.ready_cake.models import Cake


def user_orders(user):
    """Заказы пользователя: его собственные и гостевые на тот же телефон."""
    return Order.objects.filter(
        Q(customer=user) | Q(customer__isnull=True, guest_phone=str(user.phone or ""))
    )


def find_order_for_payment(number, token):
    """Заказ для страницы оплаты.

    Номер заказа подбирается перебором, поэтому нужен ещё и секретный токен.
    Логин не требуется: гость получает ссылку сразу после оформления.
    """
    return get_object_or_404(Order, number=number, payment_token=token)


@login_required(login_url="/?reg=code")
def lk(request):
    return render(request, "lk.html", {"orders": user_orders(request.user)})


@login_required(login_url="/?reg=code")
def order_history(request):
    return render(request, "lk-order.html", {"orders": user_orders(request.user)})


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
    promo = PromoCode.objects.filter(code__iexact=code).first()
    if promo is None:
        return "Промокод не найден"

    discount = promo.discount_for(subtotal)
    if discount <= 0:
        return promo.reject_reason(subtotal)

    order.promo = promo
    order.promo_code = promo.code
    order.promo_discount = discount
    return ""


def order_delivery_kwargs(request, form):
    """Контакты и доставка — одинаковы для своего и готового торта."""
    return {
        "customer": request.user if request.user.is_authenticated else None,
        "guest_name": form.cleaned_data.get("guest_name", ""),
        "guest_phone": form.cleaned_data["guest_phone"],
        "guest_email": form.cleaned_data.get("guest_email", ""),
        "delivery_date": form.cleaned_data["delivery_date"],
        "delivery_time": form.cleaned_data["delivery_time"],
        "address_snapshot": {"street": form.cleaned_data["address"]},
        "comment": form.cleaned_data.get("comment", ""),
        "delivery_comment": form.cleaned_data.get("delivery_comment", ""),
        "estimated_delivery_at": form.delivery_moment,
    }


def place_order(form, order):
    """Сохраняет заказ, применяет промокод и пишет событие создания.

    Возвращает False, если промокод отклонён: заказ не сохраняется,
    а в форме появляется ошибка поля promo.
    """
    promo_error = apply_promo(order, order.subtotal, form.get_promo())
    if promo_error:
        form.add_error("promo", promo_error)
        return False

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
            author=order.customer,
            author_label="" if order.customer else order.guest_name,
        )

    return True


@require_POST
def order_create(request):
    form = OrderForm(request.POST, user=request.user)
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
        order = Order(**priced, **order_delivery_kwargs(request, form))

        if place_order(form, order):
            return redirect(
                "orders:pay", number=order.number, token=order.payment_token
            )

    messages = [
        message for field_errors in form.errors.values() for message in field_errors
    ]

    posted = {
        key: value
        for key, value in form.data.items()
        if key not in ("csrfmiddlewaretoken", "options") and value
    }
    order_prefill = {**build_order_prefill(request.user), **posted}

    return render(
        request,
        "index.html",
        {
            "cake_details": build_cake_details(),
            "form": form,
            "order_errors": list(dict.fromkeys(messages)),
            "order_prefill": order_prefill,
        },
    )


def _positive_int(value, default):
    """Положительное целое из query-параметра, иначе значение по умолчанию."""
    try:
        number = int(value)
    except (TypeError, ValueError):
        return default
    return number if 1 <= number <= MAX_CAKE_QTY else default


def selected_quantities(request):
    """Отмеченные торты и их количества: {id торта: количество}.

    POST разбираем всегда, даже с ошибками валидации, чтобы клиент не терял
    выбор. GET используется для перехода из каталога (?cake=<id>&qty=<n>).
    """
    if request.method == "POST":
        raw = request.POST.get("cakes")
        try:
            parsed = json.loads(raw) if raw else []
        except (TypeError, ValueError):
            return {}
        if not isinstance(parsed, list):
            return {}
        return {
            item["id"]: _positive_int(item.get("qty"), 0)
            for item in parsed
            if isinstance(item, dict)
            and isinstance(item.get("id"), int)
            and not isinstance(item.get("id"), bool)
        }

    cake_id = (
        int(request.GET["cake"]) if request.GET.get("cake", "").isdigit() else None
    )
    if cake_id is None or not Cake.objects.filter(pk=cake_id, is_active=True).exists():
        return {}
    return {cake_id: _positive_int(request.GET.get("qty"), 1)}


def ready_cakes_total(items):
    """Сумма готовых тортов для показа на странице оформления."""
    return sum(int(cake.price) * qty for cake, qty in items)


def ready_order_create(request):
    """Оформление заказа готовых тортов из каталога, без конфигурации."""
    form = ReadyCakeOrderForm(
        request.POST or None,
        user=request.user,
        initial=None if request.method == "POST" else build_order_prefill(request.user),
    )
    cakes = list(Cake.objects.filter(is_active=True))

    if request.method == "POST" and form.is_valid():
        order = Order(
            **price_ready_cakes(form.cleaned_data["cakes"]),
            **order_delivery_kwargs(request, form),
        )

        if place_order(form, order):
            return redirect(
                "orders:pay", number=order.number, token=order.payment_token
            )

    messages = [
        message for field_errors in form.errors.values() for message in field_errors
    ]
    posted = {
        key: value
        for key, value in form.data.items()
        if key not in ("csrfmiddlewaretoken", "options") and value
    }

    # При ошибке показываем то, что клиент уже выбрал, чтобы не начинать заново.
    selected = selected_quantities(request)
    items = [
        (cake, selected.get(cake.pk, 0)) for cake in cakes if selected.get(cake.pk)
    ]

    return render(
        request,
        "ready_cake_order.html",
        {
            "cakes": cakes,
            "cakes_json": json.dumps(
                [
                    {
                        "id": cake.pk,
                        "title": cake.title,
                        "price": int(cake.price),
                        "weight": float(cake.weight) if cake.weight is not None else 0,
                        "description": cake.description,
                        "image": cake.image.url,
                    }
                    for cake in cakes
                ],
                ensure_ascii=False,
            ),
            "selected_json": json.dumps(
                {str(cake.pk): qty for cake, qty in items}, ensure_ascii=False
            ),
            "max_qty": MAX_CAKE_QTY,
            "total": ready_cakes_total(items),
            "form": form,
            "order_errors": list(dict.fromkeys(messages)),
            "order_prefill": {**build_order_prefill(request.user), **posted},
        },
    )


def payment_context(order, form):
    return {
        "order": order,
        "form": form,
        "payment_methods": Order.PAYMENT_METHOD_CHOICES,
    }


def payment_page(request, number, token):
    order = find_order_for_payment(number, token)
    form = PaymentForm(initial={"payment_method": order.payment_method})
    return render(request, "payment.html", payment_context(order, form))


@require_POST
def payment_process(request, number, token):
    order = find_order_for_payment(number, token)
    if order.is_paid:
        return redirect("orders:pay", number=order.number, token=order.payment_token)

    form = PaymentForm(request.POST)
    if not form.is_valid():
        return render(request, "payment.html", payment_context(order, form), status=400)

    old_status = order.payment_status
    order.payment_method = form.cleaned_data["payment_method"]
    # mark_paid() сохраняет только payment_status/paid_at/updated_at,
    # поэтому способ оплаты пишем отдельным save().
    order.save(update_fields=["payment_method", "updated_at"])
    order.mark_paid()

    OrderEvent.objects.create(
        order=order,
        event_type=OrderEvent.TYPE_PAYMENT,
        from_status=old_status,
        to_status=order.payment_status,
        message=f"Оплата: {order.get_payment_method_display()}",
        author=request.user if request.user.is_authenticated else None,
        author_label="" if request.user.is_authenticated else order.guest_name,
    )
    return redirect("orders:pay", number=order.number, token=order.payment_token)
