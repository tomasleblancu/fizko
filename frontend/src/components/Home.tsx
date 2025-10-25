import { useState, useCallback, useEffect } from "react";
import clsx from "clsx";
import { Home as HomeIcon, Users, Settings } from "lucide-react";

import { Header } from "./Header";
import { ChatKitPanel } from "./ChatKitPanel";
import { FinancialDashboard } from "./FinancialDashboard";
import { FinancialDashboardDrawer } from "./FinancialDashboardDrawer";
import { ProfileSettings } from "./ProfileSettings";
import { ProfileSettingsDrawer } from "./ProfileSettingsDrawer";
import { Contacts } from "./Contacts";
import { ContactsDrawer } from "./ContactsDrawer";
import { LoginOverlay } from "./LoginOverlay";
import { OnboardingModal } from "./OnboardingModal";
import type { ViewType } from "./layout/NavigationPills";
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
  const { setSendUserMessage, setOnChateableClick } = useChat();

  const [sendMessage, setSendMessage] = useState<((text: string, metadata?: Record<string, any>) => Promise<void>) | null>(null);

  // Track active company ID from thread metadata
  const [activeCompanyId, setActiveCompanyId] = useState<string | null>(null);

  // Mobile drawer state
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [isContactsDrawerOpen, setIsContactsDrawerOpen] = useState(false);
  const [isSettingsDrawerOpen, setIsSettingsDrawerOpen] = useState(false);

  // View state: 'dashboard', 'contacts', or 'settings'
  const [currentView, setCurrentView] = useState<ViewType>('dashboard');

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

  // Register callback to close drawers when chateable is clicked
  useEffect(() => {
    const closeAllDrawers = () => {
      setIsDrawerOpen(false);
      setIsContactsDrawerOpen(false);
      setIsSettingsDrawerOpen(false);
    };
    setOnChateableClick(closeAllDrawers);
  }, [setOnChateableClick]);

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

  // Handle navigation between views
  const handleNavigateToContacts = useCallback(() => {
    setCurrentView('contacts');
  }, []);

  const handleNavigateToSettings = useCallback(() => {
    setCurrentView('settings');
  }, []);

  const handleNavigateToDashboard = useCallback(() => {
    setCurrentView('dashboard');
  }, []);

  const containerClass = clsx(
    "h-[100dvh] overflow-hidden bg-gradient-to-br transition-colors duration-300",
    scheme === "dark"
      ? "from-slate-900 via-slate-950 to-slate-850 text-slate-100"
      : "from-slate-100 via-white to-slate-200 text-slate-900"
  );

  // Show loading state while checking auth or session status is unknown
  if (isLoading) {
    return (
      <div className={containerClass}>
        <div className="flex h-[100dvh] items-center justify-center">
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
        <div className="flex h-[100dvh] w-full flex-col-reverse gap-0 p-0 lg:flex-row">
          {/* Chat Panel Container - Blurred background */}
          <div className="relative flex h-full w-full flex-col lg:w-[35%] lg:flex-none lg:border-r lg:border-slate-200 dark:lg:border-slate-800">
            <div className="relative flex flex-1 items-stretch overflow-hidden bg-white/80 backdrop-blur dark:bg-slate-900/70 blur-md pointer-events-none">
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
              onNavigateToContacts={handleNavigateToContacts}
              currentView={currentView}
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
      <div className="flex h-[100dvh] w-full flex-col-reverse gap-0 p-0 lg:flex-row">
        {/* Chat Panel Container */}
        <div className="relative flex min-h-0 flex-1 w-full flex-col lg:w-[35%] lg:flex-none lg:h-full lg:border-r lg:border-slate-200 dark:lg:border-slate-800">
          {/* ChatKit Panel */}
          <div className="relative flex flex-1 items-stretch overflow-hidden bg-white dark:bg-slate-900">
            <ChatKitPanel
              theme={scheme}
              onResponseEnd={handleResponseEnd}
              onThemeRequest={handleThemeChange}
              onSendMessageReady={handleSendMessageReady}
              currentCompanyId={activeCompanyId}
              onCompanyIdChange={handleCompanyIdChange}
            />
          </div>

          {/* Mobile: Navigation Pills to open dashboard, contacts or settings */}
          <div className="relative z-[60] flex-shrink-0 p-4 flex items-center justify-center bg-white dark:bg-slate-900 lg:hidden">
            <div className="flex items-center gap-1.5 rounded-xl bg-slate-100 p-1.5 dark:bg-slate-800 transition-colors shadow-sm">
              <button
                onClick={() => {
                  setIsDrawerOpen(!isDrawerOpen);
                  setIsContactsDrawerOpen(false);
                  setIsSettingsDrawerOpen(false);
                }}
                className={clsx(
                  "flex items-center justify-center rounded-lg px-4 py-3 transition-all duration-200 ease-in-out",
                  "transform active:scale-95",
                  isDrawerOpen
                    ? "bg-white text-emerald-600 shadow-sm dark:bg-slate-900 dark:text-emerald-400"
                    : "text-slate-600 hover:bg-slate-200/50 hover:text-slate-900 hover:scale-105 dark:text-slate-300 dark:hover:bg-slate-700/50 dark:hover:text-slate-100"
                )}
                aria-label="Abrir Dashboard"
              >
                <HomeIcon className={clsx(
                  "h-5 w-5 transition-transform duration-200",
                  isDrawerOpen && "scale-110"
                )} />
              </button>
              <button
                onClick={() => {
                  setIsContactsDrawerOpen(!isContactsDrawerOpen);
                  setIsDrawerOpen(false);
                  setIsSettingsDrawerOpen(false);
                }}
                className={clsx(
                  "flex items-center justify-center rounded-lg px-4 py-3 transition-all duration-200 ease-in-out",
                  "transform active:scale-95",
                  isContactsDrawerOpen
                    ? "bg-white text-emerald-600 shadow-sm dark:bg-slate-900 dark:text-emerald-400"
                    : "text-slate-600 hover:bg-slate-200/50 hover:text-slate-900 hover:scale-105 dark:text-slate-300 dark:hover:bg-slate-700/50 dark:hover:text-slate-100"
                )}
                aria-label="Abrir Contactos"
              >
                <Users className={clsx(
                  "h-5 w-5 transition-transform duration-200",
                  isContactsDrawerOpen && "scale-110"
                )} />
              </button>
              <button
                onClick={() => {
                  setIsSettingsDrawerOpen(!isSettingsDrawerOpen);
                  setIsDrawerOpen(false);
                  setIsContactsDrawerOpen(false);
                }}
                className={clsx(
                  "flex items-center justify-center rounded-lg px-4 py-3 transition-all duration-200 ease-in-out",
                  "transform active:scale-95",
                  isSettingsDrawerOpen
                    ? "bg-white text-emerald-600 shadow-sm dark:bg-slate-900 dark:text-emerald-400"
                    : "text-slate-600 hover:bg-slate-200/50 hover:text-slate-900 hover:scale-105 dark:text-slate-300 dark:hover:bg-slate-700/50 dark:hover:text-slate-100"
                )}
                aria-label="Abrir Ajustes"
              >
                <Settings className={clsx(
                  "h-5 w-5 transition-transform duration-200",
                  isSettingsDrawerOpen && "scale-110"
                )} />
              </button>
            </div>
          </div>
        </div>

        {/* Desktop: Show dashboard, contacts, or settings based on currentView */}
        <div className="relative hidden h-full flex-col lg:flex lg:flex-1">
          <div className="relative flex flex-1 items-stretch overflow-hidden bg-white dark:bg-slate-900">
            {currentView === 'dashboard' ? (
              <FinancialDashboard
                scheme={scheme}
                companyId={activeCompanyId}
                company={company}
                onThemeChange={handleThemeChange}
                onNavigateToSettings={handleNavigateToSettings}
                onNavigateToContacts={handleNavigateToContacts}
                currentView={currentView}
              />
            ) : currentView === 'contacts' ? (
              <Contacts
                scheme={scheme}
                company={company}
                onNavigateBack={handleNavigateToDashboard}
                onThemeChange={handleThemeChange}
                onNavigateToDashboard={handleNavigateToDashboard}
                onNavigateToSettings={handleNavigateToSettings}
                currentView={currentView}
              />
            ) : (
              <ProfileSettings
                scheme={scheme}
                onNavigateBack={handleNavigateToDashboard}
                company={company}
                onThemeChange={handleThemeChange}
                onNavigateToDashboard={handleNavigateToDashboard}
                onNavigateToContacts={handleNavigateToContacts}
                currentView={currentView}
              />
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
        onThemeChange={handleThemeChange}
        onNavigateToContacts={() => {
          setIsDrawerOpen(false);
          setIsContactsDrawerOpen(true);
        }}
        onNavigateToSettings={() => {
          setIsDrawerOpen(false);
          setIsSettingsDrawerOpen(true);
        }}
      />

      {/* Mobile: Contacts Drawer */}
      <ContactsDrawer
        isOpen={isContactsDrawerOpen}
        onClose={() => setIsContactsDrawerOpen(false)}
        scheme={scheme}
        companyId={activeCompanyId}
        company={company}
        onThemeChange={handleThemeChange}
        onNavigateToDashboard={() => {
          setIsContactsDrawerOpen(false);
          setIsDrawerOpen(true);
        }}
        onNavigateToSettings={() => {
          setIsContactsDrawerOpen(false);
          setIsSettingsDrawerOpen(true);
        }}
      />

      {/* Mobile: Settings Drawer */}
      <ProfileSettingsDrawer
        isOpen={isSettingsDrawerOpen}
        onClose={() => setIsSettingsDrawerOpen(false)}
        scheme={scheme}
        company={company}
        onThemeChange={handleThemeChange}
        onNavigateToDashboard={() => {
          setIsSettingsDrawerOpen(false);
          setIsDrawerOpen(true);
        }}
        onNavigateToContacts={() => {
          setIsSettingsDrawerOpen(false);
          setIsContactsDrawerOpen(true);
        }}
      />
    </div>
  );
}
