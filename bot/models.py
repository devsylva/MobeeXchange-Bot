from django.db import models
from django.utils.timezone import now
from datetime import timedelta

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
    conversion_rate = models.FloatField(default=0.0)
    converted_amount = models.FloatField(default=0.0)
    status = models.CharField(max_length=10, choices=STATUS, default="pending")
    account_name = models.CharField(max_length=100, null=True, blank=True)
    account_number = models.CharField(max_length=20, null=True, blank=True)
    bank_code = models.CharField(max_length=10, null=True, blank=True)
    expired_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    def __str__(self):
        return f"Deposit Request of {self.amount} for {self.user.username}"


class WithdrawalRequest(models.Model):
    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Completed", "Completed"),
        ("Rejected", "Rejected"),
    ]
    user = models.ForeignKey(TelegramUser, on_delete=models.CASCADE, null=True, blank=True)
    transaction_id = models.IntegerField()  # Assuming this is an ID or unique identifier
    currency = models.CharField(max_length=10)  # e.g., "USDC"
    amount = models.DecimalField(max_digits=20, decimal_places=8)  # For precise amounts
    fee = models.DecimalField(max_digits=20, decimal_places=8)
    address = models.CharField(max_length=255)  # Wallet address
    created_at = models.DateTimeField(auto_now_add=True)  # Automatically set on creation
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="Completed")  # Status of the request
    network_name = models.CharField(max_length=50)  # e.g., "Polygon Mumbai 1"
    explorer_url = models.URLField(max_length=500, null=True, blank=True)  # Link to transaction explorer

    def __str__(self):
        return f"Withdrawal {self.data} - {self.status}"



class ActionToken(models.Model):
    ACTION_CHOICES = [
        ('withdrawal', 'Withdrawal'),
        ('deposit', 'Deposit'),
    ]

    user = models.ForeignKey(TelegramUser, on_delete=models.CASCADE)
    token = models.CharField(max_length=100, unique=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_valid(self):
        """Check if the token is valid (not used and not expired)."""
        return self.is_used

    def __str__(self):
        return f"Token for {self.user.username} - {self.action} - {'Used' if self.is_used else 'Valid'}"