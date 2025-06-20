import logging
from telegram import (
    Update, InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton
)
from telegram.ext import ContextTypes
from asgiref.sync import sync_to_async

from telegram_bot.models import TelegramUser
from orders.models import Order

logger = logging.getLogger(__name__)

ADMINS = [509241742]
admin_reply_sessions = {}


# Главное меню
def main_menu():
    return ReplyKeyboardMarkup([
        [KeyboardButton("❓ Задать вопрос"), KeyboardButton("📦 Статус заказа")]
    ], resize_keyboard=True)


@sync_to_async
def create_or_get_user(chat_id, first_name, last_name, username):
    return TelegramUser.objects.get_or_create(
        chat_id=chat_id,
        defaults={
            "first_name": first_name,
            "last_name": last_name,
            "username": username,
        }
    )


@sync_to_async
def get_order_with_items(order_id):
    return Order.objects.select_related('user').prefetch_related('items__product').get(id=order_id)


@sync_to_async
def save_order_chat_id(order, chat_id):
    order.tg_chat_id = chat_id
    order.save(update_fields=["tg_chat_id"])


@sync_to_async
def get_latest_order_by_chat_id(chat_id):
    return Order.objects.filter(tg_chat_id=chat_id).latest("created_at")


@sync_to_async
def mark_order_paid(order):
    order.status = 'paid'
    order.save(update_fields=["status"])


@sync_to_async
def get_first_order_item(order):
    return order.items.first()

@sync_to_async
def get_order_product_info(order):
    try:
        item = order.items.select_related("product").first()
        if item and item.product:
            return item.product.name, item.quantity
    except Exception as e:
        logger.exception(f"Ошибка при получении информации о товаре: {e}")
    return "Товар", 1

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.effective_chat.id
    args = context.args

    logger.info(f"📥 Старт команды. chat_id={chat_id}, args={args}")

    await create_or_get_user(
        chat_id=chat_id,
        first_name=user.first_name,
        last_name=user.last_name,
        username=user.username
    )

    if args and args[0].startswith("order_"):
        order_id = args[0].split("_")[1]
        try:
            order = await get_order_with_items(order_id)
            await save_order_chat_id(order, chat_id)

            product, quantity = await get_order_product_info(order)

            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("Да, оплатить", callback_data=f"pay_{order_id}"),
                 InlineKeyboardButton("Нет", callback_data="cancel_order")]
            ])

            await context.bot.send_message(
                chat_id=chat_id,
                text=(
                    f"Ваш заказ №{order.id} успешно создан!\n\n"
                    f"Товар: {product} × {quantity}\n"
                    f"Адрес доставки: {order.city}, {order.address_detail}\n"
                    f"Доставка: {order.delivery_cost} ₽\n"
                    f"Сумма: {order.total_price} ₽\n"
                    f"Итого: {order.get_total_with_delivery()} ₽\n\n"
                    f"Всё ли корректно?"
                ),
                reply_markup=keyboard
            )
        except Order.DoesNotExist:
            await context.bot.send_message(chat_id=chat_id, text="❌ Заказ не найден.")
        except Exception as e:
            logger.exception("Ошибка при обработке заказа:")
            await context.bot.send_message(chat_id=chat_id, text="❌ Произошла ошибка при обработке заказа.")

    await context.bot.send_message(
        chat_id=chat_id,
        text="📍 Используйте меню ниже для работы с ботом:",
        reply_markup=main_menu()
    )


async def handle_pay_request(context, chat_id, order_id):
    try:
        order = await get_order_with_items(order_id)
        order.status = "pending"
        await sync_to_async(order.save)(update_fields=["status"])

        for admin_id in ADMINS:
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("✉️ Ответить клиенту", callback_data=f"reply_to_{chat_id}")],
                [InlineKeyboardButton("✅ Пометить как оплачено", callback_data=f"mark_paid_{chat_id}")]
            ])
            await context.bot.send_message(
                chat_id=admin_id,
                text=(
                    f"💳 Новый запрос на оплату заказа №{order.id} от @{order.user.username or 'Без имени'} "
                    f"(chat_id: {chat_id}).\n\n💬 Скоро пришлю ссылку на оплату. Пожалуйста, ожидайте."
                ),
                reply_markup=keyboard
            )

        await context.bot.send_message(
            chat_id=chat_id,
            text="💬 Скоро пришлю ссылку на оплату. Пожалуйста, ожидайте."
        )
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
            order = await get_latest_order_by_chat_id(client_chat_id)
            await mark_order_paid(order)
            await context.bot.send_message(chat_id=client_chat_id, text="✅ Спасибо за оплату! Мы скоро отправим ваш заказ.")
            await context.bot.send_message(chat_id=chat_id, text="Статус заказа обновлён как 'Оплачено'.")
        except Order.DoesNotExist:
            await context.bot.send_message(chat_id=chat_id, text="❌ Не удалось найти заказ для обновления.")

    elif data == "cancel_order":
        await context.bot.send_message(chat_id=chat_id, text="❌ Заказ отменён. Вы можете связаться с нами, если хотите внести изменения.")


async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    text = update.message.text

    if text == "❓ Задать вопрос":
        await context.bot.send_message(chat_id=chat_id, text="✍ Напишите ваш вопрос, мы скоро ответим.")
        context.user_data["awaiting_question"] = True

    elif text == "📦 Статус заказа":
        await context.bot.send_message(chat_id=chat_id, text="📮 Укажите номер заказа.")
        context.user_data["awaiting_order_id"] = True

    elif context.user_data.get("awaiting_question"):
        for admin_id in ADMINS:
            await context.bot.send_message(chat_id=admin_id, text=f"📩 Вопрос от клиента (chat_id: {chat_id}):\n{text}")
        await context.bot.send_message(chat_id=chat_id, text="✅ Вопрос передан. Мы скоро ответим.")
        context.user_data["awaiting_question"] = False

    elif context.user_data.get("awaiting_order_id"):
        for admin_id in ADMINS:
            await context.bot.send_message(chat_id=admin_id, text=f"📦 Запрос статуса от chat_id {chat_id}:\n{text}")
        await context.bot.send_message(chat_id=chat_id, text="✅ Запрос принят.")
        context.user_data["awaiting_order_id"] = False

    elif chat_id in admin_reply_sessions:
        target_chat_id = admin_reply_sessions.pop(chat_id)
        await context.bot.send_message(chat_id=target_chat_id, text=f"📨 Администратор:\n{text}")
        await context.bot.send_message(chat_id=chat_id, text="✅ Ответ отправлен.")

    else:
        for admin_id in ADMINS:
            await context.bot.send_message(chat_id=admin_id, text=f"📩 Сообщение от клиента (chat_id: {chat_id}):\n{text}")
        await context.bot.send_message(chat_id=chat_id, text="Ваше сообщение получено.")


async def media_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    message = update.message

    if message.photo or message.document:
        for admin_id in ADMINS:
            await context.bot.forward_message(chat_id=admin_id, from_chat_id=chat_id, message_id=message.message_id)
            await context.bot.send_message(chat_id=admin_id, text=f"🛉 Чек от клиента (chat_id: {chat_id})")
