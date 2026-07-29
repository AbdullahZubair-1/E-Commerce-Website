import { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { ShoppingCartIcon, ArrowLeftIcon, CheckCircleIcon } from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';
import { PageSpinner } from '@/components/ui/Spinner';
import type { Product } from '@/types';
import { productService } from '@/services/product.service';
import { formatPrice, formatDate, getImageUrl } from '@/utils/format';
import { useAuth } from '@/hooks/useAuth';
import { useCart } from '@/hooks/useCart';
import { getErrorMessage } from '@/services/api';

export function ProductDetailPage() {
  const { slug } = useParams<{ slug: string }>();
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  const { addToCart } = useCart();

  const [product, setProduct] = useState<Product | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [quantity, setQuantity] = useState(1);
  const [addingToCart, setAddingToCart] = useState(false);

  useEffect(() => {
    if (!slug) return;
    productService.getProductBySlug(slug)
      .then(setProduct)
      .catch(() => setProduct(null))
      .finally(() => setIsLoading(false));
  }, [slug]);

  const handleAddToCart = async () => {
    if (!isAuthenticated) {
      toast.error('Please login to add items to cart.');
      navigate('/login');
      return;
    }
    if (!product) return;
    setAddingToCart(true);
    try {
      await addToCart(product.id, quantity);
      toast.success(`${product.name} added to cart!`);
    } catch (err) {
      toast.error(getErrorMessage(err));
    } finally {
      setAddingToCart(false);
    }
  };

  if (isLoading) return <PageSpinner />;
  if (!product) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-16 text-center">
        <h2 className="text-2xl font-bold text-gray-700 mb-4">Product not found</h2>
        <Link to="/products" className="btn-primary no-underline inline-block">Back to Products</Link>
      </div>
    );
  }

  const isOutOfStock = product.stock_quantity === 0;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <nav className="mb-6" aria-label="Breadcrumb">
        <Link to="/products" className="flex items-center gap-1 text-gray-500 hover:text-gray-700 text-sm no-underline">
          <ArrowLeftIcon className="h-4 w-4" /> Back to Products
        </Link>
      </nav>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-10">
        {/* Image */}
        <div className="aspect-square bg-gray-100 rounded-2xl overflow-hidden">
          <img
            src={getImageUrl(product.image_url)}
            alt={product.name}
            className="w-full h-full object-cover"
            onError={(e) => { (e.target as HTMLImageElement).src = '/placeholder-product.svg'; }}
          />
        </div>

        {/* Details */}
        <div>
          <div className="flex gap-2 mb-3">
            {product.category && (
              <span className="badge bg-orange-50 text-orange-700">{product.category.name}</span>
            )}
            {product.brand && (
              <span className="badge bg-gray-100 text-gray-600">{product.brand.name}</span>
            )}
          </div>

          <h1 className="text-3xl font-bold text-gray-900 mb-2">{product.name}</h1>
          <p className="text-4xl font-bold text-orange-600 mb-6">{formatPrice(product.price)}</p>

          {product.description && (
            <p className="text-gray-600 leading-relaxed mb-6">{product.description}</p>
          )}

          {/* Stock status */}
          <div className="flex items-center gap-2 mb-6">
            {isOutOfStock ? (
              <span className="text-red-600 font-medium text-sm">Out of Stock</span>
            ) : (
              <>
                <CheckCircleIcon className="h-5 w-5 text-green-500" aria-hidden="true" />
                <span className="text-green-600 font-medium text-sm">
                  In Stock ({product.stock_quantity} available)
                </span>
              </>
            )}
          </div>

          {/* Quantity + Add to Cart */}
          {!isOutOfStock && (
            <div className="flex items-center gap-4 mb-6">
              <div className="flex items-center border border-gray-300 rounded-lg overflow-hidden">
                <button
                  onClick={() => setQuantity((q) => Math.max(1, q - 1))}
                  className="px-3 py-2 hover:bg-gray-100 transition-colors text-gray-700"
                  aria-label="Decrease quantity"
                >
                  −
                </button>
                <span className="px-4 py-2 font-medium text-gray-900 min-w-[3rem] text-center">
                  {quantity}
                </span>
                <button
                  onClick={() => setQuantity((q) => Math.min(product.stock_quantity, q + 1))}
                  className="px-3 py-2 hover:bg-gray-100 transition-colors text-gray-700"
                  aria-label="Increase quantity"
                >
                  +
                </button>
              </div>

              <button
                onClick={handleAddToCart}
                disabled={addingToCart || isOutOfStock}
                className="flex-1 btn-primary flex items-center justify-center gap-2 py-3"
              >
                <ShoppingCartIcon className="h-5 w-5" aria-hidden="true" />
                {addingToCart ? 'Adding…' : 'Add to Cart'}
              </button>
            </div>
          )}

          {/* Metadata */}
          <div className="border-t border-gray-200 pt-4 mt-4 text-sm text-gray-500 space-y-1">
            <p>Added: {formatDate(product.created_at)}</p>
            <p>Updated: {formatDate(product.updated_at)}</p>
          </div>
        </div>
      </div>
    </div>
  );
}
