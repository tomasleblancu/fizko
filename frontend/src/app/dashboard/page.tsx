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
        {/* Left Side: Chat (35%) - Always visible */}
        <div className="flex w-[35%] flex-col border-r border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-900">
          {isDesktop && (
            <ChatKitPanel
              companyId={company.id}
              className="h-full"
            />
          )}
        </div>

        {/* Right Side: Dashboard Views (65%) - Only visible when a tab is selected */}
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
              className="rounded-lg p-2 text-slate-600 transition-colors hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800"
              aria-label="Dashboard"
            >
              <Home className="h-5 w-5" />
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
            companyId={company.id}
            className="flex-1 pb-20"
          />
        )}

        {/* Bottom Navigation */}
        <div className="fixed bottom-0 left-0 right-0 z-50 border-t border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-900">
          <div className="flex items-center justify-around px-4 py-2">
            <button
              onClick={() => setActiveTab("dashboard")}
              className={`flex flex-col items-center gap-1 rounded-lg px-4 py-2 transition-colors ${
                activeTab === "dashboard"
                  ? "text-emerald-600 dark:text-emerald-400"
                  : "text-slate-600 dark:text-slate-400"
              }`}
            >
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
              </svg>
              <span className="text-xs">Inicio</span>
            </button>

            <button
              onClick={() => setActiveTab("contacts")}
              className={`flex flex-col items-center gap-1 rounded-lg px-4 py-2 transition-colors ${
                activeTab === "contacts"
                  ? "text-emerald-600 dark:text-emerald-400"
                  : "text-slate-600 dark:text-slate-400"
              }`}
            >
              <Building2 className="h-6 w-6" />
              <span className="text-xs">Contactos</span>
            </button>

            <button
              onClick={() => setActiveTab("personnel")}
              className={`flex flex-col items-center gap-1 rounded-lg px-4 py-2 transition-colors ${
                activeTab === "personnel"
                  ? "text-emerald-600 dark:text-emerald-400"
                  : "text-slate-600 dark:text-slate-400"
              }`}
            >
              <UsersRound className="h-6 w-6" />
              <span className="text-xs">Personal</span>
            </button>

            <button
              onClick={() => setActiveTab("forms")}
              className={`flex flex-col items-center gap-1 rounded-lg px-4 py-2 transition-colors ${
                activeTab === "forms"
                  ? "text-emerald-600 dark:text-emerald-400"
                  : "text-slate-600 dark:text-slate-400"
              }`}
            >
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <span className="text-xs">Formularios</span>
            </button>

            <button
              onClick={() => setActiveTab("settings")}
              className={`flex flex-col items-center gap-1 rounded-lg px-4 py-2 transition-colors ${
                activeTab === "settings"
                  ? "text-emerald-600 dark:text-emerald-400"
                  : "text-slate-600 dark:text-slate-400"
              }`}
            >
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              <span className="text-xs">Ajustes</span>
            </button>
          </div>
        </div>

        {/* Mobile Drawer - Shows when any tab is active */}
        {activeTab && (
          <div
            className="fixed inset-0 z-40"
            style={{ pointerEvents: activeTab ? 'auto' : 'none' }}
          >
            {/* Backdrop */}
            <div
              className="absolute inset-0 bg-black/50 backdrop-blur-sm transition-opacity duration-300"
              onClick={() => setActiveTab(null)}
              aria-hidden="true"
            />

            {/* Drawer */}
            <div
              ref={drawerRef}
              className="absolute bottom-0 left-0 right-0 flex h-[90vh] flex-col transform rounded-t-2xl bg-white shadow-2xl transition-transform duration-300 ease-out dark:bg-slate-900"
              onClick={(e) => e.stopPropagation()}
              style={{ touchAction: 'pan-y' }}
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
