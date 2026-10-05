import random
import secrets

from django.utils import timezone


def make_order_number() -> str:
    """Номер заказа для клиента: дата плюс случайный хвост, до 20 символов."""
    return f"{timezone.now():%d%m%y}-{random.randint(0, 999999):06d}"


def make_payment_token() -> str:
    """Секретный токен для страницы оплаты.

    Номер заказа угадывается перебором, поэтому одного номера мало:
    оплатить заказ можно только по паре номер + токен.
    """
    return secrets.token_urlsafe(16)
