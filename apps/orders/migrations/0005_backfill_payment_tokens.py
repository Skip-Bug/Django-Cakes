import secrets

from django.db import migrations


def backfill_payment_tokens(apps, schema_editor):
    """Заказы, созданные до появления оплаты, остались без токена.

    Без токена страница оплаты для них недоступна, поэтому проставляем
    секретный токен всем заказам с пустым значением.
    """
    Order = apps.get_model("orders", "Order")
    for order in Order.objects.filter(payment_token=""):
        order.payment_token = secrets.token_urlsafe(16)
        order.save(update_fields=["payment_token"])


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0004_order_payment_method_order_payment_token"),
    ]

    operations = [
        migrations.RunPython(backfill_payment_tokens, migrations.RunPython.noop),
    ]
