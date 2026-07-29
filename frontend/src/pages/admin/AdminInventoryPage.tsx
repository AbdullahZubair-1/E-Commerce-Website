import { useState, useEffect } from 'react';
import { PencilIcon, CheckIcon, XMarkIcon } from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';
import { PageSpinner } from '@/components/ui/Spinner';
import { Pagination } from '@/components/ui/Pagination';
import type { Product } from '@/types';
import { productService } from '@/services/product.service';
import { getErrorMessage } from '@/services/api';
import { getImageUrl } from '@/utils/format';

export function AdminInventoryPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [totalPages, setTotalPages] = useState(1);
  const [page, setPage] = useState(1);
  const [isLoading, setIsLoading] = useState(true);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editValue, setEditValue] = useState<number>(0);
  const [saving, setSaving] = useState(false);

  // Keep page in a ref so the effect closure always reads the latest value
  // without needing to list it as a dependency that would re-create the fn.

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      setIsLoading(true);
      try {
        const data = await productService.getProducts({
          page,
          page_size: 20,
        });
        if (!cancelled) {
          setProducts(data.items);
          setTotalPages(data.total_pages);
          setIsLoading(false);
        }
      } catch {
        if (!cancelled) setIsLoading(false);
      }
    };

    load();
    return () => {
      cancelled = true;
    };
  }, [page]);

  const startEdit = (product: Product) => {
    setEditingId(product.id);
    setEditValue(product.stock_quantity);
  };

  const cancelEdit = () => setEditingId(null);

  const saveStock = async (product: Product) => {
    if (editValue < 0) {
      toast.error('Stock cannot be negative.');
      return;
    }
    setSaving(true);
    try {
      const updated = await productService.updateStock(product.id, editValue);
      setProducts((prev) => prev.map((p) => (p.id === updated.id ? updated : p)));
      setEditingId(null);
      toast.success(`Stock updated for ${product.name}.`);
    } catch (err) {
      toast.error(getErrorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  const getStockColor = (qty: number) => {
    if (qty === 0) return 'text-red-600 font-bold';
    if (qty <= 5) return 'text-red-500 font-semibold';
    if (qty <= 10) return 'text-orange-500 font-semibold';
    return 'text-gray-700';
  };

  const getStockBadge = (qty: number) => {
    if (qty === 0) return <span className="badge bg-red-100 text-red-700">Out of Stock</span>;
    if (qty <= 5) return <span className="badge bg-red-50 text-red-600">Critical</span>;
    if (qty <= 10) return <span className="badge bg-orange-100 text-orange-700">Low</span>;
    return <span className="badge bg-green-100 text-green-700">OK</span>;
  };

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Inventory</h1>
        <p className="text-gray-500 text-sm mt-1">Manage stock levels for all products</p>
      </div>

      {/* Summary badges */}
      <div className="flex flex-wrap gap-3 mb-6">
        <div className="card px-4 py-3 flex items-center gap-2">
          <span className="badge bg-red-100 text-red-700">Out of Stock</span>
          <span className="font-semibold text-gray-900">
            {products.filter((p) => p.stock_quantity === 0).length}
          </span>
        </div>
        <div className="card px-4 py-3 flex items-center gap-2">
          <span className="badge bg-orange-100 text-orange-700">Low Stock</span>
          <span className="font-semibold text-gray-900">
            {products.filter((p) => p.stock_quantity > 0 && p.stock_quantity <= 10).length}
          </span>
        </div>
        <div className="card px-4 py-3 flex items-center gap-2">
          <span className="badge bg-green-100 text-green-700">Well Stocked</span>
          <span className="font-semibold text-gray-900">
            {products.filter((p) => p.stock_quantity > 10).length}
          </span>
        </div>
      </div>

      {isLoading ? (
        <PageSpinner />
      ) : (
        <div className="card overflow-hidden">
          <table className="w-full text-sm" role="table">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-200">
                <th className="text-left px-4 py-3 font-medium text-gray-600">Product</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600 hidden md:table-cell">
                  Category
                </th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Stock</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Status</th>
                <th className="text-right px-4 py-3 font-medium text-gray-600">Edit</th>
              </tr>
            </thead>
            <tbody>
              {products.map((product) => (
                <tr key={product.id} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-3">
                      <img
                        src={getImageUrl(product.image_url)}
                        alt={product.name}
                        className="h-9 w-9 rounded-lg object-cover bg-gray-100 flex-shrink-0"
                        onError={(e) => {
                          (e.target as HTMLImageElement).src = '/placeholder-product.svg';
                        }}
                      />
                      <span className="font-medium text-gray-900 line-clamp-1">
                        {product.name}
                      </span>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-gray-500 hidden md:table-cell">
                    {product.category?.name ?? '—'}
                  </td>
                  <td className="px-4 py-3">
                    {editingId === product.id ? (
                      <input
                        type="number"
                        min={0}
                        value={editValue}
                        onChange={(e) => setEditValue(Number(e.target.value))}
                        className="input-field w-24 text-sm py-1"
                        autoFocus
                        aria-label={`New stock quantity for ${product.name}`}
                      />
                    ) : (
                      <span className={getStockColor(product.stock_quantity)}>
                        {product.stock_quantity}
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3">{getStockBadge(product.stock_quantity)}</td>
                  <td className="px-4 py-3 text-right">
                    {editingId === product.id ? (
                      <div className="flex items-center justify-end gap-1">
                        <button
                          onClick={() => saveStock(product)}
                          disabled={saving}
                          className="p-1.5 rounded-lg bg-green-50 text-green-600 hover:bg-green-100 transition-colors disabled:opacity-50"
                          aria-label="Save stock"
                        >
                          <CheckIcon className="h-4 w-4" />
                        </button>
                        <button
                          onClick={cancelEdit}
                          className="p-1.5 rounded-lg bg-gray-50 text-gray-500 hover:bg-gray-100 transition-colors"
                          aria-label="Cancel edit"
                        >
                          <XMarkIcon className="h-4 w-4" />
                        </button>
                      </div>
                    ) : (
                      <button
                        onClick={() => startEdit(product)}
                        className="p-1.5 rounded-lg hover:bg-blue-50 text-gray-400 hover:text-blue-600 transition-colors"
                        aria-label={`Edit stock for ${product.name}`}
                      >
                        <PencilIcon className="h-4 w-4" />
                      </button>
                    )}
                  </td>
                </tr>
              ))}
              {products.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-4 py-12 text-center text-gray-400">
                    No products found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      <Pagination page={page} totalPages={totalPages} onPageChange={setPage} />
    </div>
  );
}
