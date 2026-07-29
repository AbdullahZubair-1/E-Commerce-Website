import { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Link, useNavigate } from 'react-router-dom';
import { BeakerIcon, LockClosedIcon } from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';
import { useAuth } from '@/hooks/useAuth';
import { authService } from '@/services/auth.service';
import { getErrorMessage } from '@/services/api';

const schema = z.object({
  email: z.string().email('Please enter a valid email'),
  password: z.string().min(1, 'Password is required'),
});

type FormData = z.infer<typeof schema>;

export function AdminLoginPage() {
  const { isAuthenticated, isOwner, setOwnerSession } = useAuth();
  const navigate = useNavigate();
  const [submitting, setSubmitting] = useState(false);

  // Already authenticated as owner — go straight to dashboard
  useEffect(() => {
    if (isAuthenticated && isOwner) {
      navigate('/admin', { replace: true });
    }
    // If authenticated but NOT owner, don't redirect — let them try owner creds
  }, [isAuthenticated, isOwner, navigate]);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormData>({ resolver: zodResolver(schema) });

  const onSubmit = async (data: FormData) => {
    setSubmitting(true);
    try {
      // Call the API directly — do NOT use the shared login() which would
      // overwrite the customer session if credentials belong to a regular user.
      const result = await authService.login(data);

      if (!result.user.is_owner) {
        // Valid credentials but not the owner — reject silently
        toast.error('Access denied. These credentials are not for the admin panel.');
        return;
      }

      // Owner confirmed — commit to the auth context via setUser which
      // writes to the owner-specific localStorage keys (never touches customer session)
      setOwnerSession(result.user, result.access_token);

      toast.success('Welcome back, Owner!');
      navigate('/admin', { replace: true });
    } catch (err) {
      toast.error(getErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <Link to="/" className="inline-flex items-center gap-2 no-underline">
            <BeakerIcon className="h-12 w-12 text-blue-400" aria-hidden="true" />
          </Link>
          <h1 className="text-2xl font-bold text-white mt-4">Admin Login</h1>
          <p className="text-gray-400 text-sm mt-1">CHEMISTO's Store — Owner Portal</p>
        </div>

        <div className="bg-gray-800 rounded-2xl p-8 border border-gray-700">
          <div className="flex items-center justify-center mb-6">
            <div className="h-14 w-14 rounded-full bg-blue-600/20 border border-blue-500/30 flex items-center justify-center">
              <LockClosedIcon className="h-6 w-6 text-blue-400" aria-hidden="true" />
            </div>
          </div>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-5" noValidate>
            <div>
              <label htmlFor="adm-email" className="block text-sm font-medium text-gray-300 mb-1">
                Email
              </label>
              <input
                id="adm-email"
                type="email"
                autoComplete="email"
                className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2.5 text-white text-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                {...register('email')}
                aria-invalid={!!errors.email}
              />
              {errors.email && (
                <p className="text-red-400 text-xs mt-1" role="alert">
                  {errors.email.message}
                </p>
              )}
            </div>

            <div>
              <label htmlFor="adm-password" className="block text-sm font-medium text-gray-300 mb-1">
                Password
              </label>
              <input
                id="adm-password"
                type="password"
                autoComplete="current-password"
                className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2.5 text-white text-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                {...register('password')}
                aria-invalid={!!errors.password}
              />
              {errors.password && (
                <p className="text-red-400 text-xs mt-1" role="alert">
                  {errors.password.message}
                </p>
              )}
            </div>

            <button
              type="submit"
              disabled={submitting}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {submitting ? 'Signing in…' : 'Sign In as Owner'}
            </button>
          </form>

          <p className="text-center text-sm text-gray-500 mt-6">
            <Link to="/" className="text-gray-400 hover:text-white no-underline transition-colors">
              ← Back to Store
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
