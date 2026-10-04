from django.shortcuts import render

from .models import CakePart
from .pricing import BASE_PRICE


def build_cake_details():
    parts = CakePart.objects.prefetch_related("options").order_by("order")

    cake_details = {"base_price": int(BASE_PRICE), "parts": []}

    for part in parts:
        options = [
            {
                "id": opt.id,
                "name": opt.name,
                "price": int(opt.price),
            }
            for opt in part.options.all()
        ]
        cake_details["parts"].append(
            {
                "id": part.id,
                "name": part.name,
                "required": part.is_required,
                "multiple": part.is_multiple,
                "requires_text": part.requires_text,
                "order": part.order,
                "hint": part.hint,
                "options": options,
            }
        )

    return cake_details


def build_order_prefill(user):
    if not user.is_authenticated:
        return {}
    return {
        "guest_name": user.name,
        "guest_email": user.email,
        "guest_phone": str(user.phone or ""),
        "address": user.address or "",
    }


def index(request):
    return render(
        request,
        "index.html",
        {
            "cake_details": build_cake_details(),
            "order_errors": [],
            "order_prefill": build_order_prefill(request.user),
        },
    )
