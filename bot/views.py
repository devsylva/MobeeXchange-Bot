from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
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
from .mobee_utils import createFiatDeposit
from threading import Lock
import requests

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

# Global variable to hold the Application instance (initialized lazily)
application = None

application_lock = Lock()

async def initialize_application():
    global application
    with application_lock:
        if application is None:
            logger.info("Initializing Telegram Application")
            application = Application.builder().bot(bot).build()
            application.add_handler(CommandHandler("start", start))
            application.add_handler(CallbackQueryHandler(handle_callback))
            application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_amount_input))
            await application.initialize()
            logger.info("Telegram Application initialized")
    return application

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

async def register_user(update: Update):
    """Register or update user."""
    try:
        user = update.effective_user
        from .utils import create_or_update_user
        return await create_or_update_user(
            user.id,
            user.username,
            user.first_name,
            user.last_name
        )
    except Exception as e:
        logger.error(f"Error in register_user: {str(e)}", exc_info=True)
        raise

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
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

async def handle_amount_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user input for deposit amount."""
    try:
        telegram_user = await register_user(update)
        amount_text = update.message.text.strip()

        # Validate amount
        try:
            amount = int(amount_text)
            if amount <= 0 or amount < 10000:
                raise ValueError("Amount must be positive and greater than or equal to 10000")
        except ValueError:
            await update.message.reply_text(
                "⚠️ Please enter a valid positive number greater than or equal to 10,000 for the deposit amount.",
                parse_mode='Markdown',
                reply_markup=get_deposit_menu()
            )
            return

        # Retrieve deposit method from user_data
        deposit_method = context.user_data.get('deposit_method')
        if not deposit_method:
            await update.message.reply_text(
                "⚠️ Session expired. Please select a deposit method again.",
                parse_mode='Markdown',
                reply_markup=get_deposit_menu()
            )
            return

        # For IDR (fiat) deposits, call Mobee API
        if deposit_method == "IDR":
            await update.message.reply_text(
                "Processing your fiat deposit...",
                parse_mode='Markdown'
            )
            
            bank_code = "BNI"  # Confirm this is a valid bank code
            try:
                response = await createFiatDeposit(amount, bank_code)
                try:
                    response_data = response.json()
                    if response.status_code in (200, 201):
                        text = (
                            f"✅ *Fiat Deposit Initiated*\n\n"
                            f"Amount: IDR {amount:,.2f}\n"
                            f"Bank Code: {bank_code}\n"
                            f"Transaction ID: {response_data.get('transaction_id', 'N/A')}\n\n"
                            "You'll receive a confirmation once processed."
                        )
                    else:
                        text = (
                            f"❌ *Deposit Failed*\n\n"
                            f"Error: {response_data.get('message', response.text)}\n"
                            "Please try again or contact support."
                        )
                except ValueError:
                    text = (
                        f"❌ *Deposit Failed*\n\n"
                        f"Error: Unable to parse response from server\n"
                        "Please try again or contact support."
                    )
            except requests.RequestException as e:
                text = (
                    f"❌ *Deposit Failed*\n\n"
                    f"Error: {str(e)}\n"
                    "Please try again or contact support."
                )

            keyboard = [
                [InlineKeyboardButton("↩️ Back to Deposit Options", callback_data="deposit")],
                [InlineKeyboardButton("📞 Contact Support", callback_data="support")]
            ]
            
            await update.message.reply_text(
                text,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await update.message.reply_text(
                f"⚠️ Deposit method {deposit_method} is not supported at this time.",
                parse_mode='Markdown',
                reply_markup=get_deposit_menu()
            )

        # Clear deposit state
        context.user_data.pop('deposit_method', None)

    except Exception as e:
        logger.error(f"Error handling amount input: {str(e)}", exc_info=True)
        await update.message.reply_text(
            "Sorry, there was an error processing your deposit. Please try again.",
            parse_mode='Markdown',
            reply_markup=get_main_menu()
        )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle callback queries from inline keyboard."""
    query = update.callback_query
    
    try:
        await query.answer()
        logger.info(f"Processing callback: {query.data}")

        telegram_user = await register_user(update)

        if query.data == "balance":
            from .utils import get_user_balance
            balance = await get_user_balance(telegram_user)
            text = f"💰 *Your Current Balance*\n\nAvailable: ${balance:.2f} USDT"
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
            currency = query.data.split('_')[1]
            context.user_data['deposit_method'] = currency
            await query.message.edit_text(
                f"💸 *Enter Deposit Amount*\n\nPlease type the amount you want to deposit in {currency}:",
                parse_mode='Markdown'
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

        elif query.data == "history":
            try:
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

    except Exception as e:
        logger.error(f"Error in callback handler: {str(e)}", exc_info=True)
        try:
            await query.message.edit_text(
                "Sorry, an error occurred. Please try again.",
                parse_mode='Markdown',
                reply_markup=get_main_menu()
            )
        except Exception:
            pass

@csrf_exempt
@async_handler
async def telegram_webhook(request):
    if request.method != 'POST':
        return HttpResponse('Only POST requests are allowed', status=405)
    
    try:
        logger.info("Received webhook request")
        update_data = json.loads(request.body.decode('utf-8'))
        update = Update.de_json(update_data, bot)
        
        # Initialize application if not already done
        await initialize_application()
        
        async with asyncio.timeout(30):
            await application.process_update(update)
            
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