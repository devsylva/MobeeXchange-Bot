from asgiref.sync import sync_to_async
from bot.models import TelegramUser, ActionToken
from uuid import uuid4
from django.utils.timezone import now
from datetime import timedelta
from bot.models import ActionToken
import logging  

loggger = logging.getLogger(__name__)

@sync_to_async
def create_or_update_user(user_id, username, first_name, last_name):
    """Async wrapper for database operations"""
    try:
        telegram_user, created = TelegramUser.objects.get_or_create(
            telegram_id=user_id,
            defaults={
                'username': username,
                'first_name': first_name,
                'last_name': last_name
            }
        )
        if not created:
            telegram_user.username = username
            telegram_user.first_name = first_name
            telegram_user.last_name = last_name
            telegram_user.save()
        return telegram_user
    except Exception as e:
        logger.error(f"Database error in create_or_update_user: {str(e)}", exc_info=True)
        raise


@sync_to_async
def get_user_balance(telegram_user):
    """Async wrapper for getting user balance"""
    try:
        telegram_user.refresh_from_db()
        return telegram_user.balance
    except Exception as e:
        logger.error(f"Error getting user balance: {str(e)}", exc_info=True)
        raise

@sync_to_async
def generate_action_token(user, action, expiration_minutes=5):
    """
    Generate a one-time token for a specific action (withdrawal or deposit).
    
    Args:
        user (TelegramUser): The user for whom the token is generated.
        action (str): The action type ('withdrawal' or 'deposit').
        expiration_minutes (int): Token expiration time in minutes.
    
    Returns:
        str: The generated token.
    """
    token = str(uuid4())
    ActionToken.objects.create(
        user=user,
        token=token,
        action=action,
    )
    return token


def is_tokenValid(token, action):
    """Validate a one-time token for a specific action."""
    try:
        action_token = ActionToken.objects.get(token=token, action=action)
        if action_token.is_valid():
            return True
        return False
    except ActionToken.DoesNotExist:
        return False