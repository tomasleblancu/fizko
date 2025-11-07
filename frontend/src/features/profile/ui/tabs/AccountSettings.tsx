import { useState, useEffect } from 'react';
import clsx from 'clsx';
import { LogOut } from 'lucide-react';
import { useAuth } from "@/app/providers/AuthContext";
import { useUserProfile } from "@/shared/hooks/useUserProfile";
import type { ColorScheme } from "@/shared/hooks/useColorScheme";

interface AccountSettingsProps {
  user: any;
  scheme: ColorScheme;
  profileLoading: boolean;
  profile: any;
  isInDrawer?: boolean;
}

export function AccountSettings({ user, scheme, profileLoading, profile: profileProp, isInDrawer = false }: AccountSettingsProps) {
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

      {/* Contact Information Section - Compact - Solo nombre y apellido */}
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
      </div>

      {/* Phone Number Section - Separate and prominent */}
      <div className={isInDrawer ? "py-4" : "rounded-lg border border-slate-200 bg-white p-3 shadow-sm dark:border-slate-800 dark:bg-slate-900"}>
        <div className="mb-3 flex items-center justify-between">
          <h4 className="text-base font-semibold text-slate-900 dark:text-slate-100">
            Número de Celular
          </h4>
          {celular && celular !== '+' && !isEditing && (
            <button
              onClick={() => setIsEditing(true)}
              className="text-sm font-medium text-emerald-600 hover:text-emerald-700 dark:text-emerald-400 dark:hover:text-emerald-300"
            >
              Editar
            </button>
          )}
          {isEditing && (
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

        {/* No phone - Show prominent CTA */}
        {(!celular || celular === '+') && !isEditing ? (
          <div className="flex flex-col items-center justify-center py-6 px-4 text-center">
            <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-emerald-100 dark:bg-emerald-900/30">
              <svg className="h-8 w-8 text-emerald-600 dark:text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z" />
              </svg>
            </div>
            <button
              onClick={() => setIsEditing(true)}
              className="flex items-center gap-2 rounded-lg bg-gradient-to-r from-emerald-600 to-teal-600 px-6 py-3 text-base font-semibold text-white shadow-lg transition-all hover:shadow-xl hover:from-emerald-700 hover:to-teal-700 dark:from-emerald-500 dark:to-teal-500 dark:hover:from-emerald-600 dark:hover:to-teal-600"
            >
              <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              Agregar y Verificar Número
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            {/* Celular */}
            <div>
              <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">
                Ingresa tu número de celular
              </label>
              {!profile && profileLoading ? (
                <div className="h-12 w-full animate-pulse rounded-lg bg-slate-200 dark:bg-slate-700" />
              ) : (
                <>
                  <div className="relative">
                    <div className="absolute left-4 top-1/2 -translate-y-1/2 pointer-events-none">
                      <svg className="h-5 w-5 text-emerald-600 dark:text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z" />
                      </svg>
                    </div>
                    <input
                      type="tel"
                      value={celular}
                      onChange={(e) => handlePhoneChange(e.target.value)}
                      disabled={!isEditing}
                      placeholder="+56 912345678"
                      inputMode="numeric"
                      autoFocus={isEditing && (!celular || celular === '+')}
                      className={clsx(
                        "w-full rounded-lg transition-all",
                        isEditing
                          ? "border-2 border-emerald-500 bg-white pl-12 pr-4 py-3.5 text-base font-medium text-slate-900 shadow-lg placeholder-slate-400 focus:border-emerald-600 focus:outline-none focus:ring-4 focus:ring-emerald-500/20 dark:border-emerald-400 dark:bg-slate-800 dark:text-slate-100 dark:placeholder-slate-500"
                          : "border border-slate-200 bg-slate-50 pl-12 pr-4 py-2 text-sm text-slate-900 dark:border-slate-800 dark:bg-slate-800/50 dark:text-slate-100"
                      )}
                    />
                  </div>

                  {/* Verification badge inline with phone - only when NOT editing */}
                  {celular && celular !== '+' && !isEditing && (
                    <div className="mt-2 flex items-center justify-between">
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
                      {!profile?.phone_verified && (
                        <button
                          onClick={handleRequestVerification}
                          className="text-xs font-medium text-emerald-600 hover:text-emerald-700 dark:text-emerald-400 dark:hover:text-emerald-300"
                        >
                          Verificar
                        </button>
                      )}
                    </div>
                  )}

                  {/* Info message when editing */}
                  {isEditing && (
                    <p className="mt-2 text-xs text-slate-500 dark:text-slate-400 flex items-center gap-1">
                      <svg className="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      Recibirás un código de verificación por WhatsApp
                    </p>
                  )}
                </>
              )}
            </div>
          </div>
        )}
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
