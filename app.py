import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from aiogram.types import Update
from aiogram.webhook.aiohttp_server import SimpleRequestHandler
from models import Base
from database import engine
from bot import bot, dp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

WEBHOOK_HOST = os.environ["WEBHOOK_HOST"]  # e.g. https://your-app.onrender.com
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables verified/created.")

    # Register Telegram webhook
    await bot.set_webhook(WEBHOOK_URL)
    logger.info(f"Telegram webhook set to: {WEBHOOK_URL}")

    yield

    # Graceful shutdown
    await bot.delete_webhook()
    await bot.session.close()
    logger.info("Bot webhook removed and session closed.")


app = FastAPI(lifespan=lifespan)


@app.post(WEBHOOK_PATH)
async def telegram_webhook(request: Request):
    body = await request.json()
    update = Update.model_validate(body)
    await dp.feed_update(bot=bot, update=update)
    return {"ok": True}


@app.get("/health")
async def health():
    return {"status": "ok"}
