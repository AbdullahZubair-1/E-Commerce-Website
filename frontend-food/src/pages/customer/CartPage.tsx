import { Link, useNavigate } from 'react-router-dom';
import { TrashIcon, MinusIcon, PlusIcon, ShoppingCartIcon } from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';
import { useCart } from '@/hooks/useCart';
import { PageSpinner } from '@/components/ui/Spinner';
import { EmptyState } from '@/components/ui/EmptyState';
import { formatPrice, getImageUrl } from '@/utils/format';
import { getErrorMessage } from '@/services/api';

export function CartPage() {
  const { cart, isLoading, updateItem, removeItem } = useCart();
  const navigate = useNavigate();

  const handleQuantityChange = async (itemId: string, newQty: number) => {
    if (newQty < 1) return;
    try {
      await updateItem(itemId, newQty);
    } catch (err) {
      toast.error(getErrorMessage(err));
    }
  };

  const handleRemove = async (itemId: string, productName: string) => {
    try {
      await removeItem(itemId);
      toast.success(`${productName} removed from cart.`);
    } catch (err) {
      toast.error(getErrorMessage(err));
    }
  };

  if (isLoading) return <PageSpinner />;

  if (!cart || cart.items.length === 0) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-16">
        <EmptyState
          title="Your cart is empty"
          description="Browse our products and add items to your cart."
          icon={<ShoppingCartIcon className="h-20 w-20" />}
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
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Shopping Cart</h1>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Items */}
        <div className="lg:col-span-2 space-y-4">
          {cart.items.map((item) => (
            <div key={item.id} className="card p-4 flex gap-4">
              <Link to={`/products/${item.product.slug}`} className="flex-shrink-0 no-underline">
                <img
                  src={getImageUrl(item.product.image_url)}
                  alt={item.product.name}
                  className="w-20 h-20 object-cover rounded-lg bg-gray-100"
                  onError={(e) => { (e.target as HTMLImageElement).src = '/placeholder-product.svg'; }}
                />
              </Link>

              <div className="flex-1 min-w-0">
                <Link
                  to={`/products/${item.product.slug}`}
                  className="font-medium text-gray-900 hover:text-orange-600 text-sm line-clamp-2 no-underline block"
                >
                  {item.product.name}
                </Link>
                {item.product.brand && (
                  <p className="text-xs text-gray-500 mt-0.5">{item.product.brand.name}</p>
                )}
                <p className="text-orange-600 font-semibold mt-1">{formatPrice(item.product.price)}</p>
              </div>

              <div className="flex flex-col items-end justify-between flex-shrink-0">
                <button
                  onClick={() => handleRemove(item.id, item.product.name)}
                  className="text-gray-400 hover:text-red-500 transition-colors"
                  aria-label={`Remove ${item.product.name} from cart`}
                >
                  <TrashIcon className="h-4 w-4" />
                </button>

                <div className="flex items-center border border-gray-200 rounded-lg overflow-hidden">
                  <button
                    onClick={() => handleQuantityChange(item.id, item.quantity - 1)}
                    disabled={item.quantity <= 1}
                    className="p-1.5 hover:bg-gray-100 transition-colors disabled:opacity-40"
                    aria-label="Decrease quantity"
                  >
                    <MinusIcon className="h-3 w-3" />
                  </button>
                  <span className="px-3 py-1 text-sm font-medium">{item.quantity}</span>
                  <button
                    onClick={() => handleQuantityChange(item.id, item.quantity + 1)}
                    className="p-1.5 hover:bg-gray-100 transition-colors"
                    aria-label="Increase quantity"
                  >
                    <PlusIcon className="h-3 w-3" />
                  </button>
                </div>

                <p className="font-semibold text-gray-900 text-sm">
                  {formatPrice(item.subtotal)}
                </p>
              </div>
            </div>
          ))}
        </div>

        {/* Summary */}
        <div className="lg:col-span-1">
          <div className="card p-6 sticky top-20">
            <h2 className="text-lg font-semibold mb-4">Order Summary</h2>
            <div className="space-y-2 text-sm mb-4">
              <div className="flex justify-between text-gray-600">
                <span>Subtotal ({cart.item_count} items)</span>
                <span>{formatPrice(cart.total)}</span>
              </div>
              <div className="flex justify-between text-gray-600">
                <span>Shipping</span>
                <span className="text-green-600">Free</span>
              </div>
            </div>
            <div className="border-t border-gray-200 pt-4 mb-6">
              <div className="flex justify-between font-bold text-lg">
                <span>Total</span>
                <span className="text-orange-600">{formatPrice(cart.total)}</span>
              </div>
            </div>
            <button
              onClick={() => navigate('/checkout')}
              className="btn-primary w-full py-3"
            >
              Proceed to Checkout
            </button>
            <Link
              to="/products"
              className="block text-center text-sm text-orange-600 hover:text-orange-800 mt-3 no-underline"
            >
              Continue Shopping
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
