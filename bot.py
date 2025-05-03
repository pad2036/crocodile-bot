import asyncio
import logging
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor

API_TOKEN = '7781770592:AAEWu3-3wKGi8rFEOv6UImMTpCkZxLY1dro'
YANDEX_PUBLIC_LINK = 'https://disk.yandex.ru/d/ueRhAeMAuJ2OBg'

# Включаем логирование
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Временное хранилище состояний игр пользователей
user_games = {}

# Кнопки
start_kb = InlineKeyboardMarkup().add(InlineKeyboardButton("Начало игры", callback_data="start_game"))
next_kb = InlineKeyboardMarkup().add(InlineKeyboardButton("Следующая картинка", callback_data="next"))

def extract_file_links(data):
    """
    Извлекает прямые ссылки на картинки из ответа Яндекс API
    """
    items = data.get('_embedded', {}).get('items', [])
    links = [item['file'] for item in items if item['name'].endswith('.png') and 'file' in item]
    return links

async def fetch_image_links():
    async with aiohttp.ClientSession() as session:
        api_url = f"https://cloud-api.yandex.net/v1/disk/public/resources?public_key={YANDEX_PUBLIC_LINK}&limit=100&preview_size=XL&fields=_embedded.items.name,_embedded.items.file"
        async with session.get(api_url) as resp:
            data = await resp.json()
            return extract_file_links(data)

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    await message.answer("Привет! Это игра 'Крокодил'. Жми 'Начало игры', чтобы начать!", reply_markup=start_kb)

@dp.callback_query_handler(lambda c: c.data == 'start_game')
async def start_game(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    images = await fetch_image_links()
    if not images:
        await callback_query.message.answer("Не удалось загрузить картинки. Попробуйте позже.")
        return
    user_games[user_id] = {'images': images, 'current_msg': None}
    await send_next_image(callback_query.message, user_id)

@dp.callback_query_handler(lambda c: c.data == 'next')
async def next_image(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    await send_next_image(callback_query.message, user_id)

async def send_next_image(message, user_id):
    game = user_games.get(user_id)
    if not game or not game['images']:
        await message.answer("Картинки закончились! Игра окончена.")
        return
    if game['current_msg']:
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=game['current_msg'])
        except:
            pass
    image_url = game['images'].pop(0)
    msg = await bot.send_photo(chat_id=message.chat.id, photo=image_url, reply_markup=next_kb)
    game['current_msg'] = msg.message_id

@dp.message_handler(lambda message: message.text and message.text.lower() == "конец")
async def end_game(message: types.Message):
    user_id = message.from_user.id
    if user_id in user_games:
        del user_games[user_id]
    await message.answer("Игра окончена! Спасибо за участие 🎉")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
