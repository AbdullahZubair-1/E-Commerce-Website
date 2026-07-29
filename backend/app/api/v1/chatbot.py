import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from openai import AsyncOpenAI
from google import genai
from google.genai import types

from app.core.config import settings
from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.site import get_current_site
from app.models.user import User
from app.models.site import Site
from app.repositories.product import ProductRepository
from app.schemas.base import success_response

router = APIRouter(prefix="/chatbot", tags=["Chatbot"])

class ChatHistoryItem(BaseModel):
    role: Literal['user', 'assistant']
    text: str

class ChatRequest(BaseModel):
    message: str
    history: list[ChatHistoryItem] = []

class ChatResponse(BaseModel):
    reply: str

def _is_placeholder_key(value: str | None) -> bool:
    return value is None or value.strip() == '' or value.startswith('YOUR_')


def build_system_instruction(site_name: str) -> str:
    from datetime import datetime
    current_date = datetime.now().strftime("%Y-%m-%d (%A)")
    return (
        f"Your name is Ana, a friendly assistant for the {site_name} store. If asked "
        "your name, say Ana. Keep answers concise and friendly -- 1-3 short "
        "sentences unless the customer asks for more detail. You are bilingual: "
        "detect whether the customer is writing in English or Urdu, and always "
        "reply in that same language -- this includes Roman Urdu (Urdu words "
        "spelled out in plain English/Latin letters, e.g. \"ap kya bech rahe "
        "hain\"), which is extremely common and must be treated as Urdu, not "
        "English. If the customer writes in Urdu script, reply in Urdu "
        "script; if they write in Roman Urdu, reply in Roman Urdu (Urdu "
        "words in Latin letters) rather than Urdu script, so it displays "
        "correctly without needing an Urdu font. The product catalog itself is "
        "in English, so when calling search_products, always translate the "
        "search query into English first, even if the conversation is in Urdu. "
        "Whenever the "
        "customer asks about a product, price, availability, category, or brand "
        "-- ALWAYS call search_products first, even if the item sounds like it "
        "wouldn't normally fit this store. Never assume what the store "
        "does or doesn't carry from your own judgment -- the catalog is the only "
        "source of truth. Only say you don't carry something after "
        "search_products actually returns no matching results. If asked about "
        "something that is clearly not a product question at all -- general "
        "knowledge, other stores, unrelated topics -- politely say you can only "
        "help with questions about this store and its products. You only give "
        "information -- you cannot take orders, add items to a cart, process "
        "payments, or complete a purchase yourself, and you cannot offer to "
        "do any of those things either. If a customer wants to buy "
        "something, tell them to add it to their cart and check out on the "
        "website themselves; never say things like \"I've added that\", \"your order is "
        "placed\", \"would you like me to add that to your cart\", or anything else that "
        "implies you can act on their cart or order. You CAN help book a "
        "doctor appointment -- this is a real capability, not "
        "information-only. If the customer wants to see a doctor: ask what "
        "date they'd like (convert relative dates like \"tomorrow\" into "
        "YYYY-MM-DD yourself using today's date, given below), then call "
        "check_doctor_availability with that date. Share the doctor names, "
        "specialties, and a few available times. Once the customer picks a "
        "doctor and time, ask for their name, email, and phone number if you "
        "don't already have them, then call book_doctor_appointment with the "
        "exact slot they chose. After a successful booking, confirm the "
        "doctor's name and the appointment time back to the customer. If "
        "check_doctor_availability returns no doctors or no slots, say so "
        "plainly and suggest a different date -- never invent a doctor or a "
        f"time slot that wasn't actually returned by the tool. Today's date "
        f"is {current_date}."
    )

SEARCH_PRODUCTS_TOOL = types.Tool(
    function_declarations=[
        types.FunctionDeclaration(
            name="search_products",
            description=(
                "Search this store's product catalog by name, category, or "
                "brand to answer questions about products, pricing, "
                "availability, categories, or brands. Always use this before "
                "answering a product question -- never guess or make up "
                "product details."
            ),
            parameters_json_schema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "What to search for, e.g. 'lab coat' or 'safety goggles'",
                    }
                },
                "required": ["query"],
            },
        ),
        types.FunctionDeclaration(
            name="check_doctor_availability",
            description=(
                "Check which doctors are available on a given date and what "
                "times they're free. Always call this before offering a "
                "doctor appointment slot -- never invent a doctor or a time."
            ),
            parameters_json_schema={
                "type": "object",
                "properties": {
                    "date": {"type": "string", "description": "Date to check, in YYYY-MM-DD format"},
                },
                "required": ["date"],
            },
        ),
        types.FunctionDeclaration(
            name="book_doctor_appointment",
            description=(
                "Book a real appointment with a doctor. Only call this after "
                "check_doctor_availability confirmed the doctor and time are "
                "actually available, and after collecting the customer's "
                "name, email, and phone."
            ),
            parameters_json_schema={
                "type": "object",
                "properties": {
                    "doctor_name": {"type": "string", "description": "The doctor's name exactly as returned by check_doctor_availability"},
                    "slot_iso": {"type": "string", "description": "The exact ISO 8601 datetime of the slot the customer chose"},
                    "customer_name": {"type": "string", "description": "The customer's full name"},
                    "customer_email": {"type": "string", "description": "The customer's email address"},
                    "customer_phone": {"type": "string", "description": "The customer's phone number"},
                },
                "required": ["doctor_name", "slot_iso", "customer_name", "customer_email", "customer_phone"],
            },
        ),
    ]
)


def _history_to_contents(history: list[ChatHistoryItem], message: str) -> list[types.Content]:
    """Map the widget's {role: 'user'|'assistant', text} history to Gemini's
    {role: 'user'|'model', parts} Content objects."""
    contents = [
        types.Content(
            role='user' if item.role == 'user' else 'model',
            parts=[types.Part.from_text(text=item.text)],
        )
        for item in history
    ]
    contents.append(types.Content(role='user', parts=[types.Part.from_text(text=message)]))
    return contents


async def _search_products(db: AsyncSession, query: str, site_id) -> dict:
    product_repo = ProductRepository(db)
    products, _ = await product_repo.get_all(page=1, page_size=5, search=query, site_id=site_id)
    return {
        "products": [
            {
                "name": p.name,
                "price": str(p.price),
                "stock": p.stock_quantity,
                "category": p.category.name if p.category else None,
                "brand": p.brand.name if p.brand else None,
                "description": p.description,
            }
            for p in products
        ]
    }


async def _check_doctor_availability(db: AsyncSession, date: str, site_id) -> dict:
    from app.services.appointment import AppointmentService
    service = AppointmentService(db)
    doctors = await service.list_doctors(site_id)
    results = []
    for doc in doctors:
        try:
            slots = await service.get_availability(uuid.UUID(doc["id"]), site_id, date, date)
        except Exception:
            continue
        if slots:
            results.append({
                "doctor_name": doc["name"],
                "specialty": doc.get("specialty"),
                "available_slots": slots[:5],
            })
    return {"doctors": results}


async def _book_doctor_appointment(
    db: AsyncSession, doctor_name: str, slot_iso: str, customer_name: str,
    customer_email: str, customer_phone: str, site_id,
) -> dict:
    from app.services.appointment import AppointmentService
    from app.core.exceptions import NotFoundError, BadRequestError
    service = AppointmentService(db)
    doctors = await service.list_doctors(site_id)
    match = next((d for d in doctors if d["name"].strip().lower() == doctor_name.strip().lower()), None)
    if not match:
        return {"success": False, "error": f"No doctor found named '{doctor_name}'."}

    try:
        result = await service.book_appointment(
            site_id=site_id,
            doctor_id=uuid.UUID(match["id"]),
            start_iso=slot_iso,
            customer_name=customer_name,
            customer_email=customer_email,
            customer_phone=customer_phone,
        )
        await db.commit()
        return {"success": True, **result}
    except (NotFoundError, BadRequestError) as e:
        await db.rollback()
        return {"success": False, "error": str(e)}


async def _run_tool(db: AsyncSession, call, site_id) -> dict:
    args = call.args or {}
    if call.name == 'search_products':
        return await _search_products(db, args.get('query', ''), site_id=site_id)
    elif call.name == 'check_doctor_availability':
        return await _check_doctor_availability(db, args.get('date', ''), site_id=site_id)
    elif call.name == 'book_doctor_appointment':
        return await _book_doctor_appointment(
            db,
            doctor_name=args.get('doctor_name', ''),
            slot_iso=args.get('slot_iso', ''),
            customer_name=args.get('customer_name', ''),
            customer_email=args.get('customer_email', ''),
            customer_phone=args.get('customer_phone', ''),
            site_id=site_id,
        )
    return {"error": f"Unknown tool: {call.name}"}


async def _call_gemini_with_tools(client: genai.Client, db: AsyncSession, contents: list[types.Content], site_id, site_name: str) -> str:
    config = types.GenerateContentConfig(
        system_instruction=build_system_instruction(site_name),
        tools=[SEARCH_PRODUCTS_TOOL],
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
    )

    # Loop through multiple rounds of tool calls -- a single customer message
    # can reasonably need more than one tool call in sequence (e.g. check
    # availability, then check a different date). A fixed cap avoids ever
    # looping forever if the model gets stuck calling tools repeatedly.
    MAX_TOOL_ROUNDS = 4
    working_contents = list(contents)

    for _ in range(MAX_TOOL_ROUNDS):
        response = client.models.generate_content(
            model='gemini-3.1-flash-lite',
            contents=working_contents,
            config=config,
        )

        if not response.function_calls:
            text = (response.text or '').strip()
            if text:
                return text
            # No tool call AND no text -- nothing more we can do with this
            # response; fall through to the generic apology below.
            break

        call = response.function_calls[0]
        tool_result = await _run_tool(db, call, site_id)

        working_contents.append(response.candidates[0].content)
        working_contents.append(
            types.Content(
                role='user',
                parts=[types.Part.from_function_response(name=call.name, response=tool_result)],
            )
        )

    # Either ran out of rounds, or got an empty response with no tool call --
    # give the customer something honest instead of a blank/broken reply.
    return "Sorry, I couldn't quite finish that. Could you rephrase your question?"


async def _call_openai_model(openai_api_key: str, message: str, site_name: str) -> str:
    client = AsyncOpenAI(api_key=openai_api_key)
    try:
        response = await client.chat.completions.create(
            model='gpt-3.5-turbo',
            messages=[
                {
                    'role': 'system',
                    'content': (
                        f"Your name is Ana, a friendly assistant for the "
                        f"{site_name} store. Answer only "
                        "questions about this store, its products, "
                        "pricing, and shipping. You only give information -- "
                        "you cannot take orders or complete a purchase; tell "
                        "customers to use the website's cart and checkout."
                    ),
                },
                {'role': 'user', 'content': message},
            ],
            temperature=0.7,
            max_tokens=200,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f'OpenAI error: {exc}')

    return (response.choices[0].message.content or '').strip()


@router.post("/query")
async def chatbot_query(
    data: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    site: Site = Depends(get_current_site),
):
    google_api_key = settings.GOOGLE_API_KEY
    openai_api_key = settings.OPENAI_API_KEY

    if google_api_key and not _is_placeholder_key(google_api_key):
        client = genai.Client(api_key=google_api_key)
        contents = _history_to_contents(data.history, data.message)

        try:
            reply = await _call_gemini_with_tools(client, db, contents, site_id=site.id, site_name=site.name)
            if reply:
                return success_response(data={"reply": reply}, message="Chatbot response.")
        except Exception as exc:
            last_error = str(exc)
            if openai_api_key and not _is_placeholder_key(openai_api_key):
                openai_reply = await _call_openai_model(openai_api_key, data.message, site_name=site.name)
                return success_response(data={"reply": openai_reply}, message="Chatbot response.")
            raise HTTPException(
                status_code=500,
                detail=(
                    'Gemini request failed. Make sure your Gemini API key is valid and the model is supported. '
                    f'{last_error}'
                ),
            )

    if openai_api_key and not _is_placeholder_key(openai_api_key):
        openai_reply = await _call_openai_model(openai_api_key, data.message, site_name=site.name)
        return success_response(data={"reply": openai_reply}, message="Chatbot response.")

    raise HTTPException(status_code=500, detail='Chatbot API key is not configured. Set GOOGLE_API_KEY or OPENAI_API_KEY.')