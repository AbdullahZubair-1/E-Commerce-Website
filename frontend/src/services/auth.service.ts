import api from './api';
import type { APIResponse, TokenResponse, LoginPayload, RegisterPayload } from '@/types';

export const authService = {
  async register(payload: RegisterPayload): Promise<TokenResponse> {
    const res = await api.post<APIResponse<TokenResponse>>('/auth/register', payload);
    return res.data.data!;
  },

  async login(payload: LoginPayload): Promise<TokenResponse> {
    const res = await api.post<APIResponse<TokenResponse>>('/auth/login', payload);
    return res.data.data!;
  },
};
