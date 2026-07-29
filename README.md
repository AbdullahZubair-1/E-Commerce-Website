# Chemisto Multi-Site E-Commerce Platform

Two independently branded storefronts — **Chemisto** (lab/chemistry supplies) and
**Chemisto Food** — running from one shared backend and one shared database, fully
isolated from each other while sharing the same infrastructure and codebase.

Each site has its own AI assistant ("Ana"), available as both a text chatbot and a
real-time voice agent, bilingual in English and Urdu, that can search the live
product catalog and book real doctor appointments through conversation.

---

## Features

- 🏪 **Two isolated storefronts**, one backend — every product, order, customer,
  and admin action is scoped per site at the API layer, not just the UI
- 🤖 **AI chatbot + voice agent ("Ana")** — Gemini-powered text chat and a
  Pipecat/Groq/Cartesia voice agent, both bilingual (English/Urdu, including
  Roman Urdu), both strictly grounded in the real product catalog
- 📅 **Real doctor appointment booking** — Ana checks live availability and books
  real appointments via the Cal.com API, in either text or voice
- 👥 **Friends & real-time messaging** — customers on the same site can friend each
  other and chat live over WebSocket
- 🔔 **Real-time admin order notifications** — a notification bell that updates
  instantly when an order comes in, backed by both WebSocket push and persisted
  history
- 👑 **Organization superadmin dashboard** — a single, site-independent login with
  combined stats across both stores plus a per-site breakdown
- 📧 **Automated customer emails** — welcome email, order confirmation, and
  appointment confirmation, via Make.com webhooks triggered directly from the
  backend
- 📊 **Google Sheets lead log** for appointment bookings, via the same Make.com
  automation
- ✅ **Automated test suites** — 23 backend tests (pytest) and 5 end-to-end tests
  (Playwright), both run against the real app

---

## Tech stack

| Layer | Technology |
|---|---|
| Backend | FastAPI (Python, async) + PostgreSQL + SQLAlchemy 2.0 + Alembic |
| Auth | JWT (python-jose) + bcrypt |
| Text AI | Google Gemini (`google-genai`), OpenAI fallback |
| Voice AI | Pipecat + Groq (Whisper STT, `openai/gpt-oss-120b` LLM) + Cartesia (TTS) |
| Appointment booking | Cal.com REST API v2 |
| Automation | Make.com (Gmail, Google Sheets) |
| Frontend | React 18 + TypeScript + Vite + Tailwind CSS |
| Testing | pytest + pytest-asyncio (backend), Playwright (frontend E2E) |

---

## Project structure
```
backend/         FastAPI app: routes, models, services, repositories, migrations, tests/
frontend/        Chemisto storefront (blue theme), voice agent talks to :7860
frontend-food/   Chemisto Food storefront (orange theme), voice agent talks to :7861
voice-agent/     Pipecat voice agent "Ana" -- run one instance per site
docker-compose.yml
```

---

## Before you start: add your API keys

Everything else is pre-configured, but you'll need to fill in your own keys —
copy `.env.example` to `.env` in `backend/` and `voice-agent/` if you haven't
already, then fill these in:

**`backend/.env`**
- `GOOGLE_API_KEY` — powers the text chatbot. Free at https://aistudio.google.com/apikey
- `CAL_API_KEY` — powers real doctor appointment booking. From your Cal.com account
  (Settings → Developer → API Keys). Without it, booking fails gracefully with a
  clear message instead of crashing.
- `CUSTOMER_EVENTS_WEBHOOK_URL` — optional, powers registration/order confirmation
  emails via Make.com
- `MAKE_WEBHOOK_URL` — optional, powers the appointment confirmation email +
  Google Sheets lead log via Make.com

**`voice-agent/.env`**
- `GROQ_API_KEY` — free at https://console.groq.com
- `CARTESIA_API_KEY` — from https://cartesia.ai

Everything else (database credentials, JWT secret, site slugs, ports) is
already set up.

---

## Admin logins (created automatically)

The backend creates each site's owner account, and one org-level superadmin
account, automatically the first time it starts — no manual setup needed:

- Chemisto owner: `owner@chemisto.com` / `ChemistoOwner2024!`
- Chemisto Food owner: `owner@chemistofood.com` / `ChemistoFoodOwner2024!`
- Organization superadmin: `superadmin@chemisto.org` / `SuperAdmin2024!`
  — open `http://localhost:5173/superadmin` (works from either frontend) for
  combined stats across both stores, plus per-site breakdowns.

**Change all of these in `backend/.env` before any real/public deployment.**

---

## Run everything with Docker (recommended)

From the project root, after adding your API keys above:

```bash
docker compose up --build
```

Then run the database migration once (first time only):

```bash
docker compose exec backend alembic upgrade head
```

- Chemisto site: http://localhost:5173
- Chemisto Food site: http://localhost:5174
- Backend / API docs: http://localhost:8000/docs
- Chemisto voice agent: http://localhost:7860
- Chemisto Food voice agent: http://localhost:7861

---

## Run without Docker (five terminals + a Postgres instance)

```powershell
# Terminal 1 -- backend
cd backend
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
alembic upgrade head          # first time only
uvicorn app.main:app --reload

# Terminal 2 -- voice agent for Chemisto
cd voice-agent
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:SITE_SLUG = "chemisto"
python bot.py --host 0.0.0.0 --port 7860 -t webrtc

# Terminal 3 -- voice agent for Chemisto Food (same code, different site/port)
cd voice-agent
venv\Scripts\Activate.ps1
$env:SITE_SLUG = "chemisto-food"
python bot.py --host 0.0.0.0 --port 7861 -t webrtc

# Terminal 4 -- Chemisto frontend
cd frontend
npm install
npm run dev                   # http://localhost:5173

# Terminal 5 -- Chemisto Food frontend
cd frontend-food
npm install
npm run dev                   # http://localhost:5174
```

---

## Doctor appointment booking (Cal.com)

Ana can book real doctor appointments, in both text chat and voice, and the
admin panel has an **Appointments** page to manage it:

- **Doctors tab**: add a doctor (name, specialty, and their Cal.com "event
  type" ID — create that event type on your own Cal.com account first,
  using the classic **Event Types** page, not the newer "Events" product —
  then paste its ID here), and toggle doctors active/inactive.
- **Bookings tab**: every appointment customers have booked through Ana,
  with their name, email, and phone.

Cal.com's `/slots` and `/bookings` endpoints each require a **different**
`cal-api-version` header value — already handled correctly in
`backend/app/core/calcom_client.py`, but worth knowing if you ever touch that
file.

---

## Automated customer emails (Make.com)

Three emails, driven by two Make.com scenarios:

1. **Appointment confirmation** — shares the same scenario as the Google
   Sheets lead log (`MAKE_WEBHOOK_URL`): Webhook → Google Sheets "Add a Row"
   → Gmail "Send an Email".
2. **Registration + order confirmation** — share one scenario
   (`CUSTOMER_EVENTS_WEBHOOK_URL`), using a **Router** module that branches
   on an `event_type` field (`"registration"` or `"order"`) in the webhook
   payload, so both events work from a single scenario — useful if you're on
   Make's free tier, which limits how many scenarios can be active at once.

Both are optional — if the relevant env var isn't set, that email is silently
skipped and never blocks the actual registration/order/booking.

---

## Real-time chat notifications (WhatsApp, Telegram) — not implemented

Both were evaluated and deliberately not built:

- **WhatsApp** requires a Meta/Facebook developer account and, for messaging
  real customers, full Business Verification plus paid per-message usage
  beyond a very limited (5-recipient) free test tier.
- **Telegram** requires the customer to message the bot first before it can
  ever message them back — extra friction judged not worth it given lower
  Telegram adoption among this platform's expected customers.

Email confirmations (above) remain the platform's working automated customer
communication channel.

---

## Bilingual support (English / Urdu)

Both Ana's text chat and voice agent detect whether the customer is
writing/speaking in English or Urdu (including **Roman Urdu** — Urdu written
in English letters, e.g. "ap kya bech rahe hain") and reply in kind. The
voice agent is explicitly restricted to only these two languages, even if
unclear audio gets transcribed into something resembling a third language.

**One honest caveat:** Cartesia (the voice agent's text-to-speech provider)
does not officially list Urdu as a supported language — Hindi is supported,
Urdu isn't confirmed either way. The code is wired up correctly; actual
audio output quality for Urdu hasn't been independently verified. The text
chatbot's Urdu support has no such caveat — Gemini writes fluent, correct
Urdu.

---

## Friends & real-time messaging

Logged-in customers can find and friend other customers *on the same site*
(Chemisto and Chemisto Food have completely separate friend networks) and
chat in real time over WebSocket — click "Messages" in the navbar.

## Admin order notifications

Owners get a bell icon in the admin panel that lights up in real time the
moment a customer places an order — also persisted to the database, so the
unread count survives a page reload.

---

## How the two sites stay separate

- Every request from a frontend carries an `X-Site-Slug` header (`chemisto`
  or `chemisto-food`), set via each frontend's `VITE_SITE_SLUG` env var.
- The backend filters every product, category, brand, order, dashboard stat,
  registration, login, appointment, and chatbot answer by that site
  automatically — enforced at the API layer.
- The same email can register separately on each site — accounts are fully
  independent per site.
- Each site's voice agent is a separate running instance (own port, own
  `SITE_SLUG`), so it only ever searches and talks about that site's own
  products.

**A note on testing this**: don't test by typing an API URL directly into
your browser's address bar — that's a plain page navigation and doesn't
carry the `X-Site-Slug` header, so it'll always default to Chemisto's data.
Use the real site through its UI, or check the automated test suite below,
which verifies this boundary directly.

---

## Running the test suites

**Backend (pytest)** — 23 tests against the real app and a real (isolated)
database. No separate database setup needed; the suite runs inside its own
dedicated schema inside your existing database and cleans up after itself.

```bash
cd backend
pip install -r requirements.txt
pytest tests/ -v
```

**Frontend (Playwright)** — 5 end-to-end tests driving a real Chromium
browser. Requires the backend and the Chemisto frontend (`localhost:5173`)
to already be running.

```bash
cd frontend
npm install
npx playwright install chromium
npm run test:e2e
```

---

## Making more changes to Chemisto Food later

`frontend-food/` is a full copy of `frontend/`, already re-themed (orange,
food copy) and re-branded. If you add new pages/features to `frontend/`,
you'll need to copy those specific changes into `frontend-food/` too, since
they're separate codebases from this point on.

---

## Notes

- **Do not commit `.env` files** (they contain real secrets) to a public
  GitHub repo — make sure `.gitignore` covers `backend/.env`,
  `voice-agent/.env`, and both frontends' `.env` if present.
- Chat, admin-notification, and voice presence tracking are held in memory
  within a single backend process — fine for this deployment, but would need
  a shared store (e.g. Redis) if scaled to multiple backend processes.
- See `voice-agent/INTEGRATION.md` for details on how the voice widget is
  wired into the chat UI.

## License

Add your license here.