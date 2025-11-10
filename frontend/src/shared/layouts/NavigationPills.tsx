import clsx from 'clsx';
import { Home, Users, Settings, BookUser, FileText } from 'lucide-react';
import type { ColorScheme } from "@/shared/hooks/useColorScheme";

export type ViewType = 'dashboard' | 'contacts' | 'personnel' | 'forms' | 'settings';

interface NavigationPillsProps {
  currentView: ViewType;
  onNavigate: (view: ViewType) => void;
  scheme: ColorScheme;
}

export function NavigationPills({ currentView, onNavigate, scheme }: NavigationPillsProps) {
  const pills = [
    { id: 'dashboard' as const, icon: Home, label: 'Dashboard', ariaLabel: 'Dashboard' },
    { id: 'forms' as const, icon: FileText, label: 'Formularios', ariaLabel: 'Formularios' },
    { id: 'contacts' as const, icon: BookUser, label: 'Contactos', ariaLabel: 'Contactos' },
    { id: 'personnel' as const, icon: Users, label: 'Colaboradores', ariaLabel: 'Colaboradores' },
    { id: 'settings' as const, icon: Settings, label: 'Configuración', ariaLabel: 'Configuración' },
  ];

  return (
    <div className="flex items-center gap-1 rounded-lg bg-slate-100 p-1 dark:bg-slate-800 transition-colors">
      {pills.map((pill) => {
        const Icon = pill.icon;
        const isActive = currentView === pill.id;
        const isHome = pill.id === 'dashboard';

        return (
          <button
            key={pill.id}
            onClick={() => onNavigate(pill.id)}
            disabled={isActive}
            className={clsx(
              'rounded-md transition-all duration-200 ease-in-out',
              'transform active:scale-95',
              // Home button takes more space
              isHome ? 'px-6 py-2' : 'p-2',
              isActive
                ? 'bg-white text-emerald-600 shadow-sm cursor-default dark:bg-slate-900 dark:text-emerald-400 scale-100'
                : 'text-slate-600 hover:bg-slate-200/50 hover:text-slate-900 hover:scale-105 dark:text-slate-300 dark:hover:bg-slate-700/50 dark:hover:text-slate-100'
            )}
            aria-label={pill.ariaLabel}
            title={pill.label}
          >
            <Icon className={clsx(
              "h-5 w-5 transition-transform duration-200",
              isActive && "scale-110"
            )} />
          </button>
        );
      })}
    </div>
  );
}
