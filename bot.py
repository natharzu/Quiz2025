import os
import json
import random
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
        "❌ BOT_TOKEN is missing! "
        "Добавь переменную окружения BOT_TOKEN в Railway → Variables."
    )

# Маскируем токен в логах
masked = BOT_TOKEN[:6] + "..." if len(BOT_TOKEN) > 6 else BOT_TOKEN
print(f"🔐 BOT_TOKEN detected: {masked}")

# -----------------------------
# CONFIG
# -----------------------------
CHANNEL_ID = -1000000000000   # ← замени на ID твоего канала
JSON_FILE = "JNQuiz2025.json"

# -----------------------------
# LOAD QUESTIONS
# -----------------------------
with open(JSON_FILE, "r", encoding="utf-8") as f:
    questions = json.load(f)

# Преобразуем dict → list, если нужно
if isinstance(questions, dict):
    questions = list(questions.values())

print(f"📚 Loaded {len(questions)} questions")


state = {"index": 0}

# -----------------------------
# SEND QUIZ WITH INLINE BUTTONS
# -----------------------------
async def send_quiz(context: ContextTypes.DEFAULT_TYPE, q):
    text = f"❓ *{q['question']}*\n\n"
    for key, value in q["options"].items():
        text += f"*{key})* {value}\n"

    keyboard = [
        [
            InlineKeyboardButton("A", callback_data="answer|A"),
            InlineKeyboardButton("B", callback_data="answer|B"),
            InlineKeyboardButton("C", callback_data="answer|C"),
            InlineKeyboardButton("D", callback_data="answer|D"),
        ]
    ]

    await context.bot.send_message(
        chat_id=CHANNEL_ID,
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# -----------------------------
# HANDLE ANSWER
# -----------------------------
async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_choice = query.data.split("|")[1]
    q = questions[state["index"] - 1]
    correct = q["correct"]

    if user_choice == correct:
        reply = "✅ Правильно!"
    else:
        reply = f"❌ Неправильно. Правильный ответ: *{correct}*"

    reply += f"\n\nℹ️ {q['explanation']}"

    await query.edit_message_reply_markup(None)
    await query.message.reply_text(reply, parse_mode="Markdown")

# -----------------------------
# NEXT QUESTION
# -----------------------------
async def next_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = questions[state["index"]]
    await send_quiz(context, q)
    state["index"] = (state["index"] + 1) % len(questions)

# -----------------------------
# RANDOM QUESTION
# -----------------------------
async def random_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = random.choice(questions)
    await send_quiz(context, q)

# -----------------------------
# START QUIZ
# -----------------------------
async def start_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await next_question(update, context)

# -----------------------------
# DAILY QUIZ (10 QUESTIONS)
# -----------------------------
async def daily_quiz(context: ContextTypes.DEFAULT_TYPE):
    for _ in range(10):
        q = questions[state["index"]]
        await send_quiz(context, q)
        state["index"] = (state["index"] + 1) % len(questions)

# -----------------------------
# MAIN
# -----------------------------
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_quiz))
    app.add_handler(CommandHandler("next", next_question))
    app.add_handler(CommandHandler("random", random_question))

    app.add_handler(CallbackQueryHandler(handle_answer, pattern="^answer"))

    # Daily quiz at 10:00 UTC (12:00 Oslo)
    app.job_queue.run_daily(
        daily_quiz,
        time=time(10, 0)
    )

    app.run_polling()

if __name__ == "__main__":
    main()
