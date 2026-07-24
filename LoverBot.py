import asyncio
import sys
import logging
import os
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

# Состояния анимаций (чтобы можно было остановить)
active_animations: Dict[str, bool] = {}

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
    """Редактирование сообщения с защитой от всех ошибок."""
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


def get_kb(text: str, data: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=text, callback_data=data)]])


# --- INLINE QUERY (ВЫБОР ИЗ ДВУХ ВАРИАНТОВ) ---

@router.inline_query()
async def inline_handler(query: types.InlineQuery):
    results = [
        # Вариант 1: Сердце
        InlineQueryResultArticle(
            id="h1",
            title="❤️ Магическое Сердце",
            description="Бесконечная смена цветов (идеальная форма)",
            input_message_content=InputTextMessageContent(message_text="<b>Загрузка магии...</b>", parse_mode="HTML"),
            reply_markup=get_kb("Запустить ❤️", "start_heart")
        ),
        # Вариант 2: Квест
        InlineQueryResultArticle(
            id="q1",
            title="🐝 Квест: Даша и Пчела",
            description="Экшен-история с анимациями и ПВО",
            input_message_content=InputTextMessageContent(message_text="👧 Даша: Привет, любимый! Смотри: ❤️"),
            reply_markup=get_kb("Взять сердечко ❤️", "step_1")
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
    stop_kb = get_kb("🛑 Остановить", "stop_heart")

    idx = 0
    while active_animations.get(iid):
        content = HEART_TEMPLATE.format(c=COLORS[idx % len(COLORS)])
        if not await safe_edit(iid, content, stop_kb): break
        await asyncio.sleep(0.9)
        idx += 1


@router.callback_query(F.data == "stop_heart")
async def stop_heart(call: types.CallbackQuery):
    active_animations[call.inline_message_id] = False
    await safe_edit(call.inline_message_id, "<b>Сердце замерло... ❤️</b>")
    await call.answer("Остановлено")


# --- ЛОГИКА КВЕСТА (ПОКАДРОВАЯ АНИМАЦИЯ) ---

async def play_frames(iid: str, frames: List[str], speed: float = 1.0):
    """Проигрывает список кадров с заданной скоростью."""
    for frame in frames:
        await safe_edit(iid, frame)
        await asyncio.sleep(speed)


@router.callback_query(F.data == "step_1")
async def quest_step_1(call: types.CallbackQuery):
    iid = call.inline_message_id
    await call.answer()

    # Анимация кражи
    frames = [
        "👧 Даша: ❤️\n\n　　　　　　　　🐝💨",
        "👧 Даша: ❤️\n\n　　　　　🐝💨",
        "👧 Даша: ОЙ! КТО ЭТО?!\n\n　🐝💨❤️",
        "👧 Даша: ОНА УКРАЛА СЕРДЦЕ! СТОЙ, БЛЯДОТА!!\n\n🐝💨❤️　　　　　　　"
    ]
    await play_frames(iid, frames, 1.1)
    await safe_edit(iid, "🐝💨❤️\n\n👦 Ты: НЕ ПЕРЕЖИВАЙ, Я ЕЁ ПОЙМАЮ!", get_kb("ПОГНАТЬСЯ! 🏃💨", "step_2"))


@router.callback_query(F.data == "step_2")
async def quest_step_2(call: types.CallbackQuery):
    iid = call.inline_message_id
    await call.answer()

    # Анимация погони (бежим влево за пчелой)
    frames = [
        "👦 Ты: ВЕРНИ СЕРДЦЕ!\n\n🐝💨❤️　　　　　🏃👦",
        "👦 Ты: Я БЫСТРЕЕ!\n\n🐝💨❤️　　　🏃👦　",
        "👦 Ты: ЕЩЁ ЧУТЬ-ЧУТЬ!\n\n🐝💨❤️　🏃👦　　",
        "👦 Ты: ПОПАЛАСЬ!!\n\n🐝❤️🏃👦　　　　"
    ]
    await play_frames(iid, frames, 1.2)
    await safe_edit(iid, "👦 Ты: Погоди... Ты чего встала?\n\n🐝　　🧍👦", get_kb("Что она делает? 😰", "step_3"))


@router.callback_query(F.data == "step_3")
async def quest_step_3(call: types.CallbackQuery):
    iid = call.inline_message_id
    await call.answer()

    # Анимация укуса
    await safe_edit(iid, "👦 Ты: Ой-ой...\n\n🐝💨💥👦")
    await asyncio.sleep(1.5)
    await safe_edit(iid, "👦 Ты: АААААААА!!!\n\n🐝💨　🔥👦🔥")
    await asyncio.sleep(1.2)
    await safe_edit(iid, "👦 Ты: *падаю без сил*\n\n🐝💨　　🤕💤")
    await asyncio.sleep(2.5)

    await safe_edit(iid, "👧 Даша: ТЫ УЖАЛИЛА МОЕГО ПАРНЯ?! ПИЗДА ТЕБЕ ШЛЮХА МОХНАТАЯ!\n\n🐝　　　　　　😡👧📡",
                    get_kb("Даша, ПВО?! 🛰", "step_4"))


@router.callback_query(F.data == "step_4")
async def quest_step_4(call: types.CallbackQuery):
    iid = call.inline_message_id
    await call.answer()

    await safe_edit(iid, "👧 Даша: ЦЕЛЬ ЗАХВАЧЕНА. ОГОНЬ!\n\n🐝🎯　　　　　🛰👧")
    await asyncio.sleep(2.0)

    # Полет ракеты (справа налево)
    frames = [
        "👧 Даша: ПУСК!!\n\n🐝　　　　🚀💨　🛰👧",
        "👧 Даша: ЛЕТИТ!\n\n🐝　　🚀💨　　　🛰👧",
        "💥💥💥 Б А - Б А Х ! ! ! 💥💥💥\n\n　　　🔥🐝🔥"
    ]
    await play_frames(iid, frames, 1.0)
    await asyncio.sleep(2.5)

    await safe_edit(iid, "👧 Даша: Всё хорошо, я рядом...\n\n🤕　👧❤️", get_kb("Открыть глаза 👁", "step_5"))


@router.callback_query(F.data == "step_5")
async def quest_step_5(call: types.CallbackQuery):
    iid = call.inline_message_id
    await call.answer()

    await safe_edit(iid, "👦 Ты: Даша... Ты лучшая. Спасибо!\n\n👦✨❤️✨👧")
    await asyncio.sleep(2.5)
    await safe_edit(iid, "🌹 👩‍❤️‍👨 🌹\n\nКОНЕЦ ИСТОРИИ", get_kb("Сначала 🔄", "restart_quest"))


@router.callback_query(F.data == "restart_quest")
async def restart_quest(call: types.CallbackQuery):
    # Просто возвращаем к первому шагу квеста
    await safe_edit(call.inline_message_id, "👧 Даша: Привет, любимый! Смотри: ❤️",
                    get_kb("Взять сердечко ❤️", "step_1"))


# --- ВЕБ-СЕРВЕР ДЛЯ RENDER (ЧТОБЫ НЕ ЗАСЫПАЛ) ---
async def handle(request):
    return web.Response(text="I'm alive!")

async def run_http_server():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', int(os.getenv("PORT", 8080)))
    await site.start()
    print(f">>> Веб-сервер запущен на порту {os.getenv('PORT', 8080)}")

# --- ЗАПУСК ---
async def main():
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)
    
    # Запускаем веб-сервер фоном
    await run_http_server()
    
    print(">>> ИНЛАЙН-БОТ ВЫСШЕГО КАЧЕСТВА ЗАПУЩЕН!")
    await dp.start_polling(bot)


if __name__ == '__main__':
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass