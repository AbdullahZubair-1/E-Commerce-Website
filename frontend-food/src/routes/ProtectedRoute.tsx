import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import { PageSpinner } from '@/components/ui/Spinner';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requireOwner?: boolean;
  redirectTo?: string;
}

export function ProtectedRoute({
  children,
  requireOwner = false,
  redirectTo = '/login',
}: ProtectedRouteProps) {
  const { isAuthenticated, isOwner, isLoading } = useAuth();
  const location = useLocation();

  // While auth state is being restored from localStorage, show a spinner.
  // Never redirect until we know for certain what the auth state is.
  if (isLoading) {
    return <PageSpinner />;
  }

  if (!isAuthenticated) {
    return (
      <Navigate
        to={redirectTo}
        state={{ from: location }}
        replace
      />
    );
  }

  // Authenticated but not the owner — redirect away from admin routes
  if (requireOwner && !isOwner) {
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
}
