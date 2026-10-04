from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("orders", "0002_alter_order_base_price_alter_order_delivery_fee_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="order",
            name="delivery_slot",
        ),
    ]
