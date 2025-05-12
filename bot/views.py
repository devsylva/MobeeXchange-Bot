from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import Application, CommandHandler, CallbackContext, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from bot.models import TelegramUser
import json
from .keyboards import get_main_menu, get_deposit_menu
from django.http import HttpResponse
from asgiref.sync import sync_to_async
import logging
import asyncio
import sys
from telegram.request import HTTPXRequest
from functools import wraps

# Configure Windows event loop policy if needed
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Configure logging
logger = logging.getLogger(__name__)

# Configure request parameters with more generous timeouts
request_kwargs = {
    'connection_pool_size': 20,
    'connect_timeout': 30.0,
    'read_timeout': 30.0,
    'write_timeout': 30.0,
    'pool_timeout': 3.0,
}

# Initialize bot with custom connection pool settings
bot = Bot(
    token=settings.TELEGRAM_BOT_TOKEN,
    get_updates_request=HTTPXRequest(**request_kwargs),
    request=HTTPXRequest(**request_kwargs)
)

def async_handler(func):
    @wraps(func)
    def wrapped(request, *args, **kwargs):
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        try:
            return loop.run_until_complete(func(request, *args, **kwargs))
        except Exception as e:
            logger.error(f"Error in async handler: {str(e)}", exc_info=True)
            return HttpResponse("Internal Server Error", status=500)
    return wrapped

def landingPage(request):
    return render(request, 'landingpage.html')

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
def get_user_profit(telegram_user):
    """Async wrapper for getting user profit"""
    try:
        telegram_user.refresh_from_db()
        return telegram_user.profit
    except Exception as e:
        logger.error(f"Error getting user profit: {str(e)}", exc_info=True)
        raise

async def register_user(update: Update):
    """Register or update user"""
    try:
        user = update.effective_user
        return await create_or_update_user(
            user.id,
            user.username,
            user.first_name,
            user.last_name
        )
    except Exception as e:
        logger.error(f"Error in register_user: {str(e)}", exc_info=True)
        raise

async def start(update: Update):
    try:
        telegram_user = await register_user(update)
        logger.info(f"User started bot: {telegram_user.telegram_id}")

        welcome_text = (
            f"🌟 *Welcome to Mobee Exchange Trading Bot!* 🌟\n\n"
            f"Hello {update.effective_user.first_name}!\n\n"
            "🚀 *Your Gateway to Smart Exchange* 🚀\n\n"
            "Choose from the options below to:\n"
            "• Check your balance\n"
            "• Make deposits/withdrawals\n"
            "• View transaction history\n"
            "• Get support\n"
            "🔐 *Safe & Secure Exchange*\n"
            "📊 *Real-time Updates*\n"
            "💯 *24/7 Support*\n"
        )

        await update.message.reply_text(
            text=welcome_text,
            parse_mode='Markdown',
            reply_markup=get_main_menu()
        )
    except Exception as e:
        logger.error(f"Error in start command: {str(e)}", exc_info=True)
        await update.message.reply_text(
            "Sorry, there was an error. Please try again later.",
            parse_mode='Markdown'
        )

async def handle_callback(update: Update):
    """Handle callback queries from inline keyboard"""
    query = update.callback_query
    
    try:
        # Answer callback query immediately
        await query.answer()
        logger.info(f"Processing callback: {query.data}")

        # Get or register user
        telegram_user = await register_user(update)

        if query.data == "balance":
            balance = await get_user_balance(telegram_user)
            text = f"💰 *Your Current Balance*\n\nAvailable: ${balance:.2f} USDT"
            await query.message.edit_text(
                text,
                parse_mode='Markdown',
                reply_markup=get_main_menu()
            )

        elif query.data == "profit":
            profit = await get_user_profit(telegram_user)
            text = f"📈 *Your Total Profit*\n\nTotal: ${profit:.2f} USDT"
            await query.message.edit_text(
                text,
                parse_mode='Markdown',
                reply_markup=get_main_menu()
            )
        
        elif query.data == "deposit":
            text = "📥 *Deposit Methods*\n\nChoose your preferred deposit method:"
            await query.message.edit_text(
                text,
                parse_mode='Markdown',
                reply_markup=get_deposit_menu()
            )

        elif query.data == "main_menu":
            await query.message.edit_text(
                "Main Menu",
                parse_mode='Markdown',
                reply_markup=get_main_menu()
            )

        elif query.data.startswith('deposit_'):
            try:
                crypto = query.data.split('_')[1]
                # Show loading message while getting address
                await query.message.edit_text(
                    "Getting deposit address...",
                    parse_mode='Markdown'
                )
                
                from .utils import getDepositAddress
                address_info = await getDepositAddress(crypto)
                
                if address_info:
                    memo_text = f"\n📝 *Memo/Tag:* `{address_info['memo']}`" if address_info.get('memo') else ""
                    text = (
                        f"🏦 *Deposit {crypto}*\n\n"
                        f"💳 *Deposit Address:*\n`{address_info['address']}`"
                        f"{memo_text}\n\n"
                        f"🔄 *Network:* {address_info['network']}\n\n"
                        "⚠️ *Important Notes:*\n"
                        f"• Send only {crypto} to this address\n"
                        "• Deposits will be credited after confirmations\n"
                        "• Include memo/tag if provided\n\n"
                        "Need help? Contact support."
                    )
                    
                    keyboard = [
                        [InlineKeyboardButton("↩️ Back to Deposit Options", callback_data="deposit")],
                        [InlineKeyboardButton("📞 Contact Support", callback_data="support")]
                    ]
                    
                    await query.message.edit_text(
                        text,
                        parse_mode='Markdown',
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
                else:
                    await query.message.edit_text(
                        "Sorry, deposit address not available. Please contact support.",
                        parse_mode='Markdown',
                        reply_markup=get_main_menu()
                    )
            except Exception as e:
                logger.error(f"Error getting deposit address: {str(e)}", exc_info=True)
                await query.message.edit_text(
                    "Sorry, there was an error getting the deposit address. Please try again.",
                    parse_mode='Markdown',
                    reply_markup=get_main_menu()
                )

        

        elif query.data == "support":
            support_username = "@AlgoAceSupport"
            text = (
                "🛟 *Need Help?*\n\n"
                f"Contact our support team directly: {support_username}\n\n"
                "Please include:\n"
                "• Your issue description\n"
                "• Transaction ID (if applicable)\n"
                "• Screenshots (if relevant)\n\n"
                "Our team typically responds within 24 hours."
            )
            keyboard = [[InlineKeyboardButton("Contact Support", url=f"https://t.me/{support_username[1:]}")]]
            await query.message.edit_text(
                text,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

        elif query.data == "copy_trading":
            support_username = "@AlgoAceSupport"
            text = (
                "🛟 *Copy Trading Option?*\n\n"
                f"Contact our support team directly: {support_username}\n\n"
                "Our team typically responds within 24 hours."
            )
            keyboard = [[InlineKeyboardButton("Contact Support", url=f"https://t.me/{support_username[1:]}")]]
            await query.message.edit_text(
                text,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

        


        elif query.data == "history":
            try:
                # Show loading message
                await query.message.edit_text(
                    "Loading transaction history...",
                    parse_mode='Markdown'
                )
                
                from .utils import getTransactionhistory
                transactions = await getTransactionhistory(telegram_user)
                
                if not transactions:
                    await query.message.edit_text(
                        "No transaction history found.",
                        parse_mode='Markdown',
                        reply_markup=get_main_menu()
                    )
                    return

                text = "*📊 Recent Transactions:*\n\n"
                for tx in transactions[:10]:
                    status_emoji = {
                        'pending': '⏳',
                        'completed': '✅',
                        'failed': '❌',
                        'cancelled': '🚫'
                    }.get(tx.status, '❓')
                    
                    text += (
                        f"{status_emoji} *{tx.transaction_type.title()}*\n"
                        f"Amount: {tx.amount} {tx.currency}\n"
                        f"Status: {tx.status.title()}\n"
                        f"Date: {tx.created_at.strftime('%Y-%m-%d %H:%M')}\n\n"
                    )
                
                keyboard = [
                    [InlineKeyboardButton("↩️ Back to Menu", callback_data="main_menu")]
                ]
                
                await query.message.edit_text(
                    text,
                    parse_mode='Markdown',
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            except Exception as e:
                logger.error(f"Error getting transaction history: {str(e)}", exc_info=True)
                await query.message.edit_text(
                    "Sorry, there was an error fetching your transaction history. Please try again.",
                    parse_mode='Markdown',
                    reply_markup=get_main_menu()
                )

        elif query.data == "faq":
            try:
                await query.message.edit_text(
                    "Loading FAQ categories...",
                    parse_mode='Markdown'
                )
                
                from .utils import getFaqCategories
                categories = await getFaqCategories()
                
                text = "*❓ Frequently Asked Questions*\n\nSelect a category:"
                keyboard = []
                
                for category in categories:
                    keyboard.append([InlineKeyboardButton(
                        category['category'].title(),
                        callback_data=f"faq_{category['category']}"
                    )])
                
                keyboard.append([InlineKeyboardButton("↩️ Back to Menu", callback_data="main_menu")])
                
                await query.message.edit_text(
                    text,
                    parse_mode='Markdown',
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            except Exception as e:
                logger.error(f"Error getting FAQ categories: {str(e)}", exc_info=True)
                await query.message.edit_text(
                    "Sorry, there was an error fetching the FAQ categories. Please try again.",
                    parse_mode='Markdown',
                    reply_markup=get_main_menu()
                )

        elif query.data.startswith("faq_"):
            try:
                category = query.data.split('_')[1]
                await query.message.edit_text(
                    f"Loading {category} FAQs...",
                    parse_mode='Markdown'
                )
                
                from .utils import getCategoryFaqs
                faqs = await getCategoryFaqs(category)
                
                text = f"*{category.title()} FAQ:*\n\n"
                for faq in faqs:
                    text += f"*Q: {faq.question}*\n"
                    text += f"A: {faq.answer}\n\n"
                
                keyboard = [
                    [InlineKeyboardButton("↩️ Back to FAQ", callback_data="faq")],
                    [InlineKeyboardButton("📞 Contact Support", callback_data="support")]
                ]
                
                await query.message.edit_text(
                    text,
                    parse_mode='Markdown',
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            except Exception as e:
                logger.error(f"Error getting FAQs for category {category}: {str(e)}", exc_info=True)
                await query.message.edit_text(
                    "Sorry, there was an error fetching the FAQs. Please try again.",
                    parse_mode='Markdown',
                    reply_markup=get_main_menu()
                )

    except Exception as e:
        logger.error(f"Error in callback handler: {str(e)}", exc_info=True)
        try:
            await query.message.edit_text(
                "Sorry, an error occurred. Please try again.",
                parse_mode='Markdown',
                reply_markup=get_main_menu()
            )
        except Exception:
            pass  # If edit fails, we've already answered the callback query

@csrf_exempt
@async_handler
async def telegram_webhook(request):
    if request.method != 'POST':
        return HttpResponse('Only POST requests are allowed', status=405)
    
    try:
        logger.info("Received webhook request")
        update_data = json.loads(request.body.decode('utf-8'))
        update = Update.de_json(update_data, bot)
        
        async with asyncio.timeout(30):  # 30 seconds timeout
            if update.message and update.message.text == '/start':
                await start(update)
            elif update.callback_query:
                await handle_callback(update)
            
        return HttpResponse('OK')
    except asyncio.TimeoutError:
        logger.error("Request timed out")
        return HttpResponse('Request timed out', status=504)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in webhook request: {str(e)}")
        return HttpResponse('Invalid JSON', status=400)
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}", exc_info=True)
        return HttpResponse('Internal Server Error', status=500)