import asyncio
import os
import json
import random
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import FSInputFile, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from dotenv import load_dotenv

# Load the .env file
load_dotenv()


BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "data")
PHOTOS_DIR = os.path.join(DATA_DIR, "memo_photo")

TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TOKEN:
    print("Warning: TELEGRAM_TOKEN not set. Set env var to run the bot.")

bot = Bot(token=TOKEN) if TOKEN else None
dp = Dispatcher()

QUESTIONS_PATH = os.path.join(BASE_DIR, "questions.json")
with open(QUESTIONS_PATH, "r", encoding="utf-8") as f:
    QUESTIONS_DATA = json.load(f)

blocks = QUESTIONS_DATA.get("blocks", [])
question_map = {}
block_map = {}
for b in blocks:
    block_map[b["id"]] = b
    for q in b.get("questions", []):
        question_map[q["id"]] = q

# Load simulations (quize.json) for mini-simulations
SIM_PATH = os.path.join(BASE_DIR, "quize.json")
SIMULATIONS = []
if os.path.exists(SIM_PATH):
    try:
        with open(SIM_PATH, "r", encoding="utf-8") as f:
            sim_data = json.load(f)
            SIMULATIONS = sim_data.get("simulations", [])
    except Exception:
        SIMULATIONS = []

# Memo items mapping
MEMO_ITEMS = {
    1: {
        "title": "Основные формы голосования РФ",
        "file": os.path.join(PHOTOS_DIR, "pamyatka_formy_golosovania.png")
    },
    2: {
        "title": "Избирательное право России",
        "file": os.path.join(PHOTOS_DIR, "pamyatka_izbiratelnoe_pravo.png")
    },
    3: {
        "title": "Избирательные системы",
        "file": os.path.join(PHOTOS_DIR, "pamyatka_izbiratelnye_sistemy.png")
    },
    4: {
        "title": "Основные принципы избирательного права",
        "file": os.path.join(PHOTOS_DIR, "pamyatka_printsipy.png")
    },
    5: {
        "title": "Стадии избирательного процесса",
        "file": os.path.join(PHOTOS_DIR, "pamyatka_stadii_izbiratelnogo_protsessa.png")
    },
    6: {
        "title": "Избирательные цензы",
        "file": os.path.join(PHOTOS_DIR, "pamyatka_tsenzy.png")
    },
    7: {
        "title": "Ключевые участники избирательного процесса",
        "file": os.path.join(PHOTOS_DIR, "pamyatki_uchastniki_izbir_protsessa.png")
    }
}

# Main menu keyboard
main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📋 Памятка"), KeyboardButton(text="❓ Частые вопросы")],
        [KeyboardButton(text="🎯 Пройти тест"), KeyboardButton(text="ℹ️ Помощь")],
    ],
    resize_keyboard=True
)

@dp.message(Command("start", "help"))
async def send_welcome(message: types.Message):
    await message.reply(
        "Привет! 👋 Я бот-справочник по избирательному праву.\n\n"
        "Выбери нужный раздел:",
        reply_markup=main_keyboard
    )


@dp.message(F.text == "📋 Памятка")
async def memo_handler(message: types.Message):
    text = "Выберите тему справочника:\n\n"
    buttons = []
    for item_id, item_data in MEMO_ITEMS.items():
        text += f"{item_id}. {item_data['title']}\n"
        buttons.append([InlineKeyboardButton(text=f"{item_id}. {item_data['title']}", callback_data=f"memo_{item_id}")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.reply(text, reply_markup=keyboard)


@dp.callback_query(F.data.startswith("memo_"))
async def memo_callback(callback_query: types.CallbackQuery):
    memo_id = int(callback_query.data.split("_")[1])
    if memo_id in MEMO_ITEMS:
        item = MEMO_ITEMS[memo_id]
        if os.path.exists(item["file"]):
            try:
                await bot.send_photo(
                    callback_query.message.chat.id,
                    FSInputFile(item["file"]),
                    caption=item["title"]
                )
            except Exception as e:
                await callback_query.message.reply(f"Ошибка при отправке фото: {e}")
        else:
            await callback_query.message.reply(f"Файл не найден: {item['file']}")
    await callback_query.answer()


@dp.message(F.text == "❓ Частые вопросы")
async def faq_handler(message: types.Message):
    text = "Часто спрашиваемые вопросы:\n\n"
    buttons = []
    for b in blocks:
        text += f"{b['id']}. {b['title']}\n"
        buttons.append([InlineKeyboardButton(text=f"{b['id']}. {b['title']}", callback_data=f"block_{b['id']}")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.reply(text, reply_markup=keyboard)


@dp.callback_query(F.data.startswith("block_"))
async def block_callback(callback_query: types.CallbackQuery):
    block_id = int(callback_query.data.split("_")[1])
    if block_id in block_map:
        b = block_map[block_id]
        text = f"Вопросы — {b['title']}:\n\n"
        buttons = []
        for q in b.get("questions", []):
            text += f"{q['id']}. {q['q']}\n"
            buttons.append([InlineKeyboardButton(text=f"❓ {q['id']}", callback_data=f"question_{q['id']}")])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        await callback_query.message.reply(text, reply_markup=keyboard)
    await callback_query.answer()


@dp.callback_query(F.data.startswith("question_"))
async def question_callback(callback_query: types.CallbackQuery):
    question_id = int(callback_query.data.split("_")[1])
    if question_id in question_map:
        q = question_map[question_id]
        text = f"❓ {q['q']}\n\n✅ {q['a']}"
        await callback_query.message.reply(text)
    await callback_query.answer()


# Track which simulation user is on
user_sim_state = {}


@dp.message(F.text == "🎯 Пройти тест")
async def test_handler(message: types.Message):
    if not SIMULATIONS:
        await message.reply("Симуляции не найдены. Добавьте файл `quize.json` в проект.")
        return
    chat_id = message.chat.id
    user_sim_state[chat_id] = SIMULATIONS[0].get('id')
    sim = SIMULATIONS[0]
    await send_raw_simulation(chat_id, sim)


# Функция для вывода теста в сыром текстовом формате с инлайн-кнопками для выбора ответа
async def send_raw_simulation(chat_id: int, sim: dict):
    text = f"🎭 МИНИ-СИМУЛЯЦИЯ — Сценарий {sim.get('id')}\n\n{sim.get('scenario')}\n\n"
    
    buttons = []
    for opt in sim.get('options', []):
        text += f"{opt['id']}. {opt['text']}\n"
        buttons.append([InlineKeyboardButton(text=f"Вариант {opt['id']}", callback_data=f"sim_{sim['id']}_opt_{opt['id']}")])
        
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await bot.send_message(chat_id, text, reply_markup=keyboard)


async def send_simulation_message(chat_id: int, sim: dict, reply_to: types.Message | None = None):
    # Эта функция теперь тоже использует формат raw вывода при переключении сценариев
    await send_raw_simulation(chat_id, sim)


@dp.callback_query(F.data.startswith("sim_"))
async def sim_callback(callback_query: types.CallbackQuery):
    data = callback_query.data
    parts = data.split("_")
    
    if len(parts) >= 4 and parts[2] == "opt":
        try:
            sim_id = int(parts[1])
        except ValueError:
            await callback_query.answer()
            return
        opt_id = parts[3]
        sim = next((s for s in SIMULATIONS if s.get('id') == sim_id), None)
        if not sim:
            await callback_query.message.reply("Сценарий не найден.")
            await callback_query.answer()
            return
        opt = next((o for o in sim.get('options', []) if o.get('id') == opt_id), None)
        if not opt:
            await callback_query.message.reply("Вариант не найден.")
            await callback_query.answer()
            return

        correct = opt.get('is_correct', False)
        header = "✅ Правильно!" if correct else "❌ Неверно"
        feedback = opt.get('feedback', '')
        consequences = opt.get('consequences', '')
        text = f"{header}\n\n{feedback}\n\nПоследствия: {consequences}"

        idx = next((i for i, s in enumerate(SIMULATIONS) if s.get('id') == sim_id), None)
        next_btns = []
        next_btns.append(InlineKeyboardButton(text="Попробовать ещё раз", callback_data=f"sim_retry_{sim_id}"))
        if idx is not None and idx + 1 < len(SIMULATIONS):
            next_id = SIMULATIONS[idx + 1].get('id')
            next_btns.append(InlineKeyboardButton(text="Следующий сценарий", callback_data=f"sim_next_{next_id}"))
        else:
            next_btns.append(InlineKeyboardButton(text="Завершить симуляцию", callback_data=f"sim_end"))

        keyboard = InlineKeyboardMarkup(inline_keyboard=[[b] for b in next_btns])
        await callback_query.message.reply(text, reply_markup=keyboard)
        await callback_query.answer()
        return

    if data.startswith("sim_retry_"):
        try:
            sim_id = int(data.split("_")[2])
        except Exception:
            await callback_query.answer()
            return
        sim = next((s for s in SIMULATIONS if s.get('id') == sim_id), None)
        if sim:
            await send_simulation_message(callback_query.message.chat.id, sim, reply_to=callback_query.message)
        await callback_query.answer()
        return

    if data.startswith("sim_next_"):
        try:
            next_id = int(data.split("_")[2])
        except Exception:
            await callback_query.answer()
            return
        sim = next((s for s in SIMULATIONS if s.get('id') == next_id), None)
        if sim:
            await send_simulation_message(callback_query.message.chat.id, sim, reply_to=callback_query.message)
        await callback_query.answer()
        return

    if data == "sim_end":
        await callback_query.message.reply("Симуляция завершена. Спасибо за участие! Возврат в меню — через кнопку 'ℹ️ Помощь' или '📋 Памятка'.")
        await callback_query.answer()
        return


@dp.message(F.text == "ℹ️ Помощь")
async def help_handler(message: types.Message):
    await message.reply(
        "ℹ️ Помощь\n\n"
        "📋 Памятка — выбери тему и получи памятку в виде фотографии\n"
        "❓ Частые вопросы — ответы на популярные вопросы об избирательном праве\n"
        "🎯 Пройти тест — тестирование знаний\n\n"
        "Также ты можешь отправить номер вопроса, чтобы получить ответ."
    )


@dp.message()
async def text_handler(message: types.Message):
    txt = message.text.strip()
    if txt.isdigit():
        num = int(txt)
        if num in block_map:
            b = block_map[num]
            text = f"Вопросы — {b['title']}:\n\n"
            buttons = []
            for q in b.get("questions", []):
                text += f"{q['id']}. {q['q']}\n"
                buttons.append([InlineKeyboardButton(text=f"❓ {q['id']}", callback_data=f"question_{q['id']}")])
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
            await message.reply(text, reply_markup=keyboard)
            return
        if num in question_map:
            q = question_map[num]
            text = f"❓ {q['q']}\n\n✅ {q['a']}"
            await message.reply(text)
            return
    await message.reply("Не распознана команда. Используй кнопки меню выше или отправь номер вопроса/блока.")


async def main():
    if not TOKEN:
        print("Set TELEGRAM_TOKEN environment variable and run again.")
        return
    await dp.start_polling(bot, skip_updates=True)


if __name__ == '__main__':
    asyncio.run(main())