from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_main_menu():
    keyboard = [
        [
            InlineKeyboardButton("💰 Check Balance", callback_data='balance'),
            InlineKeyboardButton("📥 Make Deposit", callback_data='deposit')
        ],
        [
            InlineKeyboardButton("📤 Request Withdrawal", callback_data='withdrawal'),
            InlineKeyboardButton("📊 Transaction History", callback_data='history')
        ],
        [InlineKeyboardButton("📞 Customer Support", callback_data='support')],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_deposit_menu():
    keyboard = [
        [
            InlineKeyboardButton("Bitcoin (BTC)", callback_data="deposit_BTC"),
            InlineKeyboardButton("USDT", callback_data="deposit_USDT_TRC20")
        ],
        [
            InlineKeyboardButton("XRP", callback_data="deposit_XRP"),
            InlineKeyboardButton("Solana (SOL)", callback_data="deposit_SOL")
        ],
        [InlineKeyboardButton("↩️ Back to Menu", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)