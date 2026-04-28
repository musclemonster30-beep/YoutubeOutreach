import time
import requests
import os

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def send_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": text
    }
    requests.post(url, data=data)


def run_outreach():
    print("Outreach bot started")

    while True:
        try:
            send_message("Bot is alive 🚀")
            time.sleep(60)
        except Exception as e:
            print("Error:", e)
            time.sleep(10)
