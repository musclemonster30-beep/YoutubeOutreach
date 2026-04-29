import os
import time
import requests
import random

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print("Telegram error:", e)


# TEMP: fake leads (next step = real scraping)
def get_fake_leads():
    sample_channels = [
        "FitnessWithRaj",
        "CryptoMindset",
        "DailyHustleYT",
        "GrowthLab",
        "StreetWorkoutPro"
    ]
    return random.sample(sample_channels, 3)


def run_outreach():
    print("=== OUTREACH STARTED ===")

    while True:
        try:
            print("Running outreach cycle...")

            leads = get_fake_leads()

            if leads:
                msg = "🔥 New Leads Found:\n\n"
                for lead in leads:
                    msg += f"- {lead}\n"

                print(msg)
                send_telegram_message(msg)

        except Exception as e:
            print("ERROR:", e)
            send_telegram_message(f"⚠️ Error: {e}")

        time.sleep(600)  # every 10 mins
