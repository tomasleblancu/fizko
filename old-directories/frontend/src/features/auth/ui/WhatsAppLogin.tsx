/**
 * WhatsAppLogin Component
 *
 * Flujo de autenticación con WhatsApp OTP:
 * 1. Usuario ingresa número de teléfono
 * 2. Backend envía código OTP de 6 dígitos vía WhatsApp
 * 3. Usuario ingresa código recibido
 * 4. Backend valida y genera JWT de Supabase
 * 5. Usuario queda autenticado
 */

import { useState } from 'react';
import { API_BASE_URL } from '@/shared/lib/config';

interface WhatsAppLoginProps {
  onSuccess?: () => void;
  onError?: (error: string) => void;
}

type Step = 'phone' | 'otp';

export function WhatsAppLogin({ onSuccess, onError }: WhatsAppLoginProps) {
  const [phone, setPhone] = useState('');
  const [otp, setOtp] = useState('');
  const [step, setStep] = useState<Step>('phone');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [countdown, setCountdown] = useState(0);

  // Formatear teléfono para mostrar: +56 9 1234 5678
  const formatPhoneDisplay = (value: string): string => {
    const cleaned = value.replace(/\D/g, '');
    if (cleaned.startsWith('56')) {
      const parts = [];
      parts.push('+56');
      if (cleaned.length > 2) parts.push(cleaned[2]);
      if (cleaned.length > 3) parts.push(cleaned.substring(3, 7));
      if (cleaned.length > 7) parts.push(cleaned.substring(7, 11));
      return parts.join(' ');
    }
    return value;
  };

  // Normalizar teléfono para API: +56912345678
  const normalizePhone = (value: string): string => {
    const cleaned = value.replace(/\D/g, '');
    if (!cleaned.startsWith('56')) {
      return `+56${cleaned}`;
    }
    return `+${cleaned}`;
  };

  const handlePhoneChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value.replace(/\D/g, '');
    // Solo números, máximo 11 dígitos (56 + 9 dígitos)
    if (value.length <= 11) {
      setPhone(value);
    }
  };

  const handleOtpChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value.replace(/\D/g, '');
    if (value.length <= 6) {
      setOtp(value);
    }
  };

  const startCountdown = () => {
    setCountdown(60);
    const interval = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          clearInterval(interval);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
  };

  const requestOTP = async () => {
    setLoading(true);
    setError(null);

    try {
      const normalizedPhone = normalizePhone(phone);
      const response = await fetch(`${API_BASE_URL}/auth/whatsapp/request-otp`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone: normalizedPhone }),
      });

      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data.detail || 'Error al enviar código');
      }

      const data = await response.json();

      // En desarrollo, mostrar el código en consola
      if (data.otp) {
        console.log('🔐 OTP (solo desarrollo):', data.otp);
      }

      setStep('otp');
      startCountdown();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Error al enviar código';
      setError(message);
      onError?.(message);
    } finally {
      setLoading(false);
    }
  };

  const verifyOTP = async () => {
    setLoading(true);
    setError(null);

    try {
      const normalizedPhone = normalizePhone(phone);
      const response = await fetch(`${API_BASE_URL}/auth/whatsapp/verify-otp`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone: normalizedPhone, otp }),
      });

      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data.detail || 'Código inválido');
      }

      const data = await response.json();

      // Importar Supabase y establecer sesión
      const { supabase } = await import('@/shared/lib/supabase');
      const { error: sessionError } = await supabase.auth.setSession({
        access_token: data.access_token,
        refresh_token: data.refresh_token,
      });

      if (sessionError) {
        throw sessionError;
      }

      // Éxito - redirigir o callback
      onSuccess?.();
      window.location.href = '/';
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Código inválido o expirado';
      setError(message);
      onError?.(message);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (step === 'phone') {
      requestOTP();
    } else {
      verifyOTP();
    }
  };

  const isPhoneValid = phone.length >= 9; // Al menos 9 dígitos
  const isOtpValid = otp.length === 6;

  return (
    <div className="w-full max-w-md mx-auto">
      <form onSubmit={handleSubmit} className="space-y-4">
        {step === 'phone' ? (
          <>
            {/* Paso 1: Ingresar número */}
            <div>
              <label htmlFor="phone" className="block text-sm font-medium text-gray-700 mb-2">
                Número de teléfono
              </label>
              <div className="relative">
                <input
                  id="phone"
                  type="tel"
                  placeholder="9 1234 5678"
                  value={formatPhoneDisplay(phone)}
                  onChange={handlePhoneChange}
                  className="w-full px-4 py-3 pl-12 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  disabled={loading}
                  autoFocus
                />
                <div className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500">
                  +56
                </div>
              </div>
              <p className="mt-2 text-xs text-gray-500">
                Recibirás un código de verificación por WhatsApp
              </p>
            </div>

            <button
              type="submit"
              disabled={loading || !isPhoneValid}
              className="w-full bg-[#25D366] hover:bg-[#20BA5A] text-white font-medium py-3 px-4 rounded-lg disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Enviando...
                </>
              ) : (
                <>
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413Z"/>
                  </svg>
                  Enviar código por WhatsApp
                </>
              )}
            </button>
          </>
        ) : (
          <>
            {/* Paso 2: Ingresar código OTP */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <label htmlFor="otp" className="block text-sm font-medium text-gray-700">
                  Código de verificación
                </label>
                <button
                  type="button"
                  onClick={() => {
                    setStep('phone');
                    setOtp('');
                    setError(null);
                  }}
                  className="text-sm text-gray-600 hover:text-gray-900"
                >
                  Cambiar número
                </button>
              </div>
              <p className="text-sm text-gray-600 mb-4">
                Código enviado a{' '}
                <span className="font-medium">{formatPhoneDisplay(phone)}</span>
              </p>
              <input
                id="otp"
                type="text"
                inputMode="numeric"
                placeholder="000000"
                value={otp}
                onChange={handleOtpChange}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg text-center text-2xl font-mono tracking-widest focus:ring-2 focus:ring-green-500 focus:border-transparent"
                disabled={loading}
                autoFocus
                maxLength={6}
              />
            </div>

            <button
              type="submit"
              disabled={loading || !isOtpValid}
              className="w-full bg-green-600 hover:bg-green-700 text-white font-medium py-3 px-4 rounded-lg disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? (
                <div className="flex items-center justify-center gap-2">
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Verificando...
                </div>
              ) : (
                'Verificar código'
              )}
            </button>

            {countdown > 0 ? (
              <p className="text-center text-sm text-gray-500">
                Reenviar código en {countdown}s
              </p>
            ) : (
              <button
                type="button"
                onClick={() => {
                  setOtp('');
                  requestOTP();
                }}
                className="w-full text-sm text-gray-600 hover:text-gray-900 py-2"
                disabled={loading}
              >
                Reenviar código
              </button>
            )}
          </>
        )}

        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        )}
      </form>
    </div>
  );
}
