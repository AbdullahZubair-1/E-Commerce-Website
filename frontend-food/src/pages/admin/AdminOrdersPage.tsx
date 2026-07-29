import { useState, useEffect } from 'react';
import { ChevronDownIcon } from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';
import { Modal } from '@/components/ui/Modal';
import { PageSpinner } from '@/components/ui/Spinner';
import { Pagination } from '@/components/ui/Pagination';
import type { Order, OrderSummary, OrderStatus, PaginatedData } from '@/types';
import { orderService } from '@/services/order.service';
import { formatPrice, formatDateTime, getOrderStatusColor, capitalizeFirst } from '@/utils/format';
import { getErrorMessage } from '@/services/api';

const ALL_STATUSES: OrderStatus[] = [
  'pending', 'confirmed', 'processing', 'shipped', 'delivered', 'cancelled',
];

export function AdminOrdersPage() {
  const [data, setData] = useState<PaginatedData<OrderSummary> | null>(null);
  const [page, setPage] = useState(1);
  const [filterStatus, setFilterStatus] = useState<OrderStatus | ''>('');
  const [isLoading, setIsLoading] = useState(true);
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [updatingStatus, setUpdatingStatus] = useState(false);
  const [newStatus, setNewStatus] = useState<OrderStatus>('pending');

  const fetchOrders = async (p = page) => {
    setIsLoading(true);
    try {
      const result = await orderService.getAllOrders(
        p,
        20,
        filterStatus || undefined,
      );
      setData(result);
    } catch {
      setData(null);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    setPage(1);
    fetchOrders(1);
  }, [filterStatus]);

  useEffect(() => {
    fetchOrders(page);
  }, [page]);

  const openDetail = async (orderId: string) => {
    setDetailLoading(true);
    try {
      const order = await orderService.getOrderById(orderId);
      setSelectedOrder(order);
      setNewStatus(order.status);
    } catch (err) {
      toast.error(getErrorMessage(err));
    } finally {
      setDetailLoading(false);
    }
  };

  const handleStatusUpdate = async () => {
    if (!selectedOrder) return;
    setUpdatingStatus(true);
    try {
      const updated = await orderService.updateOrderStatus(selectedOrder.id, newStatus);
      setSelectedOrder(updated);
      setNewStatus(updated.status);
      toast.success('Order status updated.');
      fetchOrders(page);
    } catch (err) {
      toast.error(getErrorMessage(err));
    } finally {
      setUpdatingStatus(false);
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6 flex-wrap gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Orders</h1>
          <p className="text-gray-500 text-sm mt-1">
            {data?.total ?? 0} orders total
          </p>
        </div>

        {/* Status filter */}
        <div className="relative">
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value as OrderStatus | '')}
            className="input-field pr-8 appearance-none min-w-[160px]"
            aria-label="Filter by status"
          >
            <option value="">All Statuses</option>
            {ALL_STATUSES.map((s) => (
              <option key={s} value={s}>{capitalizeFirst(s)}</option>
            ))}
          </select>
          <ChevronDownIcon className="h-4 w-4 text-gray-400 absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none" aria-hidden="true" />
        </div>
      </div>

      {isLoading ? (
        <PageSpinner />
      ) : (
        <div className="card overflow-hidden">
          <table className="w-full text-sm" role="table">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-200">
                <th className="text-left px-4 py-3 font-medium text-gray-600">Order ID</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600 hidden lg:table-cell">Date</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600 hidden sm:table-cell">Items</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Total</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Status</th>
                <th className="text-right px-4 py-3 font-medium text-gray-600">Action</th>
              </tr>
            </thead>
            <tbody>
              {data?.items.map((order) => (
                <tr key={order.id} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="px-4 py-3 font-mono text-xs font-medium text-gray-700">
                    #{order.id.slice(0, 8).toUpperCase()}
                  </td>
                  <td className="px-4 py-3 text-gray-500 hidden lg:table-cell">
                    {formatDateTime(order.created_at)}
                  </td>
                  <td className="px-4 py-3 text-gray-600 hidden sm:table-cell">
                    {order.item_count} item{order.item_count !== 1 ? 's' : ''}
                  </td>
                  <td className="px-4 py-3 font-semibold text-gray-900">
                    {formatPrice(order.total_amount)}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`badge ${getOrderStatusColor(order.status)}`}>
                      {capitalizeFirst(order.status)}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button
                      onClick={() => openDetail(order.id)}
                      className="text-orange-600 hover:text-orange-800 text-xs font-medium"
                    >
                      View
                    </button>
                  </td>
                </tr>
              ))}
              {(!data || data.items.length === 0) && (
                <tr>
                  <td colSpan={6} className="px-4 py-12 text-center text-gray-400">
                    No orders found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {data && (
        <Pagination page={page} totalPages={data.total_pages} onPageChange={setPage} />
      )}

      {/* Order detail modal */}
      <Modal
        isOpen={!!selectedOrder || detailLoading}
        onClose={() => setSelectedOrder(null)}
        title={selectedOrder ? `Order #${selectedOrder.id.slice(0, 8).toUpperCase()}` : 'Loading…'}
        size="lg"
      >
        {detailLoading ? (
          <PageSpinner />
        ) : selectedOrder ? (
          <div className="space-y-5">
            {/* Meta */}
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <p className="text-gray-500 text-xs mb-0.5">Placed</p>
                <p className="font-medium">{formatDateTime(selectedOrder.created_at)}</p>
              </div>
              <div>
                <p className="text-gray-500 text-xs mb-0.5">Total</p>
                <p className="font-bold text-orange-600 text-lg">{formatPrice(selectedOrder.total_amount)}</p>
              </div>
            </div>

            {/* Shipping */}
            <div className="bg-gray-50 rounded-xl p-4">
              <p className="text-xs font-medium text-gray-500 mb-1">Shipping Address</p>
              <p className="text-sm whitespace-pre-line">{selectedOrder.shipping_address}</p>
              {selectedOrder.notes && (
                <>
                  <p className="text-xs font-medium text-gray-500 mt-3 mb-1">Notes</p>
                  <p className="text-sm">{selectedOrder.notes}</p>
                </>
              )}
            </div>

            {/* Items */}
            <div>
              <p className="text-sm font-semibold text-gray-900 mb-2">Items</p>
              <div className="space-y-2">
                {selectedOrder.items.map((item) => (
                  <div
                    key={item.id}
                    className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0 text-sm"
                  >
                    <div>
                      <p className="font-medium text-gray-900">{item.product_name}</p>
                      <p className="text-xs text-gray-400">
                        {formatPrice(item.product_price)} × {item.quantity}
                      </p>
                    </div>
                    <p className="font-semibold">{formatPrice(item.subtotal)}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Status update */}
            <div className="border-t border-gray-200 pt-4">
              <p className="text-sm font-semibold text-gray-900 mb-3">Update Status</p>
              <div className="flex gap-3">
                <div className="relative flex-1">
                  <select
                    value={newStatus}
                    onChange={(e) => setNewStatus(e.target.value as OrderStatus)}
                    className="input-field appearance-none pr-8"
                    aria-label="New order status"
                  >
                    {ALL_STATUSES.map((s) => (
                      <option key={s} value={s}>{capitalizeFirst(s)}</option>
                    ))}
                  </select>
                  <ChevronDownIcon className="h-4 w-4 text-gray-400 absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none" aria-hidden="true" />
                </div>
                <button
                  onClick={handleStatusUpdate}
                  disabled={updatingStatus || newStatus === selectedOrder.status}
                  className="btn-primary px-6 disabled:opacity-50"
                >
                  {updatingStatus ? 'Saving…' : 'Update'}
                </button>
              </div>
              <p className="text-xs text-gray-400 mt-2">
                Current: <span className={`badge ${getOrderStatusColor(selectedOrder.status)}`}>{capitalizeFirst(selectedOrder.status)}</span>
              </p>
            </div>
          </div>
        ) : null}
      </Modal>
    </div>
  );
}
