import { useState, useEffect, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { ProductCard } from '@/components/products/ProductCard';
import { ProductFiltersPanel } from '@/components/products/ProductFilters';
import { Pagination } from '@/components/ui/Pagination';
import { PageSpinner } from '@/components/ui/Spinner';
import { EmptyState } from '@/components/ui/EmptyState';
import type { Product, ProductFilters, PaginatedData } from '@/types';
import { productService } from '@/services/product.service';
import { CubeIcon } from '@heroicons/react/24/outline';

export function ProductsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [data, setData] = useState<PaginatedData<Product> | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const filters: ProductFilters = {
    page: Number(searchParams.get('page') ?? 1),
    page_size: 20,
    search: searchParams.get('search') ?? undefined,
    category_id: searchParams.get('category_id') ?? undefined,
    brand_id: searchParams.get('brand_id') ?? undefined,
  };

  const fetchProducts = useCallback(async () => {
    setIsLoading(true);
    try {
      const result = await productService.getProducts(filters);
      setData(result);
    } catch {
      setData(null);
    } finally {
      setIsLoading(false);
    }
  }, [searchParams]);

  useEffect(() => {
    fetchProducts();
  }, [fetchProducts]);

  const handleFiltersChange = (newFilters: ProductFilters) => {
    const params = new URLSearchParams();
    if (newFilters.page && newFilters.page > 1) params.set('page', String(newFilters.page));
    if (newFilters.search) params.set('search', newFilters.search);
    if (newFilters.category_id) params.set('category_id', newFilters.category_id);
    if (newFilters.brand_id) params.set('brand_id', newFilters.brand_id);
    setSearchParams(params);
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Products</h1>

      <div className="flex flex-col lg:flex-row gap-8">
        <ProductFiltersPanel filters={filters} onFiltersChange={handleFiltersChange} />

        <div className="flex-1">
          {isLoading ? (
            <PageSpinner />
          ) : !data || data.items.length === 0 ? (
            <EmptyState
              title="No products found"
              description="Try adjusting your filters or search terms."
              icon={<CubeIcon className="h-16 w-16" />}
            />
          ) : (
            <>
              <p className="text-sm text-gray-500 mb-4">
                Showing {data.items.length} of {data.total} products
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-6">
                {data.items.map((product) => (
                  <ProductCard key={product.id} product={product} />
                ))}
              </div>
              <Pagination
                page={data.page}
                totalPages={data.total_pages}
                onPageChange={(p) => handleFiltersChange({ ...filters, page: p })}
              />
            </>
          )}
        </div>
      </div>
    </div>
  );
}
