import { useEffect, useRef } from 'react';
import { X } from 'lucide-react';
import clsx from 'clsx';
import { FinancialDashboard } from './FinancialDashboard';
import type { ColorScheme } from "@/shared/hooks/useColorScheme";
import type { Company } from "@/shared/types/fizko";

interface FinancialDashboardDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  scheme: ColorScheme;
  companyId: string | null;
  company: Company | null;
  onThemeChange?: (scheme: ColorScheme) => void;
  onNavigateToContacts?: () => void;
  onNavigateToSettings?: () => void;
}

export function FinancialDashboardDrawer({
  isOpen,
  onClose,
  scheme,
  companyId,
  company,
  onThemeChange,
  onNavigateToContacts,
  onNavigateToSettings,
}: FinancialDashboardDrawerProps) {
  const drawerRef = useRef<HTMLDivElement>(null);
  const startY = useRef<number>(0);
  const currentY = useRef<number>(0);

  // Close on Escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
    };
  }, [isOpen, onClose]);

  // Handle swipe down to close
  const handleTouchStart = (e: React.TouchEvent) => {
    startY.current = e.touches[0].clientY;
    currentY.current = startY.current;
  };

  const handleTouchMove = (e: React.TouchEvent) => {
    currentY.current = e.touches[0].clientY;
    const diff = currentY.current - startY.current;

    // Only allow dragging down
    if (diff > 0 && drawerRef.current) {
      drawerRef.current.style.transform = `translateY(${diff}px)`;
    }
  };

  const handleTouchEnd = () => {
    const diff = currentY.current - startY.current;

    if (drawerRef.current) {
      drawerRef.current.style.transform = '';
    }

    // Close if dragged more than 100px down
    if (diff > 100) {
      onClose();
    }
  };

  // Always render to allow animations to work
  return (
    <div
      className={clsx(
        "fixed inset-0 z-50 lg:hidden",
        !isOpen && "pointer-events-none"
      )}
    >
      {/* Backdrop */}
      <div
        className={clsx(
          "absolute inset-0 bg-black/50 backdrop-blur-sm transition-opacity duration-500",
          isOpen ? "opacity-100 pointer-events-auto" : "opacity-0 pointer-events-none"
        )}
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Drawer */}
      <div
        ref={drawerRef}
        className={clsx(
          "absolute bottom-0 left-0 right-0 h-[85vh] transform rounded-t-3xl bg-white shadow-2xl transition-all duration-500 ease-out dark:bg-slate-900",
          isOpen ? "translate-y-0 pointer-events-auto" : "translate-y-full pointer-events-none"
        )}
        style={{
          transitionTimingFunction: isOpen
            ? "cubic-bezier(0.16, 1, 0.3, 1)" // Smooth ease-out when opening
            : "cubic-bezier(0.4, 0, 0.2, 1)" // Smooth when closing
        }}
      >
        {/* Handle Bar - Touch events only here */}
        <div
          className="flex items-center justify-center py-3"
          onTouchStart={handleTouchStart}
          onTouchMove={handleTouchMove}
          onTouchEnd={handleTouchEnd}
        >
          <div className="h-1.5 w-12 rounded-full bg-slate-300 dark:bg-slate-700" />
        </div>

        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute right-4 top-4 z-20 rounded-full bg-slate-100 p-2 transition-colors hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700"
          aria-label="Cerrar dashboard financiero"
        >
          <X className="h-5 w-5 text-slate-600 dark:text-slate-300" />
        </button>

        {/* Content - Financial Dashboard */}
        <div className="h-[calc(100%-3rem)] overflow-hidden pb-4">
          <FinancialDashboard
            scheme={scheme}
            companyId={companyId}
            isInDrawer={true}
            company={company}
            onThemeChange={onThemeChange}
            onNavigateToContacts={onNavigateToContacts}
            onNavigateToSettings={onNavigateToSettings}
            currentView="dashboard"
          />
        </div>
      </div>
    </div>
  );
}
