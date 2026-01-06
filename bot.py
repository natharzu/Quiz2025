import json
from telegram import Update, Poll
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import os
import random

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

with open("JNQuiz2025.json", "r", encoding="utf-8") as f:
    data = json.load(f)

questions = data["questions"]
state = {"index": 0}

async def send_quiz(context: ContextTypes.DEFAULT_TYPE, q):
    options = list(q["options"].values())
    correct_letter = q["correct"]
    correct_index = list(q["options"].keys()).index(correct_letter)

    await context.bot.send_poll(
        chat_id=CHANNEL_ID,
        question=q["question"],
        options=options,
        type=Poll.QUIZ,
        correct_option_id=correct_index,
        explanation=q["explanation"]
    )

async def next_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = questions[state["index"]]
    await send_quiz(context, q)
    state["index"] = (state["index"] + 1) % len(questions)

async def random_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = random.choice(questions)
    await send_quiz(context, q)

async def start_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state["index"] = 0
    await next_question(update, context)

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state["index"] = 0
    await update.message.reply_text("Progress reset.")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Next question index: {state['index']}")

app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("next", next_question))
app.add_handler(CommandHandler("random", random_question))
app.add_handler(CommandHandler("startquiz", start_quiz))
app.add_handler(CommandHandler("reset", reset))
app.add_handler(CommandHandler("stats", stats))

app.run_polling()
