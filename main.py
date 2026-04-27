import time
import threading
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

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
        time.sleep(30)  # anti-spam delay

def main_loop():
    while True:
        print("=== Campaign Cycle Start ===")

        try:
            run_campaign()
        except Exception as e:
            print(f"Error: {e}")

        print("Sleeping for 1 hour...")
        time.sleep(3600)


# ===== Render Web Service Hack =====

PORT = int(os.environ.get("PORT", 10000))

def run_bot():
    main_loop()

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running")

if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    server.serve_forever()
