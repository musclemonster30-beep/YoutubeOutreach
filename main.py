import time
from app.ai.groq_engine import generate_message
from app.leads.lead_loader import load_leads
from app.outreach.telegram_sender import send_telegram_message

CHAT_ID = "YOUR_CHAT_ID"

def run_campaign():
    leads = load_leads()
    print(f"Loaded {len(leads)} leads")

    for lead in leads:
        message = generate_message(
            lead["name"],
            lead["platform"],
            lead["followers"]
        )

        print(f"Sending to: {lead['name']}")
        print(message)

        send_telegram_message(CHAT_ID, message)
        time.sleep(30)

def main_loop():
    while True:
        print("=== Campaign Cycle Start ===")
        try:
            run_campaign()
        except Exception as e:
            print(f"Error: {e}")

        print("Sleeping for 1 hour...")
        time.sleep(3600)

if __name__ == "__main__":
    main_loop()
