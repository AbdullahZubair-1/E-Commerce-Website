import api from './api';
import type { APIResponse, User, DashboardStats } from '@/types';

export const userService = {
  async getProfile(): Promise<User> {
    const res = await api.get<APIResponse<User>>('/profile/me');
    return res.data.data!;
  },

  async updateProfile(first_name: string, last_name: string): Promise<User> {
    const res = await api.put<APIResponse<User>>('/profile/me', { first_name, last_name });
    return res.data.data!;
  },

  async changePassword(current_password: string, new_password: string): Promise<void> {
    await api.put('/profile/me/password', { current_password, new_password });
  },

  async getDashboardStats(): Promise<DashboardStats> {
    const res = await api.get<APIResponse<DashboardStats>>('/admin/dashboard');
    return res.data.data!;
  },
};
