from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.ready_cake.models import Cake 


# Данные для 6 тортов
CAKES_DATA = [
    {
        "title": "Наполеон",
        "description": "Классический торт с тонкими коржами и нежным заварным кремом.",
        "price": Decimal("1200"),
        "weight": "1,2 кг",
        "image": "napoleon.jpg",  # Относительный путь от папки media/
    },
    {
        "title": "Прага",
        "description": "Шоколадный торт с насыщенным вкусом и абрикосовой прослойкой.",
        "price": Decimal("1500"),
        "weight": "1.5 кг",
        "image": "praga.jpg",
    },
    {
        "title": "Медовик",
        "description": "Торт с медовыми коржами и сметанным кремом.",
        "price": Decimal("1000"),
        "weight": "1.1 кг",
        "image": "medovik.jpg",
    },
    {
        "title": "Красный бархат",
        "description": "Изысканный торт с шоколадным вкусом и сливочным кремом.",
        "price": Decimal("1600"),
        "weight": "1 кг",
        "image": "red_velvet.jpg",
    },
    {
        "title": "Птичье молоко",
        "description": "Воздушное суфле на бисквитной основе.",
        "price": Decimal("1250"),
        "weight": "1 кг",
        "image": "birds_milk.jpg",
    },
    {
        "title": "Захер",
        "description": "Австрийский шоколадный торт с абрикосовой прослойкой.",
        "price": Decimal("1700"),
        "weight": "1.2 кг",
        "image": "sacher.jpg",
    },
]



class Command(BaseCommand):
    help = "Создает 6 базовых тортов в базе данных."

    @transaction.atomic
    def handle(self, *args, **options):
        created_count = 0
        updated_count = 0

        for cake_data in CAKES_DATA:
            # update_or_create создаст торт, если его нет, или обновит, если он уже есть
            obj, created = Cake.objects.update_or_create(
                title=cake_data["title"], # Ищем по названию
                defaults={
                    "description": cake_data["description"],
                    "price": cake_data["price"],
                    "weight": cake_data["weight"],
                    "image": cake_data["image"],
                }
            )

            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"+ Добавлен: {obj.title}"))
            else:
                updated_count += 1
                self.stdout.write(f"~ Обновлен: {obj.title}")

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Готово."))
        self.stdout.write(
            f"Создано новых: {created_count}. Обновлено существующих: {updated_count}."
        )


