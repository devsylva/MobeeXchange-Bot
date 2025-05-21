# MobeeXchange-Bot

A Telegram bot built with Python, Django, and the `python-telegram-bot` library to facilitate fiat-to-crypto conversions, specifically Indonesian Rupiah (IDR) to USDT. This project showcases a robust, asynchronous architecture with secure transaction handling and seamless integration with an external API for deposits.

---

## Features

- **Fiat-to-Crypto Conversion**: Convert IDR to USDT via a user-friendly Telegram bot interface.
- **Main Menu Commands**:
  - `/start`: Initializes the bot with a welcome message and main menu.
  - `/balance`: Displays the user’s current USDT balance.
  - `/deposit`: Initiates a fiat deposit process (minimum 50,000 IDR).
  - `/withdrawal`: Initiates a crypto withdrawal process (minimum 2.5 USDT, includes 1.5 USDT network fee).
  - `/history`: Shows the last 5 deposit and withdrawal transactions.
  - `/support`: Provides a link to contact support via Telegram.
  - `/main_menu`: Returns to the main menu.
- **Inline Keyboard Navigation**: Options for "Get Balance," "Deposit," "Withdraw," "Deposit History," "Withdraw History," and "Support" via an inline keyboard.
- **Secure Transactions**: Uses Django’s `transaction.atomic()` and `select_for_update()` to ensure atomic balance updates, preventing race conditions.
- **Token-Based Security**: Generates one-time tokens for deposit and withdrawal actions to secure API calls.
- **Asynchronous Processing**: Leverages `asyncio` and `sync_to_async` for non-blocking operations, ensuring scalability.
- **External API Integration**: Auto-generates deposit account details via an external API (Mobee) with HMAC SHA256 authentication.
- **Error Handling**: Robust logging and user-friendly error messages for invalid inputs or API failures.

---

## Architecture

- **Backend**: Django handles user management, database operations, and API integrations. Models include:
  - `TelegramUser`
  - `DepositRequest`
  - `WithdrawalRequest`
  - `ActionToken` (for secure transaction tracking)
- **Bot Framework**: Built with `python-telegram-bot` v20.0+, using a webhook for real-time Telegram updates.
- **Handlers**:
  - **Command Handlers**: `/start`, `/balance`, `/deposit`, `/withdrawal`, `/history`, `/support`, `/main_menu`.
  - **Callback Query Handler**: Processes inline keyboard interactions (e.g., deposit, withdrawal, history).
  - **Message Handler**: Captures user inputs for deposit amounts or wallet addresses.
- **Transaction Management**: Uses `transaction.atomic()` for atomic deposits/withdrawals and `select_for_update()` to lock user accounts during balance updates.
- **Security**:
  - HMAC SHA256 signatures for Mobee API authentication.
  - One-time tokens for deposit/withdrawal URLs to prevent unauthorized access.
  - CSRF-exempt webhook with JSON validation.
- **Timeouts and Pooling**: Configured with generous timeouts (30s) and a connection pool size of 20 for reliable API calls.

---

## Prerequisites

- **Python**: 3.8+
- **Django**: 4.0+
- **python-telegram-bot**: 20.0+
- **Telegram Bot Token**: Get one from [BotFather](https://core.telegram.org/bots#botfather).
- **Mobee API Access**: For fiat deposits.
- **Database**: PostgreSQL (or other Django-compatible DB).

---

