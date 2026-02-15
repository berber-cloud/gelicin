import asyncio
import logging
import json
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile, WebAppInfo
from aiogram.enums import ParseMode

# ================ ВСЕ ПЕРЕМЕННЫЕ ЗДЕСЬ ================
BOT_TOKEN = "8298712783:AAGGAl5RmMO_PJ3SnN_FGOGdBZpT77FV2p8"  # ВАШ ТОКЕН
# ⚠️ ВАЖНО: Здесь должен быть URL вашего приложения на GitHub Pages
# Пример: "https://ваш-username.github.io/название-репозитория"
APP_URL = "https://berber-cloud.github.io/"  # ЗАМЕНИТЕ НА ВАШ РЕАЛЬНЫЙ URL
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

# Простое хранилище рефералов (в памяти)
referrals_db = {}

def get_user_greeting(user: types.User) -> str:
    """
    Формирует приветствие в зависимости от времени суток и имени пользователя
    """
    first_name = user.first_name or ""
    last_name = user.last_name or ""
    username = user.username
    
    if username:
        display_name = f"@{username}"
    elif first_name and last_name:
        display_name = f"{first_name} {last_name}"
    elif first_name:
        display_name = first_name
    else:
        display_name = "друг"
    
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
    Создает клавиатуру с кнопкой для открытия Web App
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="🚀 Начать зарабатывать", 
                web_app=WebAppInfo(url=APP_URL)
            )]
        ]
    )
    return keyboard

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """
    Обработчик команды /start с поддержкой реферальных ссылок
    """
    try:
        user = message.from_user
        args = message.text.split()
        
        # Получаем информацию о боте
        bot_info = await bot.get_me()
        
        # Проверяем, есть ли реферальный параметр
        referrer_id = None
        if len(args) > 1 and args[1].startswith('ref_'):
            referrer_id = args[1].replace('ref_', '')
            logger.info(f"Пользователь {user.id} перешел по реферальной ссылке от {referrer_id}")
            
            if referrer_id not in referrals_db:
                referrals_db[referrer_id] = []
            
            if user.id not in referrals_db[referrer_id]:
                referrals_db[referrer_id].append(user.id)
                
                try:
                    await bot.send_message(
                        chat_id=int(referrer_id),
                        text=f"🎉 По вашей реферальной ссылке зарегистрировался новый пользователь!\n"
                             f"👤 Имя: {user.first_name}\n"
                             f"📊 Всего приглашено: {len(referrals_db[referrer_id])}\n\n"
                             f"🔗 Ваша реферальная ссылка:\n"
                             f"https://t.me/{bot_info.username}?start=ref_{referrer_id}"
                    )
                except Exception as e:
                    logger.error(f"Не удалось отправить уведомление рефереру: {e}")
        
        time_greeting, display_name = get_user_greeting(user)
        
        if referrer_id:
            caption_text = (
                f"{time_greeting}, {display_name}! 👋\n\n"
                f"✨ Вы перешли по реферальной ссылке!\n"
                f"💰 В приложении вас ждет бонус за регистрацию.\n\n"
                f"Выполняйте простые задания и зарабатывайте реальные деньги.\n\n"
                f"👇 Нажмите кнопку ниже, чтобы открыть приложение:"
            )
        else:
            # Создаем реферальный код для пользователя
            ref_code = f"ref_{user.id}"
            
            caption_text = (
                f"{time_greeting}, {display_name}! 👋\n\n"
                f"💰 Это бот с заданиями для заработка от 5000 рублей в день.\n\n"
                f"Выполняйте простые задания и получайте реальные деньги.\n\n"
                f"🔗 **Ваша реферальная ссылка:**\n"
                f"`https://t.me/{bot_info.username}?start={ref_code}`\n\n"
                f"Приглашайте друзей и получайте бонусы!\n\n"
                f"👇 Нажмите кнопку ниже, чтобы открыть приложение:"
            )
        
        # Пробуем отправить фото
        try:
            photo = FSInputFile(IMAGE_PATH)
            await message.answer_photo(
                photo=photo,
                caption=caption_text,
                reply_markup=get_main_keyboard(),
                parse_mode=ParseMode.MARKDOWN
            )
        except FileNotFoundError:
            logger.warning(f"Файл {IMAGE_PATH} не найден, отправляем только текст")
            await message.answer(
                text=caption_text,
                reply_markup=get_main_keyboard(),
                parse_mode=ParseMode.MARKDOWN
            )
            
    except Exception as e:
        logger.error(f"Ошибка в обработчике /start: {e}")
        await message.answer("Произошла ошибка. Попробуйте позже.")

@dp.message(Command("refs"))
async def cmd_refs(message: types.Message):
    """
    Команда для просмотра количества рефералов
    """
    try:
        user_id = str(message.from_user.id)
        ref_count = len(referrals_db.get(user_id, []))
        
        # Получаем информацию о боте
        bot_info = await bot.get_me()
        
        # Создаем реферальную ссылку
        ref_code = f"ref_{user_id}"
        ref_link = f"https://t.me/{bot_info.username}?start={ref_code}"
        
        await message.answer(
            f"📊 **Статистика рефералов**\n\n"
            f"👥 Приглашено друзей: **{ref_count}**\n"
            f"🔗 Ваша реферальная ссылка:\n"
            f"`{ref_link}`\n\n"
            f"✨ Приглашайте друзей и получайте бонусы в приложении!",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_main_keyboard()
        )
    except Exception as e:
        logger.error(f"Ошибка в команде /refs: {e}")
        await message.answer("Произошла ошибка. Попробуйте позже.")

@dp.message(lambda message: message.web_app_data)
async def handle_web_app_data(message: types.Message):
    """
    Обработчик данных из Web App приложения
    """
    try:
        data = json.loads(message.web_app_data.data)
        user_id = message.from_user.id
        action = data.get('action')
        
        logger.info(f"Получены данные из Web App от {user_id}: {action}")
        
        if action == 'check_subscription':
            channel = data.get('channel')
            # Здесь нужно реализовать реальную проверку подписки
            await message.answer(json.dumps({
                'status': 'success',
                'subscribed': True
            }))
            
        elif action == 'get_referrals':
            ref_count = len(referrals_db.get(str(user_id), []))
            await message.answer(json.dumps({
                'status': 'success',
                'referrals': ref_count
            }))
            
        elif action == 'withdraw':
            amount = data.get('amount')
            method = data.get('method')
            details = data.get('details')
            
            logger.info(f"Запрос на вывод от {user_id}: {amount} руб, метод: {method}")
            
            await message.answer(json.dumps({
                'status': 'success',
                'message': 'Запрос на вывод принят'
            }))
            
    except Exception as e:
        logger.error(f"Ошибка обработки данных из Web App: {e}")
        await message.answer(json.dumps({
            'status': 'error',
            'message': str(e)
        }))

@dp.message()
async def handle_all_messages(message: types.Message):
    """
    Обработчик всех остальных сообщений
    """
    await message.answer(
        "Используйте команду /start для начала работы\n"
        "Или /refs для просмотра статистики рефералов"
    )

async def main():
    """
    Главная функция запуска бота
    """
    # Получаем информацию о боте
    bot_info = await bot.get_me()
    
    logger.info(f"Бот запущен!")
    logger.info(f"URL приложения: {APP_URL}")
    logger.info(f"Username бота: @{bot_info.username}")
    logger.info(f"ID бота: {bot_info.id}")
    
    # Проверяем, что APP_URL начинается с https://
    if not APP_URL.startswith('https://'):
        logger.error("APP_URL должен начинаться с https://")
        return
    
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())