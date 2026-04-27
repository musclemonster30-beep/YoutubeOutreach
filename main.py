import os
import time
import requests
from app.ai.groq_engine import generate_message

# ENV
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# TELEGRAM SEND
def send_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text
    }
    response = requests.post(url, json=payload)
    print("Telegram response:", response.text)

# LOAD LEADS
def load_leads():
    return [
        {"name": "FitnessCreatorAlpha", "followers": "120k"},
        {"name": "BodybuilderPro", "followers": "250k"}
    ]

# MAIN LOOP (runs forever → required for Render)
def run():
    print("Bot started...")

    while True:
        leads = load_leads()

        for lead in leads:
            msg = generate_message(
                name=lead["name"],
                followers=lead["followers"]
            )

            print("Sending:", msg)
            send_telegram(msg)

            time.sleep(10)  # prevent spam

        time.sleep(300)  # wait 5 min before next cycle

if __name__ == "__main__":
    run()
