import api from './api';
import type { APIResponse } from '@/types';

export interface AdminNotification {
  id: string;
  type: string;
  title: string;
  message: string;
  order_id: string | null;
  is_read: boolean;
  created_at: string;
}

export const notificationService = {
  async list(): Promise<AdminNotification[]> {
    const res = await api.get<APIResponse<AdminNotification[]>>('/admin/notifications/');
    return res.data.data!;
  },

  async unreadCount(): Promise<number> {
    const res = await api.get<APIResponse<{ count: number }>>('/admin/notifications/unread-count');
    return res.data.data!.count;
  },

  async markRead(id: string): Promise<void> {
    await api.patch(`/admin/notifications/${id}/read`);
  },

  async markAllRead(): Promise<void> {
    await api.patch('/admin/notifications/read-all');
  },
};