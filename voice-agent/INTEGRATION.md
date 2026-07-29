# How the voice agent is wired into the site

This agent (`bot.py`) is unchanged from your original project — same Groq STT/LLM,
same Cartesia TTS, same "Ana" personality and tools. It still runs as its own
process, using Pipecat's built-in dev server (`pipecat.runner.run.main()`),
which exposes a WebRTC signaling endpoint at:

```
POST /api/offer
```

on port 7860, with permissive CORS already enabled by Pipecat itself — no
changes were needed on the Python side.

## Frontend side

`frontend/src/components/ui/ChatbotWidget.tsx` now does two things:

1. **Text mode (unchanged):** typing a message still calls
   `chatbotService.ask()` → `POST /chatbot/query` on your FastAPI backend,
   exactly as before.
2. **Voice mode (new):** the mic button in the widget header creates a
   `PipecatClient` (from `@pipecat-ai/client-js`) using
   `SmallWebRTCTransport` (from `@pipecat-ai/small-webrtc-transport`), and
   connects it to:

   ```
   VOICE_OFFER_URL = '/voice/api/offer'
   ```

   `/voice` is proxied by Vite (see `frontend/vite.config.ts`) straight to
   `http://localhost:7860`, the same way `/api` is proxied to your FastAPI
   backend on port 8000. This means the browser never needs to know the
   agent's real host — same pattern your project already used.

   Live callbacks (`onUserTranscript`, `onBotOutput`, `onBotStartedSpeaking`,
   etc.) push each finished sentence into the widget's existing `messages`
   state, so spoken turns appear as chat bubbles in the same list as typed
   ones. Ending the call (red phone icon) calls `client.disconnect()` and
   drops back into normal typing mode.

## Running it

- **Locally without Docker:** run the FastAPI backend, the Vite dev server,
  and `python bot.py --host 0.0.0.0 --port 7860 -t webrtc` (inside
  `voice-agent/`, with its own venv and `.env`) as three separate processes.
  The Vite proxy targets `localhost`, so this "just works" if all three run
  on the same machine.
- **With Docker Compose:** `docker compose up --build` starts all four
  services (`db`, `backend`, `voice-agent`, `frontend`). Note: like the
  existing `backend` proxy target, the Vite dev server proxy currently
  points at `localhost:7860`/`localhost:8000`. Inside Docker's network,
  containers reach each other by service name (e.g. `voice-agent`, not
  `localhost`), so if you hit connection errors when everything's
  containerized, update the proxy targets in `frontend/vite.config.ts` to
  `http://voice-agent:7860` and `http://backend:8000`. This is a pre-existing
  characteristic of how the project's dev-server proxy was set up (it wasn't
  introduced by this integration) — it only matters if you run everything
  inside containers rather than on your host machine.

## Requirements & browser permissions

- The voice call needs microphone access — the browser will prompt for it
  the first time you tap the mic button.
- WebRTC needs UDP connectivity between the browser and the agent; a
  restrictive corporate firewall or VPN can block this locally.
- First connection can take ~20-30 seconds the very first time the agent
  starts, while Pipecat downloads the Silero VAD model (same as before).
