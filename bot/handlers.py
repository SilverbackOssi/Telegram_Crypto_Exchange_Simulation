from telegram import Update
from telegram.ext import CallbackContext, CommandHandler, MessageHandler, filters
from wallet.services import get_user_transactions, execute_crypto_swap
from wallet.utils import get_user_wallet
from exchange.utils import get_price_data

class TelegramBotHandlers:
    @staticmethod
    def start(update: Update, context: CallbackContext):
        """Handle /start command"""
        user = update.effective_user
        # Create or get user wallet
        wallet = get_user_wallet(str(user.id))
        update.message.reply_text(f"Welcome {user.first_name}! Your wallet is ready.")

    @staticmethod
    def balance(update: Update, context: CallbackContext):
        """Show user's wallet balance"""
        user = update.effective_user
        wallet = get_user_wallet(str(user.id))
        
        balance_text = "\n".join([
            f"{currency}: {balance}" 
            for currency, balance in wallet.balance.items()
        ]) or "No balance available."
        
        update.message.reply_text(f"Your current balances:\n{balance_text}")

    @staticmethod
    def transactions(update: Update, context: CallbackContext):
        """Show user's recent transactions"""
        user = update.effective_user
        transactions = get_user_transactions(str(user.id), limit=5)
        
        if not transactions:
            update.message.reply_text("No transactions found.")
            return

        transaction_text = "\n\n".join([
            f"Type: {t.transaction_type}\n"
            f"Amount: {t.amount} {t.base_currency}\n"
            f"Time: {t.timestamp}"
            for t in transactions
        ])
        
        update.message.reply_text(f"Your recent transactions:\n{transaction_text}")

    @staticmethod
    def swap_currency(update: Update, context: CallbackContext):
        """Handle currency swap"""
        user = update.effective_user
        
        try:
            # Expecting format: /swap 0.5 BTC ETH
            amount = float(context.args[0])
            from_currency = context.args[1].upper()
            to_currency = context.args[2].upper()

            # Get current price data
            price_data = get_price_data()

            # Execute swap
            result = execute_crypto_swap(
                user_id=str(user.id),
                from_currency=from_currency,
                to_currency=to_currency,
                from_amount=amount,
                price_data=price_data
            )

            if result.success:
                update.message.reply_text(
                    f"Successfully swapped {amount} {from_currency} to {to_currency}\n"
                    f"Transaction ID: {result.transaction_record.id}"
                )
            else:
                update.message.reply_text(f"Swap failed: {result.message}")

        except (IndexError, ValueError):
            update.message.reply_text("Usage: /swap <amount> <from_currency> <to_currency>")

def setup_handlers(application):
    """Register all bot command handlers"""
    application.add_handler(CommandHandler('start', TelegramBotHandlers.start))
    application.add_handler(CommandHandler('balance', TelegramBotHandlers.balance))
    application.add_handler(CommandHandler('transactions', TelegramBotHandlers.transactions))
    application.add_handler(CommandHandler('swap', TelegramBotHandlers.swap_currency))