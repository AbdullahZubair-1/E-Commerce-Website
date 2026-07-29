import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import type { Cart } from '@/types';
import { cartService } from '@/services/cart.service';
import { useAuth } from './useAuth';

interface CartContextValue {
  cart: Cart | null;
  cartCount: number;
  isLoading: boolean;
  fetchCart: () => Promise<void>;
  addToCart: (product_id: string, quantity?: number) => Promise<void>;
  updateItem: (item_id: string, quantity: number) => Promise<void>;
  removeItem: (item_id: string) => Promise<void>;
  clearCart: () => Promise<void>;
}

const CartContext = createContext<CartContextValue | null>(null);

export function CartProvider({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuth();
  const [cart, setCart] = useState<Cart | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const fetchCart = useCallback(async () => {
    if (!isAuthenticated) {
      setCart(null);
      return;
    }
    setIsLoading(true);
    try {
      const data = await cartService.getCart();
      setCart(data);
    } catch {
      setCart(null);
    } finally {
      setIsLoading(false);
    }
  }, [isAuthenticated]);

  useEffect(() => {
    fetchCart();
  }, [fetchCart]);

  const addToCart = useCallback(async (product_id: string, quantity = 1) => {
    const updated = await cartService.addItem(product_id, quantity);
    setCart(updated);
    await fetchCart();
  }, [fetchCart]);

  const updateItem = useCallback(async (item_id: string, quantity: number) => {
    const updated = await cartService.updateItem(item_id, quantity);
    setCart(updated);
    await fetchCart();
  }, [fetchCart]);

  const removeItem = useCallback(async (item_id: string) => {
    const updated = await cartService.removeItem(item_id);
    setCart(updated);
    await fetchCart();
  }, [fetchCart]);

  const clearCart = useCallback(async () => {
    const updated = await cartService.clearCart();
    setCart(updated);
    await fetchCart();
  }, [fetchCart]);

  const cartCount = cart?.item_count ?? 0;

  return (
    <CartContext.Provider value={{ cart, cartCount, isLoading, fetchCart, addToCart, updateItem, removeItem, clearCart }}>
      {children}
    </CartContext.Provider>
  );
}

export function useCart(): CartContextValue {
  const ctx = useContext(CartContext);
  if (!ctx) throw new Error('useCart must be used inside CartProvider');
  return ctx;
}
