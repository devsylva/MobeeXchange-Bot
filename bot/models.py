from django.db import models

# Create your models here.
class TelegramUser(models.Model):
    telegram_id = models.IntegerField(default="0", unique=True, blank=True, null=True)
    username = models.CharField(max_length=50)
    first_name = models.CharField(max_length=50, null=True, blank=True)
    last_name = models.CharField(max_length=50, null=True, blank=True)
    balance = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    def __str__(self):
        return f"{self.username} or {self.telegram_id}"


class DepositRequest(models.Model):
    STATUS = (
        ("pending", "Pending"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    )
    user = models.ForeignKey(TelegramUser, on_delete=models.CASCADE)
    deposit_id = models.CharField(max_length=100, unique=True)
    transaction_id = models.CharField(max_length=100, unique=True)
    amount = models.FloatField()
    status = models.CharField(max_length=10, choices=STATUS, default="pending")
    account_name = models.CharField(max_length=100, null=True, blank=True)
    account_number = models.CharField(max_length=20, null=True, blank=True)
    bank_code = models.CharField(max_length=10, null=True, blank=True)
    expired_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    def __str__(self):
        return f"Deposit Request of {self.amount} for {self.user.username}"
