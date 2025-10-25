import { useEffect, useRef } from 'react';
import { X } from 'lucide-react';
import clsx from 'clsx';
import { ProfileSettings } from './ProfileSettings';
import type { ColorScheme } from '../hooks/useColorScheme';
import type { Company } from '../types/fizko';

interface ProfileSettingsDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  scheme: ColorScheme;
  company: Company | null;
  onThemeChange?: (scheme: ColorScheme) => void;
  onNavigateToDashboard?: () => void;
  onNavigateToContacts?: () => void;
  initialTab?: 'account' | 'company' | 'preferences' | 'subscription';
}

export function ProfileSettingsDrawer({
  isOpen,
  onClose,
  scheme,
  company,
  onThemeChange,
  onNavigateToDashboard,
  onNavigateToContacts,
  initialTab,
}: ProfileSettingsDrawerProps) {
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
        onTouchStart={handleTouchStart}
        onTouchMove={handleTouchMove}
        onTouchEnd={handleTouchEnd}
      >
        {/* Handle Bar */}
        <div className="flex items-center justify-center py-3">
          <div className="h-1.5 w-12 rounded-full bg-slate-300 dark:bg-slate-700" />
        </div>

        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute right-4 top-4 z-10 rounded-full bg-slate-100 p-2 transition-colors hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700"
          aria-label="Cerrar configuración"
        >
          <X className="h-5 w-5 text-slate-600 dark:text-slate-300" />
        </button>

        {/* Content - Profile Settings */}
        <div className="h-[calc(100%-3rem)] overflow-hidden pb-4">
          <ProfileSettings
            scheme={scheme}
            isInDrawer={true}
            company={company}
            onThemeChange={onThemeChange}
            onNavigateToDashboard={onNavigateToDashboard}
            onNavigateToContacts={onNavigateToContacts}
            currentView="settings"
            initialTab={initialTab}
          />
        </div>
      </div>
    </div>
  );
}
