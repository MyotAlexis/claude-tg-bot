import os
import anthropic
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_KEY")

client = anthropic.Anthropic(
    api_key=ANTHROPIC_KEY,
    base_url="https://api.proxyapi.ru/anthropic"
)

chat_histories = {}

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_text = update.message.text

    if user_id not in chat_histories:
        chat_histories[user_id] = []

    chat_histories[user_id].append({
        "role": "user",
        "content": user_text
    })

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system="Ты полезный ассистент. Отвечай кратко и по делу. Если нужна актуальная информация — используй поиск.",
        messages=chat_histories[user_id],
        tools=[{
            "type": "web_search_20250305",
            "name": "web_search"
        }]
    )

    # Собираем полный ответ включая результаты поиска
    assistant_reply = ""
    for block in response.content:
        if hasattr(block, "text"):
            assistant_reply += block.text

    if not assistant_reply:
        assistant_reply = "Не удалось получить ответ."

    chat_histories[user_id].append({
        "role": "assistant",
        "content": assistant_reply
    })

    await update.message.reply_text(assistant_reply)

app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.run_polling()
