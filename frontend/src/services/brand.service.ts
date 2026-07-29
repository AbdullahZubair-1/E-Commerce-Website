import api from './api';
import type { APIResponse, Brand } from '@/types';

export const brandService = {
  async getBrands(): Promise<Brand[]> {
    const res = await api.get<APIResponse<Brand[]>>('/brands/');
    return res.data.data!;
  },

  async getBrand(id: string): Promise<Brand> {
    const res = await api.get<APIResponse<Brand>>(`/brands/${id}`);
    return res.data.data!;
  },

  async createBrand(name: string, description?: string): Promise<Brand> {
    const res = await api.post<APIResponse<Brand>>('/brands/', { name, description });
    return res.data.data!;
  },

  async updateBrand(id: string, name: string, description?: string): Promise<Brand> {
    const res = await api.put<APIResponse<Brand>>(`/brands/${id}`, { name, description });
    return res.data.data!;
  },

  async deleteBrand(id: string): Promise<void> {
    await api.delete(`/brands/${id}`);
  },
};
