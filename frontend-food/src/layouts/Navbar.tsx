import { Link, NavLink, useNavigate, useLocation } from 'react-router-dom';
import {
  ShoppingCartIcon,
  UserIcon,
  Bars3Icon,
  XMarkIcon,
  BeakerIcon,
  BuildingStorefrontIcon,
  ChatBubbleLeftRightIcon,
} from '@heroicons/react/24/outline';
import { useState } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { useCart } from '@/hooks/useCart';
import toast from 'react-hot-toast';

export function Navbar() {
  const { user, isAuthenticated, logout, switchToOwnerStore, isOwner } = useAuth();
  const { cartCount } = useCart();
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);

  const handleLogout = () => {
    logout();
    toast.success('Logged out successfully.');
    navigate('/login');
    setMobileOpen(false);
  };

  const navLinkClass = ({ isActive }: { isActive: boolean }) =>
    `text-sm font-medium transition-colors ${isActive ? 'text-orange-600' : 'text-gray-600 hover:text-gray-900'}`;

  return (
    <header className="bg-white border-b border-gray-200 sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2 no-underline">
            <BeakerIcon className="h-8 w-8 text-orange-600" aria-hidden="true" />
            <span className="text-xl font-bold text-gray-900">
              Chemisto<span className="text-orange-600"> Food</span>
            </span>
          </Link>

          {/* Desktop Nav */}
          <nav className="hidden md:flex items-center gap-6" aria-label="Main navigation">
            <NavLink to="/" end className={navLinkClass}>Home</NavLink>
            <NavLink to="/products" className={navLinkClass}>Products</NavLink>
          </nav>

          {/* Actions */}
          <div className="flex items-center gap-3">
            {/* Cart */}
            <Link
              to="/cart"
              className="relative p-2 rounded-lg text-gray-600 hover:text-orange-600 hover:bg-orange-50 transition-colors no-underline"
              aria-label={`Cart with ${cartCount} items`}
            >
              <ShoppingCartIcon className="h-6 w-6" />
              {cartCount > 0 && (
                <span className="absolute -top-1 -right-1 bg-orange-600 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center font-medium">
                  {cartCount > 99 ? '99+' : cartCount}
                </span>
              )}
            </Link>

            {/* User menu */}
            {isAuthenticated ? (
              <div className="hidden md:flex items-center gap-2">
                {isOwner && location.pathname !== '/admin' && (
                  <button
                    onClick={() => {
                      switchToOwnerStore();
                      navigate('/admin');
                    }}
                    className="flex items-center gap-2 px-3 py-2 rounded-lg bg-orange-50 text-orange-700 hover:bg-orange-100 transition-colors text-sm"
                  >
                    <BuildingStorefrontIcon className="h-5 w-5" />
                    Admin Panel
                  </button>
                )}
                <Link
                  to="/messages"
                  className="flex items-center gap-2 p-2 rounded-lg text-gray-600 hover:bg-gray-100 transition-colors no-underline text-sm"
                >
                  <ChatBubbleLeftRightIcon className="h-5 w-5" />
                  <span>Messages</span>
                </Link>
                <Link
                  to="/profile"
                  className="flex items-center gap-2 p-2 rounded-lg text-gray-600 hover:bg-gray-100 transition-colors no-underline text-sm"
                >
                  <UserIcon className="h-5 w-5" />
                  <span>{user?.first_name}</span>
                </Link>
                <button
                  onClick={handleLogout}
                  className="text-sm text-gray-500 hover:text-red-600 transition-colors px-2 py-1"
                >
                  Logout
                </button>
              </div>
            ) : (
              <div className="hidden md:flex items-center gap-2">
                <Link to="/login" className="btn-secondary text-sm py-1.5 no-underline">
                  Login
                </Link>
                <Link to="/register" className="btn-primary text-sm py-1.5 no-underline">
                  Register
                </Link>
              </div>
            )}

            {/* Mobile menu button */}
            <button
              className="md:hidden p-2 rounded-lg text-gray-600 hover:bg-gray-100"
              onClick={() => setMobileOpen(!mobileOpen)}
              aria-expanded={mobileOpen}
              aria-label="Toggle mobile menu"
            >
              {mobileOpen ? <XMarkIcon className="h-6 w-6" /> : <Bars3Icon className="h-6 w-6" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile menu */}
      {mobileOpen && (
        <div className="md:hidden border-t border-gray-200 bg-white">
          <nav className="px-4 pt-3 pb-4 space-y-1" aria-label="Mobile navigation">
            <NavLink to="/" end className={navLinkClass} onClick={() => setMobileOpen(false)}>
              <div className="px-3 py-2 rounded-lg hover:bg-gray-100">Home</div>
            </NavLink>
            <NavLink to="/products" className={navLinkClass} onClick={() => setMobileOpen(false)}>
              <div className="px-3 py-2 rounded-lg hover:bg-gray-100">Products</div>
            </NavLink>
            <div className="border-t pt-3 mt-3 space-y-2">
              {isAuthenticated ? (
                <>
                  <Link
                    to="/profile"
                    className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-gray-100 text-sm text-gray-700 no-underline"
                    onClick={() => setMobileOpen(false)}
                  >
                    <UserIcon className="h-5 w-5" />
                    {user?.first_name} {user?.last_name}
                  </Link>
                  <Link
                    to="/messages"
                    className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-gray-100 text-sm text-gray-700 no-underline"
                    onClick={() => setMobileOpen(false)}
                  >
                    <ChatBubbleLeftRightIcon className="h-5 w-5" />
                    Messages
                  </Link>
                  <Link
                    to="/orders"
                    className="block px-3 py-2 rounded-lg hover:bg-gray-100 text-sm text-gray-700 no-underline"
                    onClick={() => setMobileOpen(false)}
                  >
                    My Orders
                  </Link>
                  <button
                    onClick={handleLogout}
                    className="w-full text-left px-3 py-2 rounded-lg hover:bg-red-50 text-sm text-red-600"
                  >
                    Logout
                  </button>
                  {isOwner && location.pathname !== '/admin' && (
                    <button
                      onClick={() => {
                        switchToOwnerStore();
                        navigate('/admin');
                        setMobileOpen(false);
                      }}
                      className="w-full text-left px-3 py-2 rounded-lg hover:bg-orange-50 text-sm text-orange-600"
                    >
                      Admin Panel
                    </button>
                  )}
                </>
              ) : (
                <>
                  <Link
                    to="/login"
                    className="block px-3 py-2 rounded-lg hover:bg-gray-100 text-sm text-gray-700 no-underline"
                    onClick={() => setMobileOpen(false)}
                  >
                    Login
                  </Link>
                  <Link
                    to="/register"
                    className="block px-3 py-2 rounded-lg bg-orange-600 text-white text-sm no-underline text-center"
                    onClick={() => setMobileOpen(false)}
                  >
                    Register
                  </Link>
                </>
              )}
            </div>
          </nav>
        </div>
      )}
    </header>
  );
}