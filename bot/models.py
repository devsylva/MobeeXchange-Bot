from django.db import models

# Create your models here.
class TelegramUser(models.Model):
    user_id = models.BigIntegerField(unique=True)
    username = models.CharField(max_length=255, blank=True, null=True)
    first_name = models.CharField(max_length=255, blank=True, null=True)
    last_name = models.CharField(max_length=255, blank=True, null=True)
    language_code = models.CharField(max_length=10, blank=True, null=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.username})" if self.username else f"{self.first_name} {self.last_name}"