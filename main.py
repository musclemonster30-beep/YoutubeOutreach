import os
import time
import requests
from app.ai.groq_engine import generate_message

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    r = requests.post(url, json={
        "chat_id": CHAT_ID,
        "text": text
    })
    print("Telegram:", r.text)

def run():
    print("BOT STARTED")

    while True:
        try:
            leads = [
                {"name": "FitnessCreatorAlpha", "followers": "120k"},
                {"name": "BodybuilderPro", "followers": "250k"}
            ]

            for lead in leads:
                print("Generating for:", lead)

                msg = generate_message(
                    name=lead["name"],
                    followers=lead["followers"]
                )

                print("Sending:", msg)
                send_telegram(msg)

                time.sleep(10)

            time.sleep(300)

        except Exception as e:
            print("ERROR:", str(e))
            time.sleep(30)

if __name__ == "__main__":
    run()
