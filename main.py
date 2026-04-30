import os
import re
import asyncio
import logging
import google.generativeai as genai
from aiohttp import web
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, Update
from aiogram.filters import Command, CommandStart
from groq import Groq

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Env ───────────────────────────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY       = os.getenv("GROQ_API_KEY")
GEMINI_API_KEY     = os.getenv("GEMINI_API_KEY")
WEBHOOK_HOST       = os.getenv("WEBHOOK_HOST", "https://thebizzarepast.onrender.com")
WEBHOOK_PATH       = "/webhook"
WEBHOOK_URL        = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"
WEB_SERVER_HOST    = "0.0.0.0"
WEB_SERVER_PORT    = int(os.getenv("PORT", 10000))

GROQ_FAST_MODEL     = "llama-3.1-8b-instant"
GROQ_FALLBACK_MODEL = "llama-3.3-70b-versatile"
GEMINI_SCRIPT_MODEL = "gemini-1.5-pro"

# ── Client init ───────────────────────────────────────────────────────────────
groq_client  = Groq(api_key=GROQ_API_KEY)
genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel(model_name=GEMINI_SCRIPT_MODEL)


# ════════════════════════════════════════════════════════════════════════════
# STAGE 1 — MASTER NARRATIVE SYSTEM PROMPT
# NO block numbers. NO character limits. Pure cinematic prose.
# ════════════════════════════════════════════════════════════════════════════

MASTER_NARRATIVE_SYSTEM = """
You are a world-class cinematic documentary screenwriter specializing in dark, bizarre,
and addictive WWII and Cold War espionage stories.

Style: Blend the slow dread and technical obsession of 'Chernobyl', the quiet moral horror
of 'The Zone of Interest', and the tense realism of 'The Americans'.

---

ABSOLUTE RULES — VIOLATION OF ANY RULE MEANS THE OUTPUT IS INVALID:

1. Write ONE single, continuous master script in pure flowing prose.
   No numbered blocks. No segmentation. No headers. No act breaks. No bullet points.
   If you produce a numbered block, you have failed. Start over internally.

2. Never mention character limits, block numbers, or segmentation in any form.

3. Never use these phrases anywhere in the script body:
   "as we have seen" / "it is worth noting" / "this shows us" /
   "in conclusion" / "to summarise" / "today we explore" / "in this documentary"

4. Do NOT invent major characters. Every named person must be real and accurately described.
   Invented names like fictional characters are fabrications — they destroy credibility.
   If you are uncertain about a name, use their documented title and role instead.

5. Do NOT use generic atmospheric openers:
   BANNED: "dimly lit corridors", "chilly morning", "shadows fell across",
           "it was a dark time", "the world was at war"
   REQUIRED: A specific real moment. A specific real person. A specific real detail
             that is bizarre, disturbing, or counterintuitive.

6. Do NOT summarise or conclude before reaching the target word count.

7. Do NOT truncate. If you are approaching your output limit, continue the narrative —
   do not wrap up early.

---

COLD OPEN (first 300-500 words):

Begin with a real, strange, documented detail that most people have never heard.
The opening sentence must create immediate curiosity, unease, or moral shock.
The first paragraph must make the listener lean forward.
End the cold open with one explicit unanswered question that drives everything that follows.

Examples of strong openings (do NOT copy — use the principle):
- The specific physical sensation of a real procedure being performed
- A number that seems impossible until you understand its context
- A direct quote from a real document or testimony that reframes the entire story
- A mundane bureaucratic detail that reveals something monstrous

---

OPEN LOOPS:

Every 600-900 words, introduce a named real entity — a person, a document, an operation,
a location — whose full significance you withhold. Return to it later with a revelation
that recontextualises everything before it.

---

ENTITY RULE:

Every major claim attaches to a specific real named entity.
WRONG: "a Nazi scientist", "a classified document", "a Soviet agent"
RIGHT: "SS-Hauptsturmführer Bernhard Krüger, head of Operation Bernhard"
RIGHT: "Adolf Burger, typographer, Auschwitz prisoner number 64401"
RIGHT: "the Toplitzsee, a glacial lake in the Austrian Alps, June 1945"

---

SHOW DON'T TELL — SENSORY AND SPECIFIC:

Describe what things looked, felt, sounded, and smelled like.
The physical reality of events creates visceral impact that abstract description cannot.
A prisoner aging banknotes by rubbing them between his palms for hours is more powerful
than "the prisoners were forced to work on the counterfeiting operation."

---

TONE TAGS — MAXIMUM 3 USES EACH:

Place on their own line, immediately before the sentence or paragraph they introduce.

[Cold]     — Flat. Factual. No emotion. The horror is in the absence of reaction.
[Whisper]  — Intimate. Slow. Something that was meant to stay buried.
[Clinical] — Procedural. Detached. The bureaucratic language of atrocity.

Use these only when the tone genuinely shifts. Never cluster them. Never force them.

---

SENTENCE RHYTHM — NON-NEGOTIABLE:

Short sentences cut. Long sentences build atmosphere, accumulate detail, pull the listener
through a corridor of implication until they arrive somewhere they did not expect.
Alternate. Never let three sentences run the same length. Read it back mentally —
if it sounds like a Wikipedia article, rewrite it.

---

HISTORICAL ACCURACY — MAXIMUM PRIORITY:

This channel's credibility depends entirely on factual grounding.
Real bizarre details are always more powerful than invented ones.
If a real event sounds impossible, that is the point.

---

ENDING (final 400-600 words):

Resolve the open loops one by one. Each answer must be darker than the question suggested.
End on a concrete image — physical, specific, real.
Not a moral. Not a summary. An image that stays.

---

FACT-CHECK LEDGER (append after final paragraph, one blank line gap):

[FACT_CHECK]
1. Claim: <one sentence naming a specific real person, document, or operation>
   Status: VERIFIED HISTORICAL RECORD / DECLASSIFIED DOCUMENT / UNSOLVED MYSTERY
2. Claim:
   Status:
3. Claim:
   Status:
4. Claim:
   Status:
5. Claim:
   Status:

---

TARGET LENGTH:
30-minute script: 4200-5000 words of unbroken prose
60-minute script: 8500-10500 words of unbroken prose

Begin directly with the Cold Open.
Write the full master script in one unbroken flow.
Do not stop. Do not number anything. Do not summarise early.
Every word must earn its place.
"""

# ── Quick-command prompt (list outputs — Groq fast model) ─────────────────────
QUICK_SYSTEM = """
You are the research engine for "TheBizzarePast" — a YouTube channel covering
suppressed WWII and Cold War history.

Domain: World War II (1930-1945), post-war intelligence (1945-1965), Cold War (to ~1975).

Rules:
- Every entry must name at least one specific person, document, operation, or location.
- BANNED: "a Nazi scientist", "a classified file", "a Soviet agent"
- REQUIRED: named individuals, named programs, named locations
- No preamble. No sign-off. Output the structured list only.
"""

HELP_TEXT = (
    "TheBizzarePast V2.0 — Master Narrative Engine\n\n"
    "/trend                              — 5 WWII/Cold War iceberg topics\n"
    "/figure [name]                      — 5 suppressed angles on a figure\n"
    "/event [event]                      — 5 censored sub-narratives\n"
    "/build [topic] | [30 or 60] | [standard or max]\n\n"
    "Guided flow:\n"
    "  1. /trend, /figure, or /event\n"
    "  2. Reply 1-5 to select\n"
    "  3. Reply 30 or 60\n"
    "  4. Reply standard or max\n\n"
    "Pipeline:\n"
    "  Stage 1 — Gemini 1.5 Pro: cinematic master script (no block limits)\n"
    "  Stage 2 — Smart Slicer: Python cuts prose into TTS-ready blocks\n"
    "  Fallback — Groq llama-3.3-70b if Gemini unavailable"
)

user_state: dict[int, dict] = {}

router       = Router()
bot          = Bot(token=TELEGRAM_BOT_TOKEN)
dp           = Dispatcher()
dp.include_router(router)
_active_jobs = 0


# ════════════════════════════════════════════════════════════════════════════
# STAGE 2 — SMART SLICER
# Pure Python. Receives master prose. Returns TTS-ready labelled blocks.
# ════════════════════════════════════════════════════════════════════════════

TONE_TAGS    = frozenset({"[Cold]", "[Whisper]", "[Clinical]", "[Urgent]", "[Dread]", "[Detached]"})

# Sentence boundary: end punctuation followed by whitespace + capital letter (or end of string)
SENT_BOUNDARY = re.compile(r'(?<=[.!?…])\s+(?=[A-Z\[])|(?<=[.!?…])\s*$')


def _split_sentences(text: str) -> list[str]:
    """
    Split text into individual sentences using punctuation boundaries.
    Preserves tone tags as standalone tokens.
    """
    sentences = []
    lines     = text.splitlines()

    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Tone tags live on their own line — treat as standalone token
        if line in TONE_TAGS:
            sentences.append(line)
            continue
        # Split on sentence boundaries
        parts = SENT_BOUNDARY.split(line)
        for part in parts:
            part = part.strip()
            if part:
                sentences.append(part)

    return sentences


def smart_segmenter(master_script: str, limit: int = 285) -> list[str]:
    """
    Slice a continuous master narrative into TTS-ready blocks.

    Rules:
    1. Blocks <= limit characters.
    2. Never cut mid-sentence — split only at . ! ? … boundaries.
    3. Tone tags ([Cold], [Whisper], [Clinical] etc.) are pulled onto the
       next block they precede, so each block that follows a tag begins with it.
    4. Each block prepended with [Block NNN] (3-digit zero-padded).
    5. [FACT_CHECK] ledger detected and passed through as a single unsegmented block.
    6. The last sentence of a completed block is NOT duplicated in the next block
       (overlap was removed — it caused repetition in TTS output).
    """

    # ── Separate ledger ───────────────────────────────────────────────────────
    ledger     = ""
    ledger_idx = master_script.find("[FACT_CHECK]")
    if ledger_idx != -1:
        ledger       = master_script[ledger_idx:].strip()
        master_script = master_script[:ledger_idx].strip()

    sentences   = _split_sentences(master_script)
    raw_blocks  = []
    current     = ""
    pending_tag = None   # tone tag waiting to be prepended to next block

    for token in sentences:

        # ── Token is a tone tag ───────────────────────────────────────────────
        if token in TONE_TAGS:
            # Flush current block before attaching tag to the next one
            if current.strip():
                raw_blocks.append(current.strip())
                current = ""
            pending_tag = token
            continue

        # ── Decide how to open this sentence ─────────────────────────────────
        # If there's a pending tag and current block is empty, prepend tag
        if pending_tag and not current:
            token       = f"{pending_tag} {token}"
            pending_tag = None

        candidate = (current + " " + token).strip() if current else token

        if len(candidate) <= limit:
            # Fits in current block
            current = candidate
        else:
            # Flush current block
            if current.strip():
                raw_blocks.append(current.strip())

            # Check if the sentence itself is too long
            if len(token) > limit:
                # Hard-split on word boundaries as last resort
                words = token.split()
                chunk = ""
                for word in words:
                    test = (chunk + " " + word).strip()
                    if len(test) <= limit:
                        chunk = test
                    else:
                        if chunk:
                            raw_blocks.append(chunk)
                        chunk = word
                current = chunk
            else:
                current = token

            # If there's a pending tag, prepend to new block
            if pending_tag and current and not current.startswith("["):
                current     = f"{pending_tag} {current}"
                pending_tag = None

    # Flush final block
    if current.strip():
        raw_blocks.append(current.strip())

    # ── Label blocks ──────────────────────────────────────────────────────────
    labelled = [f"[Block {i+1:03d}] {block}" for i, block in enumerate(raw_blocks)]

    # ── Append ledger as final unsegmented block ──────────────────────────────
    if ledger:
        labelled.append(f"\n{ledger}")

    return labelled


# ════════════════════════════════════════════════════════════════════════════
# LLM CALLS
# ════════════════════════════════════════════════════════════════════════════

async def groq_call(prompt: str, max_tokens: int = 1200,
                    model: str = GROQ_FAST_MODEL,
                    system: str = QUICK_SYSTEM) -> str:
    global _active_jobs
    _active_jobs += 1
    try:
        res = await asyncio.to_thread(
            lambda: groq_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user",   "content": prompt},
                ],
                max_tokens=max_tokens,
                temperature=0.78,
            )
        )
        return res.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Groq error ({model}): {e}")
        raise
    finally:
        _active_jobs -= 1


async def gemini_call(user_prompt: str) -> str:
    """
    Send master narrative request to Gemini 1.5 Pro.
    System prompt prepended directly — Gemini reads it as authoring instructions.
    """
    global _active_jobs
    _active_jobs += 1
    try:
        full_prompt = (
            f"{MASTER_NARRATIVE_SYSTEM}\n\n"
            f"{'=' * 60}\n\n"
            f"{user_prompt}"
        )
        res = await asyncio.to_thread(
            lambda: gemini_model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.82,
                    max_output_tokens=8192,   # ~6000 words headroom for 60-min scripts
                )
            )
        )
        return res.text.strip()
    except Exception as e:
        logger.error(f"Gemini error: {e}")
        raise
    finally:
        _active_jobs -= 1


async def master_script_call(user_prompt: str) -> tuple[str, str]:
    """
    Try Gemini 1.5 Pro first (quality).
    Fall back to Groq llama-3.3-70b (reliability).
    Returns (raw_master_text, provider_label).
    """
    try:
        logger.info("Stage 1: Gemini 1.5 Pro")
        text = await gemini_call(user_prompt)
        return text, "Gemini 1.5 Pro"
    except Exception as ge:
        logger.warning(f"Gemini failed ({ge}) — switching to Groq fallback")
        try:
            text = await groq_call(
                user_prompt,
                max_tokens=7000,   # raised for V2.5 long-form fallback
                model=GROQ_FALLBACK_MODEL,
                system=MASTER_NARRATIVE_SYSTEM
            )
            return text, "Groq llama-3.3-70b (fallback)"
        except Exception as qe:
            return (
                f"ENGINE ERROR\nGemini: {ge}\nGroq: {qe}",
                "none"
            )


# ════════════════════════════════════════════════════════════════════════════
# DELIVERY
# ════════════════════════════════════════════════════════════════════════════

async def send_long(message: Message, text: str):
    """Send raw text, respecting Telegram's 4096-char message limit."""
    while len(text) > 4096:
        idx = text.rfind("\n", 0, 4096)
        if idx == -1:
            idx = 4096
        await message.answer(text[:idx])
        text = text[idx:].lstrip()
        await asyncio.sleep(0.35)
    if text.strip():
        await message.answer(text)


async def deliver_blocks(message: Message, blocks: list[str]):
    """
    Batch consecutive blocks into single Telegram messages (≤4096 chars)
    to reduce notification noise. Each batch separated by blank line.
    """
    batch = ""
    for block in blocks:
        separator = "\n\n" if batch else ""
        candidate = batch + separator + block
        if len(candidate) <= 4096:
            batch = candidate
        else:
            if batch:
                await message.answer(batch)
                await asyncio.sleep(0.35)
            batch = block
    if batch:
        await message.answer(batch)


async def generate_script(message: Message, topic: str,
                           length: str, controversy: str):
    """
    Full two-stage pipeline:
      Stage 1 — LLM produces cinematic master prose (no block limits)
      Stage 2 — smart_segmenter() slices into TTS-ready labelled blocks
    """
    word_target = "4200-4800 words" if length == "30" else "8500-10000 words"

    await message.answer(
        f"PRODUCTION INITIATED — V2.0\n"
        f"Topic:  {topic}\n"
        f"Length: {length} min ({word_target})\n"
        f"Mode:   {controversy.upper()}\n\n"
        f"Stage 1 — Gemini 1.5 Pro writing master narrative...\n"
        f"(no block constraints — pure prose)\n"
        f"Stand by 30-90 seconds."
    )

    # ── Stage 1: master narrative ─────────────────────────────────────────────
    # Topic injected explicitly. Enforcement reminder repeated in user turn —
    # critical for counteracting the LLM's default tendency to revert to blocks.
    user_prompt = (
        f"TOPIC: {topic}\n"
        f"CONTROVERSY LEVEL: {controversy}\n"
        f"TARGET: {word_target} of unbroken, continuous prose.\n\n"
        f"PRE-FLIGHT CHECKLIST — CONFIRM BEFORE WRITING:\n"
        f"- You are writing ONE continuous cinematic master script.\n"
        f"- Zero numbered blocks. Zero segmentation. Zero character-limit mentions.\n"
        f"- Every named person must be real and historically accurate.\n"
        f"- The Cold Open must open on a specific, bizarre, real detail.\n"
        f"- You will not stop or summarise early.\n"
        f"- You will not wrap up before reaching {word_target}.\n\n"
        f"BEGIN THE COLD OPEN NOW:"
    )

    master, provider = await master_script_call(user_prompt)

    if master.startswith("ENGINE ERROR"):
        await message.answer(master)
        return

    word_count = len(master.split())
    await message.answer(
        f"Stage 1 complete — {provider}\n"
        f"Master script: ~{word_count:,} words\n\n"
        f"Stage 2 — Smart Slicer running..."
    )

    # ── Stage 2: slice into TTS blocks ────────────────────────────────────────
    blocks = await asyncio.to_thread(smart_segmenter, master, 285)

    await message.answer(
        f"Stage 2 complete — {len(blocks)} blocks generated\n"
        f"Delivering..."
    )

    await deliver_blocks(message, blocks)


# ════════════════════════════════════════════════════════════════════════════
# COMMAND HANDLERS
# ════════════════════════════════════════════════════════════════════════════

def parse_list_items(text: str) -> list[str]:
    items = []
    for match in re.finditer(
        r'^\s*\d+\.\s+(?:Title:\s*)?(.+?)(?=\n\s*\d+\.|\Z)',
        text, re.MULTILINE | re.DOTALL
    ):
        items.append(match.group(1).strip().split("\n")[0].strip())
        if len(items) == 5:
            break
    return items


@router.message(CommandStart())
async def cmd_start(message: Message):
    user_state.pop(message.from_user.id, None)
    await message.answer(HELP_TEXT)


@router.message(Command("help"))
async def cmd_help(message: Message):
    user_state.pop(message.from_user.id, None)
    await message.answer(HELP_TEXT)


@router.message(Command("trend"))
async def cmd_trend(message: Message):
    uid    = message.from_user.id
    prompt = (
        "Output exactly 5 viral WWII/Cold War YouTube topic ideas.\n\n"
        "FORMAT:\n"
        "[TREND_RESULTS]\n\n"
        "1. Title: <max 14 words — must be specific, not generic>\n"
        "   Teaser: <exactly 2 sentences — must name at least one real person, "
        "operation, or location>\n\n"
        "2-5: same format. No preamble. No sign-off."
    )
    result = await groq_call(prompt, 900)
    items  = parse_list_items(result)
    user_state[uid] = {"mode": "trend", "items": items, "step": "awaiting_selection"}
    await send_long(message, result)
    await message.answer("Reply 1-5 to select a topic.")


@router.message(Command("figure"))
async def cmd_figure(message: Message):
    uid   = message.from_user.id
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        await message.answer("Usage: /figure Heinrich Himmler")
        return
    name   = parts[1].strip()
    prompt = (
        f"Output exactly 5 suppressed, psychological, or disturbing historical "
        f"angles about: {name}.\n\n"
        "FORMAT:\n"
        "[FIGURE_RESULTS]\n"
        f"Name: {name}\n\n"
        "1. <1-2 sentences — must name a specific document, operation, or location>\n"
        "2-5: same. No filler. No mainstream biography."
    )
    result = await groq_call(prompt, 1200)
    items  = parse_list_items(result)
    user_state[uid] = {"mode": "figure", "items": items, "step": "awaiting_selection"}
    await send_long(message, result)
    await message.answer("Reply 1-5 to select an angle.")


@router.message(Command("event"))
async def cmd_event(message: Message):
    uid   = message.from_user.id
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        await message.answer("Usage: /event Operation Paperclip")
        return
    event  = parts[1].strip()
    prompt = (
        f"Output exactly 5 censored or suppressed sub-narratives about: {event}.\n\n"
        "FORMAT:\n"
        "[EVENT_RESULTS]\n"
        f"Event: {event}\n\n"
        "1. <1-2 sentences — must name a specific person, document, or sub-operation>\n"
        "2-5: same. No mainstream summaries."
    )
    result = await groq_call(prompt, 1200)
    items  = parse_list_items(result)
    user_state[uid] = {"mode": "event", "items": items, "step": "awaiting_selection"}
    await send_long(message, result)
    await message.answer("Reply 1-5 to select a narrative.")


BUILD_RE = re.compile(r'^(.+?)\s*\|\s*(30|60)\s*\|\s*(standard|max)$', re.IGNORECASE)

@router.message(Command("build"))
async def cmd_build(message: Message):
    uid   = message.from_user.id
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Usage: /build The Katyn Massacre | 30 | standard")
        return
    match = BUILD_RE.match(parts[1].strip())
    if not match:
        await message.answer(
            "Invalid format.\n"
            "Usage: /build The Katyn Massacre | 30 | standard\n"
            "Length: 30 or 60  |  Mode: standard or max"
        )
        return
    user_state.pop(uid, None)
    await generate_script(
        message,
        match.group(1).strip(),
        match.group(2),
        match.group(3).lower()
    )


# ── Guided state machine ──────────────────────────────────────────────────────
@router.message(F.text)
async def text_handler(message: Message):
    uid  = message.from_user.id
    text = message.text.strip().lower()
    st   = user_state.get(uid)

    if st and st.get("step") == "awaiting_selection":
        if re.match(r'^[1-5]$', text):
            idx   = int(text) - 1
            items = st.get("items", [])
            if idx < len(items):
                st["topic"] = items[idx]
                st["step"]  = "awaiting_length"
                await message.answer(
                    f"Selected: {items[idx]}\n\n"
                    "SELECT LENGTH: reply with 30 or 60"
                )
            else:
                await message.answer("Selection not found. Reply with 1-5.")
        else:
            await message.answer("Reply with a number between 1 and 5.")
        return

    if st and st.get("step") == "awaiting_length":
        if text in ("30", "60"):
            st["length"] = text
            st["step"]   = "awaiting_controversy"
            await message.answer("SELECT CONTROVERSY: reply with standard or max")
        else:
            await message.answer("Reply with 30 or 60.")
        return

    if st and st.get("step") == "awaiting_controversy":
        if text in ("standard", "max"):
            topic, length, controversy = st["topic"], st["length"], text
            user_state.pop(uid, None)
            await generate_script(message, topic, length, controversy)
        else:
            await message.answer("Reply with standard or max.")
        return

    await message.answer(HELP_TEXT)


# ════════════════════════════════════════════════════════════════════════════
# SERVER
# ════════════════════════════════════════════════════════════════════════════

async def health(request: web.Request) -> web.Response:
    return web.Response(text="OK", status=200)


async def telegram_webhook(request: web.Request) -> web.Response:
    try:
        data   = await request.json()
        update = Update(**data)
        await dp.feed_update(bot=bot, update=update)
    except Exception as e:
        logger.error(f"Webhook error: {e}")
    return web.Response(text="OK", status=200)


async def create_app() -> web.Application:
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_webhook(WEBHOOK_URL)
    logger.info(f"Webhook registered: {WEBHOOK_URL}")

    app = web.Application()
    app.router.add_get("/",         health)
    app.router.add_post("/webhook", telegram_webhook)

    async def on_shutdown(app):
        waited = 0
        while _active_jobs > 0 and waited < 15:
            logger.info(f"Draining {_active_jobs} active job(s)...")
            await asyncio.sleep(1)
            waited += 1
        await bot.session.close()
        logger.info("Session closed cleanly.")

    app.on_shutdown.append(on_shutdown)
    return app


if __name__ == "__main__":
    web.run_app(create_app(), host=WEB_SERVER_HOST, port=WEB_SERVER_PORT)
