# Telegram Quiz Bot — Russian Elective Franchise

Telegram bot (aiogram 3.x) for serving election rights Q&A with memo photos, thematic blocks, raw text tests, and mini-simulations in Russian.

## Quick Start

### 1. Get a Telegram Token
Create a bot via BotFather on Telegram to get your token.

### 2. Create `.env` file
Copy `.env.example` to `.env` and add your token:

```bash
cp .env.example .env
# Edit .env and add your token:
# TELEGRAM_TOKEN=<your-token>
```

Or set env var directly:

```powershell
$env:TELEGRAM_TOKEN = "<your-token>"
```

### 3. Install & Run

```bash
pip install -r requirements.txt
python bot.py
```

## Files

- `bot.py` — main bot with callbacks, keyboards, memo photos, tests, mini-simulations
- `questions.json` — thematic blocks with Q&A (Russian)
- `quize.json` — scenario-based mini-simulations (5 scenarios with options)
- `data/memo_photo/` — memo images (7 pamphlets)
- `requirements.txt` — dependencies
- `.env.example` — template for environment variables

## Features

### Main Menu (Button-Based)
- **📋 Памятка** — Select a memo topic to view infographic photos
- **❓ Частые вопросы** — Browse Q&A by thematic blocks (with callbacks)
- **🎯 Пройти тест** — Raw text test: see all questions, type number to get answer
- **🎭 Мини-симуляция** — Interactive scenario-based simulations with feedback
- **ℹ️ Помощь** — Help & instructions

### Memo Photos (📋 Памятка)
1. Основные формы голосования РФ
2. Избирательное право России
3. Избирательные системы
4. Основные принципы избирательного права
5. Стадии избирательного процесса
6. Избирательные цензы
7. Ключевые участники избирательного процесса

### Q&A Blocks (❓ Частые вопросы)
- Общие права и «Госуслуги»
- Процедура на участке
- Если я не могу прийти сам
- Сложные случаи (спорные вопросы)
- Ваши права

### Test Format (🎯 Пройти тест)
- Displays raw text with all questions grouped by theme
- User sends question number (e.g., `1`, `5`, `13`) to get the answer
- No callbacks, simple text-based interaction

### Mini-Simulations (🎭 Мини-симуляция)
- 5 real-life voting scenarios
- 3 options per scenario (A, B, C)
- Instant feedback with legal consequences
- Retry or advance to next scenario

## How to Use

1. Start bot → see main menu
2. **For photos:** Click "📋 Памятка" → select topic → view photo
3. **For FAQ:** Click "❓ Частые вопросы" → select block → click question → view answer
4. **For test:** Click "🎯 Пройти тест" → see all questions → type number → get answer
5. **For simulations:** Click "🎭 Мини-симуляция" → read scenario → pick A/B/C → get feedback → retry or next

## Notes

- Uses `python-dotenv` to load `TELEGRAM_TOKEN` from `.env`
- Buttons use inline/reply keyboards; all text is in Russian with emoji indicators
- Review legal accuracy of Q&A before publishing
- Fixed: `InputFile` → `FSInputFile` for aiogram 3.x compatibility
