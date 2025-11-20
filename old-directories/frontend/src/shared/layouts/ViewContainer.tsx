import { useState, useEffect } from 'react';
import clsx from 'clsx';
import { RefreshCw } from 'lucide-react';
import type { ColorScheme } from "@/shared/hooks/useColorScheme";
import { ViewHeader } from './ViewHeader';
import { NavigationPills, type ViewType } from './NavigationPills';
import { ThemeToggleButton } from './ThemeToggleButton';

interface ViewContainerProps {
  // Header
  icon: React.ReactNode;
  iconGradient: string;
  title: React.ReactNode; // Changed from string to ReactNode to accept components
  subtitle: string;

  // Navigation
  currentView: ViewType;
  onNavigate?: (view: ViewType) => void;
  showNavigation?: boolean;

  // Theme
  scheme: ColorScheme;
  onThemeChange?: (scheme: ColorScheme) => void;
  showThemeToggle?: boolean;

  // Refresh
  onRefresh?: () => void;
  isRefreshing?: boolean;

  // Content
  children: React.ReactNode;

  // Layout options
  isInDrawer?: boolean;
  contentClassName?: string;

  // Animation
  enableTransition?: boolean;
}

export function ViewContainer({
  icon,
  iconGradient,
  title,
  subtitle,
  currentView,
  onNavigate,
  showNavigation = true,
  scheme,
  onThemeChange,
  showThemeToggle = true,
  onRefresh,
  isRefreshing = false,
  children,
  isInDrawer = false,
  contentClassName = "flex-1 overflow-y-auto p-6",
  enableTransition = true,
}: ViewContainerProps) {
  // Animation state for content transitions
  const [isTransitioning, setIsTransitioning] = useState(false);
  const [displayedView, setDisplayedView] = useState(currentView);

  // Handle view transitions with fade effect
  useEffect(() => {
    if (enableTransition && currentView !== displayedView) {
      setIsTransitioning(true);
      const timer = setTimeout(() => {
        setDisplayedView(currentView);
        setIsTransitioning(false);
      }, 150); // Half of transition duration
      return () => clearTimeout(timer);
    } else if (!enableTransition) {
      setDisplayedView(currentView);
    }
  }, [currentView, displayedView, enableTransition]);

  // Render para drawer (sin header, solo contenido)
  if (isInDrawer) {
    return (
      <div className="flex h-full flex-col overflow-hidden">
        {children}
      </div>
    );
  }

  // Render completo con header
  return (
    <section className="flex h-full w-full flex-col overflow-hidden">
      {/* Header */}
      <ViewHeader
        icon={icon}
        iconGradient={iconGradient}
        title={title}
        subtitle={subtitle}
        scheme={scheme}
        rightContent={
          <>
            {/* Refresh Button */}
            {onRefresh && (
              <button
                onClick={onRefresh}
                disabled={isRefreshing}
                className={clsx(
                  'rounded-lg p-2 transition-all',
                  'hover:bg-slate-100 dark:hover:bg-slate-800',
                  'text-slate-600 dark:text-slate-300',
                  'disabled:opacity-50 disabled:cursor-not-allowed'
                )}
                aria-label="Refrescar datos"
                title="Refrescar datos"
              >
                <RefreshCw
                  className={clsx(
                    'h-5 w-5',
                    isRefreshing && 'animate-spin'
                  )}
                />
              </button>
            )}

            {/* Theme Toggle */}
            {showThemeToggle && onThemeChange && (
              <ThemeToggleButton
                scheme={scheme}
                onToggle={onThemeChange}
              />
            )}

            {/* Navigation Pills */}
            {showNavigation && onNavigate && (
              <NavigationPills
                currentView={currentView}
                onNavigate={onNavigate}
                scheme={scheme}
              />
            )}
          </>
        }
      />

      {/* Content with transition */}
      <div
        className={clsx(
          contentClassName,
          enableTransition && "transition-opacity duration-300",
          enableTransition && isTransitioning && "opacity-0",
          enableTransition && !isTransitioning && "opacity-100"
        )}
      >
        {children}
      </div>
    </section>
  );
}
