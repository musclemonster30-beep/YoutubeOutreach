import os
import time
import requests
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from app.ai.groq_engine import generate_message

# ENV
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# SEND TO TELEGRAM
def send_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    response = requests.post(url, json={
        "chat_id": CHAT_ID,
        "text": text
    })
    print("Telegram:", response.text)


# YOUR BOT LOOP
def run_bot():
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


# FAKE WEB SERVER (FOR RENDER)
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running")


def start_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("", port), Handler)
    print(f"Server running on port {port}")
    server.serve_forever()


# RUN BOTH
if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    start_server()
