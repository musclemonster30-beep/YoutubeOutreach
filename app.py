import os
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from aiogram.types import Update
from models import Base
from database import engine
from bot import bot, dp

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

WEBHOOK_HOST = os.environ.get("WEBHOOK_HOST")
if not WEBHOOK_HOST:
    raise RuntimeError(
        "WEBHOOK_HOST is not set. "
        "Go to Render Dashboard → Web Service → Environment → "
        "add WEBHOOK_HOST = https://youtubeoutreach.onrender.com"
    )

WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

# Keep-alive ping every 10 minutes to prevent Render free tier spin-down
async def keep_alive():
    import aiohttp
    url = f"{WEBHOOK_HOST}/health"
    while True:
        await asyncio.sleep(600)
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    logger.info(f"Keep-alive ping: {resp.status}")
        except Exception as e:
            logger.warning(f"Keep-alive ping failed: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables verified/created.")

    await bot.set_webhook(WEBHOOK_URL, drop_pending_updates=True)
    logger.info(f"Telegram webhook set to: {WEBHOOK_URL}")

    # Start keep-alive background task
    task = asyncio.create_task(keep_alive())
    logger.info("Keep-alive task started.")

    yield

    task.cancel()
    await bot.delete_webhook()
    await bot.session.close()
    logger.info("Shutdown complete.")


app = FastAPI(lifespan=lifespan)


@app.post(WEBHOOK_PATH)
async def telegram_webhook(request: Request):
    try:
        body = await request.json()
        update = Update.model_validate(body)
        await dp.feed_update(bot=bot, update=update)
        return Response(status_code=200)
    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        return Response(status_code=200)  # Always return 200 to Telegram


@app.get("/health")
async def health():
    return {"status": "ok", "service": "MuscleMonster Outreach Bot"}


@app.get("/")
async def root():
    return {"status": "ok", "message": "MuscleMonster Outreach Bot is running."}
