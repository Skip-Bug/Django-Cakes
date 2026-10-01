import random

from django.utils import timezone


def make_order_number() -> str:
    """Номер заказа для клиента: дата плюс случайный хвост, до 20 символов."""
    return f"{timezone.now():%d%m%y}-{random.randint(0, 999999):06d}"
