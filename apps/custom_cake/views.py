from django.shortcuts import render

from .models import CakePart


def index(request):
    parts = CakePart.objects.prefetch_related("options").order_by("order")

    cake_details = {"parts": []}

    for part in parts:
        options = []
        for opt in part.options.all():
            options.append(
                {
                    "id": opt.id,
                    "name": opt.name,
                    "price": int(opt.price),
                }
            )
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

    return render(request, "index.html", {"cake_details": cake_details})
