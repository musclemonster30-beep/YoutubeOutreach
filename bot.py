import os
import logging
from aiogram import Bot, Dispatcher, Router
from aiogram.types import Message
from aiogram.filters import Command
from sqlalchemy import select
from database import AsyncSessionLocal
from models import Lead

logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise RuntimeError(
        "TELEGRAM_TOKEN is not set. "
        "Go to Render Dashboard → Web Service → Environment → add TELEGRAM_TOKEN."
    )

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()
router = Router()
dp.include_router(router)


@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "<b>MuscleMonster Outreach Bot</b>\n\n"
        "Commands:\n"
        "/leads — View top 5 pending leads\n"
        "/addlead — Add a new lead\n"
        "/pitch supplement — Generate supplement pitch\n"
        "/pitch apparel — Generate apparel pitch\n"
        "/help — Show this message",
        parse_mode="HTML"
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "<b>Available Commands:</b>\n\n"
        "/leads\n"
        "→ Lists top 5 pending leads\n\n"
        "/addlead Company | email@domain.com | niche\n"
        "→ Example: /addlead MuscleTech | bd@muscletech.com | supplement\n\n"
        "/pitch supplement\n"
        "→ Generates acquisition pitch for supplement brands\n\n"
        "/pitch apparel\n"
        "→ Generates acquisition pitch for apparel brands\n\n"
        "/updatestatus company_name | new_status\n"
        "→ Example: /updatestatus MuscleTech | contacted\n"
        "→ Statuses: pending, contacted, negotiating, closed, dead",
        parse_mode="HTML"
    )


@router.message(Command("leads"))
async def cmd_leads(message: Message):
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Lead)
                .where(Lead.status == "pending")
                .order_by(Lead.created_at.desc())
                .limit(5)
            )
            leads = result.scalars().all()

        if not leads:
            await message.answer(
                "No pending leads found.\n\n"
                "Add one with:\n"
                "/addlead Company | email@domain.com | niche"
            )
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

    except Exception as e:
        logger.error(f"/leads error: {e}")
        await message.answer("Database error fetching leads. Check logs.")


@router.message(Command("addlead"))
async def cmd_addlead(message: Message):
    args = message.text.strip().split(maxsplit=1)
    if len(args) < 2:
        await message.answer(
            "Usage: /addlead Company Name | email@domain.com | niche\n\n"
            "Example:\n"
            "/addlead MuscleTech | bd@muscletech.com | supplement"
        )
        return

    parts = [p.strip() for p in args[1].split("|")]
    if len(parts) != 3:
        await message.answer(
            "Format error — need exactly 3 fields separated by |\n\n"
            "Example:\n"
            "/addlead MuscleTech | bd@muscletech.com | supplement"
        )
        return

    company_name, contact_email, niche = parts

    if not company_name or not contact_email or not niche:
        await message.answer("All three fields (company, email, niche) are required.")
        return

    try:
        new_lead = Lead(
            company_name=company_name,
            contact_email=contact_email,
            niche=niche.lower(),
            status="pending"
        )
        async with AsyncSessionLocal() as session:
            session.add(new_lead)
            await session.commit()

        await message.answer(
            f"✅ <b>Lead added successfully!</b>\n\n"
            f"🏢 {company_name}\n"
            f"📧 {contact_email}\n"
            f"🏷 Niche: {niche.lower()}\n"
            f"📌 Status: pending\n\n"
            f"Run /leads to see your pipeline.",
            parse_mode="HTML"
        )

    except Exception as e:
        logger.error(f"/addlead error: {e}")
        await message.answer("Database error saving lead. Check logs.")


@router.message(Command("updatestatus"))
async def cmd_updatestatus(message: Message):
    valid_statuses = ["pending", "contacted", "negotiating", "closed", "dead"]
    args = message.text.strip().split(maxsplit=1)

    if len(args) < 2:
        await message.answer(
            "Usage: /updatestatus Company Name | new_status\n\n"
            f"Valid statuses: {', '.join(valid_statuses)}\n\n"
            "Example:\n"
            "/updatestatus MuscleTech | contacted"
        )
        return

    parts = [p.strip() for p in args[1].split("|")]
    if len(parts) != 2:
        await message.answer(
            "Format error — need company name and status separated by |\n\n"
            "Example: /updatestatus MuscleTech | contacted"
        )
        return

    company_name, new_status = parts
    new_status = new_status.lower()

    if new_status not in valid_statuses:
        await message.answer(
            f"Invalid status: <b>{new_status}</b>\n\n"
            f"Valid options: {', '.join(valid_statuses)}",
            parse_mode="HTML"
        )
        return

    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Lead).where(Lead.company_name.ilike(f"%{company_name}%"))
            )
            lead = result.scalars().first()

            if not lead:
                await message.answer(f"No lead found matching: <b>{company_name}</b>", parse_mode="HTML")
                return

            old_status = lead.status
            lead.status = new_status
            await session.commit()

        await message.answer(
            f"✅ <b>Status updated!</b>\n\n"
            f"🏢 {lead.company_name}\n"
            f"📌 {old_status} → <b>{new_status}</b>",
            parse_mode="HTML"
        )

    except Exception as e:
        logger.error(f"/updatestatus error: {e}")
        await message.answer("Database error updating status. Check logs.")


@router.message(Command("pitch"))
async def cmd_pitch(message: Message):
    args = message.text.strip().split(maxsplit=1)
    if len(args) < 2:
        await message.answer(
            "Usage: /pitch <niche>\n\n"
            "Supported niches:\n"
            "• /pitch supplement\n"
            "• /pitch apparel"
        )
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
            "• Every product mention or review reaches a warm, trust-verified audience\n"
            "• Channel authority compounds over time — unlike ad spend that stops the moment you pause\n\n"
            "<b>What's included in the deal:</b>\n"
            "• Full transfer of the YouTube channel and all associated assets\n"
            "• Complete content library and subscriber base\n"
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
            "<b>What's included in the deal:</b>\n"
            "• Full transfer of the YouTube channel and all associated assets\n"
            "• Complete content library and subscriber base\n"
            "• Transition support to ensure continuity of audience trust\n\n"
            "Open to discussing valuation, deal structure, and transition terms.\n"
            "Reply to schedule a call."
        )

    else:
        pitch = (
            f"No pitch template for niche: <b>{niche}</b>\n\n"
            "Supported niches:\n"
            "• /pitch supplement\n"
            "• /pitch apparel"
        )

    await message.answer(pitch, parse_mode="HTML")
