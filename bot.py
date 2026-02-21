import asyncio
import logging
import json
import redis.asyncio as redis
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile, WebAppInfo
from aiogram.enums import ParseMode

# ================ ВСЕ ПЕРЕМЕННЫЕ ЗДЕСЬ ================
BOT_TOKEN = "8298712783:AAGGAl5RmMO_PJ3SnN_FGOGdBZpT77FV2p8"  # ВАШ ТОКЕН
APP_URL = "https://coolrayhgs.github.io/brzhtrd"  # ВАШ URL НА GITHUB PAGES
IMAGE_PATH = "image.jpg"  # ПУТЬ К ИЗОБРАЖЕНИЮ
REDIS_HOST = "localhost"  # ХОСТ REDIS
REDIS_PORT = 6379  # ПОРТ REDIS
REDIS_DB = 0  # НОМЕР БАЗЫ ДАННЫХ

# Бонусы за задания
CHANNEL_BONUS = 300  # Бонус за подписку на канал
REFERRAL_BONUS = 6000  # Бонус за 20 рефералов
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

# Подключение к Redis
redis_client = None

# Список каналов для подписки
CHANNELS = [
    {"id": "@channel1", "name": "Канал 1", "bonus": 300},
    {"id": "@channel2", "name": "Канал 2", "bonus": 300},
    {"id": "@channel3", "name": "Канал 3", "bonus": 300},
    {"id": "@channel4", "name": "Канал 4", "bonus": 300},
    {"id": "@channel5", "name": "Канал 5", "bonus": 299}
]

async def init_redis():
    """Инициализация подключения к Redis"""
    global redis_client
    redis_client = await redis.from_url(
        f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}",
        decode_responses=True
    )
    logger.info("✅ Подключено к Redis")

async def get_user_data(user_id: int) -> dict:
    """Получение данных пользователя из Redis"""
    key = f"user:{user_id}"
    data = await redis_client.get(key)
    
    if data:
        return json.loads(data)
    else:
        # Создаем нового пользователя
        user_data = {
            'balance': 0,
            'referrals': [],
            'referral_count': 0,
            'completed_tasks': [],
            'subscribed_channels': [],
            'created_at': datetime.now().isoformat()
        }
        await redis_client.set(key, json.dumps(user_data))
        return user_data

async def save_user_data(user_id: int, data: dict):
    """Сохранение данных пользователя в Redis"""
    key = f"user:{user_id}"
    await redis_client.set(key, json.dumps(data))

async def check_subscription(user_id: int, channel: str) -> bool:
    """Проверка подписки пользователя на канал"""
    try:
        # Получаем информацию о пользователе в канале
        chat = await bot.get_chat(channel)
        member = await bot.get_chat_member(chat.id, user_id)
        
        # Проверяем статус подписки
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        logger.error(f"Ошибка проверки подписки на {channel}: {e}")
        return False

def get_user_greeting(user: types.User) -> str:
    """Формирует приветствие в зависимости от времени суток"""
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
    """Создает клавиатуру с кнопкой для открытия Web App"""
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
    """Обработчик команды /start с поддержкой реферальных ссылок"""
    try:
        user = message.from_user
        args = message.text.split()
        
        # Получаем информацию о боте
        bot_info = await bot.get_me()
        
        # Получаем данные пользователя
        user_data = await get_user_data(user.id)
        
        # Проверяем, есть ли реферальный параметр
        if len(args) > 1 and args[1].isdigit():
            referrer_id = int(args[1])
            logger.info(f"Пользователь {user.id} перешел по реферальной ссылке от {referrer_id}")
            
            # Проверяем, что реферер существует и это не сам пользователь
            if referrer_id != user.id:
                # Получаем данные реферера
                referrer_data = await get_user_data(referrer_id)
                
                # Добавляем реферала если его еще нет
                if user.id not in referrer_data['referrals']:
                    referrer_data['referrals'].append(user.id)
                    referrer_data['referral_count'] = len(referrer_data['referrals'])
                    
                    # Проверяем, достиг ли реферер 20 рефералов
                    if referrer_data['referral_count'] >= 20 and 'referral_20' not in referrer_data['completed_tasks']:
                        # Начисляем бонус
                        referrer_data['balance'] += REFERRAL_BONUS
                        referrer_data['completed_tasks'].append('referral_20')
                        
                        # Сохраняем данные реферера
                        await save_user_data(referrer_id, referrer_data)
                        
                        # Уведомляем реферера
                        try:
                            await bot.send_message(
                                chat_id=referrer_id,
                                text=f"🎉 **Поздравляем!**\n\n"
                                     f"Вы пригласили 20 друзей!\n"
                                     f"💰 На ваш баланс начислено {REFERRAL_BONUS} ₽\n\n"
                                     f"Баланс: {referrer_data['balance']} ₽",
                                parse_mode=ParseMode.MARKDOWN
                            )
                        except Exception as e:
                            logger.error(f"Не удалось отправить уведомление: {e}")
                    else:
                        # Сохраняем данные реферера
                        await save_user_data(referrer_id, referrer_data)
                    
                    # Уведомляем реферера о новом реферале
                    try:
                        await bot.send_message(
                            chat_id=referrer_id,
                            text=f"🎉 По вашей ссылке зарегистрировался новый пользователь!\n"
                                 f"👤 Имя: {user.first_name}\n"
                                 f"📊 Всего приглашено: {referrer_data['referral_count']}/20\n\n"
                                 f"🔗 Ваша ссылка:\n"
                                 f"https://t.me/{bot_info.username}?start={referrer_id}"
                        )
                    except Exception as e:
                        logger.error(f"Не удалось отправить уведомление: {e}")
        
        time_greeting, display_name = get_user_greeting(user)
        
        # Создаем реферальную ссылку для пользователя
        ref_link = f"https://t.me/{bot_info.username}?start={user.id}"
        
        # Получаем актуальные данные после возможных изменений
        user_data = await get_user_data(user.id)
        
        caption_text = (
            f"{time_greeting}, {display_name}! 👋\n\n"
            f"💰 **Ваш баланс:** {user_data['balance']} ₽\n"
            f"👥 **Приглашено друзей:** {user_data['referral_count']}/20\n"
            f"✅ **Выполнено заданий:** {len(user_data['completed_tasks'])}\n\n"
            f"🔗 **Ваша реферальная ссылка:**\n"
            f"`{ref_link}`\n\n"
            f"Приглашайте друзей и получайте бонус 6000 ₽ за 20 приглашений!\n\n"
            f"👇 Нажмите кнопку ниже, чтобы открыть приложение:"
        )
        
        try:
            photo = FSInputFile(IMAGE_PATH)
            await message.answer_photo(
                photo=photo,
                caption=caption_text,
                reply_markup=get_main_keyboard(),
                parse_mode=ParseMode.MARKDOWN
            )
        except FileNotFoundError:
            await message.answer(
                text=caption_text,
                reply_markup=get_main_keyboard(),
                parse_mode=ParseMode.MARKDOWN
            )
            
    except Exception as e:
        logger.error(f"Ошибка в обработчике /start: {e}")
        await message.answer("Произошла ошибка. Попробуйте позже.")

@dp.message(Command("balance"))
async def cmd_balance(message: types.Message):
    """Команда для просмотра баланса"""
    try:
        user_id = message.from_user.id
        user_data = await get_user_data(user_id)
        
        # Создаем реферальную ссылку
        bot_info = await bot.get_me()
        ref_link = f"https://t.me/{bot_info.username}?start={user_id}"
        
        await message.answer(
            f"💰 **Ваш баланс:** {user_data['balance']} ₽\n"
            f"👥 **Приглашено друзей:** {user_data['referral_count']}/20\n"
            f"✅ **Выполнено заданий:** {len(user_data['completed_tasks'])}\n\n"
            f"🔗 **Ваша реферальная ссылка:**\n"
            f"`{ref_link}`\n\n"
            f"🎯 **До бонуса за рефералов:** {20 - user_data['referral_count']} чел.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_main_keyboard()
        )
    except Exception as e:
        logger.error(f"Ошибка в команде balance: {e}")
        await message.answer("Произошла ошибка. Попробуйте позже.")

@dp.message(lambda message: message.web_app_data)
async def handle_web_app_data(message: types.Message):
    """Обработчик данных из Web App приложения"""
    try:
        data = json.loads(message.web_app_data.data)
        user_id = message.from_user.id
        action = data.get('action')
        
        logger.info(f"Получены данные из Web App от {user_id}: {action}")
        
        if action == 'check_subscription':
            # Проверка подписки на канал
            channel = data.get('channel')
            channel_id = data.get('channel_id')
            
            # Проверяем подписку
            is_subscribed = await check_subscription(user_id, channel)
            
            if is_subscribed:
                # Получаем данные пользователя
                user_data = await get_user_data(user_id)
                
                # Проверяем, не выполнял ли уже это задание
                task_key = f"sub_{channel_id}"
                if task_key not in user_data['completed_tasks']:
                    # Начисляем бонус
                    user_data['balance'] += CHANNEL_BONUS
                    user_data['completed_tasks'].append(task_key)
                    user_data['subscribed_channels'].append(channel)
                    
                    # Сохраняем данные
                    await save_user_data(user_id, user_data)
                    
                    await message.answer(json.dumps({
                        'status': 'success',
                        'subscribed': True,
                        'bonus': CHANNEL_BONUS,
                        'new_balance': user_data['balance']
                    }))
                else:
                    await message.answer(json.dumps({
                        'status': 'success',
                        'subscribed': True,
                        'already_completed': True
                    }))
            else:
                await message.answer(json.dumps({
                    'status': 'success',
                    'subscribed': False
                }))
        
        elif action == 'get_user_data':
            # Отправка данных пользователя в приложение
            user_data = await get_user_data(user_id)
            
            # Формируем список заданий с их статусом
            tasks_status = []
            for i, channel in enumerate(CHANNELS, 1):
                task_key = f"sub_channel{i}"
                tasks_status.append({
                    'id': f'channel{i}',
                    'completed': task_key in user_data['completed_tasks']
                })
            
            # Добавляем реферальное задание
            tasks_status.append({
                'id': 'referral',
                'completed': 'referral_20' in user_data['completed_tasks'],
                'progress': user_data['referral_count']
            })
            
            await message.answer(json.dumps({
                'balance': user_data['balance'],
                'referrals': user_data['referral_count'],
                'tasks': tasks_status
            }))
        
        elif action == 'withdraw':
            # Обработка вывода средств
            amount = data.get('amount')
            method = data.get('method')
            details = data.get('details')
            
            user_data = await get_user_data(user_id)
            
            # Проверяем достаточно ли средств
            if user_data['balance'] >= 1500:
                # Здесь можно добавить логику вывода
                logger.info(f"Запрос на вывод от {user_id}: {amount} руб, метод: {method}")
                
                # Временно просто списываем баланс
                user_data['balance'] -= amount
                await save_user_data(user_id, user_data)
                
                await message.answer(json.dumps({
                    'status': 'success',
                    'message': 'Запрос на вывод принят. Средства поступят в течение 8 часов',
                    'new_balance': user_data['balance']
                }))
            else:
                await message.answer(json.dumps({
                    'status': 'error',
                    'message': 'Недостаточно средств. Минимум 1500 ₽'
                }))
            
    except Exception as e:
        logger.error(f"Ошибка обработки данных из Web App: {e}")
        await message.answer(json.dumps({
            'status': 'error',
            'message': str(e)
        }))

@dp.message()
async def handle_all_messages(message: types.Message):
    """Обработчик всех остальных сообщений"""
    await message.answer(
        "Используйте команду /start для начала работы\n"
        "Или /balance для просмотра баланса"
    )

async def main():
    """Главная функция запуска бота"""
    # Инициализируем Redis
    await init_redis()
    
    # Получаем информацию о боте
    bot_info = await bot.get_me()
    
    logger.info(f"✅ Бот запущен! Username: @{bot_info.username}")
    logger.info(f"✅ URL приложения: {APP_URL}")
    logger.info(f"✅ Каналы для проверки: {len(CHANNELS)}")
    
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
    finally:
        await bot.session.close()
        if redis_client:
            await redis_client.close()

if __name__ == "__main__":
    asyncio.run(main())