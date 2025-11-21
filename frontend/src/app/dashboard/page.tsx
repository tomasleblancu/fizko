"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState, useRef } from "react";
import { createBrowserClient } from "@supabase/ssr";
import { Bell, Sun, Home, Building2, UsersRound, FileText, Settings, X } from "lucide-react";
import { Header, type TabType } from "@/components/layout/Header";
import { DashboardView } from "@/components/features/dashboard/DashboardView";
import { ContactsView } from "@/components/features/dashboard/ContactsView";
import { PersonnelView } from "@/components/features/dashboard/PersonnelView";
import { FormsView } from "@/components/features/dashboard/FormsView";
import { SettingsView } from "@/components/features/dashboard/SettingsView";
import { ChatKitPanel } from "@/components/chat/chatkit-panel";
import { useUserSessions } from "@/hooks/useUserSessions";

export default function DashboardPage() {
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<TabType | null>(null);
  const [isDesktop, setIsDesktop] = useState(false);
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);
  const drawerRef = useRef<HTMLDivElement>(null);
  const startY = useRef<number>(0);
  const currentY = useRef<number>(0);
  const isDraggingRef = useRef<boolean>(false);
  const router = useRouter();
  const redirectInitiated = useRef(false);

  const supabase = createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY!
  );

  // Fetch user sessions with companies
  const { data: sessions, isLoading: sessionsLoading, error: sessionsError } = useUserSessions();

  useEffect(() => {
    const checkUser = async () => {
      const {
        data: { user },
      } = await supabase.auth.getUser();

      // Middleware already handles auth redirect, no need to check here
      setUser(user);
      setLoading(false);
    };

    checkUser();
  }, [router, supabase.auth]);

  // Detect screen size and set default tab for desktop
  useEffect(() => {
    const checkScreenSize = () => {
      const desktop = window.matchMedia("(min-width: 1024px)").matches;
      setIsDesktop(desktop);

      // If desktop and no tab selected, default to dashboard
      if (desktop && !activeTab) {
        setActiveTab("dashboard");
      }
    };

    // Check on mount
    checkScreenSize();

    // Listen for resize
    window.addEventListener("resize", checkScreenSize);
    return () => window.removeEventListener("resize", checkScreenSize);
  }, [activeTab]);

  // Set initial selected session when sessions load
  useEffect(() => {
    if (sessions && sessions.length > 0 && !selectedSessionId) {
      setSelectedSessionId(sessions[0].id);
    }
  }, [sessions, selectedSessionId]);

  // Redirect to onboarding if no sessions
  useEffect(() => {
    if (!sessionsLoading && !redirectInitiated.current && sessions !== undefined && (!sessions || sessions.length === 0)) {
      redirectInitiated.current = true;
      window.location.href = '/onboarding/sii';
    }
  }, [sessions, sessionsLoading]);

  // Disable pull-to-refresh when drawer is open on mobile
  useEffect(() => {
    if (activeTab && !isDesktop) {
      // Prevent pull-to-refresh on mobile when drawer is open
      document.body.style.overscrollBehavior = 'none';

      return () => {
        // Re-enable pull-to-refresh when drawer closes
        document.body.style.overscrollBehavior = '';
      };
    }
  }, [activeTab, isDesktop]);

  // Auto-close drawer on mobile when chateable message is sent
  useEffect(() => {
    if (!isDesktop && activeTab) {
      const handleChateableMessage = () => {
        setActiveTab(null);
      };

      window.addEventListener('chatkit:sendMessage' as any, handleChateableMessage as EventListener);

      return () => {
        window.removeEventListener('chatkit:sendMessage' as any, handleChateableMessage as EventListener);
      };
    }
  }, [isDesktop, activeTab]);

  const handleLogout = async () => {
    await supabase.auth.signOut();
    router.push("/");
  };

  // Handle drag to close drawer (supports both touch and mouse)
  const handleDragStart = (clientY: number) => {
    startY.current = clientY;
    currentY.current = clientY;
    isDraggingRef.current = true;
  };

  const handleDragMove = (clientY: number) => {
    if (!isDraggingRef.current) return;

    currentY.current = clientY;
    const diff = currentY.current - startY.current;

    // Only allow dragging down from the handle bar
    if (diff > 0 && drawerRef.current) {
      drawerRef.current.style.transform = `translateY(${diff}px)`;
      drawerRef.current.style.transition = 'none';
    }
  };

  const handleDragEnd = () => {
    if (!isDraggingRef.current) return;

    const diff = currentY.current - startY.current;
    isDraggingRef.current = false;

    if (drawerRef.current) {
      // Close if dragged more than 150px down
      if (diff > 150) {
        // Animate drawer closing
        drawerRef.current.style.transition = 'transform 0.3s ease-out';
        drawerRef.current.style.transform = 'translateY(100%)';

        // Close after animation
        setTimeout(() => {
          setActiveTab(null);
          if (drawerRef.current) {
            drawerRef.current.style.transform = '';
            drawerRef.current.style.transition = '';
          }
        }, 300);
      } else {
        // Snap back to original position
        drawerRef.current.style.transition = 'transform 0.3s ease-out';
        drawerRef.current.style.transform = '';
      }
    }
  };

  // Touch event handlers
  const handleTouchStart = (e: React.TouchEvent) => {
    e.preventDefault();
    handleDragStart(e.touches[0].clientY);
  };

  const handleTouchMove = (e: React.TouchEvent) => {
    e.preventDefault();
    handleDragMove(e.touches[0].clientY);
  };

  const handleTouchEnd = (e: React.TouchEvent) => {
    e.preventDefault();
    handleDragEnd();
  };

  // Mouse event handlers
  const handleMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    handleDragStart(e.clientY);

    // Add global mouse event listeners
    const handleGlobalMouseMove = (e: MouseEvent) => {
      handleDragMove(e.clientY);
    };

    const handleGlobalMouseUp = () => {
      handleDragEnd();
      window.removeEventListener('mousemove', handleGlobalMouseMove);
      window.removeEventListener('mouseup', handleGlobalMouseUp);
    };

    window.addEventListener('mousemove', handleGlobalMouseMove);
    window.addEventListener('mouseup', handleGlobalMouseUp);
  };

  // Combined loading state
  if (loading || sessionsLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-emerald-50 via-white to-teal-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-emerald-500 border-t-transparent" />
      </div>
    );
  }

  // Error state
  if (sessionsError) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-emerald-50 via-white to-teal-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900">
        <div className="text-center">
          <p className="text-red-600 dark:text-red-400">Error al cargar las sesiones</p>
          <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">
            {sessionsError.message}
          </p>
        </div>
      </div>
    );
  }

  // No sessions available - show loader while redirecting
  if (!sessions || sessions.length === 0) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-emerald-50 via-white to-teal-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-emerald-500 border-t-transparent" />
      </div>
    );
  }

  // Get the selected session or default to the first one
  const activeSession = selectedSessionId
    ? sessions.find(s => s.id === selectedSessionId) || sessions[0]
    : sessions[0];

  const company = activeSession.company;

  const renderView = () => {
    switch (activeTab) {
      case "dashboard":
        return <DashboardView companyId={company.id} />;
      case "contacts":
        return <ContactsView companyId={company.id} />;
      case "personnel":
        return <PersonnelView companyId={company.id} />;
      case "forms":
        return <FormsView companyId={company.id} />;
      case "settings":
        return <SettingsView userId={user?.id} companyId={company.id} companyData={company} onLogout={handleLogout} />;
      default:
        return <DashboardView companyId={company.id} />;
    }
  };

  return (
    <div className="fixed inset-0 flex flex-col overflow-hidden bg-gradient-to-br from-emerald-50 via-white to-teal-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900">
      {/* Desktop: Split View Layout */}
      <div className="hidden lg:flex lg:flex-1 lg:overflow-hidden">
        {/* Left Side: Chat (30%) - Always visible */}
        <div className="flex w-[30%] flex-col border-r border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-900">
          {isDesktop && (
            <ChatKitPanel
              key={company.id}
              companyId={company.id}
              className="h-full"
            />
          )}
        </div>

        {/* Right Side: Dashboard Views (70%) - Only visible when a tab is selected */}
        {activeTab && (
          <div className="flex flex-1 flex-col overflow-hidden">
            {/* Header with integrated tabs */}
            <div className="flex-shrink-0 border-b border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-900">
              <Header
                companyName={company.trade_name || company.business_name || "Mi Empresa"}
                companyRut={company.rut}
                onMenuClick={() => {}}
                activeTab={activeTab}
                onTabChange={setActiveTab}
                sessions={sessions}
                selectedSessionId={selectedSessionId}
                onSessionChange={setSelectedSessionId}
              />
            </div>

            {/* View Content - Scrollable */}
            <div className="flex flex-1 flex-col overflow-hidden bg-white dark:bg-slate-900">
              <div className="flex-1 overflow-y-auto px-6 py-6">{renderView()}</div>
            </div>
          </div>
        )}

        {/* Desktop: Floating Tab Icons - Only visible when no tab is selected */}
        {!activeTab && (
          <div className="absolute right-6 top-6 flex items-center gap-2 rounded-lg border border-slate-200 bg-white p-2 shadow-lg dark:border-slate-700 dark:bg-slate-900">
            <button
              onClick={() => setActiveTab("dashboard")}
              className="rounded-full p-3 bg-emerald-500 text-white shadow-lg shadow-emerald-500/50 transition-all hover:bg-emerald-600 dark:bg-emerald-600 dark:hover:bg-emerald-700"
              aria-label="Dashboard"
            >
              <Home className="h-6 w-6" />
            </button>

            <button
              onClick={() => setActiveTab("contacts")}
              className="rounded-lg p-2 text-slate-600 transition-colors hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800"
              aria-label="Contactos"
            >
              <Building2 className="h-5 w-5" />
            </button>

            <button
              onClick={() => setActiveTab("personnel")}
              className="rounded-lg p-2 text-slate-600 transition-colors hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800"
              aria-label="Personal"
            >
              <UsersRound className="h-5 w-5" />
            </button>

            <button
              onClick={() => setActiveTab("forms")}
              className="rounded-lg p-2 text-slate-600 transition-colors hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800"
              aria-label="Formularios"
            >
              <FileText className="h-5 w-5" />
            </button>

            <button
              onClick={() => setActiveTab("settings")}
              className="rounded-lg p-2 text-slate-600 transition-colors hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800"
              aria-label="Configuración"
            >
              <Settings className="h-5 w-5" />
            </button>

            <div className="mx-2 h-6 w-px bg-slate-200 dark:bg-slate-700" />

            {/* Notifications */}
            <button
              className="relative rounded-lg p-2 hover:bg-slate-100 dark:hover:bg-slate-800"
              aria-label="Notificaciones"
            >
              <Bell className="h-5 w-5 text-slate-600 dark:text-slate-400" />
              <span className="absolute right-1.5 top-1.5 h-2 w-2 rounded-full bg-emerald-500" />
            </button>

            {/* Theme Toggle */}
            <button
              onClick={() => {
                const newTheme = document.documentElement.classList.contains("dark") ? "light" : "dark";
                if (newTheme === "dark") {
                  document.documentElement.classList.add("dark");
                } else {
                  document.documentElement.classList.remove("dark");
                }
              }}
              className="rounded-lg p-2 hover:bg-slate-100 dark:hover:bg-slate-800"
              aria-label="Cambiar tema"
            >
              <Sun className="h-5 w-5 text-slate-600 dark:text-slate-400" />
            </button>
          </div>
        )}
      </div>

      {/* Mobile: Chat full screen + Bottom menu */}
      <div className="flex flex-1 flex-col overflow-hidden lg:hidden">
        {/* Chat takes full screen */}
        {!isDesktop && (
          <ChatKitPanel
            key={company.id}
            companyId={company.id}
            className="flex-1 pb-20"
          />
        )}

        {/* Bottom Navigation */}
        <div className="fixed bottom-0 left-0 right-0 z-50 border-t border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-900">
          <div className="flex items-center justify-around px-4 py-3">
            <button
              onClick={() => setActiveTab("dashboard")}
              className="transition-all"
              aria-label="Dashboard"
            >
              <div className={`rounded-full p-3.5 transition-all ${
                activeTab === "dashboard"
                  ? "bg-emerald-500 text-white shadow-lg shadow-emerald-500/50"
                  : "bg-emerald-100 text-emerald-600 dark:bg-emerald-900/30 dark:text-emerald-400"
              }`}>
                <Home className="h-7 w-7" />
              </div>
            </button>

            <button
              onClick={() => setActiveTab("contacts")}
              className={`rounded-lg p-2 transition-all ${
                activeTab === "contacts"
                  ? "bg-emerald-500 text-white shadow-lg shadow-emerald-500/50"
                  : "text-slate-600 dark:text-slate-400"
              }`}
              aria-label="Contactos"
            >
              <Building2 className="h-6 w-6" />
            </button>

            <button
              onClick={() => setActiveTab("personnel")}
              className={`rounded-lg p-2 transition-all ${
                activeTab === "personnel"
                  ? "bg-emerald-500 text-white shadow-lg shadow-emerald-500/50"
                  : "text-slate-600 dark:text-slate-400"
              }`}
              aria-label="Personal"
            >
              <UsersRound className="h-6 w-6" />
            </button>

            <button
              onClick={() => setActiveTab("forms")}
              className={`rounded-lg p-2 transition-all ${
                activeTab === "forms"
                  ? "bg-emerald-500 text-white shadow-lg shadow-emerald-500/50"
                  : "text-slate-600 dark:text-slate-400"
              }`}
              aria-label="Formularios"
            >
              <FileText className="h-6 w-6" />
            </button>

            <button
              onClick={() => setActiveTab("settings")}
              className={`rounded-lg p-2 transition-all ${
                activeTab === "settings"
                  ? "bg-emerald-500 text-white shadow-lg shadow-emerald-500/50"
                  : "text-slate-600 dark:text-slate-400"
              }`}
              aria-label="Configuración"
            >
              <Settings className="h-6 w-6" />
            </button>
          </div>
        </div>

        {/* Mobile Drawer - Shows when any tab is active */}
        {activeTab && (
          <div
            className="fixed inset-0 z-40"
            style={{ pointerEvents: activeTab ? 'auto' : 'none' }}
          >
            {/* Transparent Backdrop - Click to close */}
            <div
              className="absolute inset-0"
              onClick={() => setActiveTab(null)}
              aria-hidden="true"
            />

            {/* Drawer */}
            <div
              ref={drawerRef}
              className="absolute bottom-0 left-0 right-0 flex h-[80vh] flex-col transform rounded-t-2xl bg-white transition-transform duration-300 ease-out dark:bg-slate-900"
              style={{
                touchAction: 'pan-y',
                boxShadow: '0 -8px 32px rgba(0, 0, 0, 0.15), 0 -4px 16px rgba(0, 0, 0, 0.1), 0 0 0 1px rgba(0, 0, 0, 0.05)'
              }}
            >
              {/* Handle Bar - Supports both touch and mouse */}
              <div
                className="flex flex-shrink-0 items-center justify-center py-5 cursor-grab active:cursor-grabbing"
                onTouchStart={handleTouchStart}
                onTouchMove={handleTouchMove}
                onTouchEnd={handleTouchEnd}
                onMouseDown={handleMouseDown}
                style={{ touchAction: 'none' }}
              >
                <div className="h-1.5 w-20 rounded-full bg-slate-400 dark:bg-slate-500" />
              </div>

              {/* Close Button */}
              <button
                onClick={() => setActiveTab(null)}
                className="absolute right-4 top-4 z-20 rounded-full bg-slate-100 p-2.5 shadow-md transition-colors hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700"
                aria-label="Cerrar"
              >
                <X className="h-6 w-6 text-slate-700 dark:text-slate-200" />
              </button>

              {/* Content - Now with proper flex-1 and overflow */}
              <div className="flex-1 overflow-y-auto overflow-x-hidden px-4 pb-24">
                {renderView()}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
