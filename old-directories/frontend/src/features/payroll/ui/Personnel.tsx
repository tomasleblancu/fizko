import { useState, useCallback } from 'react';
import clsx from 'clsx';
import { Users, FileText, Briefcase } from 'lucide-react';
import { PeopleList } from './PeopleList';
import { ViewContainer } from '@/shared/layouts/ViewContainer';
import { FizkoLogo } from '@/shared/ui/branding/FizkoLogo';
import type { ViewType } from '@/shared/layouts/NavigationPills';
import type { ColorScheme } from "@/shared/hooks/useColorScheme";
import type { Company } from "@/shared/types/fizko";

type PersonnelTab = 'employees' | 'payroll';

interface PersonnelProps {
  scheme: ColorScheme;
  isInDrawer?: boolean;
  onNavigateBack?: () => void;
  company: Company | null;
  onThemeChange?: (scheme: ColorScheme) => void;
  onNavigateToDashboard?: () => void;
  onNavigateToContacts?: () => void;
  onNavigateToForms?: () => void;
  onNavigateToSettings?: () => void;
  currentView?: ViewType;
}

export function Personnel({
  scheme,
  isInDrawer = false,
  onNavigateBack,
  company,
  onThemeChange,
  onNavigateToDashboard,
  onNavigateToContacts,
  onNavigateToForms,
  onNavigateToSettings,
  currentView = 'personnel',
}: PersonnelProps) {
  const [activeTab, setActiveTab] = useState<PersonnelTab>('employees');

  // Handle navigation
  const handleNavigate = useCallback((view: ViewType) => {
    if (view === 'dashboard' && onNavigateToDashboard) onNavigateToDashboard();
    if (view === 'contacts' && onNavigateToContacts) onNavigateToContacts();
    if (view === 'forms' && onNavigateToForms) onNavigateToForms();
    if (view === 'settings' && onNavigateToSettings) onNavigateToSettings();
  }, [onNavigateToDashboard, onNavigateToContacts, onNavigateToForms, onNavigateToSettings]);

  const tabs = [
    { id: 'employees' as const, icon: Users, label: 'Empleados' },
    { id: 'payroll' as const, icon: FileText, label: 'Liquidaciones' },
  ];

  return (
    <ViewContainer
      icon={<FizkoLogo className="h-7 w-7" />}
      iconGradient="from-white to-white"
      title="Colaboradores"
      subtitle="Gestiona empleados y liquidaciones"
      currentView={currentView}
      onNavigate={handleNavigate}
      scheme={scheme}
      onThemeChange={onThemeChange}
      isInDrawer={isInDrawer}
      contentClassName="flex-1 overflow-hidden flex flex-col"
    >
      {/* Tabs */}
      <div className="flex-shrink-0 border-b border-slate-200/60 px-6 dark:border-slate-800/60">
        <div className="flex gap-1">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;

            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={clsx(
                  'inline-flex items-center gap-2 border-b-2 px-4 py-3 text-base font-medium transition-colors',
                  isActive
                    ? 'border-emerald-600 text-emerald-600 dark:border-emerald-400 dark:text-emerald-400'
                    : 'border-transparent text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100'
                )}
              >
                <Icon
                  className={clsx(
                    'h-5 w-5 transition-colors',
                    isActive
                      ? 'text-emerald-600 dark:text-emerald-400'
                      : 'text-slate-400'
                  )}
                />
                {tab.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* Tab content */}
      <div className="flex-1 overflow-y-auto px-4 sm:px-6 py-4 sm:py-6">
        {activeTab === 'employees' && (
          <PeopleList scheme={scheme} company={company} />
        )}

        {activeTab === 'payroll' && (
          <div className="flex flex-col items-center justify-center h-64 space-y-3">
            <FileText className="h-16 w-16 text-slate-300 dark:text-slate-600" />
            <p className="text-slate-500 dark:text-slate-400 text-center">
              Gestión de liquidaciones
            </p>
            <p className="text-sm text-slate-400 dark:text-slate-500 text-center max-w-md">
              Esta funcionalidad estará disponible próximamente.
            </p>
          </div>
        )}
      </div>
    </ViewContainer>
  );
}
