import { useState, useEffect, useRef } from 'react';
import { PlusIcon, PencilIcon, TrashIcon, PhotoIcon } from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';
import { Modal } from '@/components/ui/Modal';
import { PageSpinner } from '@/components/ui/Spinner';
import { Pagination } from '@/components/ui/Pagination';
import type { Product, Category, Brand } from '@/types';
import { productService } from '@/services/product.service';
import { categoryService } from '@/services/category.service';
import { brandService } from '@/services/brand.service';
import { formatPrice, getImageUrl } from '@/utils/format';
import { getErrorMessage } from '@/services/api';

export function AdminProductsPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [brands, setBrands] = useState<Brand[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [isLoading, setIsLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingProduct, setEditingProduct] = useState<Product | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<Product | null>(null);
  const [saving, setSaving] = useState(false);
  const [imagePreview, setImagePreview] = useState<string | null>(null);

  const formRef = useRef<HTMLFormElement>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const fetchProducts = async (p = page) => {
    setIsLoading(true);
    try {
      const data = await productService.getProducts({ page: p, page_size: 15 });
      setProducts(data.items);
      setTotal(data.total);
      setTotalPages(data.total_pages);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    Promise.all([
      categoryService.getCategories(),
      brandService.getBrands(),
    ]).then(([cats, brds]) => { setCategories(cats); setBrands(brds); });
    fetchProducts();
  }, []);

  useEffect(() => { fetchProducts(page); }, [page]);

  const openCreate = () => {
    setEditingProduct(null);
    setImagePreview(null);
    setModalOpen(true);
  };

  const openEdit = (product: Product) => {
    setEditingProduct(product);
    setImagePreview(product.image_url ?? null);
    setModalOpen(true);
  };

  const handleSave = async () => {
    if (!formRef.current) return;
    const fd = new FormData(formRef.current);

    // Remove empty optional fields
    if (!fd.get('description')) fd.delete('description');
    if (!fd.get('category_id')) fd.delete('category_id');
    if (!fd.get('brand_id')) fd.delete('brand_id');

    const imageFile = fd.get('image') as File;
    if (!imageFile || imageFile.size === 0) fd.delete('image');

    setSaving(true);
    try {
      if (editingProduct) {
        await productService.updateProduct(editingProduct.id, fd);
        toast.success('Product updated.');
      } else {
        await productService.createProduct(fd);
        toast.success('Product created.');
      }
      setModalOpen(false);
      setPage(1);
      fetchProducts(1);
    } catch (err) {
      toast.error(getErrorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    try {
      await productService.deleteProduct(deleteTarget.id);
      toast.success('Product deleted.');
      setDeleteTarget(null);
      fetchProducts(page);
    } catch (err) {
      toast.error(getErrorMessage(err));
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Products</h1>
          <p className="text-gray-500 text-sm mt-1">{total} products total</p>
        </div>
        <button onClick={openCreate} className="btn-primary flex items-center gap-2">
          <PlusIcon className="h-4 w-4" aria-hidden="true" />
          Add Product
        </button>
      </div>

      {isLoading ? (
        <PageSpinner />
      ) : (
        <div className="card overflow-hidden">
          <table className="w-full text-sm" role="table">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-200">
                <th className="text-left px-4 py-3 font-medium text-gray-600">Product</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600 hidden md:table-cell">Category</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Price</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Stock</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600 hidden sm:table-cell">Status</th>
                <th className="text-right px-4 py-3 font-medium text-gray-600">Actions</th>
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
                        className="h-10 w-10 rounded-lg object-cover bg-gray-100 flex-shrink-0"
                        onError={(e) => { (e.target as HTMLImageElement).src = '/placeholder-product.svg'; }}
                      />
                      <span className="font-medium text-gray-900 line-clamp-1">{product.name}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-gray-500 hidden md:table-cell">
                    {product.category?.name ?? '—'}
                  </td>
                  <td className="px-4 py-3 font-medium">{formatPrice(product.price)}</td>
                  <td className="px-4 py-3">
                    <span className={product.stock_quantity === 0 ? 'text-red-600 font-medium' : product.stock_quantity <= 10 ? 'text-orange-500 font-medium' : 'text-gray-700'}>
                      {product.stock_quantity}
                    </span>
                  </td>
                  <td className="px-4 py-3 hidden sm:table-cell">
                    <span className={`badge ${product.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'}`}>
                      {product.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <button
                        onClick={() => openEdit(product)}
                        className="p-1.5 rounded-lg hover:bg-blue-50 text-gray-400 hover:text-blue-600 transition-colors"
                        aria-label={`Edit ${product.name}`}
                      >
                        <PencilIcon className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => setDeleteTarget(product)}
                        className="p-1.5 rounded-lg hover:bg-red-50 text-gray-400 hover:text-red-600 transition-colors"
                        aria-label={`Delete ${product.name}`}
                      >
                        <TrashIcon className="h-4 w-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
              {products.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-4 py-12 text-center text-gray-400">No products yet.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      <Pagination page={page} totalPages={totalPages} onPageChange={setPage} />

      {/* Create/Edit Modal */}
      <Modal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        title={editingProduct ? 'Edit Product' : 'Add New Product'}
        size="lg"
      >
        <form ref={formRef} onSubmit={(e) => { e.preventDefault(); handleSave(); }} className="space-y-4">
          <div>
            <label htmlFor="p-name" className="block text-sm font-medium text-gray-700 mb-1">
              Name <span className="text-red-500">*</span>
            </label>
            <input
              id="p-name"
              name="name"
              type="text"
              required
              defaultValue={editingProduct?.name}
              className="input-field"
            />
          </div>

          <div>
            <label htmlFor="p-desc" className="block text-sm font-medium text-gray-700 mb-1">Description</label>
            <textarea
              id="p-desc"
              name="description"
              rows={3}
              defaultValue={editingProduct?.description ?? ''}
              className="input-field resize-none"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="p-price" className="block text-sm font-medium text-gray-700 mb-1">
                Price <span className="text-red-500">*</span>
              </label>
              <input
                id="p-price"
                name="price"
                type="number"
                step="0.01"
                min="0.01"
                required
                defaultValue={editingProduct?.price}
                className="input-field"
              />
            </div>
            <div>
              <label htmlFor="p-stock" className="block text-sm font-medium text-gray-700 mb-1">
                Stock Qty <span className="text-red-500">*</span>
              </label>
              <input
                id="p-stock"
                name="stock_quantity"
                type="number"
                min="0"
                required
                defaultValue={editingProduct?.stock_quantity ?? 0}
                className="input-field"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="p-category" className="block text-sm font-medium text-gray-700 mb-1">Category</label>
              <select id="p-category" name="category_id" defaultValue={editingProduct?.category_id ?? ''} className="input-field">
                <option value="">— None —</option>
                {categories.map((c) => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </select>
            </div>
            <div>
              <label htmlFor="p-brand" className="block text-sm font-medium text-gray-700 mb-1">Brand</label>
              <select id="p-brand" name="brand_id" defaultValue={editingProduct?.brand_id ?? ''} className="input-field">
                <option value="">— None —</option>
                {brands.map((b) => (
                  <option key={b.id} value={b.id}>{b.name}</option>
                ))}
              </select>
            </div>
          </div>

          {editingProduct && (
            <div>
              <label htmlFor="p-active" className="block text-sm font-medium text-gray-700 mb-1">Status</label>
              <select id="p-active" name="is_active" defaultValue={editingProduct.is_active ? 'true' : 'false'} className="input-field">
                <option value="true">Active</option>
                <option value="false">Inactive</option>
              </select>
            </div>
          )}

          {/* Image upload */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Product Image</label>
            <div
              className="border-2 border-dashed border-gray-300 rounded-xl p-4 text-center cursor-pointer hover:border-blue-400 transition-colors"
              onClick={() => fileRef.current?.click()}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => e.key === 'Enter' && fileRef.current?.click()}
              aria-label="Upload product image"
            >
              {imagePreview ? (
                <img src={getImageUrl(imagePreview)} alt="Preview" className="h-24 w-24 object-cover rounded-lg mx-auto" />
              ) : (
                <div className="text-gray-400">
                  <PhotoIcon className="h-10 w-10 mx-auto mb-2" aria-hidden="true" />
                  <p className="text-sm">Click to upload image</p>
                  <p className="text-xs mt-1">JPEG, PNG, WebP (max 5MB)</p>
                </div>
              )}
              <input
                ref={fileRef}
                name="image"
                type="file"
                accept="image/jpeg,image/png,image/webp,image/gif"
                className="hidden"
                onChange={(e) => {
                  const f = e.target.files?.[0];
                  if (f) setImagePreview(URL.createObjectURL(f));
                }}
              />
            </div>
          </div>

          <div className="flex gap-3 pt-2">
            <button type="button" onClick={() => setModalOpen(false)} className="btn-secondary flex-1">
              Cancel
            </button>
            <button type="submit" disabled={saving} className="btn-primary flex-1">
              {saving ? 'Saving…' : editingProduct ? 'Update Product' : 'Create Product'}
            </button>
          </div>
        </form>
      </Modal>

      {/* Delete confirmation */}
      <Modal
        isOpen={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        title="Delete Product"
        size="sm"
      >
        <p className="text-gray-600 mb-6">
          Are you sure you want to delete <strong>{deleteTarget?.name}</strong>? This action cannot be undone.
        </p>
        <div className="flex gap-3">
          <button onClick={() => setDeleteTarget(null)} className="btn-secondary flex-1">Cancel</button>
          <button onClick={handleDelete} className="btn-danger flex-1">Delete</button>
        </div>
      </Modal>
    </div>
  );
}
