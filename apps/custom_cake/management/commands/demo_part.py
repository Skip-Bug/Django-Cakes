from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.custom_cake.models import CakePart, CakePartOption

DATA = [
    (
        "Уровни",
        {
            "is_required": True,
            "is_multiple": False,
            "requires_text": False,
            "order": 1,
        },
        [
            ("1 уровень", "400"),
            ("2 уровня", "750"),
            ("3 уровня", "1100"),
        ],
    ),
    (
        "Форма",
        {
            "is_required": True,
            "is_multiple": False,
            "requires_text": False,
            "order": 2,
        },
        [
            ("Квадрат", "600"),
            ("Круг", "400"),
            ("Прямоугольник", "1000"),
        ],
    ),
    (
        "Топпинг",
        {
            "is_required": True,
            "is_multiple": False,
            "requires_text": False,
            "order": 3,
        },
        [
            ("Без топпинга", "0"),
            ("Белый соус", "200"),
            ("Карамельный сироп", "180"),
            ("Кленовый сироп", "200"),
            ("Клубничный сироп", "300"),
            ("Черничный сироп", "350"),
            ("Молочный шоколад", "200"),
        ],
    ),
    (
        "Ягоды",
        {
            "is_required": False,
            "is_multiple": True,
            "requires_text": False,
            "order": 4,
        },
        [
            ("Ежевика", "400"),
            ("Малина", "300"),
            ("Голубика", "450"),
            ("Клубника", "500"),
        ],
    ),
    (
        "Декор",
        {
            "is_required": False,
            "is_multiple": True,
            "requires_text": False,
            "order": 5,
        },
        [
            ("Фисташки", "300"),
            ("Безе", "400"),
            ("Фундук", "350"),
            ("Пекан", "300"),
            ("Маршмеллоу", "200"),
            ("Марципан", "280"),
        ],
    ),
    (
        "Надпись",
        {
            "is_required": False,
            "is_multiple": False,
            "requires_text": True,
            "order": 6,
            "hint": "Разместим любую надпись, например: «С днем рождения!»",
        },
        [
            ("Надпись", "500"),
        ],
    ),
]


class Command(BaseCommand):
    help = "Заполняет БД частями и вариантами торта из ТЗ."

    @transaction.atomic
    def handle(self, *args, **options):
        parts_created = 0
        parts_updated = 0
        options_created = 0
        options_updated = 0

        for part_name, part_flags, options in DATA:
            part, created = CakePart.objects.update_or_create(
                name=part_name,
                defaults=part_flags,
            )
            if created:
                parts_created += 1
                self.stdout.write(self.style.SUCCESS(f"+ Часть: {part_name}"))
            else:
                parts_updated += 1
                self.stdout.write(f"~ Часть обновлена: {part_name}")

            for index, (option_name, price) in enumerate(options, start=1):
                _, opt_created = CakePartOption.objects.update_or_create(
                    part=part,
                    name=option_name,
                    defaults={
                        "price": Decimal(price),
                        "is_active": True,
                        "order": index,
                    },
                )
                if opt_created:
                    options_created += 1
                else:
                    options_updated += 1

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Готово."))
        self.stdout.write(
            f"Частей: создано {parts_created}, обновлено {parts_updated}",
        )
        self.stdout.write(
            f"Вариантов: создано {options_created}, обновлено {options_updated}"
        )
