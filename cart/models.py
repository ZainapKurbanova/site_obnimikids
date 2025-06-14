from django.db import models
from django.contrib.auth import get_user_model
from catalog.models import Product, Size

User = get_user_model()

class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Товар")
    color = models.CharField(max_length=50, verbose_name="Цвет", default="Не указан")
    size = models.ForeignKey(Size, on_delete=models.SET_NULL, null=True, verbose_name="Размер")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Количество")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата добавления")

    class Meta:
        verbose_name = "Элемент корзины"
        verbose_name_plural = "Элементы корзины"
        unique_together = ['user', 'product', 'color', 'size']

    def __str__(self):
        return f"{self.product.name} (Цвет: {self.color}, Размер: {self.size}, Количество: {self.quantity}) для {self.user.email}"

    def get_total_price(self):
        return self.product.price * self.quantity