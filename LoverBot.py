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
animation_settings: Dict[str, dict] = {}

# --- ПАРАМЕТРЫ ВИЗУАЛА ---
COLORS = ["❤️", "💖", "💝", "💗", "💓", "🧡", "💛", "💚", "💙", "💜"]
PHRASES = ["ЛЮБЛЮ", "ТЕБЯ", "ОЧЕНЬ", "СИЛЬНО", "ТЫ МОЯ", "ЖИЗНЬ", "СЧАСТЬЕ"]

# Шаблоны для пульсации
HEART_BIG = (
    "<code>"
    "  {c}{c}   {c}{c}  \n"
    " {c}{c}{c}{c} {c}{c}{c}{c} \n"
    "{c}{c}{c}{c}{c}{c}{c}{c}{c}{c}{c}\n"
    "{c}{c} {text} {c}{c}\n"
    " {c}{c}{c}{c}{c}{c}{c}{c}{c} \n"
    "  {c}{c}{c}{c}{c}{c}{c}  \n"
    "   {c}{c}{c}{c}{c}   \n"
    "    {c}{c}{c}    \n"
    "     {c}     "
    "</code>"
)

HEART_SMALL = (
    "<code>"
    "          \n"
    "   {c}{c} {c}{c}   \n"
    "  {c}{c}{c}{c}{c}{c}{c}  \n"
    "  {c} {text} {c}  \n"
    "   {c}{c}{c}{c}{c}   \n"
    "    {c}{c}{c}    \n"
    "     {c}      \n"
    "          \n"
    "          "
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


def get_control_kb(iid: str) -> InlineKeyboardMarkup:
    settings = animation_settings.get(iid, {"mode": "rainbow", "pulse": True})
    mode = settings["mode"]
    pulse = settings["pulse"]
    
    buttons = [
        [
            InlineKeyboardButton(text="🌈 Радуга" if mode != "rainbow" else "✅ Радуга", callback_data="set_rainbow"),
            InlineKeyboardButton(text="🎲 Хаос" if mode != "chaos" else "✅ Хаос", callback_data="set_chaos")
        ],
        [
            InlineKeyboardButton(text="💓 Пульс: ВКЛ" if pulse else "💤 Пульс: ВЫКЛ", callback_data="toggle_pulse")
        ],
        [InlineKeyboardButton(text="🛑 Остановить", callback_data="stop_heart")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# --- INLINE QUERY ---

@router.inline_query()
async def inline_handler(query: types.InlineQuery):
    results = [
        InlineQueryResultArticle(
            id="h2",
            title="✨ Живое Сердце 3.0",
            description="Пульсация, градиенты и нежные слова",
            input_message_content=InputTextMessageContent(message_text="<b>Пробуждение магии...</b>", parse_mode="HTML"),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Оживить сердце ✨", callback_data="start_heart")]])
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
    animation_settings[iid] = {"mode": "rainbow", "pulse": True}

    idx = 0
    phrase_idx = 0
    tick = 0
    
    while active_animations.get(iid):
        settings = animation_settings.get(iid)
        mode = settings["mode"]
        pulse = settings["pulse"]
        
        # 1. Определяем цвет
        if mode == "rainbow":
            color = COLORS[idx % len(COLORS)]
        else:
            color = random.choice(COLORS)
        
        # 2. Определяем текст (меняем каждые 4 тика)
        if tick % 4 == 0:
            current_text = PHRASES[phrase_idx % len(PHRASES)]
            phrase_idx += 1
        else:
            current_text = PHRASES[(phrase_idx - 1) % len(PHRASES)]

        # 3. Эффект пульсации (чередуем большой/маленький шаблон)
        if pulse:
            template = HEART_BIG if tick % 2 == 0 else HEART_SMALL
        else:
            template = HEART_BIG
            
        # Центрируем текст внутри сердца (5 символов макс)
        display_text = current_text.center(5)

        content = template.format(c=color, text=display_text)
        
        if not await safe_edit(iid, content, get_control_kb(iid)): 
            break
        
        idx += 1
        tick += 1
        await asyncio.sleep(0.6) # Оптимальная скорость для пульсации


@router.callback_query(F.data.startswith("set_"))
async def set_mode(call: types.CallbackQuery):
    mode = call.data.split("_")[1]
    iid = call.inline_message_id
    if iid in animation_settings:
        animation_settings[iid]["mode"] = mode
    await call.answer(f"Режим: {mode}")


@router.callback_query(F.data == "toggle_pulse")
async def toggle_pulse(call: types.CallbackQuery):
    iid = call.inline_message_id
    if iid in animation_settings:
        animation_settings[iid]["pulse"] = not animation_settings[iid]["pulse"]
        status = "Включена" if animation_settings[iid]["pulse"] else "Выключена"
        await call.answer(f"Пульсация: {status}")


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
    print(">>> ЖИВОЕ СЕРДЦЕ ЗАПУЩЕНО!")
    await dp.start_polling(bot)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
