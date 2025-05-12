from django.db import models

# Create your models here.
class TelegramUser(models.Model):
    telegram_id = models.IntegerField(default="0", unique=True, blank=True, null=True)
    username = models.CharField(max_length=50)
    first_name = models.CharField(max_length=50, null=True, blank=True)
    last_name = models.CharField(max_length=50, null=True, blank=True)
    balance = models.FloatField(default=0.0)
    profit = models.FloatField(default=0.0)
    referral_code = models.CharField(max_length=10)
    referred_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    def __str__(self):
        return f"{self.username} or {self.telegram_id}"

    def save(self, *args, **kwargs):
        if not self.referral_code:
            import random
            import string
            # Generate unique referral code
            while True:
                code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
                if not TelegramUser.objects.filter(referral_code=code).exists():
                    self.referral_code = code
                    break
        super().save(*args, **kwargs)


class CryptoAddress(models.Model):
    CURRENCY_CHOICES = [
        ('BTC', 'Bitcoin'),
        ('USDT_TRC20', 'USDT TRC20'),
        ('USDT_ERC20', 'USDT ERC20'),
        ('XRP', 'Ripple'),
        ('SOL', 'Solana'),
    ]

    NETWORK_CHOICES = [
        ('BITCOIN', 'Bitcoin'),
        ('TRC20', 'Tron TRC20'),
        ('ERC20', 'Ethereum ERC20'),
        ('XRP', 'Ripple'),
        ('SOLANA', 'Solana'),
    ]

    currency = models.CharField(max_length=20, choices=CURRENCY_CHOICES, unique=True)
    network = models.CharField(max_length=20, choices=NETWORK_CHOICES)
    address = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    memo = models.CharField(max_length=100, blank=True, null=True)  # For currencies that need memo/tag
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    class Meta:
        verbose_name = 'Crypto Address'
        verbose_name_plural = 'Crypto Addresses'

    def __str__(self):
        return f"{self.get_currency_display()} - {self.address[:10]}..."


class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('deposit', 'Deposit'),
        ('withdrawal', 'Withdrawal')
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled')
    ]

    user = models.ForeignKey(TelegramUser, on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    currency = models.CharField(max_length=20)
    amount = models.DecimalField(max_digits=18, decimal_places=8)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    address = models.CharField(max_length=255)  # For withdrawals
    tx_hash = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    def __str__(self):
        return f"{self.transaction_type} - {self.amount} {self.currency}"


# FAQ model for easy management
class FAQ(models.Model):
    CATEGORY_CHOICES = [
        ('general', 'General'),
        ('trading', 'Trading'),
        ('deposit', 'Deposits'),
        ('withdrawal', 'Withdrawals'),
        ('security', 'Security')
    ]

    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    question = models.CharField(max_length=255)
    answer = models.TextField()
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['category', 'order']

    def __str__(self):
        return f"{self.category}: {self.question}"