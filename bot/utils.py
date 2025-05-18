from asgiref.sync import sync_to_async
from bot.models import TelegramUser, DepositRequest
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
def create_deposit_request(telegram_user, deposit_id, transaction_id, amount, account_name, account_number, bank_code, expired_at):
    """Async wrapper for creating deposit request"""
    try:
        deposit_request = DepositRequest(
            user=user,
            deposit_id=deposit_id,
            transaction_id=transaction_id,
            amount=amount,
            account_name=account_name,
            account_number=account_number,
            bank_code=bank_code,
            expired_at=expired_at
        )
        deposit_request.save()
        return deposit_request
    except Exception as e:
        logger.error(f"Database error in create_deposit_request: {str(e)}", exc_info=True)
        raise