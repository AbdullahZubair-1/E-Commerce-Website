import axios, { AxiosError } from 'axios';
import type { APIResponse } from '@/types';

// Identifies which storefront this deployment belongs to. Set once per
// deployment via VITE_SITE_SLUG (e.g. "chemisto" or "chemisto-food") --
// see .env.example. Falls back to "chemisto" if not set, so local dev
// keeps working without any extra setup.
export const SITE_SLUG = import.meta.env.VITE_SITE_SLUG || 'chemisto';

const api = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
    'X-Site-Slug': SITE_SLUG,
  },
  timeout: 15000,
});

// Attach JWT token to every request
api.interceptors.request.use((config) => {
  // Prefer the shared active token, but fall back to the owner session token
  // when on admin pages. This ensures admin XHRs include Authorization
  // even if the owner session hasn't been mirrored to localStorage yet.
  let token = localStorage.getItem('access_token');
  try {
    if (!token && typeof window !== 'undefined' && window.location.pathname.startsWith('/admin')) {
      // If an owner session exists in sessionStorage, use it for admin requests.
      token = sessionStorage.getItem('o_token') ?? token;
      if (token) {
        localStorage.setItem('access_token', token);
      }
    }
  } catch (err) {
    // Ignore storage errors (e.g., SSR or privacy settings)
  }

  if (token) {
    // Normalize token: strip any "Bearer " prefix that might have been
    // stored accidentally so we don't produce "Bearer Bearer <token>".
    const raw = token.startsWith('Bearer ') ? token.slice(7) : token;
    config.headers.Authorization = `Bearer ${raw}`;
  }
  return config;
});

// Handle 401 – auto-logout
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
      // Only redirect if not already on auth pages
      if (!window.location.pathname.startsWith('/login') &&
          !window.location.pathname.startsWith('/register') &&
          !window.location.pathname.startsWith('/admin') &&
          !window.location.pathname.startsWith('/superadmin')) {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export function getErrorMessage(error: unknown): string {
  if (error instanceof AxiosError) {
    const data = error.response?.data as APIResponse | undefined;
    if (data?.message) return data.message;
    if (error.message) return error.message;
  }
  return 'An unexpected error occurred.';
}

export default api;
