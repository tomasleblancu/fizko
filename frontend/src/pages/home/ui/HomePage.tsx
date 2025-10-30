import { useEffect, useState } from 'react';
import { useAuth } from "@/app/providers/AuthContext";
import Landing from './Landing';
import Home from "@/features/dashboard/ui/Home";
import { useColorScheme } from "@/shared/hooks/useColorScheme";
import { useCallback } from 'react';

/**
 * Root component that handles routing logic:
 * - If user is not authenticated: show Landing page
 * - If user is authenticated: show App (Home)
 */
export default function Root() {
  const { session, loading } = useAuth();
  const { scheme, setScheme } = useColorScheme();
  const [shouldShowApp, setShouldShowApp] = useState(false);

  const handleThemeChange = useCallback(
    (value: "light" | "dark") => {
      setScheme(value);
    },
    [setScheme]
  );

  useEffect(() => {
    // Wait until auth is loaded
    if (loading) return;

    if (session) {
      // User is logged in, show the app
      setShouldShowApp(true);
    } else {
      // User is not logged in, show landing
      setShouldShowApp(false);
    }
  }, [session, loading]);

  // Show nothing while loading auth state
  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center bg-gradient-to-br from-blue-50 via-white to-purple-50 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900">
        <div className="text-center">
          <div className="mb-4 inline-block h-12 w-12 animate-spin rounded-full border-4 border-solid border-blue-600 border-r-transparent"></div>
          <p className="text-slate-600 dark:text-slate-400">Cargando...</p>
        </div>
      </div>
    );
  }

  // Show Landing or Home based on auth state
  return shouldShowApp ? (
    <Home scheme={scheme} handleThemeChange={handleThemeChange} />
  ) : (
    <Landing />
  );
}
