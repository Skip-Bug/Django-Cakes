from decimal import Decimal

from apps.custom_cake.pricing import BASE_PRICE, DELIVERY_FEE
from apps.orders.models import READY_PART_NAME

# Наценка за срочный заказ: на сайте обещано +20%.
URGENCY_SURCHARGE_RATE = Decimal("0.20")

# Заказы с доставкой раньше суток считаются срочными.
URGENCY_LEAD_HOURS = 24


def calculate_price(options, is_urgent=False):
    """Пересчитывает стоимость заказа на сервере.

    options — список экземпляров CakePartOption, выбранных клиентом.
    Возвращает kwargs для создания Order: разобранные суммы и снимок
    конфигурации для options_snapshot.
    """
    options_total = Decimal("0")
    inscription_price = Decimal("0")
    snapshot = {}

    for option in options:
        part = option.part
        price = option.price

        if part.requires_text:
            inscription_price += price
        else:
            options_total += price

        entry = {"id": option.id, "name": option.name, "price": int(price)}

        existing = snapshot.get(part.name)
        if isinstance(existing, list):
            existing.append(entry)
        elif existing is None:
            snapshot[part.name] = entry
        else:
            snapshot[part.name] = [existing, entry]

    subtotal = BASE_PRICE + options_total + inscription_price
    urgency_surcharge = (
        (subtotal * URGENCY_SURCHARGE_RATE).quantize(Decimal("1"))
        if is_urgent
        else Decimal("0")
    )
    total = subtotal + urgency_surcharge + int(DELIVERY_FEE) 
    
    return {
        "base_price": int(BASE_PRICE),
        "options_total": int(options_total),
        "inscription_price": int(inscription_price),
        "urgency_surcharge": int(urgency_surcharge),
        "delivery_fee": int(DELIVERY_FEE),
        "total": int(total),
        "options_snapshot": snapshot,
        "is_urgent": is_urgent,
    }

