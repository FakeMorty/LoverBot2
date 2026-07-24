import asyncio
import sys
import logging
import os
import random
from aiohttp import web
from dotenv import load_dotenv
from typing import Dict, List
from aiogram import Bot, Dispatcher, types, Router, F
from aiogram.exceptions import TelegramBadRequest, TelegramRetryAfter
from aiogram.types import (
    InlineQueryResultArticle,
    InputTextMessageContent,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

load_dotenv()

# --- НАСТРОЙКИ ---
API_TOKEN = os.getenv('API_TOKEN', '8471337212:AAF_JtNRVpqsDCqV-CG-BE8vLKg4bp-NexY')

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()
router = Router()

# Состояния анимаций
active_animations: Dict[str, bool] = {}
animation_modes: Dict[str, str] = {}

# --- ПАРАМЕТРЫ ВИЗУАЛА ---
COLORS = ["❤️", "💖", "💝", "💗", "💓", "🧡", "💛", "💚", "💙", "💜"]

# Идеальное сердце
HEART_TEMPLATE = (
    "<code>"
    "  {c}{c}   {c}{c}  \n"
    " {c}{c}{c}{c} {c}{c}{c}{c} \n"
    "{c}{c}{c}{c}{c}{c}{c}{c}{c}{c}{c}\n"
    "{c}{c} ЛЮБЛЮ {c}{c}\n"
    " {c}{c}{c}{c}{c}{c}{c}{c}{c} \n"
    "  {c}{c}{c}{c}{c}{c}{c}  \n"
    "   {c}{c}{c}{c}{c}   \n"
    "    {c}{c}{c}    \n"
    "     {c}     "
    "</code>"
)


# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---

async def safe_edit(iid: str, text: str, kb: InlineKeyboardMarkup = None):
    try:
        await bot.edit_message_text(
            text=text, inline_message_id=iid,
            reply_markup=kb, parse_mode="HTML"
        )
        return True
    except TelegramRetryAfter as e:
        await asyncio.sleep(e.retry_after)
        return False
    except TelegramBadRequest as e:
        if "message is not modified" in str(e): return True
        return False
    except Exception:
        return False


def get_heart_kb(mode="rainbow") -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(text="🌈 Радуга" if mode != "rainbow" else "✅ Радуга", callback_data="set_rainbow"),
            InlineKeyboardButton(text="🎲 Хаос" if mode != "chaos" else "✅ Хаос", callback_data="set_chaos")
        ],
        [InlineKeyboardButton(text="🛑 Остановить", callback_data="stop_heart")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# --- INLINE QUERY ---

@router.inline_query()
async def inline_handler(query: types.InlineQuery):
    results = [
        InlineQueryResultArticle(
            id="h1",
            title="❤️ Магическое Сердце 2.0",
            description="Бесконечная анимация с выбором режимов",
            input_message_content=InputTextMessageContent(message_text="<b>Загрузка магии...</b>", parse_mode="HTML"),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Запустить ❤️", callback_data="start_heart")]])
        )
    ]
    await query.answer(results, cache_time=1)


# --- ЛОГИКА СЕРДЦА ---

@router.callback_query(F.data == "start_heart")
async def heart_logic(call: types.CallbackQuery):
    iid = call.inline_message_id
    if not iid or active_animations.get(iid): return
    await call.answer()

    active_animations[iid] = True
    animation_modes[iid] = "rainbow"

    idx = 0
    while active_animations.get(iid):
        mode = animation_modes.get(iid, "rainbow")
        
        if mode == "rainbow":
            color = COLORS[idx % len(COLORS)]
            idx += 1
        else:
            color = random.choice(COLORS)

        content = HEART_TEMPLATE.format(c=color)
        if not await safe_edit(iid, content, get_heart_kb(mode)): 
            break
        await asyncio.sleep(0.8)


@router.callback_query(F.data.startswith("set_"))
async def set_mode(call: types.CallbackQuery):
    mode = call.data.split("_")[1]
    iid = call.inline_message_id
    if iid:
        animation_modes[iid] = mode
    await call.answer(f"Режим: {mode}")


@router.callback_query(F.data == "stop_heart")
async def stop_heart(call: types.CallbackQuery):
    iid = call.inline_message_id
    active_animations[iid] = False
    await safe_edit(iid, "<b>Сердце замерло... ❤️</b>")
    await call.answer("Остановлено")


# --- ВЕБ-СЕРВЕР ДЛЯ RENDER ---
async def handle(request):
    return web.Response(text="I'm alive!")

async def run_http_server():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

async def main():
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)
    await run_http_server()
    print(">>> БОТ ЗАПУЩЕН!")
    await dp.start_polling(bot)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
