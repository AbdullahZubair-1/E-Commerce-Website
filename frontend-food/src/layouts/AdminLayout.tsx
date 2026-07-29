import { Outlet, NavLink, Link, useNavigate } from 'react-router-dom';
import {
  BeakerIcon,
  Squares2X2Icon,
  CubeIcon,
  ShoppingBagIcon,
  ArchiveBoxIcon,
  ArrowRightOnRectangleIcon,
  TagIcon,
  BuildingStorefrontIcon,
  CalendarDaysIcon,
} from '@heroicons/react/24/outline';
import { useAuth } from '@/hooks/useAuth';
import toast from 'react-hot-toast';
import { NotificationBell } from '@/components/admin/NotificationBell';

const navItems = [
  { to: '/admin', label: 'Dashboard', icon: Squares2X2Icon, end: true },
  { to: '/admin/products', label: 'Products', icon: CubeIcon },
  { to: '/admin/inventory', label: 'Inventory', icon: ArchiveBoxIcon },
  { to: '/admin/orders', label: 'Orders', icon: ShoppingBagIcon },
  { to: '/admin/categories', label: 'Categories', icon: TagIcon },
  { to: '/admin/appointments', label: 'Appointments', icon: CalendarDaysIcon },
];

export function AdminLayout() {
  const { user, logout, switchToOwnerStore } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    toast.success('Logged out.');
    navigate('/admin/login');
  };

  const handleSwitchToStore = () => {
    switchToOwnerStore();
    navigate('/');
  };

  return (
    <div className="min-h-screen flex bg-gray-100">
      {/* Sidebar */}
      <aside className="w-64 bg-gray-900 flex flex-col flex-shrink-0" aria-label="Admin navigation">
        <div className="p-5 border-b border-gray-800">
          <Link to="/admin" className="flex items-center gap-2 no-underline">
            <BeakerIcon className="h-7 w-7 text-orange-400" aria-hidden="true" />
            <div>
              <div className="text-white font-bold text-sm">Chemisto Food</div>
              <div className="text-gray-400 text-xs">Admin Panel</div>
            </div>
          </Link>
        </div>

        <nav className="flex-1 p-4 space-y-1">
          {navItems.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors no-underline ${
                  isActive
                    ? 'bg-orange-600 text-white'
                    : 'text-gray-400 hover:bg-gray-800 hover:text-white'
                }`
              }
            >
              <Icon className="h-5 w-5 flex-shrink-0" aria-hidden="true" />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="p-4 border-t border-gray-800">
          <div className="flex items-center gap-3 mb-3 px-3">
            <div className="h-8 w-8 rounded-full bg-orange-600 flex items-center justify-center text-white text-sm font-medium flex-shrink-0">
              {user?.first_name?.[0]}
            </div>
            <div className="text-sm truncate">
              <div className="text-white font-medium">{user?.first_name} {user?.last_name}</div>
              <div className="text-gray-400 text-xs truncate">{user?.email}</div>
            </div>
          </div>
          <button
            onClick={handleSwitchToStore}
            className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-orange-400 hover:bg-gray-800 hover:text-white transition-colors mb-2"
          >
            <BuildingStorefrontIcon className="h-5 w-5" aria-hidden="true" />
            Back to Store
          </button>
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-gray-400 hover:bg-gray-800 hover:text-red-400 transition-colors"
          >
            <ArrowRightOnRectangleIcon className="h-5 w-5" aria-hidden="true" />
            Logout
          </button>
        </div>
      </aside>

      {/* Main content */}
      <div className="flex-1 overflow-auto">
        <div className="flex items-center justify-end px-8 py-4 bg-white border-b border-gray-200">
          <NotificationBell />
        </div>
        <main className="p-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}