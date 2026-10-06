from django.core.validators import MinValueValidator
from django.db import models


class CakePart(models.Model):
    name = models.CharField("Название части", max_length=50)
    hint = models.CharField("Подсказка", max_length=255, blank=True)
    is_required = models.BooleanField("Обязательная часть", default=False)

    requires_text = models.BooleanField("Требует текста", default=False)
    order = models.PositiveIntegerField("Порядок в форме", default=0)

    class Meta:
        verbose_name = "Часть торта"
        verbose_name_plural = "Части торта"
        ordering = ["order"]

    def __str__(self):
        return self.name


class CakePartOption(models.Model):
    part = models.ForeignKey(
        CakePart,
        on_delete=models.CASCADE,
        related_name="options",
        verbose_name="Часть",
    )
    name = models.CharField("Название варианта", max_length=50)
    price = models.DecimalField(
        "Цена варианта",
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    is_active = models.BooleanField("Активна", default=True)
    order = models.PositiveIntegerField("Порядок в форме", default=0)

    class Meta:
        verbose_name = "Варианты части"
        verbose_name_plural = "Варианты частей"
        ordering = ["part", "order", "name"]
        unique_together = ("part", "name")

    def __str__(self):
        return f"{self.part.name}: {self.name}"
