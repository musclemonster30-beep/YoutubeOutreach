import os
import sqlite3
import logging
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from groq import Groq

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

app = Flask(__name__)

# ENV CONFIG
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not TOKEN:
    logger.error("FATAL: TELEGRAM_BOT_TOKEN is not set!")

client = None
if GROQ_API_KEY:
    try:
        client = Groq(api_key=GROQ_API_KEY)
        logger.info("Groq AI Engine Initialized")
    except Exception as e:
        logger.error(f"Failed to initialize Groq: {e}")

TELEGRAM_API = f"https://api.telegram.org/bot{TOKEN}"
DB_FILE = "bot_data.db"

def init_db():
    try:
        with sqlite3.connect(DB_FILE) as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS states (chat_id TEXT PRIMARY KEY, state TEXT)")
            conn.commit()
    except Exception as e:
        logger.error(f"Database Init Error: {e}")

# Initialize DB on startup
init_db()

def get_state(chat_id):
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.execute("SELECT state FROM states WHERE chat_id = ?", (str(chat_id),))
            row = cursor.fetchone()
            return row[0] if row else "START"
    except Exception:
        return "START"

def save_state(chat_id, state):
    try:
        with sqlite3.connect(DB_FILE) as conn:
            conn.execute("INSERT OR REPLACE INTO states (chat_id, state) VALUES (?, ?)", (str(chat_id), state))
            conn.commit()
    except Exception as e:
        logger.error(f"DB Write Error: {e}")

def generate_ai_response(user_text, current_state):
    if not client:
        return "I'm interested! Type /details to see stats or /offer for the proposal."
    prompt = f"Agent selling 165k sub YouTube channel. User state: {current_state}. User said: {user_text}. Respond in 2 lines."
    try:
        completion = client.chat.completions.create(
            model="llama-3.1-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=100
        )
        return completion.choices[0].message.content.strip()
    except Exception:
        return "Check /details for stats. Interested in a breakdown?"

def send_message(chat_id, text):
    url = f"{TELEGRAM_API}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception:
        pass

@app.route("/", methods=["GET"])
def health():
    return "Bot Active", 200

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    if not data or "message" not in data:
        return jsonify({"status": "ok"})
    message = data["message"]
    chat_id = message["chat"]["id"]
    text = message.get("text", "").strip()
    text_lower = text.lower()
    if not text:
        return jsonify({"status": "ok"})
    state = get_state(chat_id)
    if text_lower == "/start":
        save_state(chat_id, "QUALIFYING")
        send_message(chat_id, "Do you run or promote anything in the fitness space?")
    elif text_lower == "/details":
        send_message(chat_id, "Stats: 165k Subs, 1.2M Monthly Views, Bodybuilding Niche.")
    elif text_lower == "/offer":
        send_message(chat_id, "We are selling this 165k asset. Interested in the revenue breakdown?")
    else:
        reply = generate_ai_response(text, state)
        send_message(chat_id, reply)
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
