from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import DepositRequest, TelegramUser

@receiver(post_save, sender=DepositRequest)
def update_user_balance(sender, instance, **kwargs):
    # Check if the status is "completed"
    if instance.status == "completed":
        # Get the associated TelegramUser
        user = instance.user
        # Update the user's balance
        user.balance += instance.amount
        # Save the updated user instance
        user.save()