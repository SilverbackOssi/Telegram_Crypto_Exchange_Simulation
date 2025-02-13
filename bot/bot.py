from telegram.ext import Application
from .handlers import setup_handlers
from django.conf import settings


def initialize_bot():
    """Initialize Telegram Bot Application"""
    application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()

    # Setup command handlers
    setup_handlers(application)

    return application


# Start bot in a separate thread or process
bot = initialize_bot()
