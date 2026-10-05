from django.db import models

from apps.custom_cake.models import CakePart


class Cake(models.Model):
    title = models.CharField(verbose_name="Название", max_length=200)
    description = models.TextField(verbose_name="Описание")
    price = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Цена")
    weight = models.DecimalField(
        max_digits=5, decimal_places=2, verbose_name="Вес (кг)"
    )
    image = models.ImageField(upload_to="images/cakes", verbose_name="Картинка")
    is_active = models.BooleanField(
        "В наличии", default=True, help_text="Снятый с продажи торт скрыт из каталога"
    )
    restricted_parts = models.ManyToManyField(
        "custom_cake.CakePart",
        verbose_name="Ограничения кастомизации",
        blank=True,
        help_text="Если заполнено — используются только эти части. Если пусто — все части доступны.",
    )

    class Meta:
        verbose_name = "Торт"
        verbose_name_plural = "Торты"
        ordering = ("id",)

    def __str__(self):
        return self.title

    @property
    def available_parts(self):
        """Возвращает parts, доступные для этого торта."""
        if self.restricted_parts.exists():
            return self.restricted_parts.all()
        return CakePart.objects.all()
