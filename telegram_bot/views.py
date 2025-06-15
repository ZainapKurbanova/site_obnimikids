import logging
import os
import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from telegram import Update
from telegram.ext import Application
from telegram_bot.handlers import setup_handlers

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
application = Application.builder().token(BOT_TOKEN).build()
setup_handlers(application)

# Запускаем application (в фоне)
import asyncio
asyncio.get_event_loop().create_task(application.initialize())
asyncio.get_event_loop().create_task(application.start())

logger = logging.getLogger(__name__)

@csrf_exempt
async def telegram_webhook(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))
            update = Update.de_json(data, application.bot)
            await application.update_queue.put(update)  # безопасно добавляем обновление в очередь
            return JsonResponse({"ok": True})
        except Exception as e:
            logger.exception("Ошибка в webhook:")
            return JsonResponse({"ok": False, "error": str(e)}, status=400)
    return JsonResponse({"ok": True})
