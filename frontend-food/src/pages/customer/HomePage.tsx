import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { ArrowRightIcon, CakeIcon, ShieldCheckIcon, TruckIcon, CurrencyDollarIcon } from '@heroicons/react/24/outline';
import { ProductCard } from '@/components/products/ProductCard';
import { PageSpinner } from '@/components/ui/Spinner';
import type { Product, Category } from '@/types';
import { productService } from '@/services/product.service';
import { categoryService } from '@/services/category.service';
import { useAuth } from '@/hooks/useAuth';

const features = [
  {
    icon: CakeIcon,
    title: 'Fresh & Quality',
    description: 'Every item is sourced and checked for freshness before it ships.',
  },
  {
    icon: ShieldCheckIcon,
    title: 'Food Safety Certified',
    description: 'Products comply with international food safety standards.',
  },
  {
    icon: TruckIcon,
    title: 'Fast Delivery',
    description: 'Secure packaging and prompt shipping straight to your door.',
  },
  {
    icon: CurrencyDollarIcon,
    title: 'Competitive Pricing',
    description: 'Great everyday prices and discounts for bulk orders.',
  },
];

export function HomePage() {
  const [featuredProducts, setFeaturedProducts] = useState<Product[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const { isAuthenticated, user } = useAuth();

  useEffect(() => {
    Promise.all([
      productService.getProducts({ page: 1, page_size: 8 }),
      categoryService.getCategories(),
    ]).then(([products, cats]) => {
      setFeaturedProducts(products.items);
      setCategories(cats.slice(0, 6));
      setIsLoading(false);
    }).catch(() => setIsLoading(false));
  }, []);

  return (
    <div>
      {/* Hero */}
      <section className="bg-gradient-to-br from-orange-900 via-orange-800 to-indigo-900 text-white py-24 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <div className="flex items-center justify-center mb-6">
            <CakeIcon className="h-16 w-16 text-orange-300" aria-hidden="true" />
          </div>
          <h1 className="text-5xl font-bold mb-4">
            Chemisto<span className="text-orange-300"> Food</span>
          </h1>
          <p className="text-xl text-orange-200 mb-8 max-w-2xl mx-auto leading-relaxed">
            Fresh groceries, pantry staples, and specialty ingredients, delivered to your door.
            Quality food, every time.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              to="/products"
              className="inline-flex items-center gap-2 bg-white text-orange-900 font-semibold px-8 py-3 rounded-full hover:bg-orange-50 transition-colors no-underline"
            >
              Shop Now <ArrowRightIcon className="h-4 w-4" />
            </Link>
            {isAuthenticated ? (
              <Link
                to="/orders"
                className="inline-flex items-center gap-2 border-2 border-white text-white font-semibold px-8 py-3 rounded-full hover:bg-white/10 transition-colors no-underline"
              >
                My Orders <ArrowRightIcon className="h-4 w-4" />
              </Link>
            ) : (
              <Link
                to="/register"
                className="inline-flex items-center gap-2 border-2 border-white text-white font-semibold px-8 py-3 rounded-full hover:bg-white/10 transition-colors no-underline"
              >
                Create Account
              </Link>
            )}
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-16 px-4 bg-white" aria-labelledby="features-heading">
        <div className="max-w-7xl mx-auto">
          <h2 id="features-heading" className="sr-only">Our Features</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {features.map((f) => (
              <div key={f.title} className="text-center p-6">
                <div className="inline-flex items-center justify-center h-14 w-14 rounded-2xl bg-orange-50 mb-4">
                  <f.icon className="h-7 w-7 text-orange-600" aria-hidden="true" />
                </div>
                <h3 className="font-semibold text-gray-900 mb-1">{f.title}</h3>
                <p className="text-sm text-gray-500 leading-relaxed">{f.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Categories */}
      {categories.length > 0 && (
        <section className="py-16 px-4 bg-gray-50" aria-labelledby="categories-heading">
          <div className="max-w-7xl mx-auto">
            <div className="flex items-center justify-between mb-8">
              <h2 id="categories-heading" className="text-2xl font-bold text-gray-900">Shop by Category</h2>
              <Link to="/products" className="text-orange-600 hover:text-orange-800 text-sm font-medium flex items-center gap-1 no-underline">
                View all <ArrowRightIcon className="h-4 w-4" />
              </Link>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
              {categories.map((cat) => (
                <Link
                  key={cat.id}
                  to={`/products?category_id=${cat.id}`}
                  className="card p-4 text-center hover:shadow-md hover:border-orange-200 transition-all no-underline group"
                >
                  <div className="h-10 w-10 rounded-full bg-orange-100 flex items-center justify-center mx-auto mb-2 group-hover:bg-orange-600 transition-colors">
                    <CakeIcon className="h-5 w-5 text-orange-600 group-hover:text-white" aria-hidden="true" />
                  </div>
                  <p className="text-xs font-medium text-gray-700 leading-tight">{cat.name}</p>
                </Link>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* Featured Products */}
      <section className="py-16 px-4" aria-labelledby="products-heading">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-between mb-8">
            <h2 id="products-heading" className="text-2xl font-bold text-gray-900">Featured Products</h2>
            <Link to="/products" className="text-orange-600 hover:text-orange-800 text-sm font-medium flex items-center gap-1 no-underline">
              View all <ArrowRightIcon className="h-4 w-4" />
            </Link>
          </div>

          {isLoading ? (
            <PageSpinner />
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
              {featuredProducts.map((product) => (
                <ProductCard key={product.id} product={product} />
              ))}
            </div>
          )}
        </div>
      </section>

      {/* CTA */}
      <section className="bg-orange-700 py-16 px-4">
        <div className="max-w-2xl mx-auto text-center text-white">
          {isAuthenticated ? (
            <>
              <h2 className="text-3xl font-bold mb-3">Welcome back, {user?.first_name}!</h2>
              <p className="text-orange-200 mb-6">
                Continue browsing our latest arrivals and check your order history.
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Link
                  to="/products"
                  className="inline-flex items-center gap-2 bg-white text-orange-700 font-semibold px-8 py-3 rounded-full hover:bg-orange-50 transition-colors no-underline"
                >
                  Browse Products <ArrowRightIcon className="h-4 w-4" />
                </Link>
                <Link
                  to="/orders"
                  className="inline-flex items-center gap-2 border-2 border-white text-white font-semibold px-8 py-3 rounded-full hover:bg-white/10 transition-colors no-underline"
                >
                  My Orders
                </Link>
              </div>
            </>
          ) : (
            <>
              <h2 className="text-3xl font-bold mb-3">Ready to fill your pantry?</h2>
              <p className="text-orange-200 mb-6">
                Create a free account to manage orders, track deliveries, and access bulk pricing.
              </p>
              <Link
                to="/register"
                className="inline-flex items-center gap-2 bg-white text-orange-700 font-semibold px-8 py-3 rounded-full hover:bg-orange-50 transition-colors no-underline"
              >
                Get Started <ArrowRightIcon className="h-4 w-4" />
              </Link>
            </>
          )}
        </div>
      </section>
    </div>
  );
}
