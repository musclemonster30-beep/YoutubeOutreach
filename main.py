    1 import os
     2 import sqlite3
     3 import logging
     4 import requests
     5 from flask import Flask, request, jsonify
     6 from dotenv import load_dotenv
     7 from groq import Groq
     8
     9 # Setup logging
    10 logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    11 logger = logging.getLogger(__name__)
    12
    13 load_dotenv()
    14
    15 app = Flask(__name__)
    16
    17 # ENV CONFIG
    18 TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    19 GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    20
    21 # CRITICAL: Check token on startup
    22 if not TOKEN:
    23     logger.error("FATAL: TELEGRAM_BOT_TOKEN is not set in Environment Variables!")
    24     # We don't raise here to prevent a crash loop before logs can be read, 
    25     # but we handle it in the routes.
    26
    27 client = None
    28 if GROQ_API_KEY:
    29     try:
    30         client = Groq(api_key=GROQ_API_KEY)
    31         logger.info("Groq AI Engine Initialized")
    32     except Exception as e:
    33         logger.error(f"Failed to initialize Groq: {e}")
    34
    35 TELEGRAM_API = f"https://api.telegram.org/bot{TOKEN}"
    36 DB_FILE = "bot_data.db"
    37
    38 # --- DATABASE LOGIC ---
    39 def init_db():
    40     try:
    41         with sqlite3.connect(DB_FILE) as conn:
    42             conn.execute("CREATE TABLE IF NOT EXISTS states (chat_id TEXT PRIMARY KEY, state TEXT)")
    43             conn.commit()
    44             logger.info("Database initialized successfully.")
    45     except Exception as e:
    46         logger.error(f"Database Init Error: {e}")
    47
    48 # RUN DB INIT ON MODULE LOAD (Required for Gunicorn)
    49 init_db()
    50
    51 def get_state(chat_id):
    52     try:
    53         with sqlite3.connect(DB_FILE) as conn:
    54             cursor = conn.execute("SELECT state FROM states WHERE chat_id = ?", (str(chat_id),))
    55             row = cursor.fetchone()
    56             return row[0] if row else "START"
    57     except Exception as e:
    58         logger.error(f"DB Read Error: {e}")
    59         return "START"
    60
    61 def save_state(chat_id, state):
    62     try:
    63         with sqlite3.connect(DB_FILE) as conn:
    64             conn.execute("INSERT OR REPLACE INTO states (chat_id, state) VALUES (?, ?)", (str(chat_id), state))
    65             conn.commit()
    66     except Exception as e:
    67         logger.error(f"DB Write Error: {e}")
    68
    69 # --- AI ENGINE ---
    70 def generate_ai_response(user_text, current_state):
    71     if not client:
    72         return "I'm interested! Type /details to see the channel stats or /offer to see our proposal."
    73
    74     prompt = f"""
    75     You are an expert Sales Agent selling a 165k subscriber YouTube channel in the Bodybuilding/Fitness niche.
    76     Goal: Close a deal or partner with a serious buyer.
    77     Tone: Direct, confident, professional.
    78     Context: 165k subs, 1.2M monthly views, Bodybuilding niche.
    79     User state: {current_state}
    80     User said: "{user_text}"
    81     """
    82     try:
    83         completion = client.chat.completions.create(
    84             model="llama-3.1-70b-versatile",
    85             messages=[{"role": "user", "content": prompt}],
    86             temperature=0.7,
    87             max_tokens=150
    88         )
    89         return completion.choices[0].message.content.strip()
    90     except Exception as e:
    91         logger.error(f"AI Error: {e}")
    92         return "I'd love to discuss that. Can you check /details for the stats first?"
    93
    94 # --- TELEGRAM LOGIC ---
    95 def send_message(chat_id, text):
    96     url = f"{TELEGRAM_API}/sendMessage"
    97     payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    98     try:
    99         requests.post(url, json=payload, timeout=10)
   100     except Exception as e:
   101         logger.error(f"Telegram Error: {e}")
   102
   103 @app.route("/", methods=["GET"])
   104 def health():
   105     return jsonify({
   106         "status": "active", 
   107         "ai_enabled": bool(client),
   108         "token_set": bool(TOKEN)
   109     }), 200
   110
   111 # Webhook route handles the token safely
   112 @app.route("/webhook", methods=["POST"])
   113 def webhook_simple():
   114     return webhook_logic()
   115
   116 # Or the token-based route for extra security
   117 if TOKEN:
   118     @app.route(f"/{TOKEN}", methods=["POST"])
   119     def webhook_secure():
   120         return webhook_logic()
   121
   122 def webhook_logic():
   123     data = request.json
   124     if not data or "message" not in data:
   125         return jsonify({"status": "ok"})
   126
   127     message = data["message"]
   128     chat_id = message["chat"]["id"]
   129     text = message.get("text", "").strip()
   130     text_lower = text.lower()
   131
   132     if not text:
   133         return jsonify({"status": "ok"})
   134
   135     state = get_state(chat_id)
   136     
   137     if text_lower == "/start":
   138         save_state(chat_id, "QUALIFYING")
   139         send_message(chat_id, "Quick question — do you run or promote anything in the fitness space?")
   140     elif text_lower == "/details":
   141         send_message(chat_id, "<b>📊 Stats:</b> 165k Subs, 1.2M Monthly Views, Bodybuilding Niche.")
   142     elif text_lower == "/offer":
   143         send_message(chat_id, "We are selling this 165k asset. Interested in the revenue breakdown?")
   144     else:
   145         ai_reply = generate_ai_response(text, state)
   146         send_message(chat_id, ai_reply)
   147
   148     return jsonify({"status": "ok"})
   149
   150 if __name__ == "__main__":
   151     port = int(os.environ.get("PORT", 5000))
   152     app.run(host="0.0.0.0", port=port)
