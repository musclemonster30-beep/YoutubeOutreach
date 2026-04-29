import os
import time
import requests
from groq import Groq

# ENV VARIABLES
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# INIT GROQ
client = Groq(api_key=GROQ_API_KEY)


def send_telegram_message(text):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": text
        }
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print("Telegram error:", e)


def generate_message(topic):
    try:
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {"role": "system", "content": "You are an outreach assistant."},
                {"role": "user", "content": f"Write a short outreach message about {topic}"}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print("Groq error:", e)
        return None


def run_outreach():
    print("=== OUTREACH STARTED ===")

    last_status_time = 0

    while True:
        try:
            print("Running outreach cycle...")

            # EXAMPLE TASK (replace later with real scraping logic)
            topic = "YouTube growth"
            message = generate_message(topic)

            if message:
                print("Generated message:", message)

                # SEND ONLY WHEN ACTUAL MESSAGE EXISTS
                send_telegram_message(f"🔥 Outreach Message:\n\n{message}")

            # STATUS UPDATE ONLY EVERY 10 MINUTES
            current_time = time.time()
            if current_time - last_status_time > 600:
                print("Status: bot alive")
                send_telegram_message("🚀 Bot running нормально")
                last_status_time = current_time

        except Exception as e:
            print("ERROR:", e)
            send_telegram_message(f"⚠️ Error: {e}")

        time.sleep(300)  # runs every 5 minutes
