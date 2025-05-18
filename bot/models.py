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
        ("Confirmed", "Confirmed"),
        ("Rejected", "Rejected"),
    ]
    user = models.ForeignKey(TelegramUser, on_delete=models.CASCADE, null=True, blank=True)
    data = models.IntegerField()  # Assuming this is an ID or unique identifier
    currency = models.CharField(max_length=10)  # e.g., "USDC"
    amount = models.DecimalField(max_digits=20, decimal_places=8)  # For precise amounts
    address = models.CharField(max_length=255)  # Wallet address
    txn_hash = models.CharField(max_length=255, null=True, blank=True)  # Transaction hash
    created_at = models.DateTimeField(auto_now_add=True)  # Automatically set on creation
    confirmed_at = models.DateTimeField(null=True, blank=True)  # Set when confirmed
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="Pending")  # Status of the request
    rejected_reason = models.TextField(null=True, blank=True)  # Reason for rejection
    network_name = models.CharField(max_length=50)  # e.g., "Polygon Mumbai 1"
    explorer_url = models.URLField(max_length=500, null=True, blank=True)  # Link to transaction explorer

    def __str__(self):
        return f"Withdrawal {self.data} - {self.status}"
