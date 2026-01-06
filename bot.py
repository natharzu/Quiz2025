import os
import json
from datetime import time

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# -----------------------------
# READ TOKEN SAFELY
# -----------------------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError(
        "❌ BOT_TOKEN is missing! Добавь переменную окружения BOT_TOKEN в Railway → Variables."
    )

masked = BOT_TOKEN[:6] + "..." if len(BOT_TOKEN) > 6 else BOT_TOKEN
print(f"🔐 BOT_TOKEN detected: {masked}")

# -----------------------------
# READ CHANNEL_ID SAFELY
# -----------------------------
CHANNEL_ID_RAW = os.getenv("CHANNEL_ID")

if not CHANNEL_ID_RAW:
    raise RuntimeError(
        "❌ CHANNEL_ID is missing! Добавь переменную окружения CHANNEL_ID в Railway → Variables."
    )

try:
    CHANNEL_ID = int(CHANNEL_ID_RAW)
except ValueError:
    raise RuntimeError(
        f"❌ CHANNEL_ID must be an integer. Сейчас: {CHANNEL_ID_RAW}"
    )

print(f"📡 CHANNEL_ID detected: {CHANNEL_ID}")

# -----------------------------
# LOAD QUESTIONS
# -----------------------------
JSON_FILE = "JNQuiz2025.json"

with open(JSON_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

questions = data.get("questions", [])
print(f"📚 Loaded {len(questions)} questions")

# Global sequential index
state = {"index": 0}

# -----------------------------
# SEND QUIZ (SEQUENTIAL + NUMBERING)
# -----------------------------
async def send_quiz(context: ContextTypes.DEFAULT_TYPE, q, index):
    total = len(questions)
    number = index + 1

    text = f"*Вопрос {number}/{total}*\n\n"
    text += f"❓ *{q['question']}*\n\n"

    for key, value in q["options"].items():
        text += f"*{key})* {value}\n"

    keyboard = [
        [
            InlineKeyboardButton("A", callback_data=f"answer|A|{index}"),
            InlineKeyboardButton("B", callback_data=f"answer|B|{index}"),
            InlineKeyboardButton("C", callback_data=f"answer|C|{index}"),
            InlineKeyboardButton("D", callback_data=f"answer|D|{index}"),
        ]
    ]

    await context.bot.send_message(
        chat_id=CHANNEL_ID,
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# -----------------------------
# HANDLE ANSWER (PRIVATE FEEDBACK)
# -----------------------------
async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # Telegram покажет выбранный вариант только пользователю

    user_choice, _, q_index_str = query.data.split("|")
    q_index = int(q_index_str)
    q = questions[q_index]

    correct = q["correct"]

    if user_choice == correct:
        reply = "✅ Правильно!"
    else:
        reply = f"❌ Неправильно. Правильный ответ: *{correct}*"

    reply += f"\n\nℹ️ {q['explanation']}"

    # отправляем объяснение в личку пользователю
    await context.bot.send_message(
        chat_id=query.from_user.id,
        text=reply,
        parse_mode="Markdown"
    )

# -----------------------------
# NEXT QUESTION (SEQUENTIAL)
# -----------------------------
async def next_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    idx = state["index"]
    q = questions[idx]

    await send_quiz(context, q, idx)

    state["index"] = (idx + 1) % len(questions)

# -----------------------------
# START QUIZ
# -----------------------------
async def start_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await next_question(update, context)

# -----------------------------
# DAILY QUIZ (10 SEQUENTIAL QUESTIONS)
# -----------------------------
async def daily_quiz(context: ContextTypes.DEFAULT_TYPE):
    for _ in range(10):
        idx = state["index"]
        q = questions[idx]

        await send_quiz(context, q, idx)

        state["index"] = (idx + 1) % len(questions)

# -----------------------------
# DEBUG COMMAND
# -----------------------------
async def debug(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    text = (
        f"🔍 Debug info:\n"
        f"- chat_id: `{chat.id}`\n"
        f"- type: {chat.type}\n"
        f"- title: {chat.title}\n"
        f"- username: @{chat.username if chat.username else '—'}"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

# -----------------------------
# MAIN
# -----------------------------
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_quiz))
    app.add_handler(CommandHandler("next", next_question))
    app.add_handler(CommandHandler("debug", debug))

    app.add_handler(CallbackQueryHandler(handle_answer, pattern="^answer"))

    app.job_queue.run_daily(
        daily_quiz,
        time=time(10, 0)
    )

    app.run_polling()

if __name__ == "__main__":
    main()
