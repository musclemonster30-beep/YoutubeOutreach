# YouTube Channel Sales Bot (Telegram)

This is a production-ready Telegram bot designed to qualify leads and sell a 165k subscriber bodybuilding YouTube channel.

## Tech Stack
- Python 3.11+
- Flask (Web Server)
- Requests (API communication)
- Gunicorn (Production WSGI)

## Installation

1. **Clone/Copy files** into your server.
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Configure Environment**:
   - Create a `.env` file based on `.env.example`.
   - Add your `TELEGRAM_BOT_TOKEN` from [@BotFather](https://t.me/botfather).

## Deployment (Render.com)

1. Create a new **Web Service** on Render.
2. Connect your repository.
3. Set **Runtime** to `Python 3`.
4. Set **Build Command**: `pip install -r requirements.txt`
5. Set **Start Command**: `gunicorn main:app`
6. Add your `TELEGRAM_BOT_TOKEN` in the **Environment** section.

## Webhook Setup

Telegram requires a webhook to send messages to your bot. Replace `YOUR_BOT_TOKEN` and `YOUR_APP_URL` in the following URL and open it in your browser:

```text
https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook?url=<YOUR_APP_URL>/<YOUR_BOT_TOKEN>
```

Example for Render:
`https://api.telegram.org/bot12345:ABCDE/setWebhook?url=https://your-app.onrender.com/12345:ABCDE`

## Command System
- `/start` - Initiates the qualification flow.
- `/details` - Shows channel statistics.
- `/offer` - Sends the sales pitch.
- `/proof` - Sends performance claims.

## Conversation Logic
The bot tracks user state in-memory to:
1. Ask if they are in the fitness space.
2. Ask what they sell.
3. Ask about their current traffic source.
4. Push a CTA for stats and price breakdown.
