import os
import json
import random
import logging
from dotenv import load_dotenv

# Импортируем модули VK API
import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Загрузка файла .env
load_dotenv()

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "data")
PHOTOS_DIR = os.path.join(DATA_DIR, "memo_photo")

TOKEN = os.getenv("VK_TOKEN")
GROUP_ID = os.getenv("GROUP_ID")

if not TOKEN or not GROUP_ID:
    print("Критическая ошибка: Убедитесь, что VK_TOKEN и GROUP_ID заданы в .env")
    exit(1)

# Авторизация в VK API
vk_session = vk_api.VkApi(token=TOKEN)
vk = vk_session.get_api()
longpoll = VkBotLongPoll(vk_session, group_id=GROUP_ID)

# Загрузка FAQ (questions.json)
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

# Загрузка симуляций (quize.json)
SIM_PATH = os.path.join(BASE_DIR, "quize.json")
SIMULATIONS = []
if os.path.exists(SIM_PATH):
    try:
        with open(SIM_PATH, "r", encoding="utf-8") as f:
            sim_data = json.load(f)
            SIMULATIONS = sim_data.get("simulations", [])
    except Exception:
        SIMULATIONS = []

# Карты памяток
MEMO_ITEMS = {
    1: {"title": "Основные формы голосования РФ", "file": os.path.join(PHOTOS_DIR, "pamyatka_formy_golosovania.png")},
    2: {"title": "Избирательное право России", "file": os.path.join(PHOTOS_DIR, "pamyatka_izbiratelnoe_pravo.png")},
    3: {"title": "Избирательные системы", "file": os.path.join(PHOTOS_DIR, "pamyatka_izbiratelnye_sistemy.png")},
    4: {"title": "Основные принципы избирательного права", "file": os.path.join(PHOTOS_DIR, "pamyatka_printsipy.png")},
    5: {"title": "Стадии избирательного процесса", "file": os.path.join(PHOTOS_DIR, "pamyatka_stadii_izbiratelnogo_protsessa.png")},
    6: {"title": "Избирательные цензы", "file": os.path.join(PHOTOS_DIR, "pamyatka_tsenzy.png")},
    7: {"title": "Ключевые участники избирательного процесса", "file": os.path.join(PHOTOS_DIR, "pamyatki_uchastniki_izbir_protsessa.png")}
}

# Хранилище состояний симуляции для пользователей
user_sim_state = {}

# Функция отправки текстовых сообщений с клавиатурой
def send_msg(user_id, text, keyboard=None):
    params = {
        'user_id': user_id,
        'message': text,
        'random_id': random.randint(1, 10000000)
    }
    if keyboard:
        params['keyboard'] = keyboard.get_keyboard()
    vk.messages.send(**params)

# Функция для загрузки и отправки фото во ВКонтакте
def send_photo(user_id, file_path, caption=""):
    try:
        upload = vk_api.VkUpload(vk_session)
        photo = upload.photo_messages(photos=file_path)[0]
        attachment = f"photo{photo['owner_id']}_{photo['id']}"
        
        vk.messages.send(
            user_id=user_id,
            attachment=attachment,
            message=caption,
            random_id=random.randint(1, 10000000)
        )
    except Exception as e:
        send_msg(user_id, f"Ошибка при отправке фото: {e}")

# Главное меню (обычные кнопки под полем ввода)
def get_main_keyboard():
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button("📋 Памятка", color=VkKeyboardColor.PRIMARY)
    keyboard.add_button("❓ Частые вопросы", color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button("🎯 Пройти тест", color=VkKeyboardColor.POSITIVE)
    keyboard.add_button("ℹ️ Помощь", color=VkKeyboardColor.SECONDARY)
    return keyboard

# Меню выбора памяток (Инлайн-кнопки в самом сообщении)
def show_memo_menu(user_id):
    text = "Выберите тему справочника:\n\n"
    keyboard = VkKeyboard(inline=True)
    
    for item_id, item_data in MEMO_ITEMS.items():
        text += f"{item_id}. {item_data['title']}\n"
        keyboard.add_callback_button(
            label=f"Тема {item_id}",
            color=VkKeyboardColor.SECONDARY,
            payload={"type": f"memo_{item_id}"}
        )
        if item_id % 3 == 0:  # Перенос строки каждые 3 кнопки
            keyboard.add_line()
            
    send_msg(user_id, text, keyboard)

# Меню выбора разделов FAQ (Инлайн-кнопки) с автопереносом строк
def show_faq_menu(user_id):
    text = "Часто спрашиваемые вопросы:\n\n"
    keyboard = VkKeyboard(inline=True)
    
    for index, b in enumerate(blocks):
        # Если это не первая кнопка и индекс делится на 2, делаем перенос строки
        # (в ряду будет по 2 кнопки, что отлично смотрится на мобильных телефонах)
        if index > 0 and index % 2 == 0:
            keyboard.add_line()
            
        text += f"{b['id']}. {b['title']}\n"
        keyboard.add_callback_button(
            label=f"Блок {b['id']}",
            color=VkKeyboardColor.PRIMARY,
            payload={"type": f"block_{b['id']}"}
        )
        
    send_msg(user_id, text, keyboard)

# Отображение вопросов внутри выбранного блока FAQ с автопереносом строк
def show_block_questions(user_id, block_id):
    if block_id in block_map:
        b = block_map[block_id]
        text = f"Вопросы — {b['title']}:\n\n"
        keyboard = VkKeyboard(inline=True)
        
        for index, q in enumerate(b.get("questions", [])):
            if index > 0 and index % 2 == 0:
                keyboard.add_line()
                
            text += f"{q['id']}. {q['q']}\n"
            keyboard.add_callback_button(
                label=f"❓ Вопрос {q['id']}",
                color=VkKeyboardColor.SECONDARY,
                payload={"type": f"question_{q['id']}"}
            )
                
        send_msg(user_id, text, keyboard)

# Генерация сценария симуляции (Инлайн-кнопки)
def send_raw_simulation(user_id, sim):
    text = f"🎭 МИНИ-СИМУЛЯЦИЯ — Сценарий {sim.get('id')}\n\n{sim.get('scenario')}\n\n"
    keyboard = VkKeyboard(inline=True)
    
    for opt in sim.get('options', []):
        text += f"{opt['id']}. {opt['text']}\n"
        keyboard.add_callback_button(
            label=f"Вариант {opt['id']}",
            color=VkKeyboardColor.PRIMARY,
            payload={"type": f"sim_{sim['id']}_opt_{opt['id']}"}
        )
    send_msg(user_id, text, keyboard)

# Обработка нажатий на инлайн-кнопки (Callback-события)
def handle_callback(event):
    user_id = event.obj.user_id
    payload = event.obj.payload
    payload_type = payload.get("type", "")
    
    # 1. Обработка Памяток
    if payload_type.startswith("memo_"):
        memo_id = int(payload_type.split("_")[1])
        if memo_id in MEMO_ITEMS:
            item = MEMO_ITEMS[memo_id]
            if os.path.exists(item["file"]):
                send_photo(user_id, item["file"], item["title"])
            else:
                send_msg(user_id, f"Файл не найден: {item['file']}")
                
    # 2. Обработка Выбора Блока FAQ
    elif payload_type.startswith("block_"):
        block_id = int(payload_type.split("_")[1])
        show_block_questions(user_id, block_id)
        
    # 3. Обработка конкретного вопроса FAQ
    elif payload_type.startswith("question_"):
        q_id = int(payload_type.split("_")[1])
        if q_id in question_map:
            q = question_map[q_id]
            send_msg(user_id, f"❓ {q['q']}\n\n✅ {q['a']}")
            
    # 4. Обработка ответов симулятора
    elif payload_type.startswith("sim_"):
        parts = payload_type.split("_")
        
        if len(parts) >= 4 and parts[2] == "opt":
            sim_id = int(parts[1])
            opt_id = parts[3]
            
            sim = next((s for s in SIMULATIONS if s.get('id') == sim_id), None)
            if not sim: return
            opt = next((o for o in sim.get('options', []) if o.get('id') == opt_id), None)
            if not opt: return
            
            correct = opt.get('is_correct', False)
            header = "✅ Правильно!" if correct else "❌ Неверно"
            text = f"{header}\n\n{opt.get('feedback', '')}\n\nПоследствия: {opt.get('consequences', '')}"
            
            # Строим кнопки навигации теста
            idx = next((i for i, s in enumerate(SIMULATIONS) if s.get('id') == sim_id), None)
            keyboard = VkKeyboard(inline=True)
            
            keyboard.add_callback_button(
                label="Попробовать ещё раз", 
                color=VkKeyboardColor.SECONDARY, 
                payload={"type": f"sim_retry_{sim_id}"}
            )
            
            if idx is not None and idx + 1 < len(SIMULATIONS):
                next_id = SIMULATIONS[idx + 1].get('id')
                keyboard.add_line()
                keyboard.add_callback_button(
                    label="Следующий сценарий", 
                    color=VkKeyboardColor.POSITIVE, 
                    payload={"type": f"sim_next_{next_id}"}
                )
            else:
                keyboard.add_line()
                keyboard.add_callback_button(
                    label="Завершить симуляцию", 
                    color=VkKeyboardColor.NEGATIVE, 
                    payload={"type": "sim_end"}
                )
                
            send_msg(user_id, text, keyboard)
            
        elif payload_type.startswith("sim_retry_") or payload_type.startswith("sim_next_"):
            target_id = int(parts[2])
            sim = next((s for s in SIMULATIONS if s.get('id') == target_id), None)
            if sim:
                send_raw_simulation(user_id, sim)
                
        elif payload_type == "sim_end":
            send_msg(user_id, "Симуляция завершена. Спасибо за участие!", get_main_keyboard())

    # Обязательно подтверждаем обработку callback-кнопки во VK
    vk.messages.sendMessageEventAnswer(
        event_id=event.obj.event_id,
        user_id=event.obj.user_id,
        peer_id=event.obj.peer_id
    )

# Главный цикл прослушивания событий
def main():
    print("Бот ВКонтакте успешно запущен и слушает сервер...")
    
    for event in longpoll.listen():
        # Обработка входящих текстовых сообщений
        if event.type == VkBotEventType.MESSAGE_NEW and event.from_user:
            user_id = event.obj.message['from_id']
            text = event.obj.message['text'].strip()
            
            if text in ["/start", "/help", "ℹ️ Помощь"]:
                welcome_text = (
                    "Привет! 👋 Я бот-справочник по избирательному праву.\n\n"
                    "📋 Памятка — темы в виде инфографики\n"
                    "❓ Частые вопросы — база знаний\n"
                    "🎯 Пройти тест — интерактивный симулятор\n\n"
                    "Также можно отправить номер блока или вопроса текстом."
                )
                send_msg(user_id, welcome_text, get_main_keyboard())
                
            elif text == "📋 Памятка":
                show_memo_menu(user_id)
                
            elif text == "❓ Частые вопросы":
                show_faq_menu(user_id)
                
            elif text == "🎯 Пройти тест":
                if not SIMULATIONS:
                    send_msg(user_id, "Симуляции не найдены. Добавьте файл `quize.json` в проект.")
                else:
                    user_sim_state[user_id] = SIMULATIONS[0].get('id')
                    send_raw_simulation(user_id, SIMULATIONS[0])
                    
            elif text.isdigit():
                num = int(text)
                if num in block_map:
                    show_block_questions(user_id, num)
                elif num in question_map:
                    q = question_map[num]
                    send_msg(user_id, f"❓ {q['q']}\n\n✅ {q['a']}")
                else:
                    send_msg(user_id, "Такого номера вопроса или блока нет в базе.")
            else:
                send_msg(user_id, "Команда не распознана. Используйте кнопки меню.", get_main_keyboard())
                
        # Обработка кликов по инлайн кнопкам
        elif event.type == VkBotEventType.MESSAGE_EVENT:
            handle_callback(event)

if __name__ == '__main__':
    main()