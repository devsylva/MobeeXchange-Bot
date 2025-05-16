from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_main_menu():
    keyboard = [
        [
            InlineKeyboardButton("💰 Check Balance", callback_data='balance'),
            InlineKeyboardButton("📥 Make Deposit", callback_data='deposit')
        ],
        [
            InlineKeyboardButton("📤  Withdrawal", callback_data='withdrawal'),
            InlineKeyboardButton("📊 History", callback_data='history')
        ],
        [InlineKeyboardButton("📞 Customer Support", callback_data='support')],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_deposit_menu():
    keyboard = [
        [
            InlineKeyboardButton("📥 deposit IDR 💰", callback_data="deposit_IDR"),
        ],
        [InlineKeyboardButton("↩️ Back to Menu", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_withdrawal_menu():
    keyboard = [
        [
            InlineKeyboardButton("📥 withdraw USDT 💰", callback_data="withdraw_USDT"),
        ],
        [InlineKeyboardButton("↩️ Back to Menu", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)