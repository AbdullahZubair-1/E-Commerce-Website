import { useEffect, useRef, useState, useCallback } from 'react';
import { createPortal } from 'react-dom';
import {
  PaperAirplaneIcon,
  ChatBubbleLeftRightIcon,
  MicrophoneIcon,
  PhoneXMarkIcon,
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';
import { PipecatClient, AggregationType } from '@pipecat-ai/client-js';
import { SmallWebRTCTransport } from '@pipecat-ai/small-webrtc-transport';
import { chatbotService } from '@/services/chatbot.service';
import { getErrorMessage } from '@/services/api';
import type { ChatbotMessage } from '@/types';

const DEFAULT_MESSAGES: ChatbotMessage[] = [
  { role: 'assistant', text: "Hi, I'm Ana! I can help you find products, answer order questions, and guide you through checkout." },
];

// Proxied by Vite (see vite.config.ts) to the Pipecat voice-agent service,
// so the browser never needs to know its real host/port.
const VOICE_OFFER_URL = '/voice/api/offer';

type CallState = 'idle' | 'connecting' | 'live';

export function ChatbotWidget() {
  const [open, setOpen] = useState(false);
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<ChatbotMessage[]>(DEFAULT_MESSAGES);
  const [loading, setLoading] = useState(false);
  const [callState, setCallState] = useState<CallState>('idle');
  const [botSpeaking, setBotSpeaking] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const clientRef = useRef<PipecatClient | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, open, callState]);

  // Make sure a live call is torn down if the widget ever unmounts.
  useEffect(() => {
    return () => {
      clientRef.current?.disconnect().catch(() => {});
    };
  }, []);

  const sendMessage = async () => {
    const trimmed = input.trim();
    if (!trimmed) return;

    const nextMessages: ChatbotMessage[] = [...messages, { role: 'user', text: trimmed }];
    setMessages(nextMessages);
    setInput('');
    setLoading(true);

    try {
      const response = await chatbotService.ask(trimmed, nextMessages);
      setMessages((current) => [...current, { role: 'assistant', text: response.reply }]);
    } catch (error) {
      const message = getErrorMessage(error);
      toast.error(message);
      setMessages((current) => [...current, { role: 'assistant', text: message || 'Sorry, I could not answer that right now. Try again later.' }]);
    } finally {
      setLoading(false);
    }
  };

  // Lazily build the Pipecat voice client once, then reuse it for the life
  // of this widget instance.
  const getVoiceClient = useCallback(() => {
    if (clientRef.current) return clientRef.current;

    const client = new PipecatClient({
      transport: new SmallWebRTCTransport(),
      enableMic: true,
      enableCam: false,
      callbacks: {
        onBotReady: () => setCallState('live'),
        onDisconnected: () => {
          setCallState('idle');
          setBotSpeaking(false);
        },
        onBotStartedSpeaking: () => setBotSpeaking(true),
        onBotStoppedSpeaking: () => setBotSpeaking(false),
        // The raw client-js SDK (unlike @pipecat-ai/client-react's
        // <PipecatClientAudio>) does NOT auto-play the bot's incoming audio
        // track — we have to attach it to an <audio> element ourselves.
        onTrackStarted: (track, participant) => {
          if (participant?.local || track.kind !== 'audio') return;
          if (!audioRef.current) {
            audioRef.current = document.createElement('audio');
            audioRef.current.autoplay = true;
            document.body.appendChild(audioRef.current);
          }
          audioRef.current.srcObject = new MediaStream([track]);
        },
        onUserTranscript: (data) => {
          if (data.final && data.text.trim()) {
            setMessages((current) => [...current, { role: 'user', text: data.text }]);
          }
        },
        // onBotOutput fires at both "word" granularity (for TTS sync) and
        // "sentence" granularity (the complete aggregated line) — only take
        // the sentence-level events, or every word becomes its own bubble.
        onBotOutput: (data) => {
          if (data.aggregated_by === AggregationType.SENTENCE && data.text.trim()) {
            setMessages((current) => [...current, { role: 'assistant', text: data.text }]);
          }
        },
        onError: (error) => {
          const message =
            typeof error === 'string' ? error : (error as { message?: string })?.message;
          toast.error(message || 'Voice connection error.');
        },
      },
    });

    clientRef.current = client;
    return client;
  }, []);

  const startCall = async () => {
    setCallState('connecting');
    try {
      const client = getVoiceClient();
      // webrtcRequestParams is the real, current connect API for
      // SmallWebRTCTransport (the plain "connectionUrl" shorthand is
      // deprecated). requestData rides along with the offer request and
      // lets one shared voice-agent process know which storefront this call
      // is for, so it only ever talks about that site's own products.
      await client.connect({
        webrtcRequestParams: {
          endpoint: VOICE_OFFER_URL,
        },
      });
    } catch (error) {
      setCallState('idle');
      const message = error instanceof Error ? error.message : undefined;
      toast.error(message || 'Could not start the voice call. Is the voice agent running?');
    }
  };

  const endCall = async () => {
    try {
      await clientRef.current?.disconnect();
    } finally {
      setCallState('idle');
      setBotSpeaking(false);
      if (audioRef.current) {
        audioRef.current.srcObject = null;
        audioRef.current.remove();
        audioRef.current = null;
      }
    }
  };

  const toggleMic = () => {
    if (callState === 'idle') {
      startCall();
    } else {
      endCall();
    }
  };

  const statusLabel =
    callState === 'connecting' ? 'Connecting…' : callState === 'live' ? (botSpeaking ? 'Ana is speaking…' : 'Listening…') : null;

  const widget = (
    <div className="fixed bottom-4 right-4 z-[9999] flex flex-col items-end pointer-events-auto">
      {open && (
        <div className="w-[340px] max-w-full bg-white border border-slate-200 shadow-xl rounded-3xl overflow-hidden mb-3">
          <div className="bg-slate-900 text-white px-4 py-3 flex items-center justify-between gap-4">
            <div>
              <p className="text-sm font-semibold">Ana · CHEMISTO Assistant</p>
              <p className="text-xs text-slate-300">
                {statusLabel ?? 'Ask about products, orders, or shipping.'}
              </p>
            </div>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={toggleMic}
                aria-label={callState === 'idle' ? 'Start voice call' : 'End voice call'}
                className={`rounded-full p-2 transition-colors ${
                  callState === 'idle'
                    ? 'bg-slate-800 hover:bg-slate-700'
                    : 'bg-red-600 hover:bg-red-500'
                }`}
              >
                {callState === 'idle' ? (
                  <MicrophoneIcon className="h-4 w-4" />
                ) : (
                  <PhoneXMarkIcon className="h-4 w-4" />
                )}
              </button>
              <button
                type="button"
                onClick={() => setOpen(false)}
                className="rounded-full bg-slate-800 p-2 hover:bg-slate-700 transition-colors"
                aria-label="Close chatbot"
              >
                ×
              </button>
            </div>
          </div>
          <div className="h-80 overflow-y-auto p-4 space-y-4 bg-slate-50">
            {messages.map((message, index) => (
              <div
                key={`${message.role}-${index}`}
                className={`flex ${message.role === 'assistant' ? 'justify-start' : 'justify-end'}`}
              >
                <div
                  className={`rounded-2xl px-4 py-3 max-w-[80%] text-sm leading-6 ${
                    message.role === 'assistant'
                      ? 'bg-white text-slate-900 shadow-sm'
                      : 'bg-blue-600 text-white'
                  }`}
                >
                  {message.text}
                </div>
              </div>
            ))}
            {callState !== 'idle' && (
              <div className="flex justify-center">
                <div className="flex items-center gap-2 rounded-full bg-slate-200 px-3 py-1 text-xs text-slate-600">
                  <span
                    className={`h-2 w-2 rounded-full ${
                      callState === 'connecting'
                        ? 'bg-amber-400 animate-pulse'
                        : botSpeaking
                          ? 'bg-blue-500 animate-pulse'
                          : 'bg-green-500 animate-pulse'
                    }`}
                  />
                  {statusLabel}
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
          <div className="p-4 border-t border-slate-200">
            {callState === 'idle' ? (
              <div className="flex gap-2">
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      sendMessage();
                    }
                  }}
                  placeholder="Ask me anything..."
                  className="flex-1 rounded-2xl border border-slate-300 px-4 py-3 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                />
                <button
                  type="button"
                  onClick={sendMessage}
                  disabled={loading}
                  className="inline-flex items-center justify-center rounded-2xl bg-blue-600 px-4 py-3 text-white text-sm font-medium hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-slate-300"
                >
                  {loading ? 'Sending...' : <PaperAirplaneIcon className="h-4 w-4" />}
                </button>
              </div>
            ) : (
              <button
                type="button"
                onClick={endCall}
                className="w-full inline-flex items-center justify-center gap-2 rounded-2xl bg-red-600 px-4 py-3 text-white text-sm font-medium hover:bg-red-500"
              >
                <PhoneXMarkIcon className="h-4 w-4" />
                End voice call
              </button>
            )}
          </div>
        </div>
      )}
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        className="inline-flex items-center gap-2 rounded-full bg-blue-600 px-4 py-3 text-white shadow-lg shadow-blue-500/20 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-200"
      >
        <ChatBubbleLeftRightIcon className="h-5 w-5" />
        Chat
      </button>
    </div>
  );

  return createPortal(widget, document.body);
}
