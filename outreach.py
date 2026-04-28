import time
import requests
import os

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def send_message(text):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {
            "chat_id": CHAT_ID,
            "text": text
        }
        r = requests.post(url, data=data)
        print("TELEGRAM RESPONSE:", r.text)
    except Exception as e:
        print("SEND ERROR:", e)


def run_outreach():
    print("=== OUTREACH STARTED ===")

    if not TELEGRAM_BOT_TOKEN or not CHAT_ID:
        print("❌ ENV VARIABLES MISSING")
        return

    # FORCE first message
    send_message("🚀 BOT STARTED")

    while True:
        try:
            print("Loop running...")
            send_message("💰 Bot loop active")
            time.sleep(60)
        except Exception as e:
            print("LOOP ERROR:", e)
            time.sleep(5)
