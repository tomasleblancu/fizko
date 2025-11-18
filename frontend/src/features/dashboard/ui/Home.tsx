import { useState, useCallback, useEffect } from "react";
import clsx from "clsx";
import { Home as HomeIcon, Users, Settings, BookUser, Sun, Moon } from "lucide-react";
import { useQueryClient } from "@tanstack/react-query";

import { Header } from "@/widgets/navbar/Header";
import { ChatKitPanel } from "@/widgets/chat-panel/ChatKitPanel";
import { FinancialDashboard } from "./FinancialDashboard";
import { FinancialDashboardDrawer } from "./FinancialDashboardDrawer";
import { ProfileSettings } from "../../profile/ui/ProfileSettings";
import { ProfileSettingsDrawer } from "../../profile/ui/ProfileSettingsDrawer";
import { Contacts } from "../../contacts/ui/Contacts";
import { ContactsDrawer } from "../../contacts/ui/ContactsDrawer";
import { Personnel } from "../../payroll/ui/Personnel";
import { PersonnelDrawer } from "../../payroll/ui/PersonnelDrawer";
import { Forms } from "../../tax/ui/Forms";
import { LoginOverlay } from "@/shared/ui/feedback/LoginOverlay";
import { FizkoLoadingScreen } from "@/shared/ui/feedback/FizkoLoadingScreen";
import { SubscriptionBanner } from "@/shared/components/SubscriptionBanner";
import { TrialBanner } from "@/shared/components/TrialBanner";
import type { ViewType } from "@/shared/layouts/NavigationPills";
import { ColorScheme } from "@/shared/hooks/useColorScheme";
import { useAuth } from "@/app/providers/AuthContext";
import { useSession } from "@/shared/hooks/useSession";
import { useCompanyQuery } from "@/shared/hooks/useCompanyQuery";
import { useSubscription, useIsInTrial, useIsFreePlan } from "@/shared/hooks/useSubscription";
import { useSubscriptionPlans } from "@/shared/hooks/useSubscriptionPlans";
import { useF29FormsQuery } from "@/shared/hooks/useF29FormsQuery";
import { ChatProvider, useChat } from "@/app/providers/ChatContext";

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
  const queryClient = useQueryClient();
  const { session: authSession, loading: authLoading } = useAuth();
  const {
    loading: sessionLoading,
    isInitialized,
  } = useSession();

  // Lift company state to Home to avoid multiple fetches
  const { data: company = null, isLoading: companyLoading, error: companyError } = useCompanyQuery();

  // Subscription state
  const { data: subscription } = useSubscription();
  const { isInTrial, trialEndsAt } = useIsInTrial();
  const { isFreePlan } = useIsFreePlan();

  // Refresh state
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Prefetch subscription plans for instant loading when user opens subscription settings
  useSubscriptionPlans();

  // Prefetch F29 forms (monthly, current year) for instant loading when user opens forms tab
  // This runs after Home loads (enabled when company is loaded), so it doesn't block initial render
  const currentYear = new Date().getFullYear();
  useF29FormsQuery({
    companyId: company?.id,
    formType: 'monthly',
    year: currentYear,
  });

  // Chat context for chateable components
  const { setSendUserMessage, setOnChateableClick } = useChat();

  const [sendMessage, setSendMessage] = useState<((text: string, metadata?: Record<string, any>) => Promise<void>) | null>(null);

  // Track active company ID from thread metadata
  const [activeCompanyId, setActiveCompanyId] = useState<string | null>(null);

  // Mobile drawer state
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [isContactsDrawerOpen, setIsContactsDrawerOpen] = useState(false);
  const [isFormsDrawerOpen, setIsFormsDrawerOpen] = useState(false);
  const [isPersonnelDrawerOpen, setIsPersonnelDrawerOpen] = useState(false);
  const [isSettingsDrawerOpen, setIsSettingsDrawerOpen] = useState(false);

  // Settings drawer initial tab
  const [settingsInitialTab, setSettingsInitialTab] = useState<'account' | 'company' | 'preferences' | 'subscription'>('account');

  // View state: 'dashboard', 'contacts', or 'settings'
  const [currentView, setCurrentView] = useState<ViewType>('dashboard');

  // Compute overall loading state - wait until session is initialized
  // Wait for all critical data before showing UI
  // This prevents flash of "Cargando... RUT: ---" before company data loads
  const isLoading = authLoading || sessionLoading || !isInitialized || companyLoading;

  // Debug logging
  console.log('[Home] Render state:', {
    authLoading,
    sessionLoading,
    isInitialized,
    companyLoading,
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
      setIsFormsDrawerOpen(false);
      setIsPersonnelDrawerOpen(false);
      setIsSettingsDrawerOpen(false);
    };
    setOnChateableClick(closeAllDrawers);
  }, [setOnChateableClick]);

  // Prevent body scroll when any drawer is open on mobile
  useEffect(() => {
    const isAnyDrawerOpen = isDrawerOpen || isContactsDrawerOpen || isFormsDrawerOpen || isPersonnelDrawerOpen || isSettingsDrawerOpen;
    if (isAnyDrawerOpen) {
      // Prevent scroll on body (only on mobile)
      const html = document.documentElement;
      const scrollY = window.scrollY;

      document.body.style.overflow = 'hidden';
      html.style.overflow = 'hidden';

      // Store scroll position
      document.body.dataset.scrollY = String(scrollY);
    } else {
      document.body.style.overflow = '';
      document.documentElement.style.overflow = '';

      // Restore scroll position if stored
      const scrollY = document.body.dataset.scrollY;
      if (scrollY) {
        window.scrollTo(0, parseInt(scrollY));
        delete document.body.dataset.scrollY;
      }
    }

    return () => {
      document.body.style.overflow = '';
      document.documentElement.style.overflow = '';
    };
  }, [isDrawerOpen, isContactsDrawerOpen, isFormsDrawerOpen, isPersonnelDrawerOpen, isSettingsDrawerOpen]);

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

  const handleNavigateToForms = useCallback(() => {
    setCurrentView('forms');
  }, []);

  const handleNavigateToPersonnel = useCallback(() => {
    setCurrentView('personnel');
  }, []);

  const handleNavigateToSettings = useCallback(() => {
    setCurrentView('settings');
  }, []);

  const handleNavigateToDashboard = useCallback(() => {
    setCurrentView('dashboard');
  }, []);

  // Handler to open subscription settings
  const handleOpenSubscription = useCallback(() => {
    setSettingsInitialTab('subscription');
    setCurrentView('settings');
    setIsSettingsDrawerOpen(true);
    setIsDrawerOpen(false);
    setIsContactsDrawerOpen(false);
    setIsPersonnelDrawerOpen(false);
    setIsContactsDrawerOpen(false);
  }, []);

  // Handler to refresh all data
  const handleRefresh = useCallback(async () => {
    setIsRefreshing(true);
    try {
      // Invalidate all relevant queries to force refetch
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['company'] }),
        queryClient.invalidateQueries({ queryKey: ['tax-summary'] }),
        queryClient.invalidateQueries({ queryKey: ['tax-documents'] }),
        queryClient.invalidateQueries({ queryKey: ['calendar-events'] }),
        queryClient.invalidateQueries({ queryKey: ['calendar-config'] }),
        queryClient.invalidateQueries({ queryKey: ['contacts'] }),
        queryClient.invalidateQueries({ queryKey: ['people'] }),
        queryClient.invalidateQueries({ queryKey: ['forms'] }),
        queryClient.invalidateQueries({ queryKey: ['subscription'] }),
      ]);
    } finally {
      // Small delay to show the animation
      setTimeout(() => setIsRefreshing(false), 500);
    }
  }, [queryClient]);

  const containerClass = clsx(
    "fixed inset-0 overflow-hidden bg-gradient-to-br transition-colors duration-300 flex flex-col",
    scheme === "dark"
      ? "from-slate-900 via-slate-950 to-slate-850 text-slate-100"
      : "from-slate-100 via-white to-slate-200 text-slate-900"
  );

  // Show loading state while checking auth or session status is unknown
  if (isLoading) {
    return <FizkoLoadingScreen />;
  }

  // Not authenticated - show login overlay
  // Note: This case should rarely happen as HomePage redirects unauthenticated users to Landing
  if (!authSession) {
    return (
      <div className={containerClass}>
        <LoginOverlay />
      </div>
    );
  }

  // Authenticated - show real content
  // Note: Onboarding checks are now handled by HomePage which redirects to /onboarding/* routes
  const isAnyDrawerOpen = isDrawerOpen || isContactsDrawerOpen || isPersonnelDrawerOpen || isSettingsDrawerOpen;

  return (
    <div className={containerClass}>
      {/* Subscription Banners */}
      {isFreePlan && (
        <div className="relative z-50 px-3 py-2 lg:px-4 flex-shrink-0">
          <SubscriptionBanner onUpgradeClick={handleOpenSubscription} />
        </div>
      )}
      {isInTrial && trialEndsAt && (
        <div className="relative z-50 px-3 py-2 lg:px-4 flex-shrink-0">
          <TrialBanner
            trialEndsAt={trialEndsAt}
            onViewPlansClick={handleOpenSubscription}
          />
        </div>
      )}

      <div className={clsx(
        "flex flex-1 w-full flex-col-reverse gap-0 p-0 lg:flex-row min-h-0",
        isAnyDrawerOpen && "overflow-hidden lg:overflow-visible"
      )}>
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

          {/* Mobile: Navigation Pills - All icons in one component */}
          <div className="relative z-[60] flex-shrink-0 px-4 py-2 flex items-center justify-center bg-white dark:bg-slate-900 lg:hidden">
            {/* Single unified group with all navigation icons */}
            <div className="flex items-center gap-1 rounded-xl bg-slate-100 p-1 dark:bg-slate-800 transition-colors shadow-sm">
              {/* Contacts */}
              <button
                onClick={() => {
                  setIsContactsDrawerOpen(!isContactsDrawerOpen);
                  setIsDrawerOpen(false);
                  setIsPersonnelDrawerOpen(false);
                  setIsSettingsDrawerOpen(false);
                }}
                className={clsx(
                  "flex items-center justify-center rounded-lg px-3 py-2 transition-all duration-200 ease-in-out",
                  "transform active:scale-95",
                  isContactsDrawerOpen
                    ? "bg-white text-emerald-600 shadow-sm dark:bg-slate-900 dark:text-emerald-400"
                    : "text-slate-600 hover:bg-slate-200/50 hover:text-slate-900 hover:scale-105 dark:text-slate-300 dark:hover:bg-slate-700/50 dark:hover:text-slate-100"
                )}
                aria-label="Abrir Contactos"
              >
                <BookUser className={clsx(
                  "h-5 w-5 transition-transform duration-200",
                  isContactsDrawerOpen && "scale-110"
                )} />
              </button>

              {/* Personnel */}
              <button
                onClick={() => {
                  setIsPersonnelDrawerOpen(!isPersonnelDrawerOpen);
                  setIsDrawerOpen(false);
                  setIsContactsDrawerOpen(false);
                  setIsSettingsDrawerOpen(false);
                }}
                className={clsx(
                  "flex items-center justify-center rounded-lg px-3 py-2 transition-all duration-200 ease-in-out",
                  "transform active:scale-95",
                  isPersonnelDrawerOpen
                    ? "bg-white text-emerald-600 shadow-sm dark:bg-slate-900 dark:text-emerald-400"
                    : "text-slate-600 hover:bg-slate-200/50 hover:text-slate-900 hover:scale-105 dark:text-slate-300 dark:hover:bg-slate-700/50 dark:hover:text-slate-100"
                )}
                aria-label="Abrir Colaboradores"
              >
                <Users className={clsx(
                  "h-5 w-5 transition-transform duration-200",
                  isPersonnelDrawerOpen && "scale-110"
                )} />
              </button>

              {/* Home/Dashboard */}
              <button
                onClick={() => {
                  setIsDrawerOpen(!isDrawerOpen);
                  setIsContactsDrawerOpen(false);
                  setIsPersonnelDrawerOpen(false);
                  setIsSettingsDrawerOpen(false);
                }}
                className={clsx(
                  "flex items-center justify-center rounded-lg px-8 py-2 transition-all duration-200 ease-in-out",
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

              {/* Theme toggle */}
              <button
                onClick={() => handleThemeChange(scheme === 'dark' ? 'light' : 'dark')}
                className={clsx(
                  "flex items-center justify-center rounded-lg px-3 py-2 transition-all duration-200 ease-in-out",
                  "transform active:scale-95",
                  "text-slate-600 hover:bg-slate-200/50 hover:text-slate-900 hover:scale-105 dark:text-slate-300 dark:hover:bg-slate-700/50 dark:hover:text-slate-100"
                )}
                aria-label="Cambiar tema"
              >
                {scheme === 'dark' ? (
                  <Sun className="h-5 w-5" />
                ) : (
                  <Moon className="h-5 w-5" />
                )}
              </button>

              {/* Settings */}
              <button
                onClick={() => {
                  setIsSettingsDrawerOpen(!isSettingsDrawerOpen);
                  setIsDrawerOpen(false);
                  setIsContactsDrawerOpen(false);
                  setIsPersonnelDrawerOpen(false);
                }}
                className={clsx(
                  "flex items-center justify-center rounded-lg px-3 py-2 transition-all duration-200 ease-in-out",
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
                onNavigateToForms={handleNavigateToForms}
                onNavigateToPersonnel={handleNavigateToPersonnel}
                onRefresh={handleRefresh}
                isRefreshing={isRefreshing}
                currentView={currentView}
              />
            ) : currentView === 'contacts' ? (
              <Contacts
                scheme={scheme}
                company={company}
                onNavigateBack={handleNavigateToDashboard}
                onThemeChange={handleThemeChange}
                onNavigateToDashboard={handleNavigateToDashboard}
                onNavigateToForms={handleNavigateToForms}
                onNavigateToSettings={handleNavigateToSettings}
                onNavigateToPersonnel={handleNavigateToPersonnel}
                currentView={currentView}
              />
            ) : currentView === 'forms' ? (
              <Forms
                scheme={scheme}
                company={company}
                onNavigateBack={handleNavigateToDashboard}
                onThemeChange={handleThemeChange}
                onNavigateToDashboard={handleNavigateToDashboard}
                onNavigateToContacts={handleNavigateToContacts}
                onNavigateToSettings={handleNavigateToSettings}
                onNavigateToPersonnel={handleNavigateToPersonnel}
                currentView={currentView}
              />
            ) : currentView === 'personnel' ? (
              <Personnel
                scheme={scheme}
                company={company}
                onNavigateBack={handleNavigateToDashboard}
                onThemeChange={handleThemeChange}
                onNavigateToDashboard={handleNavigateToDashboard}
                onNavigateToContacts={handleNavigateToContacts}
                onNavigateToForms={handleNavigateToForms}
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
                onNavigateToForms={handleNavigateToForms}
                onNavigateToPersonnel={handleNavigateToPersonnel}
                currentView={currentView}
                initialTab={settingsInitialTab}
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

      {/* Mobile: Personnel Drawer */}
      <PersonnelDrawer
        isOpen={isPersonnelDrawerOpen}
        onClose={() => setIsPersonnelDrawerOpen(false)}
        scheme={scheme}
        company={company}
        onThemeChange={handleThemeChange}
        onNavigateToDashboard={() => {
          setIsPersonnelDrawerOpen(false);
          setIsDrawerOpen(true);
        }}
        onNavigateToContacts={() => {
          setIsPersonnelDrawerOpen(false);
          setIsContactsDrawerOpen(true);
        }}
        onNavigateToSettings={() => {
          setIsPersonnelDrawerOpen(false);
          setIsSettingsDrawerOpen(true);
        }}
        currentView={currentView}
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
        initialTab={settingsInitialTab}
      />
    </div>
  );
}
