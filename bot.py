import asyncio
import logging
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.enums import ParseMode

# ================ ВСЕ ПЕРЕМЕННЫЕ ЗДЕСЬ ================
BOT_TOKEN = "8298712783:AAGGAl5RmMO_PJ3SnN_FGOGdBZpT77FV2p8"  # ВАШ ТОКЕН
APP_URL = "t.me/coolrayhgsbot/app"  # ССЫЛКА НА ПРИЛОЖЕНИЕ
IMAGE_PATH = "image.jpg"  # ПУТЬ К ИЗОБРАЖЕНИЮ
# ======================================================

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

def get_user_greeting(user: types.User) -> str:
    """
    Формирует приветствие в зависимости от времени суток и имени пользователя
    """
    # Получаем имя пользователя
    first_name = user.first_name or ""
    last_name = user.last_name or ""
    username = user.username
    
    # Формируем отображаемое имя
    if username:
        display_name = f"@{username}"
    elif first_name and last_name:
        display_name = f"{first_name} {last_name}"
    elif first_name:
        display_name = first_name
    else:
        display_name = "друг"
    
    # Определяем время суток
    hour = datetime.now().hour
    
    if 5 <= hour < 12:
        time_greeting = "Доброе утро"
    elif 12 <= hour < 18:
        time_greeting = "Добрый день"
    elif 18 <= hour < 23:
        time_greeting = "Добрый вечер"
    else:
        time_greeting = "Доброй ночи"
    
    return time_greeting, display_name

def get_main_keyboard() -> InlineKeyboardMarkup:
    """
    Создает клавиатуру с одной зеленой кнопкой
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="Начать зарабатывать", 
                url=APP_URL,
                style="success"  # 🟢 Зеленый цвет
            )]
        ]
    )
    return keyboard

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """
    Обработчик команды /start
    """
    try:
        user = message.from_user
        time_greeting, display_name = get_user_greeting(user)
        
        # Формируем текст сообщения
        caption_text = (
            f"{time_greeting}, {display_name}! 👋\n\n"
            f"Это бот с заданиями для заработка от 5000 рублей в день.\n\n"
            f"Выполняйте простые задания за реальные деньги."
        )
        
        # Пробуем отправить фото
        try:
            photo = FSInputFile(IMAGE_PATH)
            await message.answer_photo(
                photo=photo,
                caption=caption_text,
                reply_markup=get_main_keyboard(),
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            logger.warning(f"Не удалось отправить фото: {e}")
            # Если фото не найдено, отправляем только текст
            await message.answer(
                text=caption_text,
                reply_markup=get_main_keyboard(),
                parse_mode=ParseMode.HTML
            )
            
    except Exception as e:
        logger.error(f"Ошибка в обработчике /start: {e}")
        await message.answer("Произошла ошибка. Попробуйте позже.")

@dp.message()
async def handle_all_messages(message: types.Message):
    """
    Обработчик всех остальных сообщений
    """
    await message.answer(
        "Используйте команду /start для начала работы"
    )

async def main():
    """
    Главная функция запуска бота
    """
    logger.info(f"Бот запущен!")
    logger.info(f"URL приложения: {APP_URL}")
    
    # Запускаем поллинг
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())