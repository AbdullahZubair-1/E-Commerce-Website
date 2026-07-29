// ── API Response ───────────────────────────────────────────────────────────────
export interface APIResponse<T = unknown> {
  success: boolean;
  message: string;
  data: T | null;
}

export interface PaginatedData<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// ── Auth ───────────────────────────────────────────────────────────────────────
export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  is_owner: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface RegisterPayload {
  email: string;
  first_name: string;
  last_name: string;
  password: string;
}

// ── Category ──────────────────────────────────────────────────────────────────
export interface Category {
  id: string;
  name: string;
  slug: string;
  description?: string | null;
  created_at: string;
  updated_at: string;
}

// ── Brand ─────────────────────────────────────────────────────────────────────
export interface Brand {
  id: string;
  name: string;
  slug: string;
  description?: string | null;
  created_at: string;
  updated_at: string;
}

// ── Product ───────────────────────────────────────────────────────────────────
export interface Product {
  id: string;
  name: string;
  slug: string;
  description?: string | null;
  price: string;
  stock_quantity: number;
  image_url?: string | null;
  is_active: boolean;
  category_id?: string | null;
  brand_id?: string | null;
  category?: Category | null;
  brand?: Brand | null;
  created_at: string;
  updated_at: string;
}

export interface ProductFilters {
  search?: string;
  category_id?: string;
  brand_id?: string;
  page?: number;
  page_size?: number;
}

// ── Cart ──────────────────────────────────────────────────────────────────────
export interface CartItem {
  id: string;
  cart_id: string;
  product_id: string;
  quantity: number;
  product: Product;
  subtotal: string;
  created_at: string;
  updated_at: string;
}

export interface Cart {
  id: string;
  user_id: string;
  items: CartItem[];
  total: string;
  item_count: number;
  created_at: string;
  updated_at: string;
}

// ── Order ─────────────────────────────────────────────────────────────────────
export type OrderStatus =
  | 'pending'
  | 'confirmed'
  | 'processing'
  | 'shipped'
  | 'delivered'
  | 'cancelled';

export interface OrderItem {
  id: string;
  product_id?: string | null;
  product_name: string;
  product_price: string;
  quantity: number;
  subtotal: string;
  created_at: string;
}

export interface Order {
  id: string;
  user_id: string;
  status: OrderStatus;
  total_amount: string;
  shipping_address: string;
  notes?: string | null;
  items: OrderItem[];
  created_at: string;
  updated_at: string;
}

export interface OrderSummary {
  id: string;
  status: OrderStatus;
  total_amount: string;
  shipping_address: string;
  item_count: number;
  created_at: string;
  updated_at: string;
}

export interface ChatbotMessage {
  role: 'user' | 'assistant';
  text: string;
}

export interface ChatbotResponse {
  reply: string;
}

// ── Admin ─────────────────────────────────────────────────────────────────────
export interface DashboardStats {
  products: {
    total: number;
    active: number;
    low_stock: number;
  };
  orders: {
    total: number;
    pending: number;
  };
  customers: {
    total: number;
  };
  revenue: {
    total: number;
  };
  catalog: {
    categories: number;
    brands: number;
  };
}
