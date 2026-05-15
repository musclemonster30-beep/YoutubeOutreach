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
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

_webhook_host = os.environ.get("WEBHOOK_HOST", "").rstrip("/")
if not _webhook_host:
    raise RuntimeError(
        "WEBHOOK_HOST is not set. "
        "Render Dashboard → Web Service → Environment → "
        "add WEBHOOK_HOST = https://youtubeoutreach.onrender.com"
    )

WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{_webhook_host}{WEBHOOK_PATH}"
HEALTH_URL = f"{_webhook_host}/health"


async def _keep_alive():
    """Pings /health every 10 minutes to prevent Render free-tier spin-down."""
    import aiohttp
    await asyncio.sleep(60)  # Initial delay — let the server fully start first
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(HEALTH_URL, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    logger.info(f"Keep-alive ping: {resp.status}")
        except Exception as e:
            logger.warning(f"Keep-alive ping failed: {e}")
        await asyncio.sleep(600)  # 10 minutes


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Create all database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables verified/created.")

    # 2. Register Telegram webhook — drop any stale queued updates
    await bot.set_webhook(WEBHOOK_URL, drop_pending_updates=True)
    logger.info(f"Telegram webhook registered: {WEBHOOK_URL}")

    # 3. Start keep-alive background task
    keep_alive_task = asyncio.create_task(_keep_alive())
    logger.info("Keep-alive task started.")

    yield

    # Graceful shutdown
    keep_alive_task.cancel()
    try:
        await keep_alive_task
    except asyncio.CancelledError:
        pass

    await bot.delete_webhook(drop_pending_updates=False)
    await bot.session.close()
    await engine.dispose()
    logger.info("Shutdown complete — webhook removed, DB pool closed.")


app = FastAPI(
    title="MuscleMonster Outreach Bot",
    version="2.0.0",
    lifespan=lifespan,
)


@app.post(WEBHOOK_PATH)
async def telegram_webhook(request: Request) -> Response:
    """
    Receives Telegram updates and feeds them to the aiogram dispatcher.
    Always returns 200 — Telegram disables webhooks that return repeated errors.
    """
    try:
        body = await request.json()
        update = Update.model_validate(body)
        await dp.feed_update(bot=bot, update=update)
    except Exception as e:
        # Log the error but never let it surface as a non-200 to Telegram
        logger.error(f"Webhook processing error: {e}", exc_info=True)
    return Response(status_code=200)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "MuscleMonster Outreach Bot", "version": "2.0.0"}


@app.get("/")
async def root():
    return {"status": "ok", "message": "MuscleMonster Outreach Bot is running."}
