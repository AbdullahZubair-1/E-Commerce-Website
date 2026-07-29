import api from './api';
import type { APIResponse, Cart } from '@/types';

export const cartService = {
  async getCart(): Promise<Cart> {
    const res = await api.get<APIResponse<Cart>>('/cart/');
    return res.data.data!;
  },

  async addItem(product_id: string, quantity: number = 1): Promise<Cart> {
    const res = await api.post<APIResponse<Cart>>('/cart/items', { product_id, quantity });
    return res.data.data!;
  },

  async updateItem(item_id: string, quantity: number): Promise<Cart> {
    const res = await api.put<APIResponse<Cart>>(`/cart/items/${item_id}`, { quantity });
    return res.data.data!;
  },

  async removeItem(item_id: string): Promise<Cart> {
    const res = await api.delete<APIResponse<Cart>>(`/cart/items/${item_id}`);
    return res.data.data!;
  },

  async clearCart(): Promise<Cart> {
    const res = await api.delete<APIResponse<Cart>>('/cart/');
    return res.data.data!;
  },
};
