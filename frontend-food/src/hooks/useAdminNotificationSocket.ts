import { useEffect, useRef, useCallback } from 'react';
import type { AdminNotification } from '@/services/notification.service';

const O_TOKEN = 'o_token';

interface UseAdminNotificationSocketOptions {
  onNotification: (notification: AdminNotification) => void;
}

/** Real-time push for new orders while the admin panel is open. Uses the
 * owner's own session token ('o_token'), separate from the customer/
 * superadmin sessions. */
export function useAdminNotificationSocket({ onNotification }: UseAdminNotificationSocketOptions) {
  const wsRef = useRef<WebSocket | null>(null);
  const onNotificationRef = useRef(onNotification);
  onNotificationRef.current = onNotification;
  const reconnectAttempt = useRef(0);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const closedByUs = useRef(false);

  const connect = useCallback(() => {
    const token = sessionStorage.getItem(O_TOKEN);
    if (!token) return;

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const url = `${protocol}//${window.location.host}/api/v1/admin/notifications/ws?token=${encodeURIComponent(token)}`;
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      reconnectAttempt.current = 0;
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'notification') {
          onNotificationRef.current(data.notification as AdminNotification);
        }
      } catch {
        // ignore malformed frames
      }
    };

    ws.onclose = () => {
      wsRef.current = null;
      if (closedByUs.current) return;
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
}