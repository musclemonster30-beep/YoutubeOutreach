import os
import logging
from aiogram import Bot, Dispatcher, Router
from aiogram.types import Message
from aiogram.filters import Command
from sqlalchemy import select
from database import AsyncSessionLocal
from models import Lead

logger = logging.getLogger(__name__)

_token = os.environ.get("TELEGRAM_TOKEN", "")
if not _token:
    raise RuntimeError(
        "TELEGRAM_TOKEN is not set. "
        "Render Dashboard → Web Service → Environment → add TELEGRAM_TOKEN."
    )

bot = Bot(token=_token)
dp = Dispatcher()
router = Router()
dp.include_router(router)

VALID_STATUSES = ("pending", "contacted", "negotiating", "closed", "dead")

PITCHES = {
    "supplement": (
        "<b>Acquisition Pitch — Supplement Brands</b>\n\n"
        "We are offering a strategic acquisition of <b>MuscleMonster</b>, "
        "a bodybuilding-focused YouTube channel established in <b>2015</b> with "
        "<b>165,000+ organic subscribers</b> — zero paid growth, zero inflated metrics.\n\n"
        "<b>Core audience profile:</b>\n"
        "• Male, 18–34, actively purchasing supplements, protein, and training nutrition\n"
        "• High purchase-intent segment verified through a decade of organic content engagement\n"
        "• Subscribers, not followers — the highest-trust distribution unit on any platform\n\n"
        "<b>Why this outperforms paid acquisition:</b>\n"
        "• Eliminates dependency on Meta and Google ad auctions to reach the same verified buyer\n"
        "• Owned distribution — no CPM, no algorithm tax, no spend required per impression\n"
        "• A 10-year content library drives compounding monthly views with zero incremental cost\n"
        "• Every product integration reaches a warm, pre-qualified audience — not cold traffic\n\n"
        "<b>Acquisition includes:</b>\n"
        "• Full YouTube channel transfer — all assets, history, and subscriber base\n"
        "• Complete evergreen content library\n"
        "• Structured handover with audience continuity support\n\n"
        "Open to discussing valuation methodology, deal structure, and transition terms.\n"
        "Reply to schedule a call."
    ),
    "apparel": (
        "<b>Acquisition Pitch — Apparel Brands</b>\n\n"
        "We are offering a strategic acquisition of <b>MuscleMonster</b>, "
        "a YouTube channel with <b>165,000+ organic subscribers</b> built entirely "
        "around fitness lifestyle, physique culture, and strength training since <b>2015</b>.\n\n"
        "<b>Core audience profile:</b>\n"
        "• Fitness-first demographic with high affinity for performance and lifestyle apparel\n"
        "• Buying decisions driven by identity and aspiration — the exact engine apparel brands depend on\n"
        "• A community built over a decade, not assembled through paid spend\n\n"
        "<b>Why this works for apparel:</b>\n"
        "• Channel credibility transfers directly into product credibility — lower CAC from day one\n"
        "• Ideal activation platform for drops, limited editions, ambassador programs, and lookbooks\n"
        "• Long-form video indexes on YouTube and Google — evergreen search traffic, no ongoing ad cost\n"
        "• A content moat a decade deep — competitors cannot replicate this positioning quickly\n\n"
        "<b>Acquisition includes:</b>\n"
        "• Full YouTube channel transfer — all assets, history, and subscriber base\n"
        "• Complete evergreen content library\n"
        "• Structured handover with audience continuity support\n\n"
        "Open to discussing valuation methodology, deal structure, and transition terms.\n"
        "Reply to schedule a call."
    ),
    "gym": (
        "<b>Acquisition Pitch — Gym & Fitness Facility Brands</b>\n\n"
        "We are offering a strategic acquisition of <b>MuscleMonster</b>, "
        "a YouTube channel with <b>165,000+ organic subscribers</b> and a decade of authority "
        "in bodybuilding, strength training, and gym culture — established <b>2015</b>.\n\n"
        "<b>Core audience profile:</b>\n"
        "• Dedicated gym-goers and serious training enthusiasts — not casual fitness browsers\n"
        "• High-intent audience actively seeking training resources, gym environments, and coaching\n"
        "• Proven organic engagement built without a single dollar in paid subscriber acquisition\n\n"
        "<b>Why this works for gym brands:</b>\n"
        "• Instant credibility with an audience that already lives inside gym culture\n"
        "• Owned media channel to drive memberships, merchandise, and brand partnerships\n"
        "• Replaces or dramatically reduces dependence on Meta and Google local ad spend\n"
        "• Content library doubles as perpetual top-of-funnel — viewers become members\n\n"
        "<b>Acquisition includes:</b>\n"
        "• Full YouTube channel transfer — all assets, history, and subscriber base\n"
        "• Complete evergreen content library\n"
        "• Structured handover with audience continuity support\n\n"
        "Open to discussing valuation methodology, deal structure, and transition terms.\n"
        "Reply to schedule a call."
    ),
}


@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "<b>MuscleMonster Outreach Bot</b>\n\n"
        "Deal-flow pipeline for the MuscleMonster YouTube channel acquisition.\n\n"
        "<b>Commands:</b>\n"
        "/leads — View top 5 pending leads\n"
        "/addlead — Add a prospect to the pipeline\n"
        "/updatestatus — Move a lead through the funnel\n"
        "/pitch supplement — Supplement brand pitch\n"
        "/pitch apparel — Apparel brand pitch\n"
        "/pitch gym — Gym & fitness facility pitch\n"
        "/help — Full command reference",
        parse_mode="HTML",
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "<b>Command Reference</b>\n\n"
        "<b>/leads</b>\n"
        "→ Lists top 5 pending leads\n\n"
        "<b>/addlead Company | email | niche</b>\n"
        "→ Niches: supplement, apparel, gym\n"
        "→ Example: /addlead MuscleTech | bd@muscletech.com | supplement\n\n"
        "<b>/updatestatus Company | status</b>\n"
        f"→ Statuses: {', '.join(VALID_STATUSES)}\n"
        "→ Example: /updatestatus MuscleTech | contacted\n\n"
        "<b>/pitch &lt;niche&gt;</b>\n"
        "→ /pitch supplement\n"
        "→ /pitch apparel\n"
        "→ /pitch gym",
        parse_mode="HTML",
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
                "No pending leads in the pipeline.\n\n"
                "Add one with:\n"
                "<code>/addlead Company | email | niche</code>",
                parse_mode="HTML",
            )
            return

        lines = [f"<b>Pending Leads ({len(leads)})</b>\n"]
        for i, lead in enumerate(leads, 1):
            lines.append(
                f"{i}. <b>{lead.company_name}</b>\n"
                f"   📧 {lead.contact_email}\n"
                f"   🏷 {lead.niche}\n"
                f"   🗒 {lead.notes or '—'}\n"
            )
        await message.answer("\n".join(lines), parse_mode="HTML")

    except Exception as e:
        logger.error(f"/leads db error: {e}", exc_info=True)
        await message.answer("Database error fetching leads. Check Render logs.")


@router.message(Command("addlead"))
async def cmd_addlead(message: Message):
    args = message.text.strip().split(maxsplit=1)
    if len(args) < 2:
        await message.answer(
            "Usage: <code>/addlead Company | email | niche</code>\n\n"
            "Example:\n"
            "<code>/addlead MuscleTech | bd@muscletech.com | supplement</code>",
            parse_mode="HTML",
        )
        return

    parts = [p.strip() for p in args[1].split("|")]
    if len(parts) != 3:
        await message.answer(
            "Format error — provide exactly 3 fields separated by <code>|</code>\n\n"
            "<code>/addlead Company | email | niche</code>",
            parse_mode="HTML",
        )
        return

    company_name, contact_email, niche = parts
    niche = niche.lower()

    if not all([company_name, contact_email, niche]):
        await message.answer("All three fields are required: company, email, niche.")
        return

    try:
        async with AsyncSessionLocal() as session:
            lead = Lead(
                company_name=company_name,
                contact_email=contact_email,
                niche=niche,
                status="pending",
            )
            session.add(lead)
            await session.commit()
            await session.refresh(lead)

        await message.answer(
            f"✅ <b>Lead added</b>\n\n"
            f"🏢 {lead.company_name}\n"
            f"📧 {lead.contact_email}\n"
            f"🏷 {lead.niche}\n"
            f"📌 Status: pending\n"
            f"🆔 ID: {lead.id}",
            parse_mode="HTML",
        )

    except Exception as e:
        logger.error(f"/addlead db error: {e}", exc_info=True)
        await message.answer("Database error saving lead. Check Render logs.")


@router.message(Command("updatestatus"))
async def cmd_updatestatus(message: Message):
    args = message.text.strip().split(maxsplit=1)
    if len(args) < 2:
        await message.answer(
            "Usage: <code>/updatestatus Company | new_status</code>\n\n"
            f"Valid statuses: {', '.join(VALID_STATUSES)}\n\n"
            "Example:\n"
            "<code>/updatestatus MuscleTech | contacted</code>",
            parse_mode="HTML",
        )
        return

    parts = [p.strip() for p in args[1].split("|")]
    if len(parts) != 2:
        await message.answer(
            "Format error.\n"
            "<code>/updatestatus Company | status</code>",
            parse_mode="HTML",
        )
        return

    company_name, new_status = parts
    new_status = new_status.lower()

    if new_status not in VALID_STATUSES:
        await message.answer(
            f"Invalid status: <b>{new_status}</b>\n\n"
            f"Valid options: {', '.join(VALID_STATUSES)}",
            parse_mode="HTML",
        )
        return

    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Lead).where(Lead.company_name.ilike(f"%{company_name}%"))
            )
            lead = result.scalars().first()

            if not lead:
                await message.answer(
                    f"No lead found matching: <b>{company_name}</b>\n\n"
                    "Check spelling or use /leads to see your pipeline.",
                    parse_mode="HTML",
                )
                return

            old_status = lead.status
            lead.status = new_status
            await session.commit()

        await message.answer(
            f"✅ <b>Status updated</b>\n\n"
            f"🏢 {lead.company_name}\n"
            f"📌 {old_status} → <b>{new_status}</b>",
            parse_mode="HTML",
        )

    except Exception as e:
        logger.error(f"/updatestatus db error: {e}", exc_info=True)
        await message.answer("Database error updating status. Check Render logs.")


@router.message(Command("pitch"))
async def cmd_pitch(message: Message):
    args = message.text.strip().split(maxsplit=1)
    if len(args) < 2:
        await message.answer(
            "Usage: <code>/pitch &lt;niche&gt;</code>\n\n"
            "Available niches:\n"
            "• /pitch supplement\n"
            "• /pitch apparel\n"
            "• /pitch gym",
            parse_mode="HTML",
        )
        return

    niche = args[1].strip().lower()
    pitch = PITCHES.get(niche)

    if not pitch:
        await message.answer(
            f"No pitch template for: <b>{niche}</b>\n\n"
            "Available:\n"
            "• /pitch supplement\n"
            "• /pitch apparel\n"
            "• /pitch gym",
            parse_mode="HTML",
        )
        return

    await message.answer(pitch, parse_mode="HTML")
