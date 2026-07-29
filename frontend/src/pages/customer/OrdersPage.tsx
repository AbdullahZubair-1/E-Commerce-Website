import { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { ShoppingBagIcon, ChevronRightIcon } from '@heroicons/react/24/outline';
import { PageSpinner } from '@/components/ui/Spinner';
import { EmptyState } from '@/components/ui/EmptyState';
import { Pagination } from '@/components/ui/Pagination';
import type { OrderSummary, PaginatedData } from '@/types';
import { orderService } from '@/services/order.service';
import { formatPrice, formatDate, getOrderStatusColor, capitalizeFirst } from '@/utils/format';

export function OrdersPage() {
  const location = useLocation();
  const [data, setData] = useState<PaginatedData<OrderSummary> | null>(null);
  const [page, setPage] = useState(1);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    setIsLoading(true);
    orderService.getMyOrders(page, 10)
      .then(setData)
      .catch(() => setData(null))
      .finally(() => setIsLoading(false));
  }, [page, location.key]);

  if (isLoading) return <PageSpinner />;

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">My Orders</h1>

      {!data || data.items.length === 0 ? (
        <EmptyState
          title="No orders yet"
          description="Once you place an order, it will appear here."
          icon={<ShoppingBagIcon className="h-20 w-20" />}
          action={
            <Link to="/products" className="btn-primary no-underline">
              Start Shopping
            </Link>
          }
        />
      ) : (
        <>
          <div className="space-y-4">
            {data.items.map((order) => (
              <Link
                key={order.id}
                to={`/orders/${order.id}`}
                className="card p-5 flex items-center justify-between hover:shadow-md transition-shadow no-underline group"
              >
                <div className="flex items-start gap-4">
                  <div className="h-10 w-10 rounded-full bg-blue-50 flex items-center justify-center flex-shrink-0">
                    <ShoppingBagIcon className="h-5 w-5 text-blue-600" aria-hidden="true" />
                  </div>
                  <div>
                    <p className="font-semibold text-gray-900 text-sm">
                      Order #{order.id.slice(0, 8).toUpperCase()}
                    </p>
                    <p className="text-xs text-gray-500 mt-0.5">
                      {formatDate(order.created_at)} · {order.item_count} item{order.item_count !== 1 ? 's' : ''}
                    </p>
                    <span className={`badge mt-2 ${getOrderStatusColor(order.status)}`}>
                      {capitalizeFirst(order.status)}
                    </span>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <p className="font-bold text-gray-900">{formatPrice(order.total_amount)}</p>
                  <ChevronRightIcon className="h-5 w-5 text-gray-400 group-hover:text-blue-600 transition-colors" aria-hidden="true" />
                </div>
              </Link>
            ))}
          </div>

          <Pagination
            page={data.page}
            totalPages={data.total_pages}
            onPageChange={setPage}
          />
        </>
      )}
    </div>
  );
}
