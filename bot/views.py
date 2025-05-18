from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from .keyboards import get_main_menu, get_deposit_menu, get_withdrawal_menu
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from asgiref.sync import sync_to_async
from telegram.request import HTTPXRequest
from .mobee_utils import createFiatDeposit
from django.conf import settings
from bot.models import TelegramUser, DepositRequest
from .utils import create_or_update_user, get_user_balance, create_deposit_request
import json
from threading import Lock
from functools import wraps
import requests
import logging
import asyncio
import sys

# Configure Windows event loop policy if needed
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Configure logging
logger = logging.getLogger(__name__)

IDR_DEPOSIT_MIN_AMOUNT = 10000
IDR_BANK_CODE = "BNI"

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
            application.add_handler(CallbackQueryHandler(view_payment_details, pattern='view_payment_details'))
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
    """Handle user input for deposit and withdraw amount."""
    try:
        telegram_user = await register_user(update)
        amount_text = update.message.text.strip()

        # Retrieve deposit or withdrawal method
        deposit_method = context.user_data.get('deposit_method')
        withdrawal_method = context.user_data.get('withdrawal_method')

        if not deposit_method and not withdrawal_method:
            await update.message.reply_text(
                "⚠️ Session expired. Please select a deposit or withdrawal method first.",
                parse_mode='Markdown',
                reply_markup=get_main_menu()
            )
            return

        if deposit_method:
            await process_deposit(update, context, amount_text, deposit_method)
        elif withdrawal_method:
            await process_withdrawal(update, context, amount_text, withdrawal_method)

    except Exception as e:
        # logger.error(f"Error in handle_amount_input: {str(e)}", exc_info=True)
        await update.message.reply_text(
            "Sorry, there was an error processing your request. Please try again.",
            parse_mode='Markdown',
            reply_markup=get_main_menu()
        )

async def view_payment_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the 'View Payment Details' button."""
    print("view_payment_details is called")
    query = update.callback_query
    await query.answer()

    telegram_user = await register_user(update)
    try:
        print("code is here")
        # Fetch the latest deposit request for the user
        deposit_request = await sync_to_async(
            lambda: DepositRequest.objects.filter(user=telegram_user).latest('created_at')
        )()
        # Display the payment details
        text = (
            f"✅ *Payment Details:*\n\n"
            f"• Amount: {deposit_request.amount}\n"
            f"• Bank: {deposit_request.bank_code}\n"
            f"• Account Name: {deposit_request.account_name}\n"
            f"• Account Number: {deposit_request.account_number}\n"
            f"• Expiry: {deposit_request.expired_at}\n\n"
            "Please make the payment before the expiry time."
        )
        await query.edit_message_text(text, parse_mode='Markdown')

    except DepositRequest.DoesNotExist:
        # Handle the case where the deposit instance is not found
        await query.edit_message_text(
            "⚠️ No payment details found. Please make sure you clicked the deposit link first.",
            parse_mode='Markdown'
        )
    except Exception as e:
        # Handle any other exceptions
        await query.edit_message_text(
            f"⚠️ An error occurred: {str(e)}",
            parse_mode='Markdown'
        )

async def process_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE, amount_text: str, deposit_method: str):
    """Process deposit logic."""
    telegram_user = await register_user(update)
    if deposit_method == "IDR":
        try:
            amount = int(amount_text)
            if amount < IDR_DEPOSIT_MIN_AMOUNT:
                # raise ValueError("Amount must be greater than or equal to 10,000")
                await update.message.reply_text(
                    f"⚠️ The minimum deposit amount is {IDR_DEPOSIT_MIN_AMOUNT} IDR.",
                    parse_mode='Markdown',
                    reply_markup=get_deposit_menu()
                )
                return
        except ValueError:
            await update.message.reply_text(
                "⚠️ Please enter a valid positive number",
                parse_mode='Markdown',
                reply_markup=get_deposit_menu()
            )
            return

        # Generate a link for for the user to complete deposit
        deposit_link = f"{settings.YOUR_DOMAIN}/create-deposit/{telegram_user.telegram_id}/{amount}/{deposit_method}"
        print(deposit_link)

        text = (
            f"✅ *Fiat Deposit Initiated*\n\n"
            f"Please click the link below to complete your deposit:\n\n"
            f"[Complete Deposit] (https://{deposit_link})\n\n"
            "⚠️ *Important:*\n"
            "1. Click the link above to initiate your deposit.\n"
            "2. After being redirected back, click the 'View Payment Details' button to see your payment details."
        )

        await update.message.reply_text(text, parse_mode='Markdown')

        # Add a button for "View Payment Details"
        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("View Payment Details", callback_data="view_payment_details")],
        ])
        await update.message.reply_text(
            "Click the button below after completing the deposit link:",
            reply_markup=reply_markup
        )

    context.user_data.pop('deposit_method', None)

async def process_withdrawal(update: Update, context: ContextTypes.DEFAULT_TYPE, amount_text: str, withdrawal_method: str):
    """Process withdrawal logic."""
    if withdrawal_method == "USDT":
        try:
            amount = float(amount_text)
            if amount <= 0:
                raise ValueError("Amount must be positive")
        except ValueError:
            await update.message.reply_text(
                "⚠️ Please enter a valid positive number for the withdrawal amount.",
                parse_mode='Markdown',
                reply_markup=get_withdrawal_menu()
            )
            return

        await update.message.reply_text("Processing your USDT withdrawal...", parse_mode='Markdown')

        # Handle USDT withdrawal logic here
        keyboard = [
            [InlineKeyboardButton("↩️ Back to Withdrawal Options", callback_data="withdrawal")],
            [InlineKeyboardButton("📞 Contact Support", callback_data="support")],
        ]
        await update.message.reply_text(
            "Withdrawal processing logic goes here.",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    context.user_data.pop('withdrawal_method', None)

    
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle callback queries from inline keyboard."""
    query = update.callback_query
    
    try:
        await query.answer()
        logger.info(f"Processing callback: {query.data}")

        telegram_user = await register_user(update)

        if query.data == "balance":
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

        elif query.data == "withdrawal":
            text = "📤 *Withdraw Methods*\n\nChoose your preferred withdrawal method:"
            await query.message.edit_text(
                text,
                parse_mode='Markdown',
                reply_markup=get_withdrawal_menu()
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

        elif query.data.startswith('withdraw_'):
            coin = query.data.split('_')[1]
            context.user_data['withdrawal_method'] = coin
            await query.message.edit_text(
                f"💸 *Enter Withdrawal Amount*\n\nPlease type the amount you want to withdraw in {coin}:",
                parse_mode='Markdown'
            )

        elif query.data == "support":
            text = (
                "🛟 *Need Help?*\n\n"
                f"Contact our support team directly: {support_username}\n\n"
                "Please include:\n"
                "• Your issue description\n"
                "• Transaction ID (if applicable)\n"
                "• Screenshots (if relevant)\n\n"
                "Our team typically responds within 24 hours."
            )
            keyboard = [[InlineKeyboardButton("Contact Support", url=f"https://t.me/+2F_2WCAvbQyMDhk")]]
            await query.message.edit_text(
                text,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

        # elif query.data == "history":
        #     try:
        #         await query.message.edit_text(
        #             "Loading transaction history...",
        #             parse_mode='Markdown'
        #         )
                
        #         from .utils import getTransactionhistory
        #         transactions = await getTransactionhistory(telegram_user)
                
        #         if not transactions:
        #             await query.message.edit_text(
        #                 "No transaction history found.",
        #                 parse_mode='Markdown',
        #                 reply_markup=get_main_menu()
        #             )
        #             return

        #         text = "*📊 Recent Transactions:*\n\n"
        #         for tx in transactions[:10]:
        #             status_emoji = {
        #                 'pending': '⏳',
        #                 'completed': '✅',
        #                 'failed': '❌',
        #                 'cancelled': '🚫'
        #             }.get(tx.status, '❓')
                    
        #             text += (
        #                 f"{status_emoji} *{tx.transaction_type.title()}*\n"
        #                 f"Amount: {tx.amount} {tx.currency}\n"
        #                 f"Status: {tx.status.title()}\n"
        #                 f"Date: {tx.created_at.strftime('%Y-%m-%d %H:%M')}\n\n"
        #             )
                
        #         keyboard = [
        #             [InlineKeyboardButton("↩️ Back to Menu", callback_data="main_menu")]
        #         ]
                
        #         await query.message.edit_text(
        #             text,
        #             parse_mode='Markdown',
        #             reply_markup=InlineKeyboardMarkup(keyboard)
        #         )
        #     except Exception as e:
        #         logger.error(f"Error getting transaction history: {str(e)}", exc_info=True)
        #         await query.message.edit_text(
        #             "Sorry, there was an error fetching your transaction history. Please try again.",
        #             parse_mode='Markdown',
        #             reply_markup=get_main_menu()
        #         )

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



def create_deposit_view(request, telegram_id, amount, bank_code):
    """Handle fiat deposit creation."""
    try:
        # Get the user from the database
        user = TelegramUser.objects.get(telegram_id=telegram_id)
        
        # Example: Hardcoded amount and bank code (replace with dynamic values if needed)
        amount = 100000  # Example amount
        bank_code = "BNI"
        
        # Call the createFiatDeposit function
        response_data = createFiatDeposit(amount, bank_code)
        
        # Save the deposit request in the database
        DepositRequest.objects.create(
            user=user,
            deposit_id=response_data['data']['id'],
            transaction_id=response_data['data']['transaction_id'],
            amount=response_data['data']['amount'],
            account_name=response_data['data']['account_name'],
            account_number=response_data['data']['account_number'],
            bank_code=response_data['data']['bank_code'],
            expired_at=response_data['data']['expired_at'],
            status="pending"
        )
        
        # Redirect the user back to the bot with a success message
        bot_redirect_url = f"https://t.me/{settings.TELEGRAM_BOT_USERNAME}"
        return redirect(bot_redirect_url)
    
    except TelegramUser.DoesNotExist:
        return HttpResponse("User not found", status=404)
    except Exception as e:
        return HttpResponse(f"Error: {str(e)}", status=500)


