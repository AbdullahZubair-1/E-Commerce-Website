FROM python:3.12-slim

WORKDIR /app

# System deps needed by pipecat's audio stack (silero VAD via torch/torchaudio,
# webrtc audio codecs via av/pyav, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 7860

# --host 0.0.0.0 so the container's port is reachable from outside the container
CMD ["python", "bot.py", "--host", "0.0.0.0", "--port", "7860", "-t", "webrtc"]
