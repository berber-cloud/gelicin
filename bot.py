import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes

# Токен бота
BOT_TOKEN = "8298712783:AAGGAl5RmMO_PJ3SnN_FGOGdBZpT77FV2p8"

# Ссылка на приложение
APP_URL = "t.me/coolrayhgsbot/app"  # Замените на вашу ссылку

# Включаем логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Создаем клавиатуру
    keyboard = [[InlineKeyboardButton("Начать зарабатывать", url=APP_URL)]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Путь к изображению
    with open('image.jpg', 'rb') as photo:
        await update.message.reply_photo(
            photo=photo,
            caption="Привет, {first_name}! 👋\n\n"
                   "Это бот с заданиями для заработка от 5000 рублей в день. "
                   "Выполняйте простые задания за реальные деньги.\n\n"
                   ,
            reply_markup=reply_markup
        )

# Запуск бота
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))

    print("Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()