import logging
import joblib
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Включаем логирование
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Загружаем модель и векторизатор
model = joblib.load('spam_model.pkl')
vectorizer = joblib.load('vectorizer.pkl')


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Привет! Я анти-спам бот. Я буду удалять сообщения с рекламой.')


def is_spam(message: str) -> bool:
    # Преобразуем сообщение и предсказываем
    message_vector = vectorizer.transform([message]).toarray()
    prediction = model.predict(message_vector)
    return prediction[0] == 1  # Если 1, то это спам


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message_text = update.message.text
    user_name = update.message.from_user.full_name  # Получаем полное имя пользователя
    user_username = update.message.from_user.username  # Получаем username пользователя
    user_id = update.message.from_user.id  # Получаем user_id пользователя
    chat_id = update.effective_chat.id  # Получаем chat_id чата

    if is_spam(message_text):
        # Удаляем сообщение, если оно является спамом
        await update.message.delete()
        logger.info(f"Удалено спам-сообщение от {user_name}: {message_text}")

        # Формируем ссылку на профиль пользователя
        if user_username:
            profile_link = f"https://t.me/{user_username}"
        else:
            profile_link = f"Пользователь не имеет публичного профиля. (ID: {user_id})"

        # Уведомляем о спаме в общий чат
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Сообщение от {user_name} (chat_id: {chat_id}) было удалено как спам. Профиль: {profile_link}"
        )

        # Уведомляем администратора в личные сообщения
        admin_chat_id = 1645366241  # Замените на ID администратора
        await context.bot.send_message(
            chat_id=admin_chat_id,
            text=f"Пользователь {user_name} (chat_id: {chat_id}) отправил спам-сообщение: {message_text}\nПрофиль: {profile_link}"
        )
    else:
        logger.info(f"Сообщение: {message_text}")


def main() -> None:
    TOKEN = 'Token'  # Замените на токен вашего бота

    # Создаем приложение
    application = ApplicationBuilder().token(TOKEN).build()

    # Регистрация обработчиков
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Запускаем бота
    application.run_polling()


if __name__ == '__main__':
    main()

