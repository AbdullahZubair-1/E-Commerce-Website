import asyncio
import os
import re
from datetime import datetime

import aiohttp
from dotenv import load_dotenv
from loguru import logger

from pipecat.adapters.schemas.function_schema import FunctionSchema
from pipecat.adapters.schemas.tools_schema import ToolsSchema
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.frames.frames import (
    Frame,
    LLMFullResponseEndFrame,
    LLMFullResponseStartFrame,
    LLMRunFrame,
    TextFrame,
    TTSSpeakFrame,
)
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor
from pipecat.runner.types import RunnerArguments
from pipecat.runner.utils import create_transport
from pipecat.services.cartesia.tts import CartesiaTTSService
from pipecat.services.groq.llm import GroqLLMService
from pipecat.services.groq.stt import GroqSTTService
from pipecat.transports.base_transport import TransportParams

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
CARTESIA_API_KEY = os.getenv("CARTESIA_API_KEY")
CARTESIA_VOICE_ID = os.getenv("CARTESIA_VOICE_ID", "79a125e8-cd45-4c13-8a67-188112f4dd22")  # British Lady
# Base URL of the e-commerce FastAPI backend, so Ana answers from the real
# product catalog instead of the open internet.
BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://localhost:8000/api/v1")
# Which storefront this instance of Ana serves (e.g. "chemisto" or
# "chemisto-food"). Sent as X-Site-Slug on every catalog lookup, so this
# instance only ever sees and talks about its own site's products. Run a
# separate instance of this same bot.py (different SITE_SLUG + port) per
# site -- see docker-compose.yml / voice-agent/INTEGRATION.md.
SITE_SLUG = os.getenv("SITE_SLUG", "chemisto")

# Keep the system prompt + this many most-recent messages. Older turns get
# dropped so each new request doesn't resend the entire conversation history
# (which is what burns through the daily token quota fastest).
MAX_HISTORY_MESSAGES = 10
TRIM_INTERVAL_SECONDS = 20

# Friendly display name per site slug, used in the spoken system prompt.
SITE_NAMES = {
    "chemisto": "Chemisto",
    "chemisto-food": "Chemisto Food",
}


def build_system_instruction(site_slug: str) -> str:
    store_name = SITE_NAMES.get(site_slug, site_slug.replace("-", " ").title())
    current_date = datetime.now().strftime("%Y-%m-%d (%A)")
    return f"""Your name is Ana, a friendly voice assistant for the
{store_name} store. If asked your name, say Ana. Keep every answer to 1-2
short sentences, maximum 20-25 words, unless the user explicitly asks for
more detail. Get straight to the point. You are bilingual: detect whether the
customer is speaking English or Urdu. The speech-to-text transcription may
come through in Roman/Latin letters even when the customer spoke Urdu (e.g.
"ap kya bech rahe hain") -- treat that as Urdu, not English, based on the
words and sentence structure, not the letters used. Always reply in
whichever language the customer actually spoke. You ONLY speak English and
Urdu -- never any other language, even if the transcribed text looks like
it might be in French, Turkish, Arabic, or anything else. Speech-to-text on a
live call is often unreliable and can garble unclear audio into text that
merely resembles another language; if the transcribed text doesn't clearly
read as real English or real Urdu, treat it as unclear audio -- respond in
English by default and ask the customer to repeat themselves -- rather than
replying in whatever language the garbled text superficially resembles.
The
product catalog itself is in English, so when calling search_products,
always translate the search query into English first, even if the
conversation is in Urdu. Whenever the customer asks about a
product, price, availability, category, or brand — ALWAYS call
search_products first, even if the item sounds like it wouldn't normally fit
this store. Never assume what the store does or doesn't carry from your own
judgment — the catalog is the only source of truth. Only say you don't carry
something after search_products actually returns no matching results. Use
get_current_time only for time/date questions. If asked about something that
is clearly not a product question at all — general knowledge, weather, other
stores — politely say you can only help with questions about this store and
its products. You only give information — you cannot take orders, add items
to a cart, process payments, or complete a purchase yourself, and you cannot
offer to do any of those things either. If the customer wants to buy
something, tell them to add it to their cart and check out on
the website themselves; never say things like "I've added that", "your order is
placed", "would you like me to add that to your cart", or anything else that
implies you can act on their cart or order. You CAN help book a doctor
appointment -- this is a real capability, not information-only. If the
customer wants to see a doctor: ask what date they'd like (convert relative
dates like "tomorrow" or "next Monday" into YYYY-MM-DD yourself using
today's date, given below), then call check_doctor_availability with that
date to see which doctors have open slots. Read out the doctor names,
specialties, and a few available times. Once the customer picks a doctor and
a time, ask for their name, email, and phone number if you don't already
have them, then call book_doctor_appointment with the exact slot they chose.
After a successful booking, confirm the doctor's name and the appointment
time back to the customer. If check_doctor_availability returns no doctors
or no slots, say so plainly and suggest a different date -- never invent a
doctor or a time slot that wasn't actually returned by the tool.
Today's date is {current_date}. Always write the store name and
any product, brand, or category names in normal sentence case, never in all
capital letters — this is spoken aloud, and all-caps words get read out
letter by letter instead of as a word. No formatting, no emojis, no
symbols."""


# ---- Tool schemas (definitions only — actual functions are created inside run_bot,
#      so they can speak a filler line via `task` the moment they start) ----

time_function = FunctionSchema(
    name="get_current_time",
    description="Get the current date and time",
    properties={},
    required=[],
)

search_products_function = FunctionSchema(
    name="search_products",
    description="Search this store's product catalog by name, category, or "
    "brand to answer questions about products, pricing, availability, "
    "categories, or brands. Always use this before answering a product "
    "question — never guess or make up product details.",
    properties={
        "query": {
            "type": "string",
            "description": "What to search for, e.g. 'lab coat' or 'safety goggles'",
        }
    },
    required=["query"],
)

check_doctor_availability_function = FunctionSchema(
    name="check_doctor_availability",
    description="Check which doctors are available on a given date and what "
    "times they're free. Always call this before offering a doctor "
    "appointment slot — never invent a doctor or a time.",
    properties={
        "date": {
            "type": "string",
            "description": "Date to check, in YYYY-MM-DD format",
        }
    },
    required=["date"],
)

book_doctor_appointment_function = FunctionSchema(
    name="book_doctor_appointment",
    description="Book a real appointment with a doctor. Only call this after "
    "check_doctor_availability confirmed the doctor and time are actually "
    "available, and after collecting the customer's name, email, and phone.",
    properties={
        "doctor_name": {
            "type": "string",
            "description": "The doctor's name exactly as returned by check_doctor_availability",
        },
        "slot_iso": {
            "type": "string",
            "description": "The exact ISO 8601 datetime of the slot the customer chose, as returned by check_doctor_availability",
        },
        "customer_name": {"type": "string", "description": "The customer's full name"},
        "customer_email": {"type": "string", "description": "The customer's email address"},
        "customer_phone": {"type": "string", "description": "The customer's phone number"},
    },
    required=["doctor_name", "slot_iso", "customer_name", "customer_email", "customer_phone"],
)

tools = ToolsSchema(standard_tools=[
    time_function,
    search_products_function,
    check_doctor_availability_function,
    book_doctor_appointment_function,
])

transport_params = {
    "webrtc": lambda: TransportParams(
        audio_in_enabled=True,
        audio_out_enabled=True,
        vad_analyzer=SileroVADAnalyzer(),
    ),
}


_FUNCTION_CALL_LEAK_PATTERN = re.compile(r"^\s*<function=")


class SuppressLeakedToolCallText(FrameProcessor):
    """Safety net for a known Groq/Llama-family quirk: instead of using the
    structured tool-calling mechanism, the model occasionally writes its tool
    call out as literal text (e.g. '<function=search_products>{"query": "x"}
    </function>'), which would otherwise get read aloud verbatim by TTS.

    This buffers just enough of the start of each assistant turn to tell
    whether it's a leaked tool call. If it is, the leaked text is dropped
    (never sent to TTS) and a short spoken fallback is queued instead. If
    it isn't, the buffered text is flushed immediately and every later chunk
    in that turn passes straight through, so normal speech is not delayed.

    This does not fix the underlying model flakiness -- it only stops the
    customer from hearing raw code when it happens.
    """

    def __init__(self):
        super().__init__()
        self._buffer = ""
        self._checked = False
        self._suppressing = False

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)

        if isinstance(frame, LLMFullResponseStartFrame):
            self._buffer = ""
            self._checked = False
            self._suppressing = False
            await self.push_frame(frame, direction)
            return

        if isinstance(frame, LLMFullResponseEndFrame):
            if self._buffer and not self._suppressing:
                await self.push_frame(TextFrame(text=self._buffer))
            self._buffer = ""
            self._checked = False
            self._suppressing = False
            await self.push_frame(frame, direction)
            return

        if isinstance(frame, TextFrame):
            if self._suppressing:
                return  # Swallow the rest of a turn we've already flagged as a leak.

            if self._checked:
                await self.push_frame(frame, direction)
                return

            self._buffer += frame.text

            if _FUNCTION_CALL_LEAK_PATTERN.match(self._buffer):
                logger.warning(f"Suppressed leaked tool-call text: {self._buffer!r}")
                self._suppressing = True
                self._checked = True
                self._buffer = ""
                await self.push_frame(
                    TTSSpeakFrame("Sorry, let me try that again for you."), direction
                )
                return

            stripped = self._buffer.strip()
            if len(self._buffer) >= 12 or (stripped != "" and not stripped.startswith("<")):
                # Enough evidence this is normal speech -- flush and stop
                # intercepting for the rest of this turn.
                self._checked = True
                await self.push_frame(TextFrame(text=self._buffer))
                self._buffer = ""
            return

        await self.push_frame(frame, direction)


async def run_bot(transport, runner_args: RunnerArguments):
    logger.info(f"Starting voice agent bot (site={SITE_SLUG})")

    store_name = SITE_NAMES.get(SITE_SLUG, SITE_SLUG.replace("-", " ").title())
    stt = GroqSTTService(
        api_key=GROQ_API_KEY,
        model="whisper-large-v3-turbo",
        # Whisper's language auto-detection can mishear Urdu speech as
        # English and force-fit it into English-sounding gibberish. This
        # prompt hint biases recognition toward expected vocabulary in both
        # languages. Written as plain continuation text (not a labeled
        # "Examples:" list) -- a labeled/quoted format was getting echoed
        # back verbatim into transcriptions on unclear audio instead of just
        # biasing vocabulary quietly.
        prompt=(
            f"Yeh {store_name} ki customer service call hai. Customer kabhi "
            "English mein baat karta hai, kabhi Roman Urdu mein, jaise "
            "kon kon si items hain hamare paas, ya iska price kya hai, ya "
            "yeh chahiye mujhe."
        ),
    )

    llm = GroqLLMService(
        api_key=GROQ_API_KEY,
        # llama-3.3-70b-versatile was deprecated by Groq (June 2026); this is
        # their recommended replacement, and has more reliable tool-calling
        # behavior over the OpenAI-compatible API.
        model="openai/gpt-oss-120b",
        params=GroqLLMService.InputParams(
            temperature=0.1,
            # gpt-oss models are "reasoning" models that think step-by-step
            # before answering. By default Groq includes that raw reasoning
            # trace in the response, which was leaking into what got spoken
            # to the customer. `reasoning_format` (the usual way to hide
            # this) is explicitly NOT supported for gpt-oss models per
            # Groq's docs -- include_reasoning=False is the documented way
            # to suppress it for this model family specifically.
            extra={"include_reasoning": False},
        ),
    )

    tts = CartesiaTTSService(
        api_key=CARTESIA_API_KEY,
        voice_id=CARTESIA_VOICE_ID,
    )

    messages = [{"role": "system", "content": build_system_instruction(SITE_SLUG)}]
    context = OpenAILLMContext(messages, tools)
    context_aggregator = llm.create_context_aggregator(context)

    pipeline = Pipeline(
        [
            transport.input(),
            stt,
            context_aggregator.user(),
            llm,
            SuppressLeakedToolCallText(),
            tts,
            transport.output(),
            context_aggregator.assistant(),
        ]
    )

    task = PipelineTask(
        pipeline,
        params=PipelineParams(
            enable_metrics=True,
            enable_usage_metrics=True,
        ),
    )

    # ---- Automatic history trimming ----
    # Runs in the background and periodically shrinks the context back down to
    # the system prompt + the most recent messages, so long conversations don't
    # keep growing the token cost of every single turn.
    async def trim_history_loop():
        while True:
            await asyncio.sleep(TRIM_INTERVAL_SECONDS)
            try:
                current = context.get_messages()
                if len(current) > MAX_HISTORY_MESSAGES + 1:
                    trimmed = [current[0]] + current[-MAX_HISTORY_MESSAGES:]
                    context.set_messages(trimmed)
                    logger.info(
                        f"Trimmed conversation history: {len(current)} -> {len(trimmed)} messages"
                    )
            except Exception as e:
                logger.warning(f"History trim skipped: {e}")

    trim_task = asyncio.create_task(trim_history_loop())

    # ---- Tool implementations (defined here so they can use `task` to speak a
    #      filler line immediately when the tool starts, instead of going silent) ----

    async def get_current_time(params):
        await task.queue_frames([TTSSpeakFrame("Let me check the time.")])
        now = datetime.now()
        await params.result_callback(
            {"time": now.strftime("%I:%M %p"), "date": now.strftime("%A, %B %d, %Y")}
        )

    async def search_products(params):
        await task.queue_frames([TTSSpeakFrame("Let me check that for you.")])
        query = params.arguments.get("query", "")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{BACKEND_API_URL}/products/",
                    params={"search": query, "page_size": 5},
                    headers={"X-Site-Slug": SITE_SLUG},
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as resp:
                    payload = await resp.json()
        except Exception as e:
            logger.warning(f"search_products failed: {e}")
            await params.result_callback({"products": [], "error": "catalog lookup failed"})
            return

        items = (payload.get("data") or {}).get("items", [])
        products = [
            {
                "name": item.get("name"),
                "price": item.get("price"),
                "stock": item.get("stock_quantity"),
                "category": (item.get("category") or {}).get("name"),
                "brand": (item.get("brand") or {}).get("name"),
                "description": item.get("description"),
            }
            for item in items
        ]
        await params.result_callback({"products": products})

    async def check_doctor_availability(params):
        await task.queue_frames([TTSSpeakFrame("Let me check the doctors' schedules.")])
        date = params.arguments.get("date", "")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{BACKEND_API_URL}/appointments/doctors",
                    headers={"X-Site-Slug": SITE_SLUG},
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as resp:
                    doctors_payload = await resp.json()
                doctors = (doctors_payload.get("data") or [])

                results = []
                for doc in doctors:
                    async with session.get(
                        f"{BACKEND_API_URL}/appointments/availability",
                        params={"doctor_id": doc["id"], "start_date": date, "end_date": date},
                        headers={"X-Site-Slug": SITE_SLUG},
                        timeout=aiohttp.ClientTimeout(total=10),
                    ) as slot_resp:
                        if slot_resp.status != 200:
                            continue
                        slot_payload = await slot_resp.json()
                        slots = (slot_payload.get("data") or {}).get("slots", [])
                    if slots:
                        results.append({
                            "doctor_name": doc["name"],
                            "specialty": doc.get("specialty"),
                            "available_slots": slots[:5],  # cap so this stays short to speak
                        })
        except Exception as e:
            logger.warning(f"check_doctor_availability failed: {e}")
            await params.result_callback({"doctors": [], "error": "availability lookup failed"})
            return

        await params.result_callback({"doctors": results})

    async def book_doctor_appointment(params):
        await task.queue_frames([TTSSpeakFrame("Booking that for you now.")])
        doctor_name = params.arguments.get("doctor_name", "")
        slot_iso = params.arguments.get("slot_iso", "")
        customer_name = params.arguments.get("customer_name", "")
        customer_email = params.arguments.get("customer_email", "")
        customer_phone = params.arguments.get("customer_phone", "")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{BACKEND_API_URL}/appointments/doctors",
                    headers={"X-Site-Slug": SITE_SLUG},
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as resp:
                    doctors_payload = await resp.json()
                doctors = (doctors_payload.get("data") or [])
                match = next(
                    (d for d in doctors if d["name"].strip().lower() == doctor_name.strip().lower()),
                    None,
                )
                if not match:
                    await params.result_callback({"success": False, "error": f"No doctor found named '{doctor_name}'."})
                    return

                async with session.post(
                    f"{BACKEND_API_URL}/appointments/book",
                    headers={"X-Site-Slug": SITE_SLUG, "Content-Type": "application/json"},
                    json={
                        "doctor_id": match["id"],
                        "start_iso": slot_iso,
                        "customer_name": customer_name,
                        "customer_email": customer_email,
                        "customer_phone": customer_phone,
                    },
                    timeout=aiohttp.ClientTimeout(total=15),
                ) as book_resp:
                    book_payload = await book_resp.json()
                    if book_resp.status not in (200, 201) or not book_payload.get("success"):
                        await params.result_callback({
                            "success": False,
                            "error": book_payload.get("message", "Booking failed."),
                        })
                        return
        except Exception as e:
            logger.warning(f"book_doctor_appointment failed: {e}")
            await params.result_callback({"success": False, "error": "booking request failed"})
            return

        await params.result_callback({"success": True, **book_payload.get("data", {})})

    llm.register_function("get_current_time", get_current_time)
    llm.register_function("search_products", search_products)
    llm.register_function("check_doctor_availability", check_doctor_availability)
    llm.register_function("book_doctor_appointment", book_doctor_appointment)

    @transport.event_handler("on_client_connected")
    async def on_client_connected(transport, client):
        logger.info("Client connected")
        # Fixed greeting
        messages.append(
            {
                "role": "system",
                "content": 'Say exactly: "Hi, my name is Ana. How can I help you today?" and nothing else.',
            }
        )
        await task.queue_frames([LLMRunFrame()])

    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, client):
        logger.info("Client disconnected")
        trim_task.cancel()
        await task.cancel()

    runner = PipelineRunner()
    await runner.run(task)


async def bot(runner_args: RunnerArguments):
    """Entry point called by Pipecat's built-in local dev runner. Which site
    this serves is fixed per running instance (via SITE_SLUG) -- run a
    separate instance of this same bot.py per site."""
    transport = await create_transport(runner_args, transport_params)
    await run_bot(transport, runner_args)


if __name__ == "__main__":
    from pipecat.runner.run import main

    main()