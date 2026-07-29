import { useState, useEffect } from 'react';
import {
  CubeIcon,
  ShoppingBagIcon,
  UsersIcon,
  CurrencyDollarIcon,
  TagIcon,
  ArchiveBoxIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/outline';
import { Link } from 'react-router-dom';
import { PageSpinner } from '@/components/ui/Spinner';
import type { DashboardStats } from '@/types';
import { userService } from '@/services/user.service';
import { formatPrice } from '@/utils/format';

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: React.ComponentType<{ className?: string }>;
  iconBg: string;
  iconColor: string;
  href?: string;
}

function StatCard({ title, value, subtitle, icon: Icon, iconBg, iconColor, href }: StatCardProps) {
  const content = (
    <div className="card p-6 flex items-start justify-between hover:shadow-md transition-shadow">
      <div>
        <p className="text-sm font-medium text-gray-500 mb-1">{title}</p>
        <p className="text-3xl font-bold text-gray-900">{value}</p>
        {subtitle && <p className="text-xs text-gray-400 mt-1">{subtitle}</p>}
      </div>
      <div className={`h-12 w-12 rounded-xl flex items-center justify-center flex-shrink-0 ${iconBg}`}>
        <Icon className={`h-6 w-6 ${iconColor}`} aria-hidden="true" />
      </div>
    </div>
  );

  if (href) {
    return <Link to={href} className="no-underline block">{content}</Link>;
  }
  return content;
}

export function AdminDashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    userService.getDashboardStats()
      .then(setStats)
      .catch(() => setStats(null))
      .finally(() => setIsLoading(false));
  }, []);

  if (isLoading) return <PageSpinner />;
  if (!stats) return (
    <div className="text-center py-16 text-gray-500">Failed to load dashboard statistics.</div>
  );

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-2">Dashboard</h1>
      <p className="text-gray-500 text-sm mb-8">Welcome back! Here's what's happening in your store.</p>

      {/* Stats grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatCard
          title="Total Revenue"
          value={formatPrice(stats.revenue.total)}
          subtitle="From shipped & delivered orders"
          icon={CurrencyDollarIcon}
          iconBg="bg-green-50"
          iconColor="text-green-600"
        />
        <StatCard
          title="Total Orders"
          value={stats.orders.total}
          subtitle={`${stats.orders.pending} pending`}
          icon={ShoppingBagIcon}
          iconBg="bg-orange-50"
          iconColor="text-orange-600"
          href="/admin/orders"
        />
        <StatCard
          title="Total Customers"
          value={stats.customers.total}
          icon={UsersIcon}
          iconBg="bg-purple-50"
          iconColor="text-purple-600"
        />
        <StatCard
          title="Active Products"
          value={stats.products.active}
          subtitle={`${stats.products.total} total`}
          icon={CubeIcon}
          iconBg="bg-orange-50"
          iconColor="text-orange-600"
          href="/admin/products"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Catalog summary */}
        <div className="card p-6">
          <h2 className="font-semibold text-gray-900 mb-4">Catalog</h2>
          <div className="space-y-3">
            <div className="flex items-center justify-between py-2 border-b border-gray-100">
              <div className="flex items-center gap-3">
                <div className="h-8 w-8 rounded-lg bg-orange-50 flex items-center justify-center">
                  <TagIcon className="h-4 w-4 text-orange-600" aria-hidden="true" />
                </div>
                <span className="text-sm text-gray-700">Categories</span>
              </div>
              <span className="font-semibold text-gray-900">{stats.catalog.categories}</span>
            </div>
            <div className="flex items-center justify-between py-2 border-b border-gray-100">
              <div className="flex items-center gap-3">
                <div className="h-8 w-8 rounded-lg bg-purple-50 flex items-center justify-center">
                  <CubeIcon className="h-4 w-4 text-purple-600" aria-hidden="true" />
                </div>
                <span className="text-sm text-gray-700">Brands</span>
              </div>
              <span className="font-semibold text-gray-900">{stats.catalog.brands}</span>
            </div>
            <div className="flex items-center justify-between py-2">
              <div className="flex items-center gap-3">
                <div className="h-8 w-8 rounded-lg bg-gray-50 flex items-center justify-center">
                  <ArchiveBoxIcon className="h-4 w-4 text-gray-600" aria-hidden="true" />
                </div>
                <span className="text-sm text-gray-700">Total Products</span>
              </div>
              <span className="font-semibold text-gray-900">{stats.products.total}</span>
            </div>
          </div>
        </div>

        {/* Alerts */}
        <div className="card p-6">
          <h2 className="font-semibold text-gray-900 mb-4">Alerts</h2>
          <div className="space-y-3">
            {stats.products.low_stock > 0 ? (
              <Link
                to="/admin/inventory"
                className="flex items-center gap-3 p-3 bg-orange-50 border border-orange-200 rounded-xl hover:bg-orange-100 transition-colors no-underline"
              >
                <ExclamationTriangleIcon className="h-5 w-5 text-orange-500 flex-shrink-0" aria-hidden="true" />
                <div>
                  <p className="text-sm font-medium text-orange-800">
                    {stats.products.low_stock} product{stats.products.low_stock !== 1 ? 's' : ''} low on stock
                  </p>
                  <p className="text-xs text-orange-600">Click to manage inventory</p>
                </div>
              </Link>
            ) : (
              <div className="flex items-center gap-3 p-3 bg-green-50 border border-green-200 rounded-xl">
                <div className="h-5 w-5 rounded-full bg-green-500 flex items-center justify-center flex-shrink-0">
                  <span className="text-white text-xs">✓</span>
                </div>
                <p className="text-sm text-green-800 font-medium">All products are well stocked</p>
              </div>
            )}
            {stats.orders.pending > 0 ? (
              <Link
                to="/admin/orders"
                className="flex items-center gap-3 p-3 bg-orange-50 border border-orange-200 rounded-xl hover:bg-orange-100 transition-colors no-underline"
              >
                <ShoppingBagIcon className="h-5 w-5 text-orange-500 flex-shrink-0" aria-hidden="true" />
                <div>
                  <p className="text-sm font-medium text-orange-800">
                    {stats.orders.pending} pending order{stats.orders.pending !== 1 ? 's' : ''}
                  </p>
                  <p className="text-xs text-orange-600">Click to review orders</p>
                </div>
              </Link>
            ) : (
              <div className="flex items-center gap-3 p-3 bg-gray-50 border border-gray-200 rounded-xl">
                <ShoppingBagIcon className="h-5 w-5 text-gray-400 flex-shrink-0" aria-hidden="true" />
                <p className="text-sm text-gray-600">No pending orders</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Quick actions */}
      <div className="mt-8">
        <h2 className="font-semibold text-gray-900 mb-4">Quick Actions</h2>
        <div className="flex flex-wrap gap-3">
          <Link to="/admin/products" className="btn-primary no-underline text-sm">
            + Add Product
          </Link>
          <Link to="/admin/categories" className="btn-secondary no-underline text-sm">
            Manage Categories
          </Link>
          <Link to="/admin/orders" className="btn-secondary no-underline text-sm">
            View Orders
          </Link>
          <Link to="/admin/inventory" className="btn-secondary no-underline text-sm">
            Update Inventory
          </Link>
        </div>
      </div>
    </div>
  );
}
