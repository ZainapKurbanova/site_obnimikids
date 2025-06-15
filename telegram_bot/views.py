import logging
import os
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from telegram import Update
from telegram.ext import Application
from telegram_bot.handlers import setup_handlers
import json

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
application = Application.builder().token(BOT_TOKEN).build()
setup_handlers(application)

logger = logging.getLogger(__name__)

@csrf_exempt
async def telegram_webhook(request):
    if request.method == "POST":
        try:
            data = request.body.decode("utf-8")
            update = Update.de_json(json.loads(data), application.bot)
            await application.initialize()
            await application.process_update(update)
            return JsonResponse({"ok": True})
        except Exception as e:
            logger.exception("Ошибка в webhook:")
            return JsonResponse({"ok": False, "error": str(e)}, status=400)
    return JsonResponse({"ok": True})
