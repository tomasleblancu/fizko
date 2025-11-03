import { useCallback } from 'react';
import { useAuth } from "@/app/providers/AuthContext";
import Landing from './Landing';
import Home from "@/features/dashboard/ui/Home";
import { useColorScheme } from "@/shared/hooks/useColorScheme";
import { FizkoLoadingScreen } from "@/shared/ui/feedback/FizkoLoadingScreen";

/**
 * Root component that handles routing logic:
 * - If user is not authenticated: show Landing page
 * - If user is authenticated: show App (Home)
 */
export default function Root() {
  const { session, loading } = useAuth();
  const { scheme, setScheme } = useColorScheme();

  const handleThemeChange = useCallback(
    (value: "light" | "dark") => {
      setScheme(value);
    },
    [setScheme]
  );

  // Show loading screen while auth state is being determined
  if (loading) {
    return <FizkoLoadingScreen />;
  }

  // Show Home or Landing based directly on session state
  // This prevents the flash of Landing page that occurred with the intermediate shouldShowApp state
  return session ? (
    <Home scheme={scheme} handleThemeChange={handleThemeChange} />
  ) : (
    <Landing />
  );
}
