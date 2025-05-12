from asgiref.sync import sync_to_async
from core.models import CryptoAddress, Transaction, FAQ


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


@sync_to_async
def getFaqCategories():
    """Get all active FAQ categories"""
    return FAQ.objects.filter(
        is_active=True
    ).values('category').distinct()

@sync_to_async
def getCategoryFaqs(category):
    """Get all FAQs for a category"""
    return FAQ.objects.filter(
        category=category,
        is_active=True
    ).order_by('order')

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