import api from './api';
import type { APIResponse, Product, PaginatedData, ProductFilters } from '@/types';

export const productService = {
  async getProducts(filters: ProductFilters = {}): Promise<PaginatedData<Product>> {
    const params = new URLSearchParams();
    if (filters.page) params.set('page', String(filters.page));
    if (filters.page_size) params.set('page_size', String(filters.page_size));
    if (filters.search) params.set('search', filters.search);
    if (filters.category_id) params.set('category_id', filters.category_id);
    if (filters.brand_id) params.set('brand_id', filters.brand_id);

    const res = await api.get<APIResponse<PaginatedData<Product>>>(`/products/?${params}`);
    return res.data.data!;
  },

  async getProductBySlug(slug: string): Promise<Product> {
    const res = await api.get<APIResponse<Product>>(`/products/slug/${slug}`);
    return res.data.data!;
  },

  async getProductById(id: string): Promise<Product> {
    const res = await api.get<APIResponse<Product>>(`/products/${id}`);
    return res.data.data!;
  },

  async createProduct(formData: FormData): Promise<Product> {
    const res = await api.post<APIResponse<Product>>('/admin/products', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data.data!;
  },

  async updateProduct(id: string, formData: FormData): Promise<Product> {
    const res = await api.put<APIResponse<Product>>(`/products/${id}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data.data!;
  },

  async updateStock(id: string, stock_quantity: number): Promise<Product> {
    const res = await api.patch<APIResponse<Product>>(`/products/${id}/stock`, { stock_quantity });
    return res.data.data!;
  },

  async deleteProduct(id: string): Promise<void> {
    await api.delete(`/products/${id}`);
  },

  // Admin: get all including inactive
  async getAllProducts(filters: ProductFilters = {}): Promise<PaginatedData<Product>> {
    return productService.getProducts(filters);
  },
};
