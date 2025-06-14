from django.db import models
from django.contrib.auth import get_user_model
from catalog.models import Product, Size

User = get_user_model()

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Ожидает оплаты'),
        ('paid', 'Оплата прошла'),
        ('processing', 'В обработке'),
        ('shipped', 'Отправлен'),
        ('delivered', 'Доставлен'),
        ('cancelled', 'Отменён'),
    ]

    DELIVERY_CHOICES = [
        ('post', 'Почта России'),
        ('courier', 'Курьер'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders', verbose_name="Пользователь")
    name = models.CharField(max_length=100, verbose_name="Имя")
    city = models.CharField(max_length=100, verbose_name="Город")
    address_detail = models.CharField(max_length=255, verbose_name="Детальный адрес")
    email = models.EmailField(verbose_name="E-mail")
    phone = models.CharField(max_length=20, verbose_name="Телефон")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Общая сумма")
    delivery_method = models.CharField(max_length=20, choices=DELIVERY_CHOICES, default='post', verbose_name="Способ доставки")
    delivery_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Стоимость доставки")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Статус")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    tg_chat_id = models.CharField(max_length=32, blank=True, null=True)

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"

    def __str__(self):
        return f"Заказ {self.id} от {self.user.email}"

    def get_total_with_delivery(self):
        return self.total_price + self.delivery_cost

    def get_status_display(self):
        return dict(self.STATUS_CHOICES).get(self.status, 'Неизвестен')

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name="Заказ")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Товар")
    size = models.ForeignKey(Size, on_delete=models.SET_NULL, null=True, verbose_name="Размер")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Количество")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена")

    class Meta:
        verbose_name = "Элемент заказа"
        verbose_name_plural = "Элементы заказа"

    def __str__(self):
        return f"{self.product.name} в заказе {self.order.id}"

