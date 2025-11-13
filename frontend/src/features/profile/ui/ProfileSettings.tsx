import { useState, useEffect, useCallback } from 'react';
import clsx from 'clsx';
import { User, Building2, CreditCard, Bell } from 'lucide-react';
import { useAuth } from "@/app/providers/AuthContext";
import { useUserProfile } from "@/shared/hooks/useUserProfile";
import { ProfileSettingsSkeleton } from './ProfileSettingsSkeleton';
import { useCompanySettings } from "@/shared/hooks/useCompanySettings";
import { useCompanySubscriptions, useUserNotificationPreferences } from "@/shared/hooks/useNotificationPreferences";
import { ViewContainer } from '@/shared/layouts/ViewContainer';
import { FizkoLogo } from '@/shared/ui/branding/FizkoLogo';
import { ProfileTab } from './tabs/ProfileTab';
import { CompanyTab } from './tabs/CompanyTab';
import { PreferencesTab } from './tabs/PreferencesTab';
import { SubscriptionTab } from './tabs/SubscriptionTab';
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
  const [activeTab, setActiveTab] = useState<'profile' | 'company' | 'preferences' | 'subscription'>(
    initialTab === 'account' ? 'profile' :
    initialTab === 'danger' ? 'subscription' :
    initialTab
  );

  // Pre-load notification preferences data (for Preferences tab)
  const { data: subscriptionsData, isLoading: loadingSubscriptions } = useCompanySubscriptions(company?.id);
  const { data: preferencesData, isLoading: loadingPreferences, error: preferencesError } = useUserNotificationPreferences(company?.id);

  // Pre-load company settings data (for Profile tab)
  const { settings: companySettings, loading: companySettingsLoading } = useCompanySettings(company?.id);

  // Sync activeTab with initialTab when it changes
  useEffect(() => {
    const mappedTab = initialTab === 'account' ? 'profile' :
                      initialTab === 'danger' ? 'subscription' :
                      initialTab as 'profile' | 'company' | 'preferences' | 'subscription';
    setActiveTab(mappedTab);
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
    { id: 'profile' as const, label: 'Perfil', icon: User },
    { id: 'company' as const, label: 'Mi Empresa', icon: Building2 },
    { id: 'preferences' as const, label: 'Preferencias', icon: Bell },
    { id: 'subscription' as const, label: 'Suscripción', icon: CreditCard },
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
            {/* Tabs - Responsive with horizontal scroll on mobile */}
            <div className="overflow-x-auto border-b border-slate-200/50 dark:border-slate-700/50 mb-4 pt-2 -mx-4 px-4 sm:mx-0 sm:px-0">
              <div className="flex gap-0 pb-0 min-w-max">
                {tabs.map((tab) => {
                  const Icon = tab.icon;
                  const isDanger = 'isDanger' in tab && tab.isDanger;
                  return (
                    <button
                      key={tab.id}
                      onClick={() => setActiveTab(tab.id)}
                      className={clsx(
                        'border-b-2 px-4 sm:px-5 py-3 text-sm sm:text-base font-semibold transition-all flex items-center gap-0.5 sm:gap-2 whitespace-nowrap',
                        activeTab === tab.id
                          ? 'border-emerald-600 text-emerald-600 dark:border-emerald-400 dark:text-emerald-400'
                          : 'border-transparent text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100'
                      )}
                    >
                      <Icon className="w-4 h-4 flex-shrink-0" />
                      <span className="hidden sm:inline">{tab.label}</span>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Tab Content */}
            <div className="flex-1">
              {activeTab === 'profile' && <ProfileTab user={user} scheme={scheme} profileLoading={profileLoading} profile={profile} isInDrawer={isInDrawer} />}
              {activeTab === 'company' && <CompanyTab company={company} scheme={scheme} isInDrawer={isInDrawer} preloadedSettings={companySettings} preloadedLoading={companySettingsLoading} />}
              {activeTab === 'preferences' && <PreferencesTab scheme={scheme} isInDrawer={isInDrawer} company={company} subscriptionsData={subscriptionsData} preferencesData={preferencesData} loadingSubscriptions={loadingSubscriptions} loadingPreferences={loadingPreferences} preferencesError={preferencesError} />}
              {activeTab === 'subscription' && <SubscriptionTab scheme={scheme} isInDrawer={isInDrawer} />}
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
                  'border-b-2 px-5 py-3 text-base font-semibold transition-all flex items-center gap-2',
                  activeTab === tab.id
                    ? 'border-emerald-600 text-emerald-600 dark:border-emerald-400 dark:text-emerald-400'
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
        {activeTab === 'profile' && <ProfileTab user={user} scheme={scheme} profileLoading={profileLoading} profile={profile} />}
        {activeTab === 'company' && <CompanyTab company={company} scheme={scheme} preloadedSettings={companySettings} preloadedLoading={companySettingsLoading} />}
        {activeTab === 'preferences' && <PreferencesTab scheme={scheme} company={company} subscriptionsData={subscriptionsData} preferencesData={preferencesData} loadingSubscriptions={loadingSubscriptions} loadingPreferences={loadingPreferences} preferencesError={preferencesError} />}
        {activeTab === 'subscription' && <SubscriptionTab scheme={scheme} />}
      </div>
    </ViewContainer>
  );
}
