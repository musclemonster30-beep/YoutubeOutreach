import os
from aiogram import Bot, Dispatcher, Router
from aiogram.types import Message
from aiogram.filters import Command
from sqlalchemy import select
from database import AsyncSessionLocal
from models import Lead

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()
router = Router()
dp.include_router(router)


@router.message(Command("leads"))
async def cmd_leads(message: Message):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Lead)
            .where(Lead.status == "pending")
            .order_by(Lead.created_at.desc())
            .limit(5)
        )
        leads = result.scalars().all()

    if not leads:
        await message.answer("No pending leads found.")
        return

    lines = ["<b>Top 5 Pending Leads</b>\n"]
    for i, lead in enumerate(leads, 1):
        lines.append(
            f"{i}. <b>{lead.company_name}</b>\n"
            f"   📧 {lead.contact_email}\n"
            f"   🏷 Niche: {lead.niche}\n"
            f"   🗒 {lead.notes or 'No notes'}\n"
        )

    await message.answer("\n".join(lines), parse_mode="HTML")


@router.message(Command("pitch"))
async def cmd_pitch(message: Message):
    args = message.text.strip().split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Usage: /pitch <niche>\nSupported niches: supplement, apparel")
        return

    niche = args[1].strip().lower()

    if niche == "supplement":
        pitch = (
            "<b>Acquisition Pitch — Supplement Brands</b>\n\n"
            "We are offering a strategic acquisition of <b>MuscleMonster</b>, a bodybuilding-focused YouTube channel "
            "established in 2015 with <b>165,000+ organic subscribers</b> and a highly qualified 18–34 male demographic.\n\n"
            "<b>Why this beats paid acquisition:</b>\n"
            "• Eliminates dependency on Meta/Google ad spend to reach the same verified fitness audience\n"
            "• Owned distribution — no CPM, no auction pressure, no algorithm tax on every impression\n"
            "• Existing content library drives compounding organic reach month over month\n\n"
            "<b>Bundle Option — Complete Acquisition Package:</b>\n"
            "This deal can include the premium exact-match domain <b>isoproteinpowder.com</b>, "
            "enabling an end-to-end DTC brand infrastructure: owned audience + SEO-authoritative domain "
            "in a single transaction. Ideal for launching or consolidating a private-label protein line.\n\n"
            "Open to discussing asset valuation, revenue multiples, and transition terms. "
            "Reply to schedule a call."
        )

    elif niche == "apparel":
        pitch = (
            "<b>Acquisition Pitch — Apparel Brands</b>\n\n"
            "We are offering a strategic acquisition of <b>MuscleMonster</b>, a YouTube channel with "
            "<b>165,000+ organic subscribers</b> built entirely around fitness lifestyle and physique culture — "
            "a core audience segment for performance and lifestyle apparel.\n\n"
            "<b>Brand Authority Angle:</b>\n"
            "• A decade of consistent content establishes category credibility no paid campaign can replicate\n"
            "• Channel authority transfers directly into product credibility for an acquiring apparel brand\n"
            "• Community trust = lower CAC for apparel drops, limited editions, and ambassador programs\n\n"
            "<b>Local SEO & Discovery:</b>\n"
            "• Long-form video content indexes on both YouTube and Google, driving evergreen search traffic\n"
            "• Existing video metadata targets high-intent fitness keywords for gym, training, and lifestyle queries\n"
            "• Provides a content moat competitors cannot replicate quickly\n\n"
            "Open to asset valuation discussions, earnout structures, and phased transition planning. "
            "Reply to schedule a call."
        )

    else:
        pitch = f"No pitch template found for niche: <b>{niche}</b>.\nCurrently supported: supplement, apparel."

    await message.answer(pitch, parse_mode="HTML")
