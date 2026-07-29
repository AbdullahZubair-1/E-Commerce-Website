import { Link } from 'react-router-dom';
import { BeakerIcon } from '@heroicons/react/24/outline';
import { useAuth } from '@/hooks/useAuth';

export function Footer() {
  const { isAuthenticated } = useAuth();

  return (
    <footer className="bg-gray-900 text-gray-300 mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* Brand */}
          <div>
            <div className="flex items-center gap-2 mb-3">
              <BeakerIcon className="h-7 w-7 text-orange-400" aria-hidden="true" />
              <span className="text-white font-bold text-lg">Chemisto Food</span>
            </div>
            <p className="text-sm text-gray-400 leading-relaxed">
              Your trusted source for high-quality laboratory chemicals, equipment, and supplies.
            </p>
          </div>

          {/* Shop */}
          <div>
            <h3 className="text-white font-semibold mb-3 text-sm uppercase tracking-wide">Shop</h3>
            <ul className="space-y-2 text-sm">
              <li>
                <Link to="/products" className="hover:text-white transition-colors no-underline text-gray-400">
                  All Products
                </Link>
              </li>
              <li>
                <Link to="/products?category=laboratory-chemicals" className="hover:text-white transition-colors no-underline text-gray-400">
                  Lab Chemicals
                </Link>
              </li>
              <li>
                <Link to="/products?category=safety-equipment" className="hover:text-white transition-colors no-underline text-gray-400">
                  Safety Equipment
                </Link>
              </li>
              <li>
                <Link to="/products?category=glassware" className="hover:text-white transition-colors no-underline text-gray-400">
                  Glassware
                </Link>
              </li>
            </ul>
          </div>

          {/* Account — context-aware */}
          <div>
            <h3 className="text-white font-semibold mb-3 text-sm uppercase tracking-wide">Account</h3>
            <ul className="space-y-2 text-sm">
              {isAuthenticated ? (
                <>
                  <li>
                    <Link to="/profile" className="hover:text-white transition-colors no-underline text-gray-400">
                      My Profile
                    </Link>
                  </li>
                  <li>
                    <Link to="/orders" className="hover:text-white transition-colors no-underline text-gray-400">
                      Order History
                    </Link>
                  </li>
                  <li>
                    <Link to="/cart" className="hover:text-white transition-colors no-underline text-gray-400">
                      My Cart
                    </Link>
                  </li>
                </>
              ) : (
                <>
                  <li>
                    <Link to="/register" className="hover:text-white transition-colors no-underline text-gray-400">
                      Create Account
                    </Link>
                  </li>
                  <li>
                    <Link to="/login" className="hover:text-white transition-colors no-underline text-gray-400">
                      Login
                    </Link>
                  </li>
                  <li>
                    <Link to="/orders" className="hover:text-white transition-colors no-underline text-gray-400">
                      Order History
                    </Link>
                  </li>
                </>
              )}
            </ul>
          </div>
        </div>

        <div className="border-t border-gray-800 mt-8 pt-8 text-center text-sm text-gray-500">
          <p>© {new Date().getFullYear()} Chemisto Food. All rights reserved.</p>
        </div>
      </div>
    </footer>
  );
}
