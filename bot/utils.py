from asgiref.sync import sync_to_async
from bot.models import CryptoAddress, Transaction, FAQ, TelegramUser
from .views import logger

@sync_to_async
def getDepositAddress(currency):
    try:
        address = CryptoAddress.objects.get(currency=currency, is_active=True)
        
        if address:
            return {
                'address': address.address,
                'memo': address.memo,
                'network': address.network
            }
        else:
            return None
    except CryptoAddress.DoesNotExist:
        return None


@sync_to_async
def getTransactionhistory(user, limit=10):
    return Transaction.objects.filter(user=user).order_by('-created_at')[:limit]


# @sync_to_async
# def getFaqCategories():
#     """Get all active FAQ categories"""
#     return FAQ.objects.filter(
#         is_active=True
#     ).values('category').distinct()

# @sync_to_async
# def getCategoryFaqs(category):
#     """Get all FAQs for a category"""
#     return FAQ.objects.filter(
#         category=category,
#         is_active=True
#     ).order_by('order')

@sync_to_async
def create_transaction(user, amount, transaction_type, status='pending', wallet_address=None, currency='USDT'):
    """Create a new transaction record"""
    try:
        transaction = Transaction.objects.create(
            user=user,
            amount=amount,
            transaction_type=transaction_type,
            status=status,
            wallet_address=wallet_address,
            currency=currency
        )
        return transaction
    except Exception as e:
        logger.error(f"Error creating transaction: {str(e)}", exc_info=True)
        raise

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
