import api from './api';
import type { APIResponse, Order, OrderSummary, PaginatedData, OrderStatus } from '@/types';

export const orderService = {
  async placeOrder(shipping_address: string, notes?: string): Promise<Order> {
    const res = await api.post<APIResponse<Order>>('/orders/', { shipping_address, notes });
    return res.data.data!;
  },

  async getMyOrders(page = 1, page_size = 10): Promise<PaginatedData<OrderSummary>> {
    const res = await api.get<APIResponse<PaginatedData<OrderSummary>>>(
      `/orders/my?page=${page}&page_size=${page_size}`
    );
    return res.data.data!;
  },

  async getMyOrder(order_id: string): Promise<Order> {
    const res = await api.get<APIResponse<Order>>(`/orders/my/${order_id}`);
    return res.data.data!;
  },

  // Admin
  async getAllOrders(page = 1, page_size = 20, status?: OrderStatus): Promise<PaginatedData<OrderSummary>> {
    const params = new URLSearchParams({ page: String(page), page_size: String(page_size) });
    if (status) params.set('status', status);
    const res = await api.get<APIResponse<PaginatedData<OrderSummary>>>(`/orders/admin/all?${params}`);
    return res.data.data!;
  },

  async getOrderById(order_id: string): Promise<Order> {
    const res = await api.get<APIResponse<Order>>(`/orders/admin/${order_id}`);
    return res.data.data!;
  },

  async updateOrderStatus(order_id: string, status: OrderStatus): Promise<Order> {
    const res = await api.patch<APIResponse<Order>>(`/orders/admin/${order_id}/status`, { status });
    return res.data.data!;
  },
};
