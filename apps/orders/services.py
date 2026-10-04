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
    total = subtotal + urgency_surcharge + DELIVERY_FEE  # пересмотреть

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


def price_ready_cakes(items):
    """Стоимость заказа готовых тортов: цены из справочника, без опций.

    items — список пар (Cake, количество). Готовый торт не изготавливается,
    поэтому наценка за срочность не начисляется. Доставка берётся один раз
    на заказ, а не за каждый торт.

    Название и цена сохраняются в снимке, чтобы переименование позиции
    каталога или снятие её с продажи не испортило уже принятый заказ.
    """
    snapshot = {
        READY_PART_NAME: [
            {
                "id": cake.id,
                "name": cake.title,
                "price": int(cake.price),
                "qty": qty,
            }
            for cake, qty in items
        ]
    }
    options_total = sum(int(cake.price) * qty for cake, qty in items)

    return {
        "base_price": 0,
        "options_total": options_total,
        "inscription_price": 0,
        "urgency_surcharge": 0,
        "delivery_fee": int(DELIVERY_FEE),
        "total": options_total + int(DELIVERY_FEE),
        "options_snapshot": snapshot,
        "is_urgent": False,
    }
