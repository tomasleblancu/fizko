import { useState, useEffect, useCallback } from 'react';
import clsx from 'clsx';
import { Settings, LogOut } from 'lucide-react';
import { useAuth } from "@/app/providers/AuthContext";
import { useUserProfile } from "@/shared/hooks/useUserProfile";
import { ProfileSettingsSkeleton } from './ProfileSettingsSkeleton';
import { UserNotificationPreferences } from './UserNotificationPreferences';
import { useCompanySettings } from "@/shared/hooks/useCompanySettings";
import { ViewContainer } from '@/shared/layouts/ViewContainer';
import { FizkoLogo } from '@/shared/ui/branding/FizkoLogo';
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
  onNavigateToPersonnel?: () => void;
  currentView?: ViewType;
  initialTab?: 'account' | 'company' | 'preferences' | 'subscription';
}

export function ProfileSettings({ scheme, isInDrawer = false, onNavigateBack, company, onThemeChange, onNavigateToContacts, onNavigateToDashboard, onNavigateToPersonnel, currentView = 'settings', initialTab = 'account' }: ProfileSettingsProps) {
  const { user, loading: authLoading } = useAuth();
  const { profile, loading: profileLoading } = useUserProfile();
  // Company is now passed as prop to avoid multiple fetches
  const [activeTab, setActiveTab] = useState<'account' | 'company' | 'preferences' | 'subscription'>(initialTab);

  // Sync activeTab with initialTab when it changes
  useEffect(() => {
    setActiveTab(initialTab);
  }, [initialTab]);

  // Handle navigation
  const handleNavigate = useCallback((view: ViewType) => {
    if (view === 'dashboard' && onNavigateToDashboard) onNavigateToDashboard();
    if (view === 'contacts' && onNavigateToContacts) onNavigateToContacts();
    if (view === 'personnel' && onNavigateToPersonnel) onNavigateToPersonnel();
  }, [onNavigateToDashboard, onNavigateToContacts, onNavigateToPersonnel]);

  const isLoading = authLoading || profileLoading;

  const tabs = [
    { id: 'account' as const, label: 'Cuenta' },
    { id: 'company' as const, label: 'Empresa' },
    { id: 'subscription' as const, label: 'Suscripción' },
    { id: 'preferences' as const, label: 'Preferencias' },
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
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={clsx(
                    'border-b-2 px-4 py-2.5 text-base font-medium transition-colors',
                    activeTab === tab.id
                      ? 'border-emerald-600 text-emerald-600 dark:border-emerald-400 dark:text-emerald-400'
                      : 'border-transparent text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100'
                  )}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            {/* Tab Content */}
            <div className="flex-1">
              {activeTab === 'account' && <AccountSettings user={user} scheme={scheme} profileLoading={profileLoading} profile={profile} isInDrawer={isInDrawer} />}
              {activeTab === 'company' && <CompanySettings company={company} scheme={scheme} isInDrawer={isInDrawer} />}
              {activeTab === 'subscription' && <SubscriptionSettings scheme={scheme} isInDrawer={isInDrawer} />}
              {activeTab === 'preferences' && <PreferencesSettings scheme={scheme} isInDrawer={isInDrawer} company={company} />}
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
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={clsx(
                'border-b-2 px-4 py-3 text-base font-medium transition-colors',
                activeTab === tab.id
                  ? 'border-emerald-600 text-emerald-600 dark:border-emerald-400 dark:text-emerald-400'
                  : 'border-transparent text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100'
              )}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 sm:p-6">
        {activeTab === 'account' && <AccountSettings user={user} scheme={scheme} profileLoading={profileLoading} profile={profile} />}
        {activeTab === 'company' && <CompanySettings company={company} scheme={scheme} />}
        {activeTab === 'subscription' && <SubscriptionSettings scheme={scheme} />}
        {activeTab === 'preferences' && <PreferencesSettings scheme={scheme} company={company} />}
      </div>
    </ViewContainer>
  );
}

// Account Settings Tab
function AccountSettings({ user, scheme, profileLoading, profile: profileProp, isInDrawer = false }: { user: any; scheme: ColorScheme; profileLoading: boolean; profile: any; isInDrawer?: boolean }) {
  const { profile, updateProfile, requestPhoneVerification, confirmPhoneVerification, error: profileError } = useUserProfile();
  const { signOut } = useAuth();
  const [nombre, setNombre] = useState('');
  const [apellido, setApellido] = useState('');
  const [celular, setCelular] = useState('');
  const [isEditing, setIsEditing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [showVerificationModal, setShowVerificationModal] = useState(false);
  const [verificationCode, setVerificationCode] = useState('');
  const [isVerifying, setIsVerifying] = useState(false);
  const [isSendingCode, setIsSendingCode] = useState(false);

  // Load profile data when available
  useEffect(() => {
    if (profile) {
      setNombre(profile.name || '');
      setApellido(profile.lastname || '');
      // Format phone number with country code separation
      const phone = profile.phone || '';
      if (!phone) {
        setCelular('+');
      } else {
        const cleanPhone = phone.replace(/\D/g, '');
        if (cleanPhone.length > 0) {
          const countryCodeLength = cleanPhone.length >= 2 ? (cleanPhone.startsWith('56') || cleanPhone.startsWith('1') ? 2 : 3) : cleanPhone.length;
          const countryCode = cleanPhone.slice(0, countryCodeLength);
          const number = cleanPhone.slice(countryCodeLength);
          setCelular(number ? `+${countryCode} ${number}` : `+${countryCode}`);
        } else {
          setCelular('+');
        }
      }
    }
  }, [profile]);

  const handlePhoneChange = (value: string) => {
    // Always keep the + prefix
    if (!value.startsWith('+')) {
      setCelular('+');
      return;
    }

    // Only allow + at the beginning and digits after
    const cleaned = value.slice(1).replace(/\D/g, '');

    // Format: +XX XXXXXXXXX (country code with space before number)
    let formatted = '+';
    if (cleaned.length > 0) {
      // First 1-3 digits are country code
      const countryCodeLength = cleaned.length >= 2 ? (cleaned.startsWith('56') || cleaned.startsWith('1') ? 2 : 3) : cleaned.length;
      const countryCode = cleaned.slice(0, countryCodeLength);
      const number = cleaned.slice(countryCodeLength);

      formatted = '+' + countryCode;
      if (number.length > 0) {
        formatted += ' ' + number;
      }
    }

    setCelular(formatted);
  };

  const handleSave = async () => {
    setIsSaving(true);
    // Remove formatting and only save the raw phone number
    const cleanedPhone = celular.replace(/\s/g, '');
    const phoneToSave = cleanedPhone.length > 1 ? cleanedPhone : null;
    const success = await updateProfile({
      name: nombre,
      lastname: apellido,
      phone: phoneToSave || undefined,
    });
    setIsSaving(false);
    if (success) {
      setIsEditing(false);
    }
  };

  const handleCancel = () => {
    setIsEditing(false);
    // Reset fields to original values from profile
    if (profile) {
      setNombre(profile.name || '');
      setApellido(profile.lastname || '');
      // Reformat phone on cancel
      const phone = profile.phone || '';
      if (!phone) {
        setCelular('+');
      } else {
        const cleanPhone = phone.replace(/\D/g, '');
        if (cleanPhone.length > 0) {
          const countryCodeLength = cleanPhone.length >= 2 ? (cleanPhone.startsWith('56') || cleanPhone.startsWith('1') ? 2 : 3) : cleanPhone.length;
          const countryCode = cleanPhone.slice(0, countryCodeLength);
          const number = cleanPhone.slice(countryCodeLength);
          setCelular(number ? `+${countryCode} ${number}` : `+${countryCode}`);
        } else {
          setCelular('+');
        }
      }
    }
  };

  const handleRequestVerification = async () => {
    // Open modal immediately for better UX
    setShowVerificationModal(true);
    setIsSendingCode(true);

    // Then send the verification code in the background
    const success = await requestPhoneVerification();
    setIsSendingCode(false);

    // If failed, close the modal and show error
    if (!success) {
      setShowVerificationModal(false);
    }
  };

  const handleConfirmVerification = async () => {
    if (verificationCode.length !== 6) {
      return;
    }
    setIsVerifying(true);
    const success = await confirmPhoneVerification(verificationCode);
    setIsVerifying(false);
    if (success) {
      setShowVerificationModal(false);
      setVerificationCode('');
    }
  };

  return (
    <div className={isInDrawer ? "space-y-0 divide-y divide-slate-200/50 dark:divide-slate-700/50" : "space-y-3"}>
      {/* User Info Card - Compact */}
      <div className={isInDrawer ? "py-4" : "rounded-lg border border-slate-200 bg-white p-3 shadow-sm dark:border-slate-800 dark:bg-slate-900"}>
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-emerald-600 to-teal-700 text-base font-bold text-white shadow-sm">
            {user?.email?.charAt(0).toUpperCase() || '?'}
          </div>
          <div className="min-w-0 flex-1">
            <h3 className="truncate text-base font-semibold text-slate-900 dark:text-slate-100">
              {user?.email || 'Usuario'}
            </h3>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              Cuenta activa
            </p>
          </div>
        </div>
      </div>

      {/* Contact Information Section - Compact */}
      <div className={isInDrawer ? "py-4" : "rounded-lg border border-slate-200 bg-white p-3 shadow-sm dark:border-slate-800 dark:bg-slate-900"}>
        <div className="mb-3 flex items-center justify-between">
          <h4 className="text-base font-semibold text-slate-900 dark:text-slate-100">
            Información de Contacto
          </h4>
          {!isEditing ? (
            <button
              onClick={() => setIsEditing(true)}
              className="text-sm font-medium text-emerald-600 hover:text-emerald-700 dark:text-emerald-400 dark:hover:text-emerald-300"
            >
              Editar
            </button>
          ) : (
            <div className="flex gap-2">
              <button
                onClick={handleCancel}
                disabled={isSaving}
                className="text-xs font-medium text-slate-600 hover:text-slate-700 disabled:opacity-50 dark:text-slate-400 dark:hover:text-slate-300"
              >
                Cancelar
              </button>
              <button
                onClick={handleSave}
                disabled={isSaving}
                className="text-xs font-medium text-emerald-600 hover:text-emerald-700 disabled:opacity-50 dark:text-emerald-400 dark:hover:text-emerald-300"
              >
                {isSaving ? 'Guardando...' : 'Guardar'}
              </button>
            </div>
          )}
        </div>

        <div className="space-y-3">
          {/* Nombre y Apellido en una fila */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300">
                Nombre
              </label>
              {!profile && profileLoading ? (
                <div className="mt-1 h-8 w-full animate-pulse rounded-lg bg-slate-200 dark:bg-slate-700" />
              ) : (
                <input
                  type="text"
                  value={nombre}
                  onChange={(e) => setNombre(e.target.value)}
                  disabled={!isEditing}
                  placeholder="Ingresa tu nombre"
                  className={clsx(
                    "mt-1 w-full rounded-lg border px-2.5 py-1.5 text-sm transition-colors",
                    isEditing
                      ? "border-slate-300 bg-white text-slate-900 focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
                      : "border-slate-200 bg-slate-50 text-slate-900 dark:border-slate-800 dark:bg-slate-800/50 dark:text-slate-100"
                  )}
                />
              )}
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300">
                Apellido
              </label>
              {!profile && profileLoading ? (
                <div className="mt-1 h-8 w-full animate-pulse rounded-lg bg-slate-200 dark:bg-slate-700" />
              ) : (
                <input
                  type="text"
                  value={apellido}
                  onChange={(e) => setApellido(e.target.value)}
                  disabled={!isEditing}
                  placeholder="Ingresa tu apellido"
                  className={clsx(
                    "mt-1 w-full rounded-lg border px-2.5 py-1.5 text-sm transition-colors",
                    isEditing
                      ? "border-slate-300 bg-white text-slate-900 focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
                      : "border-slate-200 bg-slate-50 text-slate-900 dark:border-slate-800 dark:bg-slate-800/50 dark:text-slate-100"
                  )}
                />
              )}
            </div>
          </div>

          {/* Celular */}
          <div>
            <label className="block text-xs font-medium text-slate-700 dark:text-slate-300">
              Celular
            </label>
            {!profile && profileLoading ? (
              <div className="mt-1 h-8 w-full animate-pulse rounded-lg bg-slate-200 dark:bg-slate-700" />
            ) : (
              <input
                type="tel"
                value={celular}
                onChange={(e) => handlePhoneChange(e.target.value)}
                disabled={!isEditing}
                placeholder="+56 912345678"
                inputMode="numeric"
                className={clsx(
                  "mt-1 w-full rounded-lg border px-2.5 py-1.5 text-sm transition-colors",
                  isEditing
                    ? "border-slate-300 bg-white text-slate-900 focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
                    : "border-slate-200 bg-slate-50 text-slate-900 dark:border-slate-800 dark:bg-slate-800/50 dark:text-slate-100"
                )}
              />
            )}
          </div>

          {/* Phone Verification Status - More compact */}
          {celular && celular !== '+' && (
            <div className="flex items-center justify-between rounded-lg bg-slate-50 px-2.5 py-2 dark:bg-slate-800/50">
              <div className="flex items-center gap-2">
                {profile?.phone_verified ? (
                  <>
                    <svg className="h-4 w-4 text-emerald-600 dark:text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <span className="text-xs font-medium text-emerald-700 dark:text-emerald-300">
                      Verificado
                    </span>
                  </>
                ) : (
                  <>
                    <svg className="h-4 w-4 text-amber-600 dark:text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                    <span className="text-xs font-medium text-amber-700 dark:text-amber-300">
                      No verificado
                    </span>
                  </>
                )}
              </div>
              {!profile?.phone_verified && !isEditing && (
                <button
                  onClick={handleRequestVerification}
                  className="text-xs font-medium text-emerald-600 hover:text-emerald-700 dark:text-emerald-400 dark:hover:text-emerald-300"
                >
                  Verificar
                </button>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Verification Modal */}
      {showVerificationModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
          <div className="mx-4 w-full max-w-md rounded-2xl border border-slate-200 bg-white p-6 shadow-2xl dark:border-slate-700 dark:bg-slate-800">
            <div className="flex items-center gap-3 mb-4">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-emerald-100 dark:bg-emerald-900/30">
                <svg className="h-6 w-6 text-emerald-600 dark:text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
              </div>
              <div>
                <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
                  Verificar Teléfono
                </h3>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  Código enviado por WhatsApp
                </p>
              </div>
            </div>

            {isSendingCode ? (
              <div className="text-center py-8">
                <div className="inline-flex items-center gap-3">
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-emerald-600 dark:border-emerald-400"></div>
                  <p className="text-sm text-slate-600 dark:text-slate-400">
                    Enviando código por WhatsApp a <span className="font-semibold text-slate-900 dark:text-slate-100">{celular}</span>
                  </p>
                </div>
              </div>
            ) : (
              <>
                <p className="text-sm text-slate-600 dark:text-slate-400">
                  Ingresa el código de 6 dígitos que te enviamos por WhatsApp a <span className="font-semibold text-slate-900 dark:text-slate-100">{celular}</span>
                </p>

                <div className="mt-6">
                  <input
                    type="text"
                    value={verificationCode}
                    onChange={(e) => {
                      const value = e.target.value.replace(/\D/g, '').slice(0, 6);
                      setVerificationCode(value);
                    }}
                    placeholder="000000"
                    maxLength={6}
                    inputMode="numeric"
                    autoFocus
                    className="w-full rounded-lg border border-slate-300 bg-white px-4 py-3 text-center text-2xl tracking-widest text-slate-900 focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
                  />
                  <p className="mt-2 text-xs text-slate-500 dark:text-slate-400 text-center">
                    El código expira en 10 minutos
                  </p>
                </div>
              </>
            )}

            {profileError && (
              <div className="mt-4 rounded-lg bg-red-50 px-3 py-2 dark:bg-red-900/20">
                <p className="text-xs text-red-700 dark:text-red-300">
                  {profileError}
                </p>
              </div>
            )}

            <div className="mt-6 flex gap-3">
              <button
                onClick={() => {
                  setShowVerificationModal(false);
                  setVerificationCode('');
                  setIsSendingCode(false);
                }}
                disabled={isVerifying || isSendingCode}
                className="flex-1 rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700"
              >
                Cancelar
              </button>
              <button
                onClick={handleConfirmVerification}
                disabled={isVerifying || isSendingCode || verificationCode.length !== 6}
                className="flex-1 rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50 dark:bg-emerald-500 dark:hover:bg-emerald-600"
              >
                {isVerifying ? 'Verificando...' : 'Verificar'}
              </button>
            </div>

            {!isSendingCode && (
              <div className="mt-4 text-center">
                <button
                  onClick={handleRequestVerification}
                  disabled={isVerifying}
                  className="text-xs text-emerald-600 hover:text-emerald-700 dark:text-emerald-400 dark:hover:text-emerald-300 disabled:opacity-50"
                >
                  Reenviar código
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Email - Compact */}
      <div className={isInDrawer ? "py-4" : "rounded-lg border border-slate-200 bg-white p-3 shadow-sm dark:border-slate-800 dark:bg-slate-900"}>
        <label className="block text-xs font-medium text-slate-700 dark:text-slate-300">
          Email
        </label>
        <input
          type="email"
          value={user?.email || ''}
          disabled
          className="mt-1 w-full rounded-lg border border-slate-200 bg-slate-50 px-2.5 py-1.5 text-sm text-slate-900 dark:border-slate-800 dark:bg-slate-800/50 dark:text-slate-100"
        />
        <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
          El email no puede ser modificado
        </p>
      </div>

      {/* SII Credentials Section - Compact */}
      <div className={isInDrawer ? "py-4" : "rounded-lg border border-slate-200 bg-white p-3 shadow-sm dark:border-slate-800 dark:bg-slate-900"}>
        <h4 className="mb-2 text-sm font-semibold text-slate-900 dark:text-slate-100">
          Credenciales SII
        </h4>
        <p className="text-xs text-slate-600 dark:text-slate-400">
          Las credenciales del SII están vinculadas a tu cuenta. Para modificarlas, contacta a soporte.
        </p>
      </div>

      {/* Logout Section - Compact */}
      <div className={isInDrawer ? "py-4" : "rounded-lg border border-red-200 bg-red-50 p-3 shadow-sm dark:border-red-800 dark:bg-red-900/20"}>
        <div className="flex items-center justify-between">
          <div>
            <h4 className="text-sm font-semibold text-red-900 dark:text-red-100">
              Cerrar Sesión
            </h4>
            <p className="mt-1 text-xs text-red-700 dark:text-red-300">
              Finaliza tu sesión actual
            </p>
          </div>
          <button
            onClick={signOut}
            className="flex items-center gap-1.5 rounded-lg bg-red-600 px-3 py-1.5 text-xs font-medium text-white transition-colors hover:bg-red-700 dark:bg-red-700 dark:hover:bg-red-800"
          >
            <LogOut className="h-3.5 w-3.5" />
            Cerrar
          </button>
        </div>
      </div>
    </div>
  );
}

// Company Settings Tab
function CompanySettings({ company, scheme, isInDrawer = false }: { company: any; scheme: ColorScheme; isInDrawer?: boolean }) {
  const { settings, updateSettings, loading: settingsLoading } = useCompanySettings(company?.id);
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
            {company.razon_social?.charAt(0).toUpperCase() || 'E'}
          </div>
          <div className="min-w-0 flex-1">
            <h3 className="truncate text-sm font-semibold text-slate-900 dark:text-slate-100">
              {company.razon_social || 'Empresa'}
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
              value={company.razon_social || ''}
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

          {company.giro && (
            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300">
                Giro
              </label>
              <input
                type="text"
                value={company.giro}
                disabled
                className="mt-1 w-full rounded-lg border border-slate-200 bg-slate-50 px-2.5 py-1.5 text-sm text-slate-900 dark:border-slate-800 dark:bg-slate-800/50 dark:text-slate-100"
              />
            </div>
          )}
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
function PreferencesSettings({ scheme, isInDrawer = false, company }: { scheme: ColorScheme; isInDrawer?: boolean; company: Company | null }) {
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
        <UserNotificationPreferences companyId={company.id} isInDrawer={isInDrawer} />
      )}
    </div>
  );
}

// Subscription Settings Tab
function SubscriptionSettings({ scheme, isInDrawer = false }: { scheme: ColorScheme; isInDrawer?: boolean }) {
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

        <div className={isInDrawer ? "space-y-3" : "grid gap-3 sm:grid-cols-2 lg:grid-cols-3"}>
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
              <span className="text-2xl font-bold text-slate-900 dark:text-slate-100">$9.990</span>
              <span className="text-xs text-slate-600 dark:text-slate-400">/mes</span>
            </div>
            <ul className="mt-3 space-y-2">
              <li className="flex items-start gap-2 text-xs text-slate-700 dark:text-slate-300">
                <svg className="h-4 w-4 flex-shrink-0 text-emerald-600 dark:text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                Sincronización básica con SII
              </li>
              <li className="flex items-start gap-2 text-xs text-slate-700 dark:text-slate-300">
                <svg className="h-4 w-4 flex-shrink-0 text-emerald-600 dark:text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                Hasta 100 documentos/mes
              </li>
              <li className="flex items-start gap-2 text-xs text-slate-700 dark:text-slate-300">
                <svg className="h-4 w-4 flex-shrink-0 text-emerald-600 dark:text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                Asistente IA básico
              </li>
              <li className="flex items-start gap-2 text-xs text-slate-700 dark:text-slate-300">
                <svg className="h-4 w-4 flex-shrink-0 text-emerald-600 dark:text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                Calendario tributario
              </li>
            </ul>
          </div>

          {/* Professional Plan - 50% OFF */}
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
              <div className="rounded-full bg-amber-100 px-2 py-0.5 text-xs font-semibold text-amber-700 dark:bg-amber-950/30 dark:text-amber-400">
                50% OFF
              </div>
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-xs text-slate-500 line-through dark:text-slate-400">$39.990</span>
              <span className="text-2xl font-bold text-emerald-600 dark:text-emerald-400">$19.990</span>
              <span className="text-xs text-slate-600 dark:text-slate-400">/mes</span>
            </div>
            <p className="mt-1 text-xs text-amber-700 dark:text-amber-400">
              Primeros 3 meses con descuento
            </p>
            <ul className="mt-3 space-y-2">
              <li className="flex items-start gap-2 text-xs text-slate-700 dark:text-slate-300">
                <svg className="h-4 w-4 flex-shrink-0 text-emerald-600 dark:text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                Resolución de F29
              </li>
              <li className="flex items-start gap-2 text-xs text-slate-700 dark:text-slate-300">
                <svg className="h-4 w-4 flex-shrink-0 text-emerald-600 dark:text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                Todo lo del plan Básico
              </li>
              <li className="flex items-start gap-2 text-xs text-slate-700 dark:text-slate-300">
                <svg className="h-4 w-4 flex-shrink-0 text-emerald-600 dark:text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                Documentos ilimitados
              </li>
              <li className="flex items-start gap-2 text-xs text-slate-700 dark:text-slate-300">
                <svg className="h-4 w-4 flex-shrink-0 text-emerald-600 dark:text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                Asistente IA avanzado
              </li>
              <li className="flex items-start gap-2 text-xs text-slate-700 dark:text-slate-300">
                <svg className="h-4 w-4 flex-shrink-0 text-emerald-600 dark:text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                Reportes personalizados
              </li>
              <li className="flex items-start gap-2 text-xs text-slate-700 dark:text-slate-300">
                <svg className="h-4 w-4 flex-shrink-0 text-emerald-600 dark:text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                Soporte por email
              </li>
            </ul>
            <button
              disabled
              className="mt-3 w-full rounded-lg bg-emerald-600 px-3 py-2 text-xs font-semibold text-white opacity-50 transition-colors dark:bg-emerald-700"
            >
              Próximamente
            </button>
          </div>

          {/* Premium Plan */}
          <div className="rounded-lg border-2 border-slate-200 bg-white p-3 dark:border-slate-700 dark:bg-slate-900">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <h5 className="text-sm font-bold text-slate-900 dark:text-slate-100">
                  Premium
                </h5>
                <p className="mt-1 text-xs text-slate-600 dark:text-slate-400">
                  Para empresas en crecimiento
                </p>
              </div>
            </div>
            <div className="mt-3 flex items-baseline gap-1">
              <span className="text-2xl font-bold text-slate-900 dark:text-slate-100">$79.990</span>
              <span className="text-xs text-slate-600 dark:text-slate-400">/mes</span>
            </div>
            <ul className="mt-3 space-y-2">
              <li className="flex items-start gap-2 text-xs text-slate-700 dark:text-slate-300">
                <svg className="h-4 w-4 flex-shrink-0 text-emerald-600 dark:text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                Todo lo del plan Básico
              </li>
              <li className="flex items-start gap-2 text-xs text-slate-700 dark:text-slate-300">
                <svg className="h-4 w-4 flex-shrink-0 text-emerald-600 dark:text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                Múltiples empresas
              </li>
              <li className="flex items-start gap-2 text-xs text-slate-700 dark:text-slate-300">
                <svg className="h-4 w-4 flex-shrink-0 text-emerald-600 dark:text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                API de integración
              </li>
              <li className="flex items-start gap-2 text-xs text-slate-700 dark:text-slate-300">
                <svg className="h-4 w-4 flex-shrink-0 text-emerald-600 dark:text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                Soporte prioritario
              </li>
              <li className="flex items-start gap-2 text-xs text-slate-700 dark:text-slate-300">
                <svg className="h-4 w-4 flex-shrink-0 text-emerald-600 dark:text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                Asesoría contable mensual
              </li>
            </ul>
            <button
              disabled
              className="mt-3 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs font-semibold text-slate-700 opacity-50 transition-colors dark:border-slate-600 dark:bg-slate-800 dark:text-slate-300"
            >
              Próximamente
            </button>
          </div>
        </div>
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
