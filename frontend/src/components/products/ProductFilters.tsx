import { useState, useEffect } from 'react';
import { MagnifyingGlassIcon, FunnelIcon, XMarkIcon } from '@heroicons/react/24/outline';
import type { Category, Brand, ProductFilters } from '@/types';
import { categoryService } from '@/services/category.service';
import { brandService } from '@/services/brand.service';

interface ProductFiltersProps {
  filters: ProductFilters;
  onFiltersChange: (filters: ProductFilters) => void;
}

export function ProductFiltersPanel({ filters, onFiltersChange }: ProductFiltersProps) {
  const [categories, setCategories] = useState<Category[]>([]);
  const [brands, setBrands] = useState<Brand[]>([]);
  const [searchInput, setSearchInput] = useState(filters.search ?? '');

  useEffect(() => {
    Promise.all([categoryService.getCategories(), brandService.getBrands()]).then(
      ([cats, brds]) => { setCategories(cats); setBrands(brds); }
    );
  }, []);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    onFiltersChange({ ...filters, search: searchInput || undefined, page: 1 });
  };

  const handleCategoryChange = (id: string) => {
    onFiltersChange({
      ...filters,
      category_id: filters.category_id === id ? undefined : id,
      page: 1,
    });
  };

  const handleBrandChange = (id: string) => {
    onFiltersChange({
      ...filters,
      brand_id: filters.brand_id === id ? undefined : id,
      page: 1,
    });
  };

  const clearFilters = () => {
    setSearchInput('');
    onFiltersChange({ page: 1, page_size: filters.page_size });
  };

  const hasActiveFilters = filters.search || filters.category_id || filters.brand_id;

  return (
    <aside className="w-full lg:w-64 flex-shrink-0">
      <div className="card p-4 sticky top-4">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-semibold flex items-center gap-2">
            <FunnelIcon className="h-4 w-4" /> Filters
          </h2>
          {hasActiveFilters && (
            <button
              onClick={clearFilters}
              className="text-xs text-blue-600 hover:text-blue-800 flex items-center gap-1"
            >
              <XMarkIcon className="h-3 w-3" /> Clear
            </button>
          )}
        </div>

        {/* Search */}
        <form onSubmit={handleSearch} className="mb-5">
          <label htmlFor="product-search" className="text-sm font-medium text-gray-700 mb-1 block">
            Search
          </label>
          <div className="relative">
            <input
              id="product-search"
              type="search"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              placeholder="Search products…"
              className="input-field pr-9 text-sm"
            />
            <button type="submit" className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-blue-600" aria-label="Search">
              <MagnifyingGlassIcon className="h-4 w-4" />
            </button>
          </div>
        </form>

        {/* Categories */}
        {categories.length > 0 && (
          <div className="mb-5">
            <h3 className="text-sm font-medium text-gray-700 mb-2">Category</h3>
            <ul className="space-y-1">
              {categories.map((cat) => (
                <li key={cat.id}>
                  <button
                    onClick={() => handleCategoryChange(cat.id)}
                    className={`w-full text-left text-sm px-2 py-1.5 rounded-lg transition-colors ${
                      filters.category_id === cat.id
                        ? 'bg-blue-50 text-blue-700 font-medium'
                        : 'text-gray-600 hover:bg-gray-100'
                    }`}
                  >
                    {cat.name}
                  </button>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Brands */}
        {brands.length > 0 && (
          <div>
            <h3 className="text-sm font-medium text-gray-700 mb-2">Brand</h3>
            <ul className="space-y-1">
              {brands.map((brand) => (
                <li key={brand.id}>
                  <button
                    onClick={() => handleBrandChange(brand.id)}
                    className={`w-full text-left text-sm px-2 py-1.5 rounded-lg transition-colors ${
                      filters.brand_id === brand.id
                        ? 'bg-blue-50 text-blue-700 font-medium'
                        : 'text-gray-600 hover:bg-gray-100'
                    }`}
                  >
                    {brand.name}
                  </button>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </aside>
  );
}
