from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import DepositRequest, TelegramUser
from django.conf import settings
from telegram import Bot
import asyncio

@receiver(post_save, sender=DepositRequest)
def update_user_balance(sender, instance, **kwargs):
    # Check if the status is "completed"
    if instance.status == "completed":
        # Get the associated TelegramUser
        user = instance.user
        # Update the user's balance
        user.balance += instance.converted_amount
        # Save the updated user instance
        user.save()

        bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
        message = (
            f"✅ *Conversion Successful!*\n\n"
            f"Conversion Rate: {instance.conversion_rate}/IDR\n"
            f"Your deposit of {instance.amount} has been successfully converted.\n"
            f"Your new balance is: {user.balance}."
        )
        async def send_message():
            await bot.send_message(
                chat_id=user.telegram_id,  # Assuming TelegramUser has a `telegram_id` field
                text=message,
                parse_mode="Markdown"
            )

        # Run the coroutine
        asyncio.run(send_message())