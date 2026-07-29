# Pipecat Voice Agent

A simple voice AI agent using Pipecat, with a built-in browser client for local testing —
no separate frontend project needed.

Stack:
- STT + LLM: Groq (free)
- TTS: ElevenLabs (free tier)
- Transport: local WebRTC (built into Pipecat's dev runner)

## Setup (Windows / PowerShell)

```powershell
cd pipecat-voice-agent

# create virtual environment
python -m venv venv
venv\Scripts\Activate.ps1

# install dependencies
pip install -r requirements.txt

# set up your keys
Copy-Item .env.example .env
notepad .env
```

Fill in `.env` with your Groq and ElevenLabs keys, then save.

## Run it

```powershell
python bot.py
```

Open **http://localhost:7860** in your browser, click Connect, allow the
microphone, and start talking.

> First run note: the first start can take ~20-30 seconds while Pipecat
> downloads the VAD model and initializes.

## Customize

- **Personality / behavior**: edit `SYSTEM_INSTRUCTION` in `bot.py`
- **Voice**: change `ELEVENLABS_VOICE_ID` in `.env` (browse voices at
  elevenlabs.io/app/voice-library)
- **Add tools/functions**: Pipecat supports function calling via
  `FunctionSchema`/`ToolsSchema` — ask if you want this added
