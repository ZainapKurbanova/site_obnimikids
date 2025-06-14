from django.db import models
from django.contrib.auth import get_user_model
from catalog.models import Product

User = get_user_model()

class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             verbose_name="Пользователь", related_name="favorites")
    product = models.ForeignKey(Product, on_delete=models.CASCADE,
                                verbose_name="Товар")
    created_at = models.DateTimeField(auto_now_add=True,
                                      verbose_name="Дата добавления")

    class Meta:
        verbose_name = "Избранное"
        verbose_name_plural = "Избранное"
        unique_together = ('user', 'product')

    def __str__(self):
        return f"{self.user.username} - {self.product.name}"