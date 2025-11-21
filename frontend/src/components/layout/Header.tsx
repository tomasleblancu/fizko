"use client";

import { Bell, Sun, Moon, Menu, Home, Building2, UsersRound, FileText, Settings, ChevronDown } from "lucide-react";
import Image from "next/image";
import { useTheme } from "next-themes";
import { useEffect, useState } from "react";
import type { SessionWithCompany } from "@/types/database";

export type TabType = "dashboard" | "contacts" | "personnel" | "forms" | "settings";

interface HeaderProps {
  onMenuClick?: () => void;
  companyName?: string;
  companyRut?: string;
  activeTab?: TabType;
  onTabChange?: (tab: TabType) => void;
  sessions?: SessionWithCompany[];
  selectedSessionId?: string | null;
  onSessionChange?: (sessionId: string) => void;
}

export function Header({
  onMenuClick,
  companyName,
  companyRut,
  activeTab,
  onTabChange,
  sessions,
  selectedSessionId,
  onSessionChange
}: HeaderProps) {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  // Show selector only if there are multiple sessions
  const showSelector = sessions && sessions.length > 1;

  return (
    <header className="bg-white dark:bg-slate-900">
      <div className="flex h-16 items-center justify-between px-4 sm:px-6 lg:px-8">
        {/* Left: Logo + Company Info */}
        <div className="flex items-center gap-4">
          <button
            onClick={onMenuClick}
            className="rounded-lg p-2 hover:bg-slate-100 dark:hover:bg-slate-800 lg:hidden"
            aria-label="Abrir menú"
          >
            <Menu className="h-5 w-5" />
          </button>

          <div className="flex items-center gap-3">
            <Image
              src="/encabezado.png"
              alt="Fizko"
              width={32}
              height={32}
              className="h-8 w-8"
            />
            <div className="hidden sm:block relative">
              {showSelector ? (
                <div className="relative">
                  <button
                    onClick={() => setIsDropdownOpen(!isDropdownOpen)}
                    className="flex items-center gap-2 rounded-lg px-2 py-1 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                  >
                    <div className="text-left">
                      <h1 className="text-sm font-semibold text-slate-900 dark:text-white">
                        {companyName || "Mi Empresa"}
                      </h1>
                      <p className="text-xs text-slate-500 dark:text-slate-400">
                        {companyRut || "12.345.678-9"}
                      </p>
                    </div>
                    <ChevronDown className={`h-4 w-4 text-slate-600 dark:text-slate-400 transition-transform ${isDropdownOpen ? 'rotate-180' : ''}`} />
                  </button>

                  {/* Dropdown */}
                  {isDropdownOpen && (
                    <>
                      {/* Backdrop to close dropdown */}
                      <div
                        className="fixed inset-0 z-10"
                        onClick={() => setIsDropdownOpen(false)}
                      />

                      {/* Dropdown menu */}
                      <div className="absolute left-0 top-full mt-2 z-20 w-72 rounded-lg border border-slate-200 bg-white shadow-lg dark:border-slate-700 dark:bg-slate-900">
                        <div className="py-1">
                          {sessions?.map((session) => (
                            <button
                              key={session.id}
                              onClick={() => {
                                onSessionChange?.(session.id);
                                setIsDropdownOpen(false);
                              }}
                              className={`w-full px-4 py-2 text-left hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors ${
                                selectedSessionId === session.id
                                  ? 'bg-emerald-50 dark:bg-emerald-900/20'
                                  : ''
                              }`}
                            >
                              <div className="text-sm font-semibold text-slate-900 dark:text-white">
                                {session.company.trade_name || session.company.business_name || "Empresa"}
                              </div>
                              <div className="text-xs text-slate-500 dark:text-slate-400">
                                {session.company.rut}
                              </div>
                            </button>
                          ))}
                        </div>
                      </div>
                    </>
                  )}
                </div>
              ) : (
                <div className="text-left">
                  <h1 className="text-sm font-semibold text-slate-900 dark:text-white">
                    {companyName || "Mi Empresa"}
                  </h1>
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    {companyRut || "12.345.678-9"}
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Right: Tabs + Actions */}
        <div className="flex items-center gap-2">
          {/* Tab Icons */}
          {onTabChange && (
            <>
              <button
                onClick={() => onTabChange("dashboard")}
                className={`rounded-full p-3 transition-all ${
                  activeTab === "dashboard"
                    ? "bg-emerald-500 text-white shadow-lg shadow-emerald-500/50 dark:bg-emerald-600"
                    : "bg-emerald-100 text-emerald-600 hover:bg-emerald-200 dark:bg-emerald-900/30 dark:text-emerald-400 dark:hover:bg-emerald-900/50"
                }`}
                aria-label="Dashboard"
              >
                <Home className="h-6 w-6" />
              </button>

              <button
                onClick={() => onTabChange("contacts")}
                className={`rounded-lg p-2 transition-colors ${
                  activeTab === "contacts"
                    ? "bg-emerald-100 text-emerald-600 dark:bg-emerald-900/30 dark:text-emerald-400"
                    : "text-slate-600 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800"
                }`}
                aria-label="Contactos"
              >
                <Building2 className="h-5 w-5" />
              </button>

              <button
                onClick={() => onTabChange("personnel")}
                className={`rounded-lg p-2 transition-colors ${
                  activeTab === "personnel"
                    ? "bg-emerald-100 text-emerald-600 dark:bg-emerald-900/30 dark:text-emerald-400"
                    : "text-slate-600 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800"
                }`}
                aria-label="Personal"
              >
                <UsersRound className="h-5 w-5" />
              </button>

              <button
                onClick={() => onTabChange("forms")}
                className={`rounded-lg p-2 transition-colors ${
                  activeTab === "forms"
                    ? "bg-emerald-100 text-emerald-600 dark:bg-emerald-900/30 dark:text-emerald-400"
                    : "text-slate-600 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800"
                }`}
                aria-label="Formularios"
              >
                <FileText className="h-5 w-5" />
              </button>

              <button
                onClick={() => onTabChange("settings")}
                className={`rounded-lg p-2 transition-colors ${
                  activeTab === "settings"
                    ? "bg-emerald-100 text-emerald-600 dark:bg-emerald-900/30 dark:text-emerald-400"
                    : "text-slate-600 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800"
                }`}
                aria-label="Configuración"
              >
                <Settings className="h-5 w-5" />
              </button>

              <div className="mx-2 h-6 w-px bg-slate-200 dark:bg-slate-700" />
            </>
          )}

          {/* Notifications */}
          <button
            className="relative rounded-lg p-2 hover:bg-slate-100 dark:hover:bg-slate-800"
            aria-label="Notificaciones"
          >
            <Bell className="h-5 w-5 text-slate-600 dark:text-slate-400" />
            <span className="absolute right-1.5 top-1.5 h-2 w-2 rounded-full bg-emerald-500" />
          </button>

          {/* Theme Toggle */}
          {mounted && (
            <button
              onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
              className="rounded-lg p-2 hover:bg-slate-100 dark:hover:bg-slate-800"
              aria-label="Cambiar tema"
            >
              {theme === "dark" ? (
                <Sun className="h-5 w-5 text-slate-600 dark:text-slate-400" />
              ) : (
                <Moon className="h-5 w-5 text-slate-600 dark:text-slate-400" />
              )}
            </button>
          )}
        </div>
      </div>
    </header>
  );
}
