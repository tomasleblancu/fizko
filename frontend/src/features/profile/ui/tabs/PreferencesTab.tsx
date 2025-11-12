import { UserNotificationPreferences } from '../UserNotificationPreferences';
import type { ColorScheme } from '@/shared/hooks/useColorScheme';
import type { Company } from '@/shared/types/fizko';

interface PreferencesTabProps {
  scheme: ColorScheme;
  isInDrawer?: boolean;
  company: Company | null;
  subscriptionsData?: any[];
  preferencesData?: any;
  loadingSubscriptions?: boolean;
  loadingPreferences?: boolean;
  preferencesError?: Error | null;
}

export function PreferencesTab({
  scheme,
  isInDrawer = false,
  company,
  subscriptionsData,
  preferencesData,
  loadingSubscriptions,
  loadingPreferences,
  preferencesError
}: PreferencesTabProps) {
  return (
    <div className="space-y-6">
      {/* Theme Preference */}
      <div>
        <h3 className="mb-3 text-lg font-semibold text-slate-900 dark:text-slate-100">
          Apariencia
        </h3>
        <div className="flex items-center justify-between rounded-lg border border-slate-200 bg-white px-4 py-3.5 dark:border-slate-700 dark:bg-slate-800/50">
          <div className="flex-1">
            <p className="text-sm font-medium text-slate-700 dark:text-slate-300">
              {scheme === 'dark' ? 'Modo oscuro' : 'Modo claro'}
            </p>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              Cambia el tema usando el botón en el encabezado
            </p>
          </div>
          <div className="flex items-center gap-3">
            {scheme === 'dark' ? (
              <svg className="h-6 w-6 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"
                />
              </svg>
            ) : (
              <svg className="h-6 w-6 text-amber-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"
                />
              </svg>
            )}
          </div>
        </div>
      </div>

      {/* Notifications */}
      {company && company.id && (
        <div>
          <h3 className="mb-3 text-lg font-semibold text-slate-900 dark:text-slate-100">
            Notificaciones
          </h3>
          <UserNotificationPreferences
            companyId={company.id}
            isInDrawer={false}
            subscriptionsData={subscriptionsData}
            preferencesData={preferencesData}
            loadingSubscriptions={loadingSubscriptions}
            loadingPreferences={loadingPreferences}
            preferencesError={preferencesError}
          />
        </div>
      )}
    </div>
  );
}
