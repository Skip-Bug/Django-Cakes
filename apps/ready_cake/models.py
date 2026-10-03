from django.db import models


class Cake(models.Model):
    title = models.CharField(verbose_name="Название", max_length=200)
    description = models.TextField(verbose_name="Описание")
    price = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Цена")
    weight = models.DecimalField(
        max_digits=5, decimal_places=2, verbose_name="Вес (кг)"
    )
    image = models.ImageField(upload_to="goods", verbose_name="Картинка")

    class Meta:
        verbose_name = "Торт"
        verbose_name_plural = "Торты"

    def __str__(self):
        return self.title
