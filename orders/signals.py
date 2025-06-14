import logging
from django.core.management.base import BaseCommand
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
from telegram_bot.models import TelegramUser
from orders.models import Order
from django.conf import settings

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

ADMINS = [509241742]
admin_reply_sessions = {}

def main_menu():
    return ReplyKeyboardMarkup([
        [KeyboardButton("❓ Задать вопрос"), KeyboardButton("📦 Статус заказа")]
    ], resize_keyboard=True)

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.effective_chat.id
    start_payload = context.args[0] if context.args else ''

    TelegramUser.objects.get_or_create(
        chat_id=chat_id,
        defaults={
            "first_name": user.first_name,
            "last_name": user.last_name,
            "username": user.username,
        }
    )

    if start_payload.startswith("order_"):
        order_id = start_payload.split("_")[1]
        try:
            order = Order.objects.get(id=order_id)
            order.tg_chat_id = chat_id
            order.save(update_fields=['tg_chat_id'])

            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton("Да, оплатить", callback_data=f"pay_{order_id}"),
                InlineKeyboardButton("Нет", callback_data="cancel_order")
            ]])

            await context.bot.send_message(
                chat_id=chat_id,
                text=f"Ваш заказ №{order.id} успешно создан!\n\n"
                     f"Товар: {order.items.first().product.name} × {order.items.first().quantity}\n"
                     f"Адрес доставки: {order.city}, {order.address_detail}\n"
                     f"Доставка: {order.delivery_cost} ₽\n"
                     f"Сумма: {order.total_price} ₽\n"
                     f"Итого: {order.get_total_with_delivery()} ₽\n\n"
                     f"Всё ли корректно?",
                reply_markup=keyboard
            )

        except Order.DoesNotExist:
            await context.bot.send_message(chat_id=chat_id, text="❌ Заказ не найден.")

    await context.bot.send_message(
        chat_id=chat_id,
        text="📍 Используйте меню ниже для работы с ботом:",
        reply_markup=main_menu()
    )

async def handle_pay_request(context, chat_id, order_id):
    try:
        order = Order.objects.get(id=order_id)
        order.status = 'pending'
        order.save(update_fields=['status'])

        for admin_id in ADMINS:
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton("✉️ Ответить клиенту", callback_data=f"reply_to_{chat_id}"),
                InlineKeyboardButton("✅ Пометить как оплачено", callback_data=f"mark_paid_{chat_id}")
            ]])
            await context.bot.send_message(
                chat_id=admin_id,
                text=(f"💳 Новый запрос на оплату заказа №{order.id} от @{order.user.username or 'Без имени'} "
                      f"(chat_id: {chat_id}).\n\n💬 Скоро пришлю ссылку на оплату."),
                reply_markup=keyboard
            )

        await context.bot.send_message(chat_id=chat_id, text="💬 Скоро пришлю ссылку на оплату.")

    except Order.DoesNotExist:
        await context.bot.send_message(chat_id=chat_id, text="❌ Заказ не найден.")

async def callback_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    chat_id = query.message.chat.id
    await query.answer()

    if data.startswith("pay_"):
        order_id = data.split("_")[1]
        await handle_pay_request(context, chat_id, order_id)

    elif data.startswith("reply_to_"):
        client_chat_id = data.split("_")[-1]
        admin_reply_sessions[chat_id] = client_chat_id
        await context.bot.send_message(chat_id=chat_id, text="✍ Введите сообщение. Оно будет отправлено клиенту.")

    elif data.startswith("mark_paid_"):
        client_chat_id = data.split("_")[-1]
        try:
            order = Order.objects.filter(tg_chat_id=client_chat_id).latest('created_at')
            order.status = 'paid'
            order.save(update_fields=['status'])
            await context.bot.send_message(chat_id=client_chat_id, text="✅ Спасибо за оплату!")
            await context.bot.send_message(chat_id=chat_id, text="Статус заказа обновлён как 'Оплачено'.")
        except Order.DoesNotExist:
            await context.bot.send_message(chat_id=chat_id, text="❌ Заказ не найден.")

    elif data == "cancel_order":
        await context.bot.send_message(chat_id=chat_id, text="❌ Заказ отменён. Свяжитесь с нами для изменений.")

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    text = update.message.text

    if text == "❓ Задать вопрос":
        await context.bot.send_message(chat_id=chat_id, text="✍ Напишите ваш вопрос.")
        context.user_data["awaiting_question"] = True
    elif text == "📦 Статус заказа":
        await context.bot.send_message(chat_id=chat_id, text="📮 Укажите номер заказа.")
        context.user_data["awaiting_order_id"] = True
    elif context.user_data.get("awaiting_question"):
        for admin_id in ADMINS:
            await context.bot.send_message(chat_id=admin_id, text=f"📩 Вопрос от клиента {chat_id}:\n{text}")
        await context.bot.send_message(chat_id=chat_id, text="✅ Вопрос отправлен. Ждите ответа.")
        context.user_data["awaiting_question"] = False
    elif context.user_data.get("awaiting_order_id"):
        for admin_id in ADMINS:
            await context.bot.send_message(chat_id=admin_id, text=f"📦 Запрос статуса от {chat_id}: {text}")
        await context.bot.send_message(chat_id=chat_id, text="✅ Запрос принят. Мы проверим и ответим.")
        context.user_data["awaiting_order_id"] = False
    elif chat_id in admin_reply_sessions:
        target_chat_id = admin_reply_sessions.pop(chat_id)
        await context.bot.send_message(chat_id=target_chat_id, text=f"📨 Админ:\n{text}")
        await context.bot.send_message(chat_id=chat_id, text="✅ Ответ отправлен.")
    else:
        for admin_id in ADMINS:
            await context.bot.send_message(chat_id=admin_id, text=f"📩 Сообщение от {chat_id}:\n{text}")
        await context.bot.send_message(chat_id=chat_id, text="✅ Мы скоро свяжемся с вами.")

async def media_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    message = update.message

    if message.photo or message.document:
        for admin_id in ADMINS:
            await context.bot.forward_message(chat_id=admin_id, from_chat_id=chat_id, message_id=message.message_id)
            await context.bot.send_message(chat_id=admin_id, text=f"🛉 Чек от клиента {chat_id}")

class Command(BaseCommand):
    help = 'Запуск Telegram-бота'

    def handle(self, *args, **options):
        application = ApplicationBuilder().token(settings.TELEGRAM_BOT_TOKEN).build()

        application.add_handler(CommandHandler("start", start_handler))
        application.add_handler(CallbackQueryHandler(callback_query_handler))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
        application.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, media_handler))

        self.stdout.write("✅ Telegram-бот запущен…")
        application.run_polling()
