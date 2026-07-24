import asyncio
import sys
import logging
import os
from aiohttp import web
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, Router, F
from aiogram.types import (
    InlineQueryResultArticle,
    InputTextMessageContent,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

load_dotenv()

# --- НАСТРОЙКИ ---
API_TOKEN = os.getenv('API_TOKEN')

if not API_TOKEN:
    logging.error("ОШИБКА: Токен бота не найден! Установите переменную окружения API_TOKEN.")
    sys.exit(1)
# Ссылка будет динамической на основе домена Render
RENDER_EXTERNAL_URL = os.getenv('RENDER_EXTERNAL_URL', 'https://loverbot2.onrender.com')

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()
router = Router()

# Статичное идеальное сердце (подобранное для Telegram)
HEART_LAYOUT = (
    "❤️❤️　　　❤️❤️\n"
    "❤️❤️❤️❤️　❤️❤️❤️❤️\n"
    "❤️❤️❤️❤️❤️❤️❤️❤️❤️\n"
    "　❤️❤️❤️❤️❤️❤️❤️\n"
    "　　❤️❤️❤️❤️❤️\n"
    "　　　❤️❤️❤️\n"
    "　　　　❤️"
)

@router.inline_query()
async def inline_handler(query: types.InlineQuery):
    # Текст сообщения с гиперссылкой
    message_text = (
        f"{HEART_LAYOUT}\n\n"
        f"Ты — моё самое дорогое сокровище. ✨\n"
        f"<a href='{RENDER_EXTERNAL_URL}'>Нажми сюда, чтобы увидеть сюрприз...</a>"
    )
    
    results = [
        InlineQueryResultArticle(
            id="static_heart",
            title="❤️ Послание Любви",
            description="Отправить сердце и ссылку на сюрприз",
            input_message_content=InputTextMessageContent(
                message_text=message_text,
                parse_mode="HTML"
            )
        )
    ]
    await query.answer(results, cache_time=1)

# --- ВЕБ-СТРАНИЦА (СЮРПРИЗ) ---
HTML_PAGE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Для тебя ❤️</title>
    <style>
        body {
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            background-color: #ffeff5;
            font-family: 'Arial', sans-serif;
            overflow: hidden;
            text-align: center;
        }
        .container {
            z-index: 10;
            padding: 20px;
            background: white;
            border-radius: 20px;
            box-shadow: 0 10px 30px rgba(255, 105, 180, 0.3);
            animation: fadeIn 2s ease-in;
        }
        h1 { color: #ff4d6d; margin-bottom: 10px; }
        p { color: #590d22; font-size: 1.2em; }
        .heart {
            position: absolute;
            color: #ff4d6d;
            font-size: 20px;
            animation: float 5s infinite ease-in;
            opacity: 0.8;
        }
        @keyframes float {
            0% { transform: translateY(100vh) rotate(0deg); opacity: 1; }
            100% { transform: translateY(-100px) rotate(360deg); opacity: 0; }
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: scale(0.9); }
            to { opacity: 1; transform: scale(1); }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>ТЫ МОЯ САМАЯ ЛЮБИМАЯ! ❤️</h1>
        <p>Я создал этого бота, чтобы напомнить тебе о том, как сильно ты мне дорога.</p>
        <p>Пусть каждый твой день будет таким же ярким, как эти сердца! ✨</p>
    </div>

    <script>
        function createHeart() {
            const heart = document.createElement('div');
            heart.classList.add('heart');
            heart.innerHTML = '❤️';
            heart.style.left = Math.random() * 100 + 'vw';
            heart.style.animationDuration = Math.random() * 3 + 2 + 's';
            document.body.appendChild(heart);
            setTimeout(() => { heart.remove(); }, 5000);
        }
        setInterval(createHeart, 300);
    </script>
</body>
</html>
"""

async def handle(request):
    return web.Response(text=HTML_PAGE, content_type='text/html')

async def run_http_server():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', int(os.getenv("PORT", 8080))).start()

async def main():
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)
    await run_http_server()
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except:
        pass
