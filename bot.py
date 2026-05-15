import os
from aiogram import Bot, Dispatcher, Router
from aiogram.types import Message
from aiogram.filters import Command
from sqlalchemy import select
from database import AsyncSessionLocal
from models import Lead

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise RuntimeError(
        "TELEGRAM_TOKEN is not set.\n"
        "Fix: Render Dashboard → Web Service → Environment → add TELEGRAM_TOKEN."
    )

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
        await message.answer("Usage: /pitch <niche>\nSupported: supplement, apparel")
        return

    niche = args[1].strip().lower()

    if niche == "supplement":
        pitch = (
            "<b>Acquisition Pitch — Supplement Brands</b>\n\n"
            "We are offering a strategic acquisition of <b>MuscleMonster</b>, "
            "a bodybuilding-focused YouTube channel established in 2015 with "
            "<b>165,000+ organic subscribers</b> and a highly engaged 18–34 male demographic.\n\n"
            "<b>What you are acquiring:</b>\n"
            "• A 10-year-old YouTube channel with deep category authority in bodybuilding and strength training\n"
            "• 165,000+ organic subscribers — zero paid growth, zero inflated metrics\n"
            "• A loyal audience that actively buys supplements, protein, and training gear\n"
            "• Full content library with evergreen videos driving compounding monthly views\n\n"
            "<b>Why this beats paid acquisition:</b>\n"
            "• Instant owned distribution to your exact target customer — no CPM, no auction, no ad fatigue\n"
            "• Every product mention, review, or integration reaches a warm, trust-verified audience\n"
            "• Channel authority compounds over time — unlike ad spend that stops the moment you pause\n\n"
            "<b>What's included:</b>\n"
            "• Full transfer of the YouTube channel and all associated assets\n"
            "• Content library, community tab, and subscriber base\n"
            "• Transition support to ensure continuity of audience trust\n\n"
            "Open to discussing valuation, deal structure, and transition terms.\n"
            "Reply to schedule a call."
        )

    elif niche == "apparel":
        pitch = (
            "<b>Acquisition Pitch — Apparel Brands</b>\n\n"
            "We are offering a strategic acquisition of <b>MuscleMonster</b>, "
            "a YouTube channel with <b>165,000+ organic subscribers</b> built entirely "
            "around fitness lifestyle, physique culture, and strength training.\n\n"
            "<b>What you are acquiring:</b>\n"
            "• A 10-year-old channel with established brand authority in the fitness space\n"
            "• 165,000+ organic subscribers with strong affinity for training and lifestyle apparel\n"
            "• A content moat built over a decade — impossible to replicate quickly\n"
            "• Full video library indexing on both YouTube and Google for high-intent fitness searches\n\n"
            "<b>Why this works for apparel:</b>\n"
            "• Direct access to a community that buys on identity and aspiration — core apparel drivers\n"
            "• Channel credibility transfers directly to product credibility — lower CAC from day one\n"
            "• Ideal platform for drops, limited editions, ambassador launches, and lookbooks\n"
            "• Evergreen content keeps driving discovery without ongoing ad spend\n\n"
            "<b>What's included:</b>\n"
            "• Full transfer of the YouTube channel and all associated assets\n"
            "• Content library, community tab, and subscriber base\n"
            "• Transition support to ensure continuity of audience trust\n\n"
            "Open to discussing valuation, deal structure, and transition terms.\n"
            "Reply to schedule a call."
        )

    else:
        pitch = (
            f"No pitch template for niche: <b>{niche}</b>.\n"
            "Currently supported: supplement, apparel"
        )

    await message.answer(pitch, parse_mode="HTML")
