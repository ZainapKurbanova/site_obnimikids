import os
import json
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from telegram import Update
from telegram.ext import Application
from telegram_bot.handlers import setup_handlers

logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
application = Application.builder().token(BOT_TOKEN).build()
setup_handlers(application)

# Флаг, чтобы инициализировать только один раз
application_ready = False

@csrf_exempt
async def telegram_webhook(request):
    global application_ready

    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))
            update = Update.de_json(data, application.bot)

            # Однократная инициализация и запуск
            if not application_ready:
                await application.initialize()
                await application.start()
                application_ready = True

            await application.update_queue.put(update)
            return JsonResponse({"ok": True})
        except Exception as e:
            logger.exception("Ошибка в webhook:")
            return JsonResponse({"ok": False, "error": str(e)}, status=400)

    return JsonResponse({"ok": True})
