import { useState, useEffect, useCallback } from 'react';
import clsx from 'clsx';
import { Settings, LogOut, FileText, User, Building2, CreditCard, Bell, AlertTriangle } from 'lucide-react';
import { useAuth } from "@/app/providers/AuthContext";
import { useUserProfile } from "@/shared/hooks/useUserProfile";
import { AccountSettings } from './tabs/AccountSettings';
import { ProfileSettingsSkeleton } from './ProfileSettingsSkeleton';
import { UserNotificationPreferences } from './UserNotificationPreferences';
import { useCompanySettings } from "@/shared/hooks/useCompanySettings";
import { useCompanySubscriptions, useUserNotificationPreferences } from "@/shared/hooks/useNotificationPreferences";
import { ViewContainer } from '@/shared/layouts/ViewContainer';
import { FizkoLogo } from '@/shared/ui/branding/FizkoLogo';
import { ChateableWrapper } from '@/shared/ui/ChateableWrapper';
import { SubscriptionSettings as SubscriptionPage } from '@/features/subscription/ui/SubscriptionSettings';
import type { ViewType } from '@/shared/layouts/NavigationPills';
import type { ColorScheme } from "@/shared/hooks/useColorScheme";
import type { Company } from "@/shared/types/fizko";

interface ProfileSettingsProps {
  scheme: ColorScheme;
  isInDrawer?: boolean;
  onNavigateBack?: () => void;
  company: Company | null;
  onThemeChange?: (scheme: ColorScheme) => void;
  onNavigateToContacts?: () => void;
  onNavigateToDashboard?: () => void;
  onNavigateToForms?: () => void;
  onNavigateToPersonnel?: () => void;
  currentView?: ViewType;
  initialTab?: 'account' | 'company' | 'preferences' | 'subscription' | 'danger';
}

export function ProfileSettings({ scheme, isInDrawer = false, onNavigateBack, company, onThemeChange, onNavigateToContacts, onNavigateToDashboard, onNavigateToForms, onNavigateToPersonnel, currentView = 'settings', initialTab = 'account' }: ProfileSettingsProps) {
  const { user, loading: authLoading } = useAuth();
  const { profile, loading: profileLoading } = useUserProfile();
  // Company is now passed as prop to avoid multiple fetches
  const [activeTab, setActiveTab] = useState<'account' | 'company' | 'preferences' | 'subscription' | 'danger'>(initialTab);

  // Pre-load notification preferences data (for Preferences tab)
  const { data: subscriptionsData, isLoading: loadingSubscriptions } = useCompanySubscriptions(company?.id);
  const { data: preferencesData, isLoading: loadingPreferences, error: preferencesError } = useUserNotificationPreferences(company?.id);

  // Pre-load company settings data (for Company tab)
  const { settings: companySettings, loading: companySettingsLoading } = useCompanySettings(company?.id);

  // Sync activeTab with initialTab when it changes
  useEffect(() => {
    setActiveTab(initialTab);
  }, [initialTab]);

  // Handle navigation
  const handleNavigate = useCallback((view: ViewType) => {
    if (view === 'dashboard' && onNavigateToDashboard) onNavigateToDashboard();
    if (view === 'contacts' && onNavigateToContacts) onNavigateToContacts();
    if (view === 'forms' && onNavigateToForms) onNavigateToForms();
    if (view === 'personnel' && onNavigateToPersonnel) onNavigateToPersonnel();
  }, [onNavigateToDashboard, onNavigateToContacts, onNavigateToForms, onNavigateToPersonnel]);

  const isLoading = authLoading || profileLoading || companySettingsLoading || loadingSubscriptions || loadingPreferences;

  const tabs = [
    { id: 'account' as const, label: 'Cuenta', icon: User },
    { id: 'company' as const, label: 'Empresa', icon: Building2 },
    { id: 'subscription' as const, label: 'Plan', icon: CreditCard },
    { id: 'preferences' as const, label: 'Preferencias', icon: Bell },
    { id: 'danger' as const, label: 'Peligro', icon: AlertTriangle, isDanger: true },
  ];

  // Show skeleton while loading
  if (isLoading && !user) {
    return <ProfileSettingsSkeleton />;
  }

  // Content for drawer view
  if (isInDrawer) {
    return (
      <div className="flex h-full flex-col overflow-hidden">
        <div className="flex-1 overflow-y-auto px-4 sm:px-6">
          <div className="flex flex-col pb-4">
            {/* Tabs */}
            <div className="flex gap-2 border-b border-slate-200/50 dark:border-slate-700/50 pb-0 mb-4 pt-2">
              {tabs.map((tab) => {
                const Icon = tab.icon;
                const isDanger = 'isDanger' in tab && tab.isDanger;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={clsx(
                      'border-b-2 px-4 py-2.5 text-base font-medium transition-colors flex items-center gap-2',
                      activeTab === tab.id
                        ? isDanger
                          ? 'border-red-600 text-red-600 dark:border-red-500 dark:text-red-500'
                          : 'border-emerald-600 text-emerald-600 dark:border-emerald-400 dark:text-emerald-400'
                        : isDanger
                          ? 'border-transparent text-red-600 hover:text-red-700 dark:text-red-500 dark:hover:text-red-400'
                          : 'border-transparent text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100'
                    )}
                  >
                    <Icon className="w-4 h-4" />
                    {tab.label}
                  </button>
                );
              })}
            </div>

            {/* Tab Content */}
            <div className="flex-1">
              {activeTab === 'account' && <AccountSettings user={user} scheme={scheme} profileLoading={profileLoading} profile={profile} isInDrawer={isInDrawer} />}
              {activeTab === 'company' && <CompanySettings company={company} scheme={scheme} isInDrawer={isInDrawer} preloadedSettings={companySettings} preloadedLoading={companySettingsLoading} />}
              {activeTab === 'subscription' && <SubscriptionPage />}
              {activeTab === 'preferences' && <PreferencesSettings scheme={scheme} isInDrawer={isInDrawer} company={company} subscriptionsData={subscriptionsData} preferencesData={preferencesData} loadingSubscriptions={loadingSubscriptions} loadingPreferences={loadingPreferences} preferencesError={preferencesError} />}
              {activeTab === 'danger' && <DangerZoneSettings user={user} scheme={scheme} />}
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Desktop view using ViewContainer
  return (
    <ViewContainer
      icon={<FizkoLogo className="h-7 w-7" />}
      iconGradient="from-white to-white"
      title="Configuración"
      subtitle="Administra tu perfil y preferencias"
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
            const isDanger = 'isDanger' in tab && tab.isDanger;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={clsx(
                  'border-b-2 px-4 py-3 text-base font-medium transition-colors flex items-center gap-2',
                  activeTab === tab.id
                    ? isDanger
                      ? 'border-red-600 text-red-600 dark:border-red-500 dark:text-red-500'
                      : 'border-emerald-600 text-emerald-600 dark:border-emerald-400 dark:text-emerald-400'
                    : isDanger
                      ? 'border-transparent text-red-600 hover:text-red-700 dark:text-red-500 dark:hover:text-red-400'
                      : 'border-transparent text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100'
                )}
              >
                <Icon className="w-4 h-4" />
                {tab.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 sm:p-6">
        {activeTab === 'account' && <AccountSettings user={user} scheme={scheme} profileLoading={profileLoading} profile={profile} />}
        {activeTab === 'company' && <CompanySettings company={company} scheme={scheme} preloadedSettings={companySettings} preloadedLoading={companySettingsLoading} />}
        {activeTab === 'subscription' && <SubscriptionPage />}
        {activeTab === 'preferences' && <PreferencesSettings scheme={scheme} company={company} subscriptionsData={subscriptionsData} preferencesData={preferencesData} loadingSubscriptions={loadingSubscriptions} loadingPreferences={loadingPreferences} preferencesError={preferencesError} />}
        {activeTab === 'danger' && <DangerZoneSettings user={user} scheme={scheme} />}
      </div>
    </ViewContainer>
  );
}

// Company Settings Tab
function CompanySettings({ company, scheme, isInDrawer = false, preloadedSettings, preloadedLoading }: { company: any; scheme: ColorScheme; isInDrawer?: boolean; preloadedSettings?: any; preloadedLoading?: boolean }) {
  const { settings: fetchedSettings, updateSettings, loading: fetchedLoading } = useCompanySettings(company?.id);
  // Use preloaded data if available, otherwise use fetched data
  const settings = preloadedSettings !== undefined ? preloadedSettings : fetchedSettings;
  const settingsLoading = preloadedLoading !== undefined ? preloadedLoading : fetchedLoading;
  const [isEditing, setIsEditing] = useState(false);
  const [editedSettings, setEditedSettings] = useState(settings);
  const [isSaving, setIsSaving] = useState(false);

  // Update local state when settings are loaded
  useEffect(() => {
    if (settings) {
      setEditedSettings(settings);
    }
  }, [settings]);

  if (!company) {
    return (
      <div className="rounded-lg border border-slate-200 bg-white p-6 text-center dark:border-slate-800 dark:bg-slate-900">
        <p className="text-sm text-slate-600 dark:text-slate-400">
          No hay empresa vinculada a esta cuenta
        </p>
      </div>
    );
  }

  const handleToggleSetting = (key: keyof typeof editedSettings) => {
    if (!editedSettings) return;
    const currentValue = editedSettings[key];
    // Cycle: null -> true -> false -> null
    let newValue: boolean | null;
    if (currentValue === null) {
      newValue = true;
    } else if (currentValue === true) {
      newValue = false;
    } else {
      newValue = null;
    }
    setEditedSettings({ ...editedSettings, [key]: newValue });
  };

  const handleSave = async () => {
    if (!editedSettings) return;
    setIsSaving(true);
    try {
      await updateSettings.mutateAsync({
        has_formal_employees: editedSettings.has_formal_employees,
        has_imports: editedSettings.has_imports,
        has_exports: editedSettings.has_exports,
        has_lease_contracts: editedSettings.has_lease_contracts,
      });
      setIsEditing(false);
    } catch (error) {
      console.error('Error updating settings:', error);
    } finally {
      setIsSaving(false);
    }
  };

  const handleCancel = () => {
    setEditedSettings(settings);
    setIsEditing(false);
  };

  const renderSettingIcon = (value: boolean | null) => {
    if (value === true) {
      return (
        <div className="flex h-6 w-6 items-center justify-center rounded-full bg-emerald-100 dark:bg-emerald-900/30">
          <svg className="h-4 w-4 text-emerald-600 dark:text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        </div>
      );
    } else if (value === false) {
      return (
        <div className="flex h-6 w-6 items-center justify-center rounded-full bg-red-100 dark:bg-red-900/30">
          <svg className="h-4 w-4 text-red-600 dark:text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </div>
      );
    } else {
      return (
        <div className="flex h-6 w-6 items-center justify-center rounded-full bg-slate-100 dark:bg-slate-800">
          <svg className="h-4 w-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
      );
    }
  };

  return (
    <div className={isInDrawer ? "space-y-0 divide-y divide-slate-200/50 dark:divide-slate-700/50" : "space-y-3"}>
      {/* Company Info Card - Compact */}
      <div className={isInDrawer ? "py-4" : "rounded-lg border border-slate-200 bg-white p-3 shadow-sm dark:border-slate-800 dark:bg-slate-900"}>
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-emerald-600 to-teal-700 text-base font-bold text-white shadow-sm">
            {company.business_name?.charAt(0).toUpperCase() || 'E'}
          </div>
          <div className="min-w-0 flex-1">
            <h3 className="truncate text-sm font-semibold text-slate-900 dark:text-slate-100">
              {company.business_name || 'Empresa'}
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              RUT: {company.rut || 'N/A'}
            </p>
          </div>
        </div>
      </div>

      {/* Company Details - Compact */}
      <div className={isInDrawer ? "py-4" : "rounded-lg border border-slate-200 bg-white p-3 shadow-sm dark:border-slate-800 dark:bg-slate-900"}>
        <div className="space-y-3">
          <div>
            <label className="block text-xs font-medium text-slate-700 dark:text-slate-300">
              Razón Social
            </label>
            <input
              type="text"
              value={company.business_name || ''}
              disabled
              className="mt-1 w-full rounded-lg border border-slate-200 bg-slate-50 px-2.5 py-1.5 text-sm text-slate-900 dark:border-slate-800 dark:bg-slate-800/50 dark:text-slate-100"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-700 dark:text-slate-300">
              RUT
            </label>
            <input
              type="text"
              value={company.rut || ''}
              disabled
              className="mt-1 w-full rounded-lg border border-slate-200 bg-slate-50 px-2.5 py-1.5 text-sm text-slate-900 dark:border-slate-800 dark:bg-slate-800/50 dark:text-slate-100"
            />
          </div>

          {company.trade_name && (
            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300">
                Nombre de Fantasía
              </label>
              <input
                type="text"
                value={company.trade_name}
                disabled
                className="mt-1 w-full rounded-lg border border-slate-200 bg-slate-50 px-2.5 py-1.5 text-sm text-slate-900 dark:border-slate-800 dark:bg-slate-800/50 dark:text-slate-100"
              />
            </div>
          )}
        </div>

        {/* SII Details button */}
        <div className="mt-3 pt-3 border-t border-slate-200 dark:border-slate-700">
          <ChateableWrapper
            message="Muéstrame la información detallada de mi empresa registrada en el SII, incluyendo socios, representantes, actividades económicas, direcciones, timbrajes y cumplimiento tributario"
            contextData={{
              companyId: company.id,
              companyRut: company.rut,
              companyName: company.business_name,
            }}
            uiComponent="company_sii_details"
            entityId={company.id}
            entityType="company"
          >
            <button className="flex items-center gap-2 rounded-lg bg-emerald-50 px-3 py-2 text-sm font-medium text-emerald-700 transition-colors hover:bg-emerald-100 dark:bg-emerald-900/30 dark:text-emerald-400 dark:hover:bg-emerald-900/50">
              <FileText className="h-4 w-4" />
              Ver Información Completa del SII
            </button>
          </ChateableWrapper>
        </div>
      </div>

      {/* Business Configuration Section */}
      <div className={isInDrawer ? "py-4" : "rounded-lg border border-slate-200 bg-white p-3 shadow-sm dark:border-slate-800 dark:bg-slate-900"}>
        <div className="mb-3 flex items-center justify-between">
          <div>
            <h4 className="text-sm font-semibold text-slate-900 dark:text-slate-100">
              Configuración del Negocio
            </h4>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Características operacionales de tu empresa
            </p>
          </div>
          {!isEditing ? (
            <button
              onClick={() => setIsEditing(true)}
              className="text-xs font-medium text-emerald-600 hover:text-emerald-700 dark:text-emerald-400 dark:hover:text-emerald-300"
            >
              Editar
            </button>
          ) : null}
        </div>

        {settingsLoading ? (
          <div className="py-4 text-center text-xs text-slate-500 dark:text-slate-400">
            Cargando configuración...
          </div>
        ) : editedSettings ? (
          <div className="space-y-2.5">
            {[
              { key: 'has_formal_employees', label: 'Empleados con contrato formal' },
              { key: 'has_imports', label: 'Realiza importaciones' },
              { key: 'has_exports', label: 'Realiza exportaciones' },
              { key: 'has_lease_contracts', label: 'Tiene contratos de arriendo' },
            ].map(({ key, label }) => (
              <div
                key={key}
                className="flex items-center justify-between rounded-lg border border-slate-200/50 bg-slate-50/30 p-2.5 dark:border-slate-700/50 dark:bg-slate-800/30"
              >
                <span className="text-xs font-medium text-slate-700 dark:text-slate-300">
                  {label}
                </span>
                {isEditing ? (
                  <button
                    onClick={() => handleToggleSetting(key as any)}
                    className="transition-transform hover:scale-105"
                  >
                    {renderSettingIcon(editedSettings[key as keyof typeof editedSettings] as boolean | null)}
                  </button>
                ) : (
                  renderSettingIcon(editedSettings[key as keyof typeof editedSettings] as boolean | null)
                )}
              </div>
            ))}

            {isEditing && (
              <div className="flex gap-2 pt-2">
                <button
                  onClick={handleSave}
                  disabled={isSaving}
                  className="flex-1 rounded-lg bg-emerald-600 py-2 text-xs font-medium text-white hover:bg-emerald-700 disabled:opacity-50 dark:bg-emerald-500 dark:hover:bg-emerald-600"
                >
                  {isSaving ? 'Guardando...' : 'Guardar cambios'}
                </button>
                <button
                  onClick={handleCancel}
                  disabled={isSaving}
                  className="flex-1 rounded-lg border border-slate-200 bg-white py-2 text-xs font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700"
                >
                  Cancelar
                </button>
              </div>
            )}
          </div>
        ) : (
          <div className="py-4 text-center text-xs text-slate-500 dark:text-slate-400">
            No hay configuración disponible
          </div>
        )}
      </div>

      <div className={isInDrawer ? "py-4" : "rounded-lg bg-amber-50 p-3 shadow-sm dark:bg-amber-950/30"}>
        <p className="text-xs text-amber-800 dark:text-amber-200">
          Los datos de la empresa son obtenidos del SII y no pueden ser modificados desde aquí.
        </p>
      </div>
    </div>
  );
}

// Preferences Settings Tab
function PreferencesSettings({
  scheme,
  isInDrawer = false,
  company,
  subscriptionsData,
  preferencesData,
  loadingSubscriptions,
  loadingPreferences,
  preferencesError
}: {
  scheme: ColorScheme;
  isInDrawer?: boolean;
  company: Company | null;
  subscriptionsData?: any[];
  preferencesData?: any;
  loadingSubscriptions?: boolean;
  loadingPreferences?: boolean;
  preferencesError?: Error | null;
}) {
  return (
    <div className={isInDrawer ? "space-y-0 divide-y divide-slate-200/50 dark:divide-slate-700/50" : "space-y-3"}>
      {/* Theme Preference - Compact */}
      <div className={isInDrawer ? "py-4" : "rounded-lg border border-slate-200 bg-white p-3 shadow-sm dark:border-slate-800 dark:bg-slate-900"}>
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <h4 className="text-sm font-semibold text-slate-900 dark:text-slate-100">
              Apariencia
            </h4>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              {scheme === 'dark' ? 'Modo oscuro' : 'Modo claro'}
            </p>
          </div>
          <div className="flex items-center gap-2">
            {scheme === 'dark' ? (
              <svg className="h-5 w-5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"
                />
              </svg>
            ) : (
              <svg className="h-5 w-5 text-amber-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
        <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">
          Cambia el tema usando el botón en el encabezado
        </p>
      </div>

      {/* Notifications - Real Implementation */}
      {company && company.id && (
        <UserNotificationPreferences
          companyId={company.id}
          isInDrawer={isInDrawer}
          subscriptionsData={subscriptionsData}
          preferencesData={preferencesData}
          loadingSubscriptions={loadingSubscriptions}
          loadingPreferences={loadingPreferences}
          preferencesError={preferencesError}
        />
      )}
    </div>
  );
}

// Subscription Settings Tab
function SubscriptionSettings({ scheme, isInDrawer = false }: { scheme: ColorScheme; isInDrawer?: boolean }) {
  const [showPlanComparison, setShowPlanComparison] = useState(false);

  return (
    <div className={isInDrawer ? "space-y-0 divide-y divide-slate-200/50 dark:divide-slate-700/50" : "space-y-4"}>
      {/* Current Plan Badge */}
      <div className={isInDrawer ? "py-4" : "rounded-lg border border-emerald-200 bg-gradient-to-r from-emerald-50 to-teal-50 p-3 dark:border-emerald-800 dark:from-emerald-950/30 dark:to-teal-950/30"}>
        <div className="flex items-center gap-2">
          <svg className="h-5 w-5 text-emerald-600 dark:text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
          <div>
            <p className="text-xs font-medium text-emerald-700 dark:text-emerald-300">
              Plan Actual: <span className="font-bold">Básico</span>
            </p>
          </div>
        </div>
      </div>

      {/* Plans Comparison */}
      <div className={isInDrawer ? "py-4" : ""}>
        <h4 className="mb-3 text-sm font-semibold text-slate-900 dark:text-slate-100">
          Planes Disponibles
        </h4>

        <div className={isInDrawer ? "space-y-3" : "grid gap-3 sm:grid-cols-2 max-w-2xl mx-auto"}>
          {/* Basic Plan */}
          <div className="rounded-lg border-2 border-slate-200 bg-white p-3 dark:border-slate-700 dark:bg-slate-900">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <h5 className="text-sm font-bold text-slate-900 dark:text-slate-100">
                  Básico
                </h5>
                <p className="mt-1 text-xs text-slate-600 dark:text-slate-400">
                  Perfecto para comenzar
                </p>
              </div>
              <div className="rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-semibold text-emerald-700 dark:bg-emerald-950/30 dark:text-emerald-400">
                Actual
              </div>
            </div>
            <div className="mt-3 flex items-baseline gap-1">
              <span className="text-2xl font-bold text-slate-900 dark:text-slate-100">0.25 UF</span>
              <span className="text-xs text-slate-600 dark:text-slate-400">/mes</span>
            </div>
          </div>

          {/* Professional Plan */}
          <div className="rounded-lg border-2 border-emerald-500 bg-white p-3 shadow-md dark:border-emerald-600 dark:bg-slate-900">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <h5 className="text-sm font-bold text-slate-900 dark:text-slate-100">
                  Profesional
                </h5>
                <p className="mt-1 text-xs text-slate-600 dark:text-slate-400">
                  Para pequeñas empresas
                </p>
              </div>
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-2xl font-bold text-emerald-600 dark:text-emerald-400">1 UF</span>
              <span className="text-xs text-slate-600 dark:text-slate-400">/mes</span>
            </div>
            <button
              disabled
              className="mt-3 w-full rounded-lg bg-emerald-600 px-3 py-2 text-xs font-semibold text-white opacity-50 transition-colors dark:bg-emerald-700"
            >
              Próximamente
            </button>
          </div>
        </div>

        {/* Plan Comparison Toggle */}
        <div className="mt-4 flex justify-center">
          <button
            onClick={() => setShowPlanComparison(!showPlanComparison)}
            className="flex items-center gap-2 rounded-lg bg-slate-100 px-4 py-2 text-xs font-medium text-slate-700 transition-colors hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700"
          >
            <span>Comparar planes</span>
            <svg
              className={clsx(
                "h-4 w-4 transition-transform",
                showPlanComparison && "rotate-180"
              )}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
        </div>

        {/* Plan Comparison Table */}
        {showPlanComparison && (
          <div className="mt-4 overflow-hidden rounded-lg border border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-900">
            <div className="overflow-x-auto">
              <table className="w-full min-w-[500px]">
                <thead>
                  <tr className="border-b border-slate-200 bg-slate-50 dark:border-slate-700 dark:bg-slate-800/50">
                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-700 dark:text-slate-300">
                      Característica
                    </th>
                    <th className="px-4 py-3 text-center text-xs font-semibold text-slate-700 dark:text-slate-300">
                      Básico
                    </th>
                    <th className="px-4 py-3 text-center text-xs font-semibold text-emerald-700 dark:text-emerald-400">
                      Profesional
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200 dark:divide-slate-700">
                  <tr className="hover:bg-slate-50 dark:hover:bg-slate-800/30">
                    <td className="px-4 py-3 text-xs text-slate-700 dark:text-slate-300">
                      Precio mensual
                    </td>
                    <td className="px-4 py-3 text-center text-xs font-medium text-slate-900 dark:text-slate-100">
                      0.25 UF
                    </td>
                    <td className="px-4 py-3 text-center text-xs font-medium text-emerald-600 dark:text-emerald-400">
                      1 UF
                    </td>
                  </tr>
                  <tr className="hover:bg-slate-50 dark:hover:bg-slate-800/30">
                    <td className="px-4 py-3 text-xs text-slate-700 dark:text-slate-300">
                      Sincronización con el SII
                    </td>
                    <td className="px-4 py-3 text-center">
                      <svg className="mx-auto h-5 w-5 text-emerald-600 dark:text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <svg className="mx-auto h-5 w-5 text-emerald-600 dark:text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                    </td>
                  </tr>
                  <tr className="hover:bg-slate-50 dark:hover:bg-slate-800/30">
                    <td className="px-4 py-3 text-xs text-slate-700 dark:text-slate-300">
                      Documentos
                    </td>
                    <td className="px-4 py-3 text-center text-xs text-slate-700 dark:text-slate-300">
                      Ilimitados
                    </td>
                    <td className="px-4 py-3 text-center text-xs text-slate-700 dark:text-slate-300">
                      Ilimitados
                    </td>
                  </tr>
                  <tr className="hover:bg-slate-50 dark:hover:bg-slate-800/30">
                    <td className="px-4 py-3 text-xs text-slate-700 dark:text-slate-300">
                      Asistente IA
                    </td>
                    <td className="px-4 py-3 text-center text-xs text-slate-700 dark:text-slate-300">
                      Básico
                    </td>
                    <td className="px-4 py-3 text-center text-xs text-slate-700 dark:text-slate-300">
                      Avanzado
                    </td>
                  </tr>
                  <tr className="hover:bg-slate-50 dark:hover:bg-slate-800/30">
                    <td className="px-4 py-3 text-xs text-slate-700 dark:text-slate-300">
                      Calendario tributario
                    </td>
                    <td className="px-4 py-3 text-center">
                      <svg className="mx-auto h-5 w-5 text-emerald-600 dark:text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <svg className="mx-auto h-5 w-5 text-emerald-600 dark:text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                    </td>
                  </tr>
                  <tr className="hover:bg-slate-50 dark:hover:bg-slate-800/30">
                    <td className="px-4 py-3 text-xs text-slate-700 dark:text-slate-300">
                      Resolución de F29
                    </td>
                    <td className="px-4 py-3 text-center">
                      <svg className="mx-auto h-5 w-5 text-slate-300 dark:text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <svg className="mx-auto h-5 w-5 text-emerald-600 dark:text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                    </td>
                  </tr>
                  <tr className="hover:bg-slate-50 dark:hover:bg-slate-800/30">
                    <td className="px-4 py-3 text-xs text-slate-700 dark:text-slate-300">
                      Reportes personalizados
                    </td>
                    <td className="px-4 py-3 text-center">
                      <svg className="mx-auto h-5 w-5 text-slate-300 dark:text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <svg className="mx-auto h-5 w-5 text-emerald-600 dark:text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                    </td>
                  </tr>
                  <tr className="hover:bg-slate-50 dark:hover:bg-slate-800/30">
                    <td className="px-4 py-3 text-xs text-slate-700 dark:text-slate-300">
                      Soporte
                    </td>
                    <td className="px-4 py-3 text-center text-xs text-slate-700 dark:text-slate-300">
                      Chat
                    </td>
                    <td className="px-4 py-3 text-center text-xs text-slate-700 dark:text-slate-300">
                      Chat + Email
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {/* Billing History */}
      <div className={isInDrawer ? "py-4" : "rounded-lg border border-slate-200 bg-white p-3 shadow-sm dark:border-slate-800 dark:bg-slate-900"}>
        <h4 className="mb-2 text-sm font-semibold text-slate-900 dark:text-slate-100">
          Historial de Facturación
        </h4>
        <p className="text-xs text-slate-600 dark:text-slate-400">
          No hay facturas disponibles para tu plan actual.
        </p>
      </div>
    </div>
  );
}

// Danger Zone Settings Tab
function DangerZoneSettings({ user, scheme }: { user: any; scheme: ColorScheme }) {
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [confirmText, setConfirmText] = useState('');
  const [isDeleting, setIsDeleting] = useState(false);

  const handleDeleteAccount = async () => {
    if (confirmText !== 'ELIMINAR') {
      return;
    }

    setIsDeleting(true);

    // TODO: Implement actual account deletion logic
    // This should call a backend endpoint to delete the user account
    try {
      // await deleteUserAccount();
      console.log('Account deletion requested');
      alert('Funcionalidad de eliminación de cuenta por implementar');
    } catch (error) {
      console.error('Error deleting account:', error);
      alert('Error al intentar eliminar la cuenta');
    } finally {
      setIsDeleting(false);
      setShowDeleteConfirm(false);
      setConfirmText('');
    }
  };

  return (
    <div className="space-y-6">
      {/* Warning Banner */}
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 dark:bg-red-900/20 dark:border-red-800">
        <div className="flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-red-600 dark:text-red-500 flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="font-semibold text-red-900 dark:text-red-300">
              Zona de Peligro
            </h3>
            <p className="text-sm text-red-700 dark:text-red-400 mt-1">
              Las acciones en esta sección son irreversibles y pueden resultar en pérdida permanente de datos.
            </p>
          </div>
        </div>
      </div>

      {/* Delete Account Section */}
      <div className="bg-white rounded-lg border border-slate-200 dark:bg-slate-900 dark:border-slate-800 overflow-hidden">
        <div className="p-6">
          <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-2">
            Eliminar cuenta
          </h3>
          <p className="text-sm text-slate-600 dark:text-slate-400 mb-4">
            Una vez que elimines tu cuenta, no hay vuelta atrás. Por favor, asegúrate de estar completamente seguro.
          </p>

          {!showDeleteConfirm ? (
            <button
              onClick={() => setShowDeleteConfirm(true)}
              className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white font-medium rounded-md transition-colors"
            >
              Eliminar mi cuenta
            </button>
          ) : (
            <div className="space-y-4 border-t border-slate-200 dark:border-slate-700 pt-4">
              <div>
                <p className="text-sm font-medium text-slate-900 dark:text-slate-100 mb-2">
                  ¿Estás absolutamente seguro?
                </p>
                <p className="text-sm text-slate-600 dark:text-slate-400 mb-4">
                  Esta acción no se puede deshacer. Esto eliminará permanentemente tu cuenta y todos los datos asociados.
                </p>
                <p className="text-sm text-slate-700 dark:text-slate-300 mb-2">
                  Por favor escribe <span className="font-mono font-bold text-red-600 dark:text-red-500">ELIMINAR</span> para confirmar:
                </p>
                <input
                  type="text"
                  value={confirmText}
                  onChange={(e) => setConfirmText(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-red-500 dark:bg-slate-800 dark:border-slate-600 dark:text-slate-100"
                  placeholder="Escribe ELIMINAR"
                />
              </div>

              <div className="flex gap-3">
                <button
                  onClick={handleDeleteAccount}
                  disabled={confirmText !== 'ELIMINAR' || isDeleting}
                  className={clsx(
                    'px-4 py-2 font-medium rounded-md transition-colors',
                    confirmText === 'ELIMINAR' && !isDeleting
                      ? 'bg-red-600 hover:bg-red-700 text-white'
                      : 'bg-slate-300 text-slate-500 cursor-not-allowed dark:bg-slate-700 dark:text-slate-500'
                  )}
                >
                  {isDeleting ? 'Eliminando...' : 'Confirmar eliminación'}
                </button>
                <button
                  onClick={() => {
                    setShowDeleteConfirm(false);
                    setConfirmText('');
                  }}
                  disabled={isDeleting}
                  className="px-4 py-2 bg-slate-200 hover:bg-slate-300 text-slate-700 font-medium rounded-md transition-colors dark:bg-slate-700 dark:hover:bg-slate-600 dark:text-slate-300"
                >
                  Cancelar
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Additional Warning */}
      <div className="bg-slate-50 border border-slate-200 rounded-lg p-4 dark:bg-slate-800/50 dark:border-slate-700">
        <p className="text-xs text-slate-600 dark:text-slate-400">
          <strong>Nota:</strong> Si tienes problemas con tu cuenta o deseas hacer una pausa temporal,
          te recomendamos contactar a nuestro equipo de soporte antes de eliminar tu cuenta.
        </p>
      </div>
    </div>
  );
}
