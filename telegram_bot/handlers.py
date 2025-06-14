from telegram.ext import CommandHandler, MessageHandler, CallbackQueryHandler, filters
from telegram_bot.views import (
    start_handler,
    callback_query_handler,
    text_handler,
    media_handler,
)

def setup_handlers(application):
    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(CallbackQueryHandler(callback_query_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    application.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, media_handler))
