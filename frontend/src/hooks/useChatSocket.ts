import { useEffect, useRef, useCallback, useState } from 'react';
import type { ChatMessage } from '@/services/social.service';

const C_TOKEN = 'c_token';

type IncomingEvent =
  | { type: 'message'; message: ChatMessage }
  | { type: 'typing'; from_user_id: string }
  | { type: 'read'; reader_id: string }
  | { type: 'error'; detail: string };

interface UseChatSocketOptions {
  onMessage: (message: ChatMessage) => void;
  onTyping?: (fromUserId: string) => void;
  onRead?: (readerId: string) => void;
}

/**
 * Opens one WebSocket connection for the whole Messages page (not per
 * conversation) and keeps it alive while the page is mounted. Reconnects
 * automatically with backoff if the connection drops.
 */
export function useChatSocket({ onMessage, onTyping, onRead }: UseChatSocketOptions) {
  const wsRef = useRef<WebSocket | null>(null);
  const onMessageRef = useRef(onMessage);
  onMessageRef.current = onMessage;
  const onTypingRef = useRef(onTyping);
  onTypingRef.current = onTyping;
  const onReadRef = useRef(onRead);
  onReadRef.current = onRead;
  const [connected, setConnected] = useState(false);
  const reconnectAttempt = useRef(0);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const closedByUs = useRef(false);

  const connect = useCallback(() => {
    const token = localStorage.getItem(C_TOKEN);
    if (!token) return;

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const url = `${protocol}//${window.location.host}/api/v1/social/ws/chat?token=${encodeURIComponent(token)}`;
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnected(true);
      reconnectAttempt.current = 0;
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as IncomingEvent;
        if (data.type === 'message') {
          onMessageRef.current(data.message);
        } else if (data.type === 'typing') {
          onTypingRef.current?.(data.from_user_id);
        } else if (data.type === 'read') {
          onReadRef.current?.(data.reader_id);
        }
      } catch {
        // ignore malformed frames
      }
    };

    ws.onclose = () => {
      setConnected(false);
      wsRef.current = null;
      if (closedByUs.current) return;
      // Reconnect with simple capped backoff.
      const delay = Math.min(1000 * 2 ** reconnectAttempt.current, 10000);
      reconnectAttempt.current += 1;
      reconnectTimer.current = setTimeout(connect, delay);
    };

    ws.onerror = () => {
      ws.close();
    };
  }, []);

  useEffect(() => {
    closedByUs.current = false;
    connect();
    return () => {
      closedByUs.current = true;
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
      wsRef.current?.close();
    };
  }, [connect]);

  const sendMessage = useCallback((recipientId: string, content: string) => {
    const ws = wsRef.current;
    if (!ws || ws.readyState !== WebSocket.OPEN) return false;
    ws.send(JSON.stringify({ type: 'message', recipient_id: recipientId, content }));
    return true;
  }, []);

  const sendTyping = useCallback((recipientId: string) => {
    const ws = wsRef.current;
    if (!ws || ws.readyState !== WebSocket.OPEN) return;
    ws.send(JSON.stringify({ type: 'typing', recipient_id: recipientId }));
  }, []);

  return { connected, sendMessage, sendTyping };
}