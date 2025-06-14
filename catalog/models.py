from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
class Size(models.Model):
    name = models.CharField(max_length=10, unique=True, verbose_name="Размер")

    class Meta:
        verbose_name = "Размер"
        verbose_name_plural = "Размеры"

    def __str__(self):
        return self.name

class Product(models.Model):
    CATEGORY_CHOICES = [
        ('children_1_6', 'Дети 1-6 лет'),
        ('babies_3_12', 'Малыши (3 – 12 месяцев)'),
    ]

    name = models.CharField(max_length=100,
                            verbose_name="Название")
    description = models.TextField(verbose_name="Описание")
    price = models.DecimalField(max_digits=10,
                                decimal_places=2, verbose_name="Цена")
    old_price = models.DecimalField(max_digits=10,
                                    decimal_places=2, null=True,
                                    blank=True, verbose_name="Старая цена")
    image = models.URLField(max_length=500,
                            verbose_name="Ссылка на изображение",
                            blank=True, null=True)
    image_file = models.FileField(upload_to='temp/',
                                  verbose_name="Изображение", blank=True, null=True)
    sizes = models.ManyToManyField(Size, verbose_name="Размеры",
                                   blank=True)
    color = models.CharField(max_length=50, verbose_name="Цвет", default="Не указан")
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default='children_1_6',
        verbose_name="Категория"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата добавления")
    average_rating = models.FloatField(default=0.0, verbose_name="Средний рейтинг")

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"

    def __str__(self):
        return f"{self.name} ({self.color})"

    def update_average_rating(self):
        reviews = self.reviews.all()
        if reviews.exists():
            avg_rating = reviews.aggregate(models.Avg('rating'))['rating__avg']
            self.average_rating = round(avg_rating, 1)
        else:
            self.average_rating = 0.0
        self.save()

class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews', verbose_name="Товар")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Пользователь")
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Рейтинг"
    )
    comment = models.TextField(verbose_name="Комментарий")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"
        unique_together = ('product', 'user')  # Один пользователь может оставить только один отзыв на товар

    def __str__(self):
        return f"Отзыв от {self.user.email} на {self.product.name}"