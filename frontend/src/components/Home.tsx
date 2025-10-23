import { useState, useCallback, useEffect } from "react";
import clsx from "clsx";
import { FileText } from "lucide-react";

import { Header } from "./Header";
import { ChatKitPanel } from "./ChatKitPanel";
import { FinancialDashboard } from "./FinancialDashboard";
import { FinancialDashboardDrawer } from "./FinancialDashboardDrawer";
import { ProfileSettings } from "./ProfileSettings";
import { ProfileSettingsDrawer } from "./ProfileSettingsDrawer";
import { LoginOverlay } from "./LoginOverlay";
import { OnboardingModal } from "./OnboardingModal";
import { ColorScheme } from "../hooks/useColorScheme";
import { useAuth } from "../contexts/AuthContext";
import { useSession } from "../hooks/useSession";
import { useCompany } from "../hooks/useCompany";
import { ChatProvider, useChat } from "../contexts/ChatContext";

export default function Home({
  scheme,
  handleThemeChange,
}: {
  scheme: ColorScheme;
  handleThemeChange: (scheme: ColorScheme) => void;
}) {
  return (
    <ChatProvider>
      <HomeContent scheme={scheme} handleThemeChange={handleThemeChange} />
    </ChatProvider>
  );
}

function HomeContent({
  scheme,
  handleThemeChange,
}: {
  scheme: ColorScheme;
  handleThemeChange: (scheme: ColorScheme) => void;
}) {
  const { session: authSession, loading: authLoading } = useAuth();
  const { needsOnboarding, saveSIICredentials, loading: sessionLoading, isInitialized } = useSession();

  // Lift company state to Home to avoid multiple fetches
  const { company, loading: companyLoading, error: companyError } = useCompany();

  // Chat context for chateable components
  const { setSendUserMessage } = useChat();

  const [sendMessage, setSendMessage] = useState<((text: string, metadata?: Record<string, any>) => Promise<void>) | null>(null);

  // Track active company ID from thread metadata
  const [activeCompanyId, setActiveCompanyId] = useState<string | null>(null);

  // Mobile drawer state
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [isSettingsDrawerOpen, setIsSettingsDrawerOpen] = useState(false);

  // View state: 'dashboard' or 'settings'
  const [currentView, setCurrentView] = useState<'dashboard' | 'settings'>('dashboard');

  // Compute overall loading state - wait until session is initialized
  // This prevents flash of onboarding form while checking session
  const isLoading = authLoading || sessionLoading || !isInitialized;

  // Debug logging
  console.log('[Home] Render state:', {
    authLoading,
    sessionLoading,
    isInitialized,
    needsOnboarding,
    isLoading,
    hasAuthSession: !!authSession,
  });

  const handleSendMessageReady = useCallback((sendFn: (text: string, metadata?: Record<string, any>) => Promise<void>) => {
    setSendMessage(() => sendFn);
    // Also register in ChatContext for chateable components
    setSendUserMessage(sendFn);
  }, [setSendUserMessage]);

  // Refresh dashboard data after each agent response
  const handleResponseEnd = useCallback(() => {
    // Dashboard components will refresh automatically via their hooks
    console.log('[Home] Response ended, dashboard will auto-refresh');
  }, []);

  // Initialize activeCompanyId from company data
  useEffect(() => {
    if (company?.id && !activeCompanyId) {
      console.log('[Home] Initializing company ID:', company.id);
      setActiveCompanyId(company.id);
    }
  }, [company?.id, activeCompanyId]);

  // Handle company_id changes from thread metadata
  const handleCompanyIdChange = useCallback((companyId: string | null) => {
    if (companyId !== activeCompanyId) {
      console.log('[Home] Company ID changed:', companyId);
      setActiveCompanyId(companyId);
    }
  }, [activeCompanyId]);

  // Handle navigation to settings
  const handleNavigateToSettings = useCallback(() => {
    setCurrentView('settings');
  }, []);

  // Handle navigation back to dashboard
  const handleNavigateToDashboard = useCallback(() => {
    setCurrentView('dashboard');
  }, []);

  const containerClass = clsx(
    "h-screen overflow-hidden bg-gradient-to-br transition-colors duration-300",
    scheme === "dark"
      ? "from-slate-900 via-slate-950 to-slate-850 text-slate-100"
      : "from-slate-100 via-white to-slate-200 text-slate-900"
  );

  // Show loading state while checking auth or session status is unknown
  if (isLoading) {
    return (
      <div className={containerClass}>
        <div className="flex h-screen items-center justify-center">
          <div className="flex flex-col items-center gap-4">
            <div className="h-12 w-12 animate-spin rounded-full border-4 border-slate-300 border-t-emerald-600 dark:border-slate-700 dark:border-t-emerald-400" />
            <p className="text-sm text-slate-600 dark:text-slate-400">
              Cargando...
            </p>
          </div>
        </div>
      </div>
    );
  }

  // Not authenticated - show login overlay
  if (!authSession) {
    return (
      <div className={containerClass}>
        <LoginOverlay />
      </div>
    );
  }

  // Authenticated but needs onboarding - show onboarding modal with dashboard background
  if (needsOnboarding) {
    return (
      <div className={containerClass}>
        <div className="mx-auto flex h-screen w-full max-w-7xl flex-col-reverse gap-6 p-6 lg:flex-row">
          {/* Chat Panel Container - Blurred background */}
          <div className="relative flex h-full w-full flex-col lg:w-[30%] lg:flex-none">
            <div className="relative flex flex-1 items-stretch overflow-hidden rounded-3xl bg-white/80 shadow-lg ring-1 ring-slate-200/60 backdrop-blur lg:shadow-xl dark:bg-slate-900/70 dark:shadow-xl lg:dark:shadow-2xl dark:ring-slate-800/60 blur-md pointer-events-none">
              <ChatKitPanel
                theme={scheme}
                onResponseEnd={handleResponseEnd}
                onThemeRequest={handleThemeChange}
                onSendMessageReady={handleSendMessageReady}
                currentCompanyId={activeCompanyId}
                onCompanyIdChange={handleCompanyIdChange}
              />
            </div>
          </div>

          {/* Dashboard - Blurred background */}
          <div className="hidden lg:block lg:flex-1 lg:overflow-hidden blur-md pointer-events-none">
            <FinancialDashboard
              scheme={scheme}
              companyId={activeCompanyId}
              company={company}
              onThemeChange={handleThemeChange}
              onNavigateToSettings={handleNavigateToSettings}
            />
          </div>
        </div>

        {/* Onboarding Modal Overlay */}
        <OnboardingModal
          scheme={scheme}
          onComplete={saveSIICredentials}
        />
      </div>
    );
  }

  // Authenticated - show real content
  return (
    <div className={containerClass}>
      <div className="mx-auto flex h-screen w-full max-w-7xl flex-col-reverse gap-0 p-0 lg:gap-6 lg:p-6 lg:flex-row">
        {/* Chat Panel Container */}
        <div className="relative flex min-h-0 flex-1 w-full flex-col lg:w-[45%] lg:flex-none lg:h-full">
          {/* ChatKit Panel */}
          <div className="relative flex flex-1 items-stretch overflow-hidden lg:rounded-3xl lg:border lg:border-slate-200 bg-white lg:shadow-lg lg:ring-1 lg:ring-slate-200/60 lg:bg-white/80 lg:backdrop-blur lg:shadow-xl dark:bg-slate-900 lg:dark:border-slate-800 lg:dark:shadow-xl lg:dark:bg-slate-900/70 lg:dark:shadow-2xl lg:dark:ring-slate-800/60">
            <ChatKitPanel
              theme={scheme}
              onResponseEnd={handleResponseEnd}
              onThemeRequest={handleThemeChange}
              onSendMessageReady={handleSendMessageReady}
              currentCompanyId={activeCompanyId}
              onCompanyIdChange={handleCompanyIdChange}
            />
          </div>

          {/* Mobile: Buttons to open dashboard or settings */}
          <div className="flex-shrink-0 p-4 flex gap-3 bg-white dark:bg-slate-900 lg:hidden lg:mt-4 lg:p-0 lg:bg-transparent lg:dark:bg-transparent">
            <button
              onClick={() => setIsDrawerOpen(true)}
              className={clsx(
                "flex flex-1 items-center justify-center gap-2 rounded-2xl bg-emerald-600 px-4 py-2 font-medium text-white shadow-lg transition-all hover:bg-emerald-700 active:scale-98 dark:bg-emerald-500 dark:hover:bg-emerald-600",
                "animate-fade-in"
              )}
            >
              <FileText className="h-4 w-4" />
              <span>Dashboard</span>
            </button>
            <button
              onClick={() => setIsSettingsDrawerOpen(true)}
              className={clsx(
                "flex items-center justify-center gap-2 rounded-2xl border-2 border-emerald-600 bg-transparent px-4 py-2 font-medium text-emerald-600 shadow-lg transition-all hover:bg-emerald-50 active:scale-98 dark:border-emerald-500 dark:text-emerald-500 dark:hover:bg-emerald-950/30",
                "animate-fade-in"
              )}
            >
              <svg
                className="h-4 w-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
                />
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                />
              </svg>
            </button>
          </div>
        </div>

        {/* Desktop: Show dashboard or settings based on currentView */}
        <div className="relative hidden h-full flex-col lg:flex lg:flex-1">
          <div className="relative flex flex-1 items-stretch overflow-hidden rounded-3xl border border-slate-200 bg-white/80 shadow-lg ring-1 ring-slate-200/60 backdrop-blur lg:shadow-xl dark:border-slate-800 dark:bg-slate-900/70 dark:shadow-xl lg:dark:shadow-2xl dark:ring-slate-800/60">
            {currentView === 'dashboard' ? (
              <FinancialDashboard
                scheme={scheme}
                companyId={activeCompanyId}
                company={company}
                onThemeChange={handleThemeChange}
                onNavigateToSettings={handleNavigateToSettings}
              />
            ) : (
              <ProfileSettings scheme={scheme} onNavigateBack={handleNavigateToDashboard} company={company} />
            )}
          </div>
        </div>
      </div>

      {/* Mobile: Dashboard Drawer */}
      <FinancialDashboardDrawer
        isOpen={isDrawerOpen}
        onClose={() => setIsDrawerOpen(false)}
        scheme={scheme}
        companyId={activeCompanyId}
        company={company}
      />

      {/* Mobile: Settings Drawer */}
      <ProfileSettingsDrawer
        isOpen={isSettingsDrawerOpen}
        onClose={() => setIsSettingsDrawerOpen(false)}
        scheme={scheme}
        company={company}
      />
    </div>
  );
}
