import { Navigate } from 'react-router-dom';
import { useAuth } from './AuthContext';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

/**
 * ProtectedRoute Component
 *
 * Wraps routes that require authentication. If user is not logged in,
 * redirects to the landing page (/).
 *
 * Usage:
 * ```tsx
 * <Route path="/admin" element={<ProtectedRoute><AdminPage /></ProtectedRoute>} />
 * ```
 */
export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { user, loading } = useAuth();

  // Show nothing while checking auth status
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-gray-600">Cargando...</div>
      </div>
    );
  }

  // Redirect to landing if not authenticated
  if (!user) {
    return <Navigate to="/" replace />;
  }

  // Render protected content if authenticated
  return <>{children}</>;
}
