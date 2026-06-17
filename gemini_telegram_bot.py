"""
Telegram Bot powered by Google Gemini (free tier)
Compatible with python-telegram-bot v13.x
"""

import os
import logging
import requests
from telegram import Update
from telegram.ext import Updater, MessageHandler, CommandHandler, Filters, CallbackContext

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
MODEL = os.environ.get("MODEL", "gemini-1.5-flash")
SYSTEM_PROMPT = os.environ.get(
    "SYSTEM_PROMPT",
    "انت مساعد ذكي اسمه Hermes. تجاوب بالعربية او حسب لغة المستخدم. كن مفيدا ومختصرا."
)

GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"
user_history = {}
MAX_HISTORY = 8


def call_gemini(messages):
    payload = {
        "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": messages,
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 800},
    }
    r = requests.post(f"{GEMINI_URL}?key={GEMINI_API_KEY}", json=payload, timeout=60)
    r.raise_for_status()
    data = r.json()
    if "candidates" not in data:
        raise RuntimeError(f"Gemini error: {data}")
    return data["candidates"][0]["content"]["parts"][0]["text"].strip()


def to_gemini_format(history):
    out = []
    for m in history:
        role = "model" if m["role"] == "assistant" else "user"
        out.append({"role": role, "parts": [{"text": m["content"]}]})
    return out


def start_cmd(update, ctx):
    update.message.reply_text("اهلا! بوت Gemini شغال. ابعت اي رسالة.")


def handle(update, ctx):
    uid = update.effective_user.id
    text = update.message.text
    h = user_history.setdefault(uid, [])
    h.append({"role": "user", "content": text})
    h[:] = h[-MAX_HISTORY:]
    try:
        reply = call_gemini(to_gemini_format(h))
    except Exception as e:
        reply = f"صار خطا: {e}"
    h.append({"role": "assistant", "content": reply})
    h[:] = h[-MAX_HISTORY:]
    update.message.reply_text(reply[:4000])


def main():
    print("Starting bot...", flush=True)
    updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start_cmd))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle))
    print("Bot running...", flush=True)
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
