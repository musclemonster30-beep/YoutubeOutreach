import requests
from app.config import TELEGRAM_TOKEN

def send_telegram_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": text
    }

    try:
        res = requests.post(url, data=payload)
        print(f"Telegram status: {res.status_code}")
    except Exception as e:
        print(f"Telegram error: {e}")
