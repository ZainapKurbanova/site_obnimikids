import logging
from django.core.management.base import BaseCommand
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove
)
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackContext,
    MessageHandler,
    Filters,
    CallbackQueryHandler
)
from telegram_bot.models import TelegramUser
from orders.models import Order
from django.conf import settings

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

ADMINS = [509241742]  # Укажи свои реальные chat_id
admin_reply_sessions = {}

# Главное меню для пользователей
def main_menu():
    return ReplyKeyboardMarkup([
        [KeyboardButton("❓ Задать вопрос"), KeyboardButton("📦 Статус заказа")]
    ], resize_keyboard=True)

def start_handler(update: Update, context: CallbackContext):
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

            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("Да, оплатить", callback_data=f"pay_{order_id}"),
                 InlineKeyboardButton("Нет", callback_data="cancel_order")]
            ])

            context.bot.send_message(
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
            context.bot.send_message(chat_id=chat_id, text="❌ Заказ не найден.")

    # Меню ВСЕГДА отправляется после приветствия
    context.bot.send_message(
        chat_id=chat_id,
        text="📍 Используйте меню ниже для работы с ботом:",
        reply_markup=main_menu()
    )

def handle_pay_request(update, context, chat_id, order_id, ADMINS):
    try:
        order = Order.objects.get(id=order_id)
        order.status = 'pending'
        order.save(update_fields=['status'])

        for admin_id in ADMINS:
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("✉️ Ответить клиенту", callback_data=f"reply_to_{chat_id}")],
                [InlineKeyboardButton("✅ Пометить как оплачено", callback_data=f"mark_paid_{chat_id}")]
            ])
            context.bot.send_message(
                chat_id=admin_id,
                text=(
                    f"💳 Новый запрос на оплату заказа №{order.id} от @{order.user.username or 'Без имени'} "
                    f"(chat_id: {chat_id}).\n\n💬 Скоро пришлю ссылку на оплату. Пожалуйста, ожидайте."
                ),
                reply_markup=keyboard
            )

        context.bot.send_message(
            chat_id=chat_id,
            text="💬 Скоро пришлю ссылку на оплату. Пожалуйста, ожидайте."
        )

    except Order.DoesNotExist:
        context.bot.send_message(chat_id=chat_id, text="❌ Заказ не найден.")

def callback_query_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data
    chat_id = query.message.chat.id
    query.answer()

    if data.startswith("pay_"):
        order_id = data.split("_")[1]
        handle_pay_request(update, context, chat_id, order_id, ADMINS)

    elif data.startswith("reply_to_"):
        client_chat_id = data.split("_")[-1]
        admin_reply_sessions[chat_id] = client_chat_id
        context.bot.send_message(chat_id=chat_id, text="✍ Введите сообщение. Оно будет отправлено клиенту.")

    elif data.startswith("mark_paid_"):
        client_chat_id = data.split("_")[-1]
        try:
            order = Order.objects.filter(tg_chat_id=client_chat_id).latest('created_at')
            order.status = 'paid'
            order.save(update_fields=['status'])
            context.bot.send_message(chat_id=client_chat_id, text="✅ Спасибо за оплату! Мы скоро отправим ваш заказ.")
            context.bot.send_message(chat_id=chat_id, text="Статус заказа обновлён как 'Оплачено'.")
        except Order.DoesNotExist:
            context.bot.send_message(chat_id=chat_id, text="❌ Не удалось найти заказ для обновления.")

    elif data == "cancel_order":
        context.bot.send_message(chat_id=chat_id, text="❌ Заказ отменён. Вы можете связаться с нами, если хотите внести изменения.")

def text_handler(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    text = update.message.text

    # Переключение режимов без return
    if text == "❓ Задать вопрос":
        context.bot.send_message(chat_id=chat_id, text="✍ Напишите ваш вопрос, мы скоро ответим.")
        context.user_data["awaiting_question"] = True
    elif text == "📦 Статус заказа":
        context.bot.send_message(chat_id=chat_id, text="📮 Укажите номер заказа. Вы можете найти его в личном кабинете.")
        context.user_data["awaiting_order_id"] = True
    elif context.user_data.get("awaiting_question"):
        for admin_id in ADMINS:
            context.bot.send_message(chat_id=admin_id, text=f"📩 Вопрос от клиента (chat_id: {chat_id}):\n{text}")
        context.bot.send_message(chat_id=chat_id, text="✅ Ваш вопрос передан. Мы свяжемся с вами как можно скорее.")
        context.user_data["awaiting_question"] = False
    elif context.user_data.get("awaiting_order_id"):
        for admin_id in ADMINS:
            context.bot.send_message(chat_id=admin_id, text=f"📦 Запрос статуса заказа от chat_id {chat_id}:\nНомер заказа: {text}")
        context.bot.send_message(chat_id=chat_id, text="Ваш запрос получен. Мы скоро проверим статус.")
        context.user_data["awaiting_order_id"] = False
    elif chat_id in admin_reply_sessions:
        target_chat_id = admin_reply_sessions.pop(chat_id)
        context.bot.send_message(chat_id=target_chat_id, text=f"📨 Администратор:\n{text}")
        context.bot.send_message(chat_id=chat_id, text="✅ Сообщение отправлено клиенту.")
    else:
        for admin_id in ADMINS:
            context.bot.send_message(chat_id=admin_id, text=f"📩 Сообщение от клиента (chat_id: {chat_id}):\n{text}")
        context.bot.send_message(chat_id=chat_id, text="Ваше сообщение получено. Мы ответим в ближайшее время.")

def media_handler(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    message = update.message

    if message.photo or message.document:
        for admin_id in ADMINS:
            context.bot.forward_message(chat_id=admin_id, from_chat_id=chat_id, message_id=message.message_id)
            context.bot.send_message(chat_id=admin_id, text=f"🛉 Чек от клиента (chat_id: {chat_id})")

def help_handler(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    context.bot.send_message(chat_id=chat_id, text="Напишите свой вопрос или воспользуйтесь кнопками ниже.", reply_markup=main_menu())

class Command(BaseCommand):
    help = 'Запуск Telegram-бота'

    def handle(self, *args, **options):
        updater = Updater(token=settings.TELEGRAM_BOT_TOKEN, use_context=True)
        dispatcher = updater.dispatcher

        dispatcher.add_handler(CommandHandler("start", start_handler))
        dispatcher.add_handler(CommandHandler("help", help_handler))
        dispatcher.add_handler(CallbackQueryHandler(callback_query_handler))
        dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, text_handler))
        dispatcher.add_handler(MessageHandler(Filters.photo | Filters.document, media_handler))

        self.stdout.write("Telegram-бот запущен…")
        updater.start_polling()
        updater.idle()