import api from './api';
import type { APIResponse, Category } from '@/types';

export const categoryService = {
  async getCategories(): Promise<Category[]> {
    const res = await api.get<APIResponse<Category[]>>('/categories/');
    return res.data.data!;
  },

  async getCategory(id: string): Promise<Category> {
    const res = await api.get<APIResponse<Category>>(`/categories/${id}`);
    return res.data.data!;
  },

  async createCategory(name: string, description?: string): Promise<Category> {
    const res = await api.post<APIResponse<Category>>('/categories/', { name, description });
    return res.data.data!;
  },

  async updateCategory(id: string, name: string, description?: string): Promise<Category> {
    const res = await api.put<APIResponse<Category>>(`/categories/${id}`, { name, description });
    return res.data.data!;
  },

  async deleteCategory(id: string): Promise<void> {
    await api.delete(`/categories/${id}`);
  },
};
