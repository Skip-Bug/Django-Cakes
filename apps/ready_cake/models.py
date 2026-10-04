from django.db import models


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

    class Meta:
        verbose_name = "Торт"
        verbose_name_plural = "Торты"
        ordering = ("id",)

    def __str__(self):
        return self.title
