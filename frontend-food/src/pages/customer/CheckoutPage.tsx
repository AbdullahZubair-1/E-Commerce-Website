import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import toast from 'react-hot-toast';
import { ShoppingBagIcon } from '@heroicons/react/24/outline';
import { useCart } from '@/hooks/useCart';
import { EmptyState } from '@/components/ui/EmptyState';
import { PageSpinner } from '@/components/ui/Spinner';
import { formatPrice, getImageUrl } from '@/utils/format';
import { orderService } from '@/services/order.service';
import { getErrorMessage } from '@/services/api';

const schema = z.object({
  shipping_address: z
    .string()
    .min(10, 'Please enter a full shipping address (min 10 characters)')
    .max(500, 'Address is too long'),
  customer_phone: z
    .string()
    .regex(/^\+[1-9]\d{6,14}$/, 'Enter phone with country code, e.g. +15551234567')
    .optional()
    .or(z.literal('')),
  notes: z.string().max(300, 'Notes too long').optional(),
});

type FormData = z.infer<typeof schema>;

export function CheckoutPage() {
  const { cart, isLoading, fetchCart } = useCart();
  const navigate = useNavigate();
  const [placing, setPlacing] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormData>({ resolver: zodResolver(schema) });

  const onSubmit = async (data: FormData) => {
    setPlacing(true);
    try {
      const order = await orderService.placeOrder(data.shipping_address, data.notes, data.customer_phone);
      await fetchCart();
      toast.success('Order placed successfully!');
      navigate(`/orders/${order.id}`);
    } catch (err) {
      toast.error(getErrorMessage(err));
    } finally {
      setPlacing(false);
    }
  };

  if (isLoading) return <PageSpinner />;

  if (!cart || cart.items.length === 0) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-16">
        <EmptyState
          title="Your cart is empty"
          description="Add some products before checking out."
          icon={<ShoppingBagIcon className="h-20 w-20" />}
          action={
            <Link to="/products" className="btn-primary no-underline">
              Shop Now
            </Link>
          }
        />
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Checkout</h1>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-10">
        {/* Shipping form */}
        <div>
          <div className="card p-6">
            <h2 className="text-lg font-semibold mb-5">Shipping Information</h2>
            <form id="checkout-form" onSubmit={handleSubmit(onSubmit)} className="space-y-5" noValidate>
              <div>
                <label htmlFor="shipping_address" className="block text-sm font-medium text-gray-700 mb-1">
                  Shipping Address <span className="text-red-500">*</span>
                </label>
                <textarea
                  id="shipping_address"
                  rows={4}
                  placeholder="123 Lab Street, Suite 4&#10;New York, NY 10001&#10;United States"
                  className="input-field resize-none"
                  {...register('shipping_address')}
                  aria-invalid={!!errors.shipping_address}
                  aria-describedby={errors.shipping_address ? 'addr-error' : undefined}
                />
                {errors.shipping_address && (
                  <p id="addr-error" className="text-red-500 text-xs mt-1" role="alert">
                    {errors.shipping_address.message}
                  </p>
                )}
              </div>

              <div>
                <label htmlFor="customer_phone" className="block text-sm font-medium text-gray-700 mb-1">
                  Phone Number <span className="text-gray-400 text-xs">(optional, for order updates via WhatsApp)</span>
                </label>
                <input
                  id="customer_phone"
                  type="tel"
                  placeholder="+15551234567"
                  className="input-field"
                  {...register('customer_phone')}
                  aria-invalid={!!errors.customer_phone}
                  aria-describedby={errors.customer_phone ? 'phone-error' : undefined}
                />
                {errors.customer_phone && (
                  <p id="phone-error" className="text-red-500 text-xs mt-1" role="alert">
                    {errors.customer_phone.message}
                  </p>
                )}
              </div>

              <div>
                <label htmlFor="notes" className="block text-sm font-medium text-gray-700 mb-1">
                  Order Notes <span className="text-gray-400 text-xs">(optional)</span>
                </label>
                <textarea
                  id="notes"
                  rows={3}
                  placeholder="Special delivery instructions, handling notes…"
                  className="input-field resize-none"
                  {...register('notes')}
                />
              </div>
            </form>
          </div>
        </div>

        {/* Order summary */}
        <div>
          <div className="card p-6">
            <h2 className="text-lg font-semibold mb-5">Order Summary</h2>

            <div className="space-y-3 mb-4 max-h-64 overflow-y-auto pr-1">
              {cart.items.map((item) => (
                <div key={item.id} className="flex items-center gap-3">
                  <img
                    src={getImageUrl(item.product.image_url)}
                    alt={item.product.name}
                    className="w-12 h-12 object-cover rounded-lg bg-gray-100 flex-shrink-0"
                    onError={(e) => { (e.target as HTMLImageElement).src = '/placeholder-product.svg'; }}
                  />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">{item.product.name}</p>
                    <p className="text-xs text-gray-500">Qty: {item.quantity}</p>
                  </div>
                  <p className="text-sm font-semibold flex-shrink-0">{formatPrice(item.subtotal)}</p>
                </div>
              ))}
            </div>

            <div className="border-t border-gray-200 pt-4 space-y-2 text-sm text-gray-600">
              <div className="flex justify-between">
                <span>Subtotal</span>
                <span>{formatPrice(cart.total)}</span>
              </div>
              <div className="flex justify-between">
                <span>Shipping</span>
                <span className="text-green-600">Free</span>
              </div>
            </div>

            <div className="border-t border-gray-200 pt-4 mt-2 flex justify-between font-bold text-lg">
              <span>Total</span>
              <span className="text-orange-600">{formatPrice(cart.total)}</span>
            </div>

            <button
              type="submit"
              form="checkout-form"
              disabled={placing}
              className="btn-primary w-full py-3 mt-6"
            >
              {placing ? 'Placing Order…' : 'Place Order'}
            </button>

            <Link
              to="/cart"
              className="block text-center text-sm text-gray-500 hover:text-gray-700 mt-3 no-underline"
            >
              ← Back to Cart
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}