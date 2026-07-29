import { useState, useEffect, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  ArrowLeftIcon,
  CheckCircleIcon,
  ClockIcon,
  TruckIcon,
  CubeIcon,
  HomeIcon,
  XCircleIcon,
  ArrowPathIcon,
  MapPinIcon,
  DocumentTextIcon,
  ShoppingBagIcon,
} from '@heroicons/react/24/outline';
import { CheckCircleIcon as CheckCircleSolid } from '@heroicons/react/24/solid';
import { PageSpinner } from '@/components/ui/Spinner';
import type { Order, OrderStatus } from '@/types';
import { orderService } from '@/services/order.service';
import { formatPrice, formatDateTime, formatDate } from '@/utils/format';

// ── Status step definitions ────────────────────────────────────────────────────
interface StatusStep {
  key: OrderStatus | 'pending';
  label: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
}

const STATUS_STEPS: StatusStep[] = [
  {
    key: 'pending',
    label: 'Order Placed',
    description: 'Your order has been received and is awaiting confirmation.',
    icon: ClockIcon,
  },
  {
    key: 'confirmed',
    label: 'Confirmed',
    description: 'Your order has been confirmed and is being prepared.',
    icon: CheckCircleIcon,
  },
  {
    key: 'processing',
    label: 'Processing',
    description: 'Your items are being packed and prepared for shipment.',
    icon: CubeIcon,
  },
  {
    key: 'shipped',
    label: 'Shipped',
    description: 'Your order is on its way to you.',
    icon: TruckIcon,
  },
  {
    key: 'delivered',
    label: 'Delivered',
    description: 'Your order has been delivered successfully.',
    icon: HomeIcon,
  },
];

// ── Helpers ────────────────────────────────────────────────────────────────────
function getStepIndex(status: OrderStatus): number {
  const map: Record<string, number> = {
    pending: 0,
    confirmed: 1,
    processing: 2,
    shipped: 3,
    delivered: 4,
    cancelled: -1,
  };
  return map[status] ?? 0;
}

function getStatusBannerStyle(status: OrderStatus) {
  if (status === 'delivered')
    return 'bg-green-50 border-green-200 text-green-800';
  if (status === 'cancelled')
    return 'bg-red-50 border-red-200 text-red-800';
  if (status === 'shipped')
    return 'bg-indigo-50 border-indigo-200 text-indigo-800';
  return 'bg-blue-50 border-blue-200 text-blue-800';
}

function getStatusMessage(status: OrderStatus): string {
  const messages: Record<OrderStatus, string> = {
    pending: 'Waiting for confirmation from the store.',
    confirmed: 'Great news — your order is confirmed!',
    processing: 'Your order is being prepared for shipment.',
    shipped: 'Your order is on its way!',
    delivered: 'Your order has been delivered. Enjoy!',
    cancelled: 'This order has been cancelled.',
  };
  return messages[status] ?? '';
}

// ── Component ──────────────────────────────────────────────────────────────────
export function OrderDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [order, setOrder] = useState<Order | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const loadOrder = useCallback(async (showSpinner = true) => {
    if (!id) return;
    if (showSpinner) setIsLoading(true);
    else setIsRefreshing(true);
    try {
      const data = await orderService.getMyOrder(id);
      setOrder(data);
    } catch {
      // On a silent background poll, keep the last known state visible.
      // Only clear the order on the initial load (showSpinner=true).
      if (showSpinner) setOrder(null);
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }, [id]);

  // Initial load
  useEffect(() => { loadOrder(); }, [loadOrder]);

  // Poll every 15 seconds for status updates.
  // Always keeps polling — clears itself when the component unmounts.
  useEffect(() => {
    if (!id) return;
    const interval = setInterval(() => {
      loadOrder(false); // silent refresh, no spinner
    }, 15000);
    return () => clearInterval(interval);
  }, [id, loadOrder]);

  // Refresh when the browser window regains focus.
  useEffect(() => {
    if (!id) return;
    const handleFocus = () => loadOrder(false);
    window.addEventListener('focus', handleFocus);
    return () => window.removeEventListener('focus', handleFocus);
  }, [id, loadOrder]);

  if (isLoading) return <PageSpinner />;

  if (!order) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-16 text-center">
        <ShoppingBagIcon className="h-16 w-16 text-gray-300 mx-auto mb-4" />
        <h2 className="text-2xl font-bold text-gray-700 mb-2">Order not found</h2>
        <p className="text-gray-500 mb-6">This order doesn't exist or doesn't belong to your account.</p>
        <Link to="/orders" className="btn-primary no-underline inline-block">
          Back to Orders
        </Link>
      </div>
    );
  }

  const currentStep = getStepIndex(order.status);
  const isCancelled = order.status === 'cancelled';
  const isDelivered = order.status === 'delivered';

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Back link */}
      <nav className="mb-6" aria-label="Breadcrumb">
        <Link
          to="/orders"
          className="inline-flex items-center gap-1 text-gray-500 hover:text-gray-700 text-sm no-underline transition-colors"
        >
          <ArrowLeftIcon className="h-4 w-4" />
          Back to My Orders
        </Link>
      </nav>

      {/* Header */}
      <div className="flex items-start justify-between mb-6 flex-wrap gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            Order #{order.id.slice(0, 8).toUpperCase()}
          </h1>
          <p className="text-gray-500 text-sm mt-1">
            Placed on {formatDateTime(order.created_at)}
          </p>
        </div>
        <button
          onClick={() => loadOrder(false)}
          disabled={isRefreshing}
          className="flex items-center gap-2 text-sm text-blue-600 hover:text-blue-800 border border-blue-200 hover:border-blue-400 rounded-lg px-3 py-1.5 transition-colors disabled:opacity-50"
          aria-label="Refresh order status"
        >
          <ArrowPathIcon className={`h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
          Refresh Status
        </button>
      </div>

      {/* Status banner */}
      <div className={`border rounded-xl p-4 mb-6 flex items-center gap-3 ${getStatusBannerStyle(order.status)}`}>
        {isCancelled ? (
          <XCircleIcon className="h-6 w-6 flex-shrink-0 text-red-500" aria-hidden="true" />
        ) : isDelivered ? (
          <CheckCircleSolid className="h-6 w-6 flex-shrink-0 text-green-500" aria-hidden="true" />
        ) : (
          <TruckIcon className="h-6 w-6 flex-shrink-0 text-blue-500" aria-hidden="true" />
        )}
        <div>
          <p className="font-semibold capitalize">{order.status}</p>
          <p className="text-sm opacity-80">{getStatusMessage(order.status)}</p>
        </div>
      </div>

      {/* ── Status Timeline ─────────────────────────────────────────────────── */}
      {!isCancelled ? (
        <div className="card p-6 mb-6">
          <h2 className="font-semibold text-gray-900 mb-6">Order Progress</h2>
          <ol className="relative" aria-label="Order status timeline">
            {STATUS_STEPS.map((step, idx) => {
              const isCompleted = idx < currentStep;
              const isCurrent = idx === currentStep;
              const isPending = idx > currentStep;
              const isLast = idx === STATUS_STEPS.length - 1;
              const Icon = step.icon;

              return (
                <li key={step.key} className={`flex gap-4 ${!isLast ? 'pb-8' : ''}`}>
                  {/* Line + icon column */}
                  <div className="flex flex-col items-center flex-shrink-0">
                    <div
                      className={`h-10 w-10 rounded-full flex items-center justify-center border-2 z-10 transition-all duration-300 ${
                        isCompleted
                          ? 'bg-blue-600 border-blue-600'
                          : isCurrent
                          ? 'bg-white border-blue-600 shadow-md shadow-blue-100'
                          : 'bg-white border-gray-200'
                      }`}
                      aria-hidden="true"
                    >
                      {isCompleted ? (
                        <CheckCircleSolid className="h-5 w-5 text-white" />
                      ) : (
                        <Icon
                          className={`h-5 w-5 ${
                            isCurrent ? 'text-blue-600' : 'text-gray-300'
                          }`}
                        />
                      )}
                    </div>
                    {/* Vertical connector */}
                    {!isLast && (
                      <div
                        className={`w-0.5 flex-1 mt-1 transition-colors duration-300 ${
                          isCompleted ? 'bg-blue-600' : 'bg-gray-200'
                        }`}
                        aria-hidden="true"
                      />
                    )}
                  </div>

                  {/* Text column */}
                  <div className={`pt-1.5 ${!isLast ? 'pb-8' : ''}`}>
                    <p
                      className={`font-semibold text-sm transition-colors ${
                        isCompleted || isCurrent ? 'text-gray-900' : 'text-gray-400'
                      }`}
                    >
                      {step.label}
                      {isCurrent && (
                        <span className="ml-2 badge bg-blue-100 text-blue-700 text-xs">
                          Current
                        </span>
                      )}
                      {isCompleted && (
                        <span className="ml-2 badge bg-green-100 text-green-700 text-xs">
                          Done
                        </span>
                      )}
                    </p>
                    <p
                      className={`text-sm mt-0.5 ${
                        isPending ? 'text-gray-300' : 'text-gray-500'
                      }`}
                    >
                      {step.description}
                    </p>
                    {/* Show timestamp for current step */}
                    {isCurrent && (
                      <p className="text-xs text-blue-500 mt-1">
                        Updated: {formatDateTime(order.updated_at)}
                      </p>
                    )}
                    {isCompleted && idx === 0 && (
                      <p className="text-xs text-gray-400 mt-1">
                        {formatDate(order.created_at)}
                      </p>
                    )}
                  </div>
                </li>
              );
            })}
          </ol>
        </div>
      ) : (
        /* Cancelled state */
        <div className="card p-6 mb-6 border-red-100">
          <div className="flex items-center gap-3 text-red-600 mb-2">
            <XCircleIcon className="h-6 w-6" aria-hidden="true" />
            <h2 className="font-semibold">Order Cancelled</h2>
          </div>
          <p className="text-sm text-gray-500">
            This order was cancelled. If you have questions, please contact support.
          </p>
        </div>
      )}

      {/* ── Two column: shipping + summary ──────────────────────────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        {/* Shipping address */}
        <div className="card p-5">
          <div className="flex items-center gap-2 mb-3">
            <MapPinIcon className="h-5 w-5 text-gray-400" aria-hidden="true" />
            <h2 className="font-semibold text-gray-900">Shipping Address</h2>
          </div>
          <p className="text-gray-600 text-sm whitespace-pre-line leading-relaxed">
            {order.shipping_address}
          </p>
        </div>

        {/* Order notes */}
        {order.notes ? (
          <div className="card p-5">
            <div className="flex items-center gap-2 mb-3">
              <DocumentTextIcon className="h-5 w-5 text-gray-400" aria-hidden="true" />
              <h2 className="font-semibold text-gray-900">Order Notes</h2>
            </div>
            <p className="text-gray-600 text-sm">{order.notes}</p>
          </div>
        ) : (
          <div className="card p-5 bg-gray-50">
            <div className="flex items-center gap-2 mb-3">
              <DocumentTextIcon className="h-5 w-5 text-gray-300" aria-hidden="true" />
              <h2 className="font-semibold text-gray-400">No Notes</h2>
            </div>
            <p className="text-gray-400 text-sm">No special instructions for this order.</p>
          </div>
        )}
      </div>

      {/* ── Items ───────────────────────────────────────────────────────────── */}
      <div className="card p-6">
        <div className="flex items-center gap-2 mb-4">
          <ShoppingBagIcon className="h-5 w-5 text-gray-400" aria-hidden="true" />
          <h2 className="font-semibold text-gray-900">
            Items Ordered
            <span className="ml-2 text-sm font-normal text-gray-400">
              ({order.items.length} item{order.items.length !== 1 ? 's' : ''})
            </span>
          </h2>
        </div>

        <div className="space-y-1">
          {order.items.map((item, idx) => (
            <div
              key={item.id}
              className={`flex items-center justify-between py-3 ${
                idx < order.items.length - 1 ? 'border-b border-gray-100' : ''
              }`}
            >
              <div className="flex items-center gap-3">
                {/* Index circle */}
                <div className="h-7 w-7 rounded-full bg-blue-50 flex items-center justify-center flex-shrink-0">
                  <span className="text-xs font-medium text-blue-600">{idx + 1}</span>
                </div>
                <div>
                  <p className="font-medium text-gray-900 text-sm">{item.product_name}</p>
                  <p className="text-xs text-gray-400 mt-0.5">
                    {formatPrice(item.product_price)} × {item.quantity}
                  </p>
                </div>
              </div>
              <p className="font-semibold text-gray-900 text-sm flex-shrink-0">
                {formatPrice(item.subtotal)}
              </p>
            </div>
          ))}
        </div>

        {/* Total */}
        <div className="border-t border-gray-200 mt-4 pt-4">
          <div className="flex justify-between text-sm text-gray-500 mb-1">
            <span>Subtotal</span>
            <span>{formatPrice(order.total_amount)}</span>
          </div>
          <div className="flex justify-between text-sm text-gray-500 mb-3">
            <span>Shipping</span>
            <span className="text-green-600">Free</span>
          </div>
          <div className="flex justify-between font-bold text-lg">
            <span>Total</span>
            <span className="text-blue-600">{formatPrice(order.total_amount)}</span>
          </div>
        </div>
      </div>

      {/* Continue shopping */}
      <div className="mt-6 text-center">
        <Link
          to="/products"
          className="text-sm text-blue-600 hover:text-blue-800 no-underline font-medium"
        >
          Continue Shopping →
        </Link>
      </div>
    </div>
  );
}
