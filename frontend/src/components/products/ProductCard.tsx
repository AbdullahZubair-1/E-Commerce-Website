import { Link } from 'react-router-dom';
import { ShoppingCartIcon } from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';
import type { Product } from '@/types';
import { formatPrice, getImageUrl } from '@/utils/format';
import { useAuth } from '@/hooks/useAuth';
import { useCart } from '@/hooks/useCart';
import { getErrorMessage } from '@/services/api';

interface ProductCardProps {
  product: Product;
}

export function ProductCard({ product }: ProductCardProps) {
  const { isAuthenticated } = useAuth();
  const { addToCart } = useCart();

  const handleAddToCart = async (e: React.MouseEvent) => {
    e.preventDefault();
    if (!isAuthenticated) {
      toast.error('Please login to add items to cart.');
      return;
    }
    try {
      await addToCart(product.id);
      toast.success(`${product.name} added to cart!`);
    } catch (err) {
      toast.error(getErrorMessage(err));
    }
  };

  const isOutOfStock = product.stock_quantity === 0;

  return (
    <Link
      to={`/products/${product.slug}`}
      className="group card overflow-hidden hover:shadow-md transition-shadow duration-200 no-underline block"
    >
      <div className="relative aspect-square bg-gray-100 overflow-hidden">
        <img
          src={getImageUrl(product.image_url)}
          alt={product.name}
          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
          onError={(e) => {
            (e.target as HTMLImageElement).src = '/placeholder-product.svg';
          }}
        />
        {isOutOfStock && (
          <div className="absolute inset-0 bg-black/40 flex items-center justify-center">
            <span className="bg-white text-gray-700 text-xs font-semibold px-3 py-1 rounded-full">
              Out of Stock
            </span>
          </div>
        )}
        {product.category && (
          <span className="absolute top-2 left-2 bg-blue-600 text-white text-xs px-2 py-1 rounded-full">
            {product.category.name}
          </span>
        )}
      </div>

      <div className="p-4">
        {product.brand && (
          <p className="text-xs text-gray-500 mb-1">{product.brand.name}</p>
        )}
        <h3 className="font-medium text-gray-900 text-sm line-clamp-2 mb-2 group-hover:text-blue-600 transition-colors">
          {product.name}
        </h3>

        <div className="flex items-center justify-between mt-auto">
          <span className="text-lg font-bold text-blue-600">
            {formatPrice(product.price)}
          </span>

          <button
            onClick={handleAddToCart}
            disabled={isOutOfStock}
            className="p-2 rounded-lg bg-blue-50 hover:bg-blue-100 text-blue-600 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
            aria-label={`Add ${product.name} to cart`}
            title={isOutOfStock ? 'Out of stock' : 'Add to cart'}
          >
            <ShoppingCartIcon className="h-5 w-5" />
          </button>
        </div>

        {product.stock_quantity > 0 && product.stock_quantity <= 10 && (
          <p className="text-xs text-orange-500 mt-1">
            Only {product.stock_quantity} left
          </p>
        )}
      </div>
    </Link>
  );
}
