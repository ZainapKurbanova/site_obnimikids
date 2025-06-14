from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class TelegramUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='telegram_user', null=True, blank=True)
    chat_id = models.CharField(max_length=32, unique=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True,null=True)
    username = models.CharField(max_length=150, blank=True)
    subscribed = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.username} (chat_id={self.chat_id})"
