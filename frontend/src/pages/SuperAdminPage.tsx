import { useEffect, useState, useCallback } from 'react';
import axios, { AxiosError } from 'axios';
import { BuildingOffice2Icon, LockClosedIcon, ArrowRightOnRectangleIcon } from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';
import { PageSpinner } from '@/components/ui/Spinner';

// Deliberately a SEPARATE axios instance with no interceptors and its own
// sessionStorage key ('sa_token'). The rest of the app has a delicate
// three-way session system (customer in localStorage, owner in
// sessionStorage, both synced through a shared 'access_token' key read by
// api.ts's interceptor). Reusing that here risks the superadmin's token
// being silently overwritten by whichever customer/owner session is also
// open in this browser. Keeping this fully separate avoids that entirely.
const superadminApi = axios.create({ baseURL: '/api/v1', timeout: 15000 });

const SA_TOKEN_KEY = 'sa_token';

interface SiteStats {
  products: number;
  orders: number;
  customers: number;
  revenue: number;
  categories: number;
  brands: number;
}

interface SiteDashboard {
  id: string;
  slug: string;
  name: string;
  stats: SiteStats;
}

interface DashboardData {
  sites: SiteDashboard[];
  totals: SiteStats;
}

function getErrorMessage(error: unknown): string {
  if (error instanceof AxiosError) {
    const data = error.response?.data as { message?: string } | undefined;
    if (data?.message) return data.message;
    if (error.message) return error.message;
  }
  return 'An unexpected error occurred.';
}

function StatCard({ label, value, prefix }: { label: string; value: number; prefix?: string }) {
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-4">
      <p className="text-xs font-medium text-slate-500 uppercase tracking-wide">{label}</p>
      <p className="text-2xl font-bold text-slate-900 mt-1">
        {prefix}
        {value.toLocaleString()}
      </p>
    </div>
  );
}

export function SuperAdminPage() {
  const [token, setToken] = useState<string | null>(() => sessionStorage.getItem(SA_TOKEN_KEY));
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [loadingDashboard, setLoadingDashboard] = useState(false);

  const fetchDashboard = useCallback(async (activeToken: string) => {
    setLoadingDashboard(true);
    try {
      const res = await superadminApi.get('/superadmin/dashboard', {
        headers: { Authorization: `Bearer ${activeToken}` },
      });
      setDashboard(res.data.data as DashboardData);
    } catch (error) {
      if (error instanceof AxiosError && error.response?.status === 401) {
        // Token expired/invalid -- drop back to the login form.
        sessionStorage.removeItem(SA_TOKEN_KEY);
        setToken(null);
        toast.error('Session expired. Please sign in again.');
      } else {
        toast.error(getErrorMessage(error));
      }
    } finally {
      setLoadingDashboard(false);
    }
  }, []);

  useEffect(() => {
    if (token) fetchDashboard(token);
  }, [token, fetchDashboard]);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const res = await superadminApi.post('/auth/superadmin-login', { email, password });
      const data = res.data.data as { access_token: string };
      sessionStorage.setItem(SA_TOKEN_KEY, data.access_token);
      setToken(data.access_token);
      toast.success('Welcome back!');
    } catch (error) {
      toast.error(getErrorMessage(error));
    } finally {
      setSubmitting(false);
    }
  };

  const handleLogout = () => {
    sessionStorage.removeItem(SA_TOKEN_KEY);
    setToken(null);
    setDashboard(null);
  };

  // ── Login screen ──────────────────────────────────────────────────────────
  if (!token) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center px-4">
        <div className="w-full max-w-md">
          <div className="text-center mb-8">
            <BuildingOffice2Icon className="h-12 w-12 text-emerald-400 mx-auto" aria-hidden="true" />
            <h1 className="text-2xl font-bold text-white mt-4">Organization Admin</h1>
            <p className="text-slate-400 text-sm mt-1">Oversees every site in the organization</p>
          </div>

          <div className="bg-slate-800 rounded-2xl p-8 border border-slate-700">
            <div className="flex items-center justify-center mb-6">
              <div className="h-14 w-14 rounded-full bg-emerald-600/20 border border-emerald-500/30 flex items-center justify-center">
                <LockClosedIcon className="h-6 w-6 text-emerald-400" aria-hidden="true" />
              </div>
            </div>

            <form onSubmit={handleLogin} className="space-y-5">
              <div>
                <label htmlFor="sa-email" className="block text-sm font-medium text-slate-300 mb-1">
                  Email
                </label>
                <input
                  id="sa-email"
                  type="email"
                  required
                  autoComplete="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2.5 text-white text-sm placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                />
              </div>
              <div>
                <label htmlFor="sa-password" className="block text-sm font-medium text-slate-300 mb-1">
                  Password
                </label>
                <input
                  id="sa-password"
                  type="password"
                  required
                  autoComplete="current-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2.5 text-white text-sm placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                />
              </div>
              <button
                type="submit"
                disabled={submitting}
                className="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-medium py-3 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {submitting ? 'Signing in…' : 'Sign In'}
              </button>
            </form>
          </div>
        </div>
      </div>
    );
  }

  // ── Dashboard ────────────────────────────────────────────────────────────
  if (loadingDashboard && !dashboard) {
    return <PageSpinner />;
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="bg-slate-900 text-white">
        <div className="max-w-6xl mx-auto px-6 py-5 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <BuildingOffice2Icon className="h-7 w-7 text-emerald-400" aria-hidden="true" />
            <div>
              <p className="font-semibold">Organization Admin</p>
              <p className="text-xs text-slate-400">Every site, at a glance</p>
            </div>
          </div>
          <button
            type="button"
            onClick={handleLogout}
            className="inline-flex items-center gap-2 text-sm text-slate-300 hover:text-white transition-colors"
          >
            <ArrowRightOnRectangleIcon className="h-4 w-4" aria-hidden="true" />
            Sign out
          </button>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-6 py-8">
        {dashboard && (
          <>
            <h2 className="text-lg font-semibold text-slate-900 mb-4">Organization totals</h2>
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4 mb-10">
              <StatCard label="Products" value={dashboard.totals.products} />
              <StatCard label="Orders" value={dashboard.totals.orders} />
              <StatCard label="Customers" value={dashboard.totals.customers} />
              <StatCard label="Revenue" value={dashboard.totals.revenue} prefix="$" />
              <StatCard label="Categories" value={dashboard.totals.categories} />
              <StatCard label="Brands" value={dashboard.totals.brands} />
            </div>

            <h2 className="text-lg font-semibold text-slate-900 mb-4">By site</h2>
            <div className="space-y-6">
              {dashboard.sites.map((site) => (
                <div key={site.id} className="bg-white rounded-2xl border border-slate-200 overflow-hidden">
                  <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between">
                    <div>
                      <p className="font-semibold text-slate-900">{site.name}</p>
                      <p className="text-xs text-slate-500">{site.slug}</p>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4 p-5">
                    <StatCard label="Products" value={site.stats.products} />
                    <StatCard label="Orders" value={site.stats.orders} />
                    <StatCard label="Customers" value={site.stats.customers} />
                    <StatCard label="Revenue" value={site.stats.revenue} prefix="$" />
                    <StatCard label="Categories" value={site.stats.categories} />
                    <StatCard label="Brands" value={site.stats.brands} />
                  </div>
                </div>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
}