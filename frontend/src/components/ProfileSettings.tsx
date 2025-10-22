import { useState, useEffect } from 'react';
import clsx from 'clsx';
import { useAuth } from '../contexts/AuthContext';
import { useUserProfile } from '../hooks/useUserProfile';
import type { ColorScheme } from '../hooks/useColorScheme';
import type { Company } from '../types/fizko';

interface ProfileSettingsProps {
  scheme: ColorScheme;
  isInDrawer?: boolean;
  onNavigateBack?: () => void;
  company: Company | null;
}

export function ProfileSettings({ scheme, isInDrawer = false, onNavigateBack, company }: ProfileSettingsProps) {
  const { user } = useAuth();
  // Company is now passed as prop to avoid multiple fetches
  const [activeTab, setActiveTab] = useState<'account' | 'company' | 'preferences'>('account');

  const tabs = [
    { id: 'account' as const, label: 'Cuenta', icon: '👤' },
    { id: 'company' as const, label: 'Empresa', icon: '🏢' },
    { id: 'preferences' as const, label: 'Preferencias', icon: '⚙️' },
  ];

  // Content for drawer view
  if (isInDrawer) {
    return (
      <div className="flex h-full flex-col space-y-4 overflow-y-auto">
        {/* Header */}
        <div className="flex-shrink-0">
          <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100">
            Configuración
          </h2>
          <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
            Administra tu perfil y preferencias
          </p>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 border-b border-slate-200 dark:border-slate-700">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={clsx(
                'flex items-center gap-2 border-b-2 px-4 py-2 text-sm font-medium transition-colors',
                activeTab === tab.id
                  ? 'border-emerald-600 text-emerald-600 dark:border-emerald-400 dark:text-emerald-400'
                  : 'border-transparent text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100'
              )}
            >
              <span>{tab.icon}</span>
              <span>{tab.label}</span>
            </button>
          ))}
        </div>

        {/* Tab Content */}
        <div className="flex-1">
          {activeTab === 'account' && <AccountSettings user={user} scheme={scheme} />}
          {activeTab === 'company' && <CompanySettings company={company} scheme={scheme} />}
          {activeTab === 'preferences' && <PreferencesSettings scheme={scheme} />}
        </div>
      </div>
    );
  }

  // Desktop view - similar structure to FinancialDashboard
  // Styles are now in the wrapper container in Home.tsx (matching ChatKit pattern)
  return (
    <section className="flex h-full w-full flex-col overflow-hidden">
      {/* Header */}
      <div className="flex-shrink-0 border-b border-slate-200/70 bg-white/50 px-6 py-3 backdrop-blur dark:border-slate-800/70 dark:bg-slate-900/50">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold text-slate-900 dark:text-slate-100">
              Configuración
            </h2>
            <p className="text-xs text-slate-600 dark:text-slate-400">
              Administra tu perfil y preferencias
            </p>
          </div>
          {onNavigateBack && (
            <button
              onClick={onNavigateBack}
              className={clsx(
                "flex items-center gap-2 rounded-lg px-3 py-1.5 text-sm font-medium transition-colors",
                "text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
              )}
            >
              <svg
                className="h-4 w-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M15 19l-7-7 7-7"
                />
              </svg>
              Volver al Dashboard
            </button>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="flex-shrink-0 border-b border-slate-200/60 px-6 dark:border-slate-800/60">
        <div className="flex gap-1">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={clsx(
                'flex items-center gap-2 border-b-2 px-4 py-3 text-sm font-medium transition-colors',
                activeTab === tab.id
                  ? 'border-emerald-600 text-emerald-600 dark:border-emerald-400 dark:text-emerald-400'
                  : 'border-transparent text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100'
              )}
            >
              <span>{tab.icon}</span>
              <span>{tab.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6">
        {activeTab === 'account' && <AccountSettings user={user} scheme={scheme} />}
        {activeTab === 'company' && <CompanySettings company={company} scheme={scheme} />}
        {activeTab === 'preferences' && <PreferencesSettings scheme={scheme} />}
      </div>
    </section>
  );
}

// Account Settings Tab
function AccountSettings({ user, scheme }: { user: any; scheme: ColorScheme }) {
  const { profile, updateProfile, requestPhoneVerification, confirmPhoneVerification } = useUserProfile();
  const [nombre, setNombre] = useState('');
  const [apellido, setApellido] = useState('');
  const [celular, setCelular] = useState('');
  const [isEditing, setIsEditing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [showVerificationModal, setShowVerificationModal] = useState(false);
  const [verificationCode, setVerificationCode] = useState('');
  const [isVerifying, setIsVerifying] = useState(false);

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
    const success = await requestPhoneVerification();
    if (success) {
      setShowVerificationModal(true);
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
    <div className="space-y-6">
      {/* User Info Card */}
      <div className="rounded-2xl border border-slate-200/70 bg-gradient-to-br from-blue-50 to-purple-50 p-6 dark:border-slate-800/70 dark:from-blue-950/30 dark:to-purple-950/30">
        <div className="flex items-center gap-4">
          <div className="flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-br from-emerald-600 to-teal-700 text-2xl font-bold text-white shadow-lg">
            {user?.email?.charAt(0).toUpperCase() || '?'}
          </div>
          <div>
            <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
              {user?.email || 'Usuario'}
            </h3>
            <p className="text-sm text-slate-600 dark:text-slate-400">
              Cuenta activa
            </p>
          </div>
        </div>
      </div>

      {/* Contact Information Section */}
      <div className="rounded-xl border border-slate-200/70 bg-white/50 p-4 dark:border-slate-800/70 dark:bg-slate-900/50">
        <div className="mb-4 flex items-center justify-between">
          <h4 className="font-medium text-slate-900 dark:text-slate-100">
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
                className="text-sm font-medium text-slate-600 hover:text-slate-700 disabled:opacity-50 dark:text-slate-400 dark:hover:text-slate-300"
              >
                Cancelar
              </button>
              <button
                onClick={handleSave}
                disabled={isSaving}
                className="text-sm font-medium text-emerald-600 hover:text-emerald-700 disabled:opacity-50 dark:text-emerald-400 dark:hover:text-emerald-300"
              >
                {isSaving ? 'Guardando...' : 'Guardar'}
              </button>
            </div>
          )}
        </div>

        <div className="space-y-4">
          {/* Nombre */}
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
              Nombre
            </label>
            <input
              type="text"
              value={nombre}
              onChange={(e) => setNombre(e.target.value)}
              disabled={!isEditing}
              placeholder="Ingresa tu nombre"
              className={clsx(
                "mt-1 w-full rounded-lg border px-3 py-2 transition-colors",
                isEditing
                  ? "border-slate-300 bg-white text-slate-900 focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
                  : "border-slate-300 bg-slate-50 text-slate-900 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
              )}
            />
          </div>

          {/* Apellido */}
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
              Apellido
            </label>
            <input
              type="text"
              value={apellido}
              onChange={(e) => setApellido(e.target.value)}
              disabled={!isEditing}
              placeholder="Ingresa tu apellido"
              className={clsx(
                "mt-1 w-full rounded-lg border px-3 py-2 transition-colors",
                isEditing
                  ? "border-slate-300 bg-white text-slate-900 focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
                  : "border-slate-300 bg-slate-50 text-slate-900 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
              )}
            />
          </div>

          {/* Celular */}
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
              Celular
            </label>
            <input
              type="tel"
              value={celular}
              onChange={(e) => handlePhoneChange(e.target.value)}
              disabled={!isEditing}
              placeholder="+56 912345678"
              inputMode="numeric"
              className={clsx(
                "mt-1 w-full rounded-lg border px-3 py-2 transition-colors",
                isEditing
                  ? "border-slate-300 bg-white text-slate-900 focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
                  : "border-slate-300 bg-slate-50 text-slate-900 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
              )}
            />
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
              Solo números. Ejemplo: +56 912345678
            </p>
          </div>

          {/* Phone Verification Status */}
          {celular && celular !== '+' && (
            <div className="mt-2 flex items-center justify-between rounded-lg border border-slate-200 bg-white p-3 dark:border-slate-700 dark:bg-slate-800">
              <div className="flex items-center gap-2">
                {profile?.phone_verified ? (
                  <>
                    <svg className="h-5 w-5 text-emerald-600 dark:text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <span className="text-sm font-medium text-emerald-700 dark:text-emerald-300">
                      Número verificado
                    </span>
                  </>
                ) : (
                  <>
                    <svg className="h-5 w-5 text-amber-600 dark:text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                    <span className="text-sm font-medium text-amber-700 dark:text-amber-300">
                      Número no verificado
                    </span>
                  </>
                )}
              </div>
              {!profile?.phone_verified && !isEditing && (
                <button
                  onClick={handleRequestVerification}
                  className="text-sm font-medium text-emerald-600 hover:text-emerald-700 dark:text-emerald-400 dark:hover:text-emerald-300"
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
            <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
              Verificar Número de Teléfono
            </h3>
            <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">
              Ingresa el código de 6 dígitos que te enviamos por SMS a {celular}
            </p>

            <div className="mt-4">
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
                className="w-full rounded-lg border border-slate-300 bg-white px-4 py-3 text-center text-2xl tracking-widest text-slate-900 focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
              />
            </div>

            <div className="mt-6 flex gap-3">
              <button
                onClick={() => {
                  setShowVerificationModal(false);
                  setVerificationCode('');
                }}
                disabled={isVerifying}
                className="flex-1 rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700"
              >
                Cancelar
              </button>
              <button
                onClick={handleConfirmVerification}
                disabled={isVerifying || verificationCode.length !== 6}
                className="flex-1 rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50 dark:bg-emerald-500 dark:hover:bg-emerald-600"
              >
                {isVerifying ? 'Verificando...' : 'Verificar'}
              </button>
            </div>

            <p className="mt-4 text-xs text-amber-600 dark:text-amber-400">
              Nota: La integración con servicio de SMS está pendiente. Por ahora, cualquier código de 6 dígitos será aceptado.
            </p>
          </div>
        </div>
      )}

      {/* Email */}
      <div className="rounded-xl border border-slate-200/70 bg-white/50 p-4 dark:border-slate-800/70 dark:bg-slate-900/50">
        <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
          Email
        </label>
        <input
          type="email"
          value={user?.email || ''}
          disabled
          className="mt-1 w-full rounded-lg border border-slate-300 bg-slate-50 px-3 py-2 text-slate-900 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
        />
        <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
          El email no puede ser modificado
        </p>
      </div>

      {/* SII Credentials Section */}
      <div className="rounded-xl border border-slate-200/70 bg-white/50 p-4 dark:border-slate-800/70 dark:bg-slate-900/50">
        <h4 className="mb-3 font-medium text-slate-900 dark:text-slate-100">
          Credenciales SII
        </h4>
        <p className="text-sm text-slate-600 dark:text-slate-400">
          Las credenciales del SII están vinculadas a tu cuenta. Para modificarlas, contacta a soporte.
        </p>
      </div>
    </div>
  );
}

// Company Settings Tab
function CompanySettings({ company, scheme }: { company: any; scheme: ColorScheme }) {
  if (!company) {
    return (
      <div className="rounded-xl border border-slate-200/70 bg-white/50 p-8 text-center dark:border-slate-800/70 dark:bg-slate-900/50">
        <p className="text-slate-600 dark:text-slate-400">
          No hay empresa vinculada a esta cuenta
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Company Info Card */}
      <div className="rounded-2xl border border-slate-200/70 bg-gradient-to-br from-emerald-50 to-teal-50 p-6 dark:border-slate-800/70 dark:from-emerald-950/30 dark:to-teal-950/30">
        <div className="flex items-center gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-emerald-600 to-teal-700 text-xl font-bold text-white shadow-lg">
            {company.razon_social?.charAt(0).toUpperCase() || 'E'}
          </div>
          <div>
            <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
              {company.razon_social || 'Empresa'}
            </h3>
            <p className="text-sm text-slate-600 dark:text-slate-400">
              RUT: {company.rut || 'N/A'}
            </p>
          </div>
        </div>
      </div>

      {/* Company Details */}
      <div className="space-y-4">
        <div className="rounded-xl border border-slate-200/70 bg-white/50 p-4 dark:border-slate-800/70 dark:bg-slate-900/50">
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
            Razón Social
          </label>
          <input
            type="text"
            value={company.razon_social || ''}
            disabled
            className="mt-1 w-full rounded-lg border border-slate-300 bg-slate-50 px-3 py-2 text-slate-900 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
          />
        </div>

        <div className="rounded-xl border border-slate-200/70 bg-white/50 p-4 dark:border-slate-800/70 dark:bg-slate-900/50">
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
            RUT
          </label>
          <input
            type="text"
            value={company.rut || ''}
            disabled
            className="mt-1 w-full rounded-lg border border-slate-300 bg-slate-50 px-3 py-2 text-slate-900 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
          />
        </div>

        {company.giro && (
          <div className="rounded-xl border border-slate-200/70 bg-white/50 p-4 dark:border-slate-800/70 dark:bg-slate-900/50">
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
              Giro
            </label>
            <input
              type="text"
              value={company.giro}
              disabled
              className="mt-1 w-full rounded-lg border border-slate-300 bg-slate-50 px-3 py-2 text-slate-900 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
            />
          </div>
        )}
      </div>

      <div className="rounded-xl border border-amber-200/70 bg-amber-50/50 p-4 dark:border-amber-900/70 dark:bg-amber-950/30">
        <p className="text-sm text-amber-800 dark:text-amber-200">
          Los datos de la empresa son obtenidos del SII y no pueden ser modificados desde aquí.
        </p>
      </div>
    </div>
  );
}

// Preferences Settings Tab
function PreferencesSettings({ scheme }: { scheme: ColorScheme }) {
  return (
    <div className="space-y-6">
      {/* Theme Preference */}
      <div className="rounded-xl border border-slate-200/70 bg-white/50 p-4 dark:border-slate-800/70 dark:bg-slate-900/50">
        <h4 className="mb-3 font-medium text-slate-900 dark:text-slate-100">
          Apariencia
        </h4>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-slate-700 dark:text-slate-300">
              Tema actual
            </p>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              {scheme === 'dark' ? 'Modo oscuro' : 'Modo claro'}
            </p>
          </div>
          <div className="flex items-center gap-2">
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
        <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">
          Cambia el tema usando el botón en el encabezado
        </p>
      </div>

      {/* Language (placeholder) */}
      <div className="rounded-xl border border-slate-200/70 bg-white/50 p-4 dark:border-slate-800/70 dark:bg-slate-900/50">
        <h4 className="mb-3 font-medium text-slate-900 dark:text-slate-100">
          Idioma
        </h4>
        <select
          disabled
          className="w-full rounded-lg border border-slate-300 bg-slate-50 px-3 py-2 text-slate-900 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
        >
          <option>Español (Chile)</option>
        </select>
        <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">
          Próximamente disponible
        </p>
      </div>

      {/* Notifications (placeholder) */}
      <div className="rounded-xl border border-slate-200/70 bg-white/50 p-4 dark:border-slate-800/70 dark:bg-slate-900/50">
        <h4 className="mb-3 font-medium text-slate-900 dark:text-slate-100">
          Notificaciones
        </h4>
        <div className="space-y-3">
          <label className="flex items-center justify-between">
            <span className="text-sm text-slate-700 dark:text-slate-300">
              Notificaciones de email
            </span>
            <input
              type="checkbox"
              disabled
              className="h-5 w-5 rounded border-slate-300 text-emerald-600 focus:ring-emerald-500 dark:border-slate-700"
            />
          </label>
          <label className="flex items-center justify-between">
            <span className="text-sm text-slate-700 dark:text-slate-300">
              Actualizaciones de documentos
            </span>
            <input
              type="checkbox"
              disabled
              className="h-5 w-5 rounded border-slate-300 text-emerald-600 focus:ring-emerald-500 dark:border-slate-700"
            />
          </label>
        </div>
        <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">
          Próximamente disponible
        </p>
      </div>
    </div>
  );
}
