import { useCallback, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from "@/app/providers/AuthContext";
import { useSession } from "@/shared/hooks/useSession";
import Landing from './Landing';
import Home from "@/features/dashboard/ui/Home";
import { useColorScheme } from "@/shared/hooks/useColorScheme";
import { FizkoLoadingScreen } from "@/shared/ui/feedback/FizkoLoadingScreen";

/**
 * Root component that handles routing logic:
 * - If user is not authenticated: show Landing page
 * - If user is authenticated but needs onboarding: redirect to /onboarding/sii
 * - If user is authenticated and onboarded but needs setup: redirect to /onboarding/setup
 * - If user is fully onboarded: show App (Home)
 */
export default function Root() {
  const navigate = useNavigate();
  const location = useLocation();
  const { session: authSession, loading: authLoading } = useAuth();
  const { needsOnboarding, needsInitialSetup, isInitialized, loading: sessionLoading } = useSession();
  const { scheme, setScheme } = useColorScheme();

  const handleThemeChange = useCallback(
    (value: "light" | "dark") => {
      setScheme(value);
    },
    [setScheme]
  );

  // Handle onboarding redirects
  useEffect(() => {
    // Skip redirect if we're still loading
    if (authLoading || sessionLoading || !isInitialized) {
      return;
    }

    // Skip redirect if not authenticated
    if (!authSession) {
      return;
    }

    // Skip redirect if we're already on an onboarding route
    if (location.pathname.startsWith('/onboarding/')) {
      return;
    }

    // Redirect to SII connection if needed
    if (needsOnboarding) {
      console.log('[HomePage] Redirecting to SII connection');
      navigate('/onboarding/sii', { replace: true });
      return;
    }

    // Redirect to company setup if needed
    if (needsInitialSetup) {
      console.log('[HomePage] Redirecting to company setup');
      navigate('/onboarding/setup', { replace: true });
      return;
    }
  }, [authSession, authLoading, sessionLoading, isInitialized, needsOnboarding, needsInitialSetup, location.pathname, navigate]);

  // Show loading screen while auth or session state is being determined
  if (authLoading || sessionLoading || !isInitialized) {
    return <FizkoLoadingScreen />;
  }

  // Show Home or Landing based directly on session state
  // IMPORTANT: Check onboarding state BEFORE rendering Home to prevent flash
  if (authSession) {
    // If needs onboarding or initial setup, show loading while redirecting
    // This prevents the flash of Home component before redirect
    if (needsOnboarding || needsInitialSetup) {
      return <FizkoLoadingScreen />;
    }

    return <Home scheme={scheme} handleThemeChange={handleThemeChange} />;
  }

  return <Landing />;
}
