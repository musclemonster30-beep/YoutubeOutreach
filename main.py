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
    raise ValueError("Missing TELEGRAM_BOT_TOKEN")

client = None
if GROQ_API_KEY:
    client = Groq(api_key=GROQ_API_KEY)
    logger.info("Groq AI Engine Initialized")
else:
    logger.warning("GROQ_API_KEY not found. AI features will be disabled.")

TELEGRAM_API = f"https://api.telegram.org/bot{TOKEN}"
DB_FILE = "bot_data.db"

# --- DATABASE LOGIC ---
def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS states (chat_id TEXT PRIMARY KEY, state TEXT)")
        conn.commit()

def get_state(chat_id):
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.execute("SELECT state FROM states WHERE chat_id = ?", (str(chat_id),))
            row = cursor.fetchone()
            return row[0] if row else "START"
    except Exception:
        return "START"

def save_state(chat_id, state):
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("INSERT OR REPLACE INTO states (chat_id, state) VALUES (?, ?)", (str(chat_id), state))
        conn.commit()

# --- AI ENGINE ---
def generate_ai_response(user_text, current_state):
    if not client:
        return "I'm interested! Type /details to see the channel stats or /offer to see our proposal."

    prompt = f"""
You are an expert Sales Agent selling a 165k subscriber YouTube channel in the Bodybuilding/Fitness niche.

Goal: Close a deal or partner with a serious buyer (Supplement brands, fitness influencers).
Tone: Direct, confident, professional, and business-focused. No generic 'influencer' fluff.

Context:
- Channel: 165,000 Subscribers
- Niche: Enhanced Bodybuilding / Fitness
- Traffic: 1.2M+ monthly views
- Monetization: Ready for affiliate, brand deals, or direct product sales.
- Current User State: {current_state}

User said: "{user_text}"

Respond in 2-3 short, punchy lines. Keep the conversation moving toward a sale or contact exchange.
"""
    try:
        completion = client.chat.completions.create(
            model="llama-3.1-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=150
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"AI Error: {e}")
        return "That's a great point. I'd love to discuss that in a quick call. Want me to send over the stats first? (/details)"

# --- TELEGRAM LOGIC ---
def send_message(chat_id, text):
    url = f"{TELEGRAM_API}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        logger.error(f"Telegram Error: {e}")

@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "active", "ai_enabled": bool(client)}), 200

@app.route(f"/{TOKEN}", methods=["POST"])
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
    logger.info(f"User {chat_id} [{state}]: {text}")

    # FIXED COMMANDS (Highest Priority)
    if text_lower == "/start":
        save_state(chat_id, "QUALIFYING")
        send_message(chat_id, "Quick question — do you run or promote anything in the fitness space?")
        return jsonify({"status": "ok"})

    elif text_lower == "/details":
        msg = (
            "<b>📊 Channel Stats:</b>\n"
            "• 165,000 Subscribers\n"
            "• Bodybuilding/Fitness Niche\n"
            "• 1.2M+ Monthly Views\n"
            "• High-intent male audience (18-34)\n\n"
            "Perfect for supplement brands or coaching programs."
        )
        send_message(chat_id, msg)
        return jsonify({"status": "ok"})

    elif text_lower == "/offer":
        send_message(chat_id, "We're looking for an outright sale or a long-term equity partner. It's a turnkey traffic engine. Interested in the revenue breakdown?")
        return jsonify({"status": "ok"})

    # CONVERSATION & AI HANDLING
    if state == "QUALIFYING":
        if any(w in text_lower for w in ["yes", "yeah", "yep", "do", "run", "promote", "coach"]):
            save_state(chat_id, "QUALIFYING_TRAFFIC")
            send_message(chat_id, "Makes sense. Are you currently running paid ads or relying on organic?")
        else:
            save_state(chat_id, "EXIT")
            send_message(chat_id, "Got it. If you're ever looking to bypass years of growth and get 165k subs instantly, let me know.")
        return jsonify({"status": "ok"})

    # If the user is further in the funnel, or asks a random question, use AI
    ai_reply = generate_ai_response(text, state)
    send_message(chat_id, ai_reply)

    # Automatically progress state if they show interest
    if any(w in text_lower for w in ["yes", "sure", "ok", "send", "price", "interested"]):
        if state == "QUALIFYING_TRAFFIC":
            save_state(chat_id, "CLOSING")
        elif state == "CLOSING":
            save_state(chat_id, "LEAD_CAPTURE")
            send_message(chat_id, "Drop your email or @username and I'll send the full deck over.")

    return jsonify({"status": "ok"})

if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
