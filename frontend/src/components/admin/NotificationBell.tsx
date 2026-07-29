import { useEffect, useRef, useState, useCallback } from 'react';
import { BellIcon, ShoppingBagIcon } from '@heroicons/react/24/outline';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { notificationService, type AdminNotification } from '@/services/notification.service';
import { useAdminNotificationSocket } from '@/hooks/useAdminNotificationSocket';
import { getErrorMessage } from '@/services/api';

function timeAgo(iso: string): string {
  const seconds = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
  if (seconds < 60) return 'just now';
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

export function NotificationBell() {
  const [open, setOpen] = useState(false);
  const [notifications, setNotifications] = useState<AdminNotification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const navigate = useNavigate();

  const refresh = useCallback(async () => {
    try {
      const [list, count] = await Promise.all([
        notificationService.list(),
        notificationService.unreadCount(),
      ]);
      setNotifications(list);
      setUnreadCount(count);
    } catch (error) {
      toast.error(getErrorMessage(error));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const handleIncoming = useCallback((notification: AdminNotification) => {
    setNotifications((current) => [notification, ...current]);
    setUnreadCount((current) => current + 1);
  }, []);

  useAdminNotificationSocket({ onNotification: handleIncoming });

  // Close dropdown on outside click.
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const handleOpen = () => {
    setOpen((v) => !v);
  };

  const handleNotificationClick = async (n: AdminNotification) => {
    if (!n.is_read) {
      try {
        await notificationService.markRead(n.id);
        setNotifications((current) => current.map((c) => (c.id === n.id ? { ...c, is_read: true } : c)));
        setUnreadCount((current) => Math.max(0, current - 1));
      } catch {
        // non-fatal
      }
    }
    setOpen(false);
    if (n.order_id) navigate('/admin/orders');
  };

  const handleMarkAllRead = async () => {
    try {
      await notificationService.markAllRead();
      setNotifications((current) => current.map((c) => ({ ...c, is_read: true })));
      setUnreadCount(0);
    } catch (error) {
      toast.error(getErrorMessage(error));
    }
  };

  return (
    <div className="relative" ref={containerRef}>
      <button
        type="button"
        onClick={handleOpen}
        className="relative p-2 rounded-lg text-gray-500 hover:bg-gray-100 hover:text-gray-700 transition-colors"
        aria-label={`Notifications${unreadCount > 0 ? `, ${unreadCount} unread` : ''}`}
      >
        <BellIcon className="h-6 w-6" />
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 bg-red-500 text-white text-[10px] rounded-full h-5 w-5 flex items-center justify-center font-medium">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 mt-2 w-80 max-h-96 overflow-y-auto bg-white rounded-2xl shadow-xl border border-gray-200 z-50">
          <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100">
            <p className="text-sm font-semibold text-gray-900">Notifications</p>
            {unreadCount > 0 && (
              <button
                type="button"
                onClick={handleMarkAllRead}
                className="text-xs text-blue-600 hover:text-blue-700"
              >
                Mark all read
              </button>
            )}
          </div>

          {loading && <p className="text-sm text-gray-400 text-center py-6">Loading…</p>}
          {!loading && notifications.length === 0 && (
            <p className="text-sm text-gray-400 text-center py-6 px-4">No notifications yet.</p>
          )}

          {notifications.map((n) => (
            <button
              key={n.id}
              type="button"
              onClick={() => handleNotificationClick(n)}
              className={`w-full text-left flex gap-3 px-4 py-3 border-b border-gray-50 hover:bg-gray-50 transition-colors ${!n.is_read ? 'bg-blue-50/50' : ''}`}
            >
              <div className="mt-0.5 shrink-0">
                <div className="h-8 w-8 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center">
                  <ShoppingBagIcon className="h-4 w-4" />
                </div>
              </div>
              <div className="min-w-0 flex-1">
                <p className={`text-sm ${!n.is_read ? 'font-semibold text-gray-900' : 'text-gray-700'}`}>{n.title}</p>
                <p className="text-xs text-gray-500 mt-0.5 line-clamp-2">{n.message}</p>
                <p className="text-[11px] text-gray-400 mt-1">{timeAgo(n.created_at)}</p>
              </div>
              {!n.is_read && <span className="h-2 w-2 rounded-full bg-blue-600 mt-1.5 shrink-0" />}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}