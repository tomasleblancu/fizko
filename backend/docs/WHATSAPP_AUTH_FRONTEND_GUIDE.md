# Guía Frontend: Autenticación por WhatsApp

Implementación paso a paso del login por WhatsApp con código OTP en React/TypeScript.

## 📋 Índice

1. [Flujo de Usuario](#flujo-de-usuario)
2. [Configuración Inicial](#configuración-inicial)
3. [Tipos TypeScript](#tipos-typescript)
4. [Servicio de Autenticación](#servicio-de-autenticación)
5. [Componentes UI](#componentes-ui)
6. [Hooks Personalizados](#hooks-personalizados)
7. [Integración Completa](#integración-completa)
8. [Manejo de Errores](#manejo-de-errores)
9. [Testing](#testing)

---

## 🎯 Flujo de Usuario

```
┌─────────────────────────────────────────────────────────┐
│  PASO 1: Ingreso de Teléfono                           │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Ingresa tu número de teléfono                   │  │
│  │  ┌──────────────────────────────────┐            │  │
│  │  │ +56 9 1234 5678                  │            │  │
│  │  └──────────────────────────────────┘            │  │
│  │  [Enviar Código]                                 │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│  PASO 2: Verificación de Código                        │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Código enviado a +56 9 1234 5678               │  │
│  │  ┌───┬───┬───┬───┬───┬───┐                      │  │
│  │  │ 1 │ 2 │ 3 │ 4 │ 5 │ 6 │                      │  │
│  │  └───┴───┴───┴───┴───┴───┘                      │  │
│  │  Expira en: 04:32                               │  │
│  │  [Verificar]                                     │  │
│  │  ¿No recibiste el código? Reenviar en 52s       │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│  PASO 3: Autenticado                                   │
│  Redirigir a /dashboard                                │
└─────────────────────────────────────────────────────────┘
```

---

## ⚙️ Configuración Inicial

### 1. Variables de Entorno

Crear `frontend/.env`:

```bash
# Backend API
VITE_BACKEND_URL=http://localhost:8000

# Supabase (ya existentes)
VITE_SUPABASE_URL=https://xxx.supabase.co
VITE_SUPABASE_ANON_KEY=eyJ...
```

### 2. Instalar Dependencias (si no están)

```bash
cd frontend
npm install @tanstack/react-query axios date-fns
```

---

## 📝 Tipos TypeScript

Crear `src/features/auth/types.ts`:

```typescript
// ============================================================================
// API Request/Response Types
// ============================================================================

export interface RequestCodeRequest {
  phone_number: string;
}

export interface RequestCodeResponse {
  success: boolean;
  message: string;
  expires_at: string; // ISO 8601 datetime
  retry_after: number; // seconds
}

export interface VerifyCodeRequest {
  phone_number: string;
  code: string;
}

export interface UserProfile {
  id: string;
  phone: string;
  email: string | null;
  created_at: string;
}

export interface VerifyCodeResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  refresh_token: string | null;
  user: UserProfile;
}

export interface ErrorResponse {
  detail: string;
  error?: string;
  attempts_remaining?: number;
}

// ============================================================================
// UI State Types
// ============================================================================

export type AuthStep = 'phone' | 'code' | 'authenticated';

export interface AuthState {
  step: AuthStep;
  phoneNumber: string;
  code: string;
  loading: boolean;
  error: string | null;
  expiresAt: Date | null;
  retryAfter: number;
}

// ============================================================================
// Storage Types
// ============================================================================

export interface StoredAuth {
  access_token: string;
  refresh_token: string | null;
  user: UserProfile;
  expires_at: number; // timestamp
}
```

---

## 🔌 Servicio de Autenticación

Crear `src/features/auth/services/phoneAuthService.ts`:

```typescript
import axios, { AxiosError } from 'axios';
import type {
  RequestCodeRequest,
  RequestCodeResponse,
  VerifyCodeRequest,
  VerifyCodeResponse,
  ErrorResponse,
  StoredAuth,
} from '../types';

const API_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

// ============================================================================
// Phone Auth API Client
// ============================================================================

export class PhoneAuthService {
  private baseURL: string;

  constructor(baseURL: string = API_URL) {
    this.baseURL = baseURL;
  }

  /**
   * PASO 1: Solicitar código de verificación
   *
   * Request:
   *   POST /api/auth/phone/request-code
   *   Body: { phone_number: "+56912345678" }
   *
   * Response (200):
   *   {
   *     "success": true,
   *     "message": "Código enviado por WhatsApp",
   *     "expires_at": "2025-11-23T22:05:00Z",
   *     "retry_after": 60
   *   }
   *
   * Error (400):
   *   {
   *     "detail": "Por favor espera 60 segundos antes de solicitar otro código."
   *   }
   */
  async requestCode(phoneNumber: string): Promise<RequestCodeResponse> {
    try {
      const response = await axios.post<RequestCodeResponse>(
        `${this.baseURL}/api/auth/phone/request-code`,
        {
          phone_number: this.normalizePhoneNumber(phoneNumber),
        } as RequestCodeRequest,
        {
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );

      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * PASO 2: Verificar código y autenticar
   *
   * Request:
   *   POST /api/auth/phone/verify-code
   *   Body: { phone_number: "+56912345678", code: "123456" }
   *
   * Response (200):
   *   {
   *     "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
   *     "token_type": "bearer",
   *     "expires_in": 3600,
   *     "refresh_token": "v1.MR...",
   *     "user": {
   *       "id": "uuid",
   *       "phone": "+56912345678",
   *       "email": null,
   *       "created_at": "2025-11-23T21:40:00Z"
   *     }
   *   }
   *
   * Error (400):
   *   {
   *     "detail": "Código incorrecto. Te quedan 2 intentos."
   *   }
   */
  async verifyCode(
    phoneNumber: string,
    code: string
  ): Promise<VerifyCodeResponse> {
    try {
      const response = await axios.post<VerifyCodeResponse>(
        `${this.baseURL}/api/auth/phone/verify-code`,
        {
          phone_number: this.normalizePhoneNumber(phoneNumber),
          code: code,
        } as VerifyCodeRequest,
        {
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );

      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * Normalizar número de teléfono a formato E.164
   */
  private normalizePhoneNumber(phone: string): string {
    // Remove whitespace and non-digit characters except +
    let normalized = phone.replace(/[\s()-]/g, '');

    // Add + prefix if missing
    if (!normalized.startsWith('+')) {
      // If starts with 56, assume Chile
      if (normalized.startsWith('56')) {
        normalized = `+${normalized}`;
      }
      // If starts with 9, assume Chile mobile
      else if (normalized.startsWith('9')) {
        normalized = `+56${normalized}`;
      }
      // Otherwise, default to Chile
      else {
        normalized = `+56${normalized}`;
      }
    }

    return normalized;
  }

  /**
   * Manejar errores de API
   */
  private handleError(error: unknown): Error {
    if (axios.isAxiosError(error)) {
      const axiosError = error as AxiosError<ErrorResponse>;

      if (axiosError.response?.data?.detail) {
        return new Error(axiosError.response.data.detail);
      }

      if (axiosError.response?.status === 429) {
        return new Error('Demasiadas solicitudes. Espera un momento e intenta nuevamente.');
      }

      if (axiosError.response?.status === 500) {
        return new Error('Error del servidor. Por favor intenta nuevamente.');
      }
    }

    return new Error('Error de conexión. Verifica tu internet e intenta nuevamente.');
  }
}

// ============================================================================
// Token Storage Management
// ============================================================================

export class AuthStorage {
  private static readonly ACCESS_TOKEN_KEY = 'access_token';
  private static readonly REFRESH_TOKEN_KEY = 'refresh_token';
  private static readonly USER_KEY = 'user';
  private static readonly EXPIRES_AT_KEY = 'token_expires_at';

  /**
   * Guardar credenciales de autenticación
   */
  static saveAuth(auth: VerifyCodeResponse): void {
    const expiresAt = Date.now() + auth.expires_in * 1000;

    localStorage.setItem(this.ACCESS_TOKEN_KEY, auth.access_token);

    if (auth.refresh_token) {
      localStorage.setItem(this.REFRESH_TOKEN_KEY, auth.refresh_token);
    }

    localStorage.setItem(this.USER_KEY, JSON.stringify(auth.user));
    localStorage.setItem(this.EXPIRES_AT_KEY, expiresAt.toString());
  }

  /**
   * Obtener token de acceso
   */
  static getAccessToken(): string | null {
    return localStorage.getItem(this.ACCESS_TOKEN_KEY);
  }

  /**
   * Obtener refresh token
   */
  static getRefreshToken(): string | null {
    return localStorage.getItem(this.REFRESH_TOKEN_KEY);
  }

  /**
   * Obtener usuario
   */
  static getUser(): UserProfile | null {
    const userStr = localStorage.getItem(this.USER_KEY);
    if (!userStr) return null;

    try {
      return JSON.parse(userStr);
    } catch {
      return null;
    }
  }

  /**
   * Verificar si el token está expirado
   */
  static isTokenExpired(): boolean {
    const expiresAt = localStorage.getItem(this.EXPIRES_AT_KEY);
    if (!expiresAt) return true;

    return Date.now() >= parseInt(expiresAt, 10);
  }

  /**
   * Limpiar todas las credenciales (logout)
   */
  static clearAuth(): void {
    localStorage.removeItem(this.ACCESS_TOKEN_KEY);
    localStorage.removeItem(this.REFRESH_TOKEN_KEY);
    localStorage.removeItem(this.USER_KEY);
    localStorage.removeItem(this.EXPIRES_AT_KEY);
  }

  /**
   * Verificar si el usuario está autenticado
   */
  static isAuthenticated(): boolean {
    const token = this.getAccessToken();
    return !!token && !this.isTokenExpired();
  }
}

// Export singleton instance
export const phoneAuthService = new PhoneAuthService();
```

---

## 🎨 Componentes UI

### Componente Principal: PhoneLogin

Crear `src/features/auth/components/PhoneLogin.tsx`:

```typescript
import { useState } from 'react';
import { PhoneInputStep } from './PhoneInputStep';
import { CodeVerificationStep } from './CodeVerificationStep';
import { phoneAuthService, AuthStorage } from '../services/phoneAuthService';
import type { AuthStep } from '../types';

export function PhoneLogin() {
  const [step, setStep] = useState<AuthStep>('phone');
  const [phoneNumber, setPhoneNumber] = useState('+56');
  const [code, setCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expiresAt, setExpiresAt] = useState<Date | null>(null);
  const [retryAfter, setRetryAfter] = useState(60);

  // =========================================================================
  // PASO 1: Request Verification Code
  // =========================================================================

  const handleRequestCode = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      console.log('📱 Requesting code for:', phoneNumber);

      const response = await phoneAuthService.requestCode(phoneNumber);

      console.log('✅ Code requested successfully:', response);

      setExpiresAt(new Date(response.expires_at));
      setRetryAfter(response.retry_after);
      setStep('code');

    } catch (err: any) {
      console.error('❌ Request code failed:', err);
      setError(err.message || 'Error al enviar código');
    } finally {
      setLoading(false);
    }
  };

  // =========================================================================
  // PASO 2: Verify Code
  // =========================================================================

  const handleVerifyCode = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      console.log('🔐 Verifying code for:', phoneNumber);

      const response = await phoneAuthService.verifyCode(phoneNumber, code);

      console.log('✅ Code verified successfully:', response.user);

      // Save auth credentials
      AuthStorage.saveAuth(response);

      // Update state
      setStep('authenticated');

      // Redirect to dashboard
      setTimeout(() => {
        window.location.href = '/dashboard';
      }, 500);

    } catch (err: any) {
      console.error('❌ Verify code failed:', err);
      setError(err.message || 'Código inválido');

      // Clear code on error
      setCode('');
    } finally {
      setLoading(false);
    }
  };

  // =========================================================================
  // Helpers
  // =========================================================================

  const handleBackToPhone = () => {
    setStep('phone');
    setCode('');
    setError(null);
  };

  // =========================================================================
  // Render
  // =========================================================================

  if (step === 'phone') {
    return (
      <PhoneInputStep
        phoneNumber={phoneNumber}
        onPhoneChange={setPhoneNumber}
        onSubmit={handleRequestCode}
        loading={loading}
        error={error}
      />
    );
  }

  if (step === 'code') {
    return (
      <CodeVerificationStep
        phoneNumber={phoneNumber}
        code={code}
        onCodeChange={setCode}
        onSubmit={handleVerifyCode}
        onBack={handleBackToPhone}
        loading={loading}
        error={error}
        expiresAt={expiresAt}
        retryAfter={retryAfter}
        onResend={handleRequestCode}
      />
    );
  }

  return (
    <div className="text-center">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto" />
      <p className="mt-4 text-gray-600">Iniciando sesión...</p>
    </div>
  );
}
```

### Paso 1: Input de Teléfono

Crear `src/features/auth/components/PhoneInputStep.tsx`:

```typescript
import { useState } from 'react';

interface PhoneInputStepProps {
  phoneNumber: string;
  onPhoneChange: (phone: string) => void;
  onSubmit: (e: React.FormEvent) => void;
  loading: boolean;
  error: string | null;
}

export function PhoneInputStep({
  phoneNumber,
  onPhoneChange,
  onSubmit,
  loading,
  error,
}: PhoneInputStepProps) {
  const [touched, setTouched] = useState(false);

  const formatPhoneNumber = (value: string) => {
    // Remove all non-digit characters except +
    let cleaned = value.replace(/[^\d+]/g, '');

    // Ensure starts with +56
    if (!cleaned.startsWith('+')) {
      if (cleaned.startsWith('56')) {
        cleaned = '+' + cleaned;
      } else if (cleaned.startsWith('9')) {
        cleaned = '+56' + cleaned;
      } else {
        cleaned = '+56' + cleaned;
      }
    }

    // Format: +56 9 1234 5678
    if (cleaned.length > 3) {
      const country = cleaned.slice(0, 3); // +56
      const rest = cleaned.slice(3);

      if (rest.length > 0) {
        const mobile = rest.slice(0, 1); // 9
        const part1 = rest.slice(1, 5);  // 1234
        const part2 = rest.slice(5, 9);  // 5678

        let formatted = `${country} ${mobile}`;
        if (part1) formatted += ` ${part1}`;
        if (part2) formatted += ` ${part2}`;

        return formatted;
      }
    }

    return cleaned;
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const formatted = formatPhoneNumber(e.target.value);
    onPhoneChange(formatted);
  };

  const isValid = phoneNumber.replace(/\s/g, '').length >= 12; // +56912345678

  return (
    <div className="w-full max-w-md mx-auto p-6 bg-white rounded-lg shadow-lg">
      <div className="text-center mb-6">
        <h2 className="text-2xl font-bold text-gray-900">
          Iniciar Sesión
        </h2>
        <p className="mt-2 text-sm text-gray-600">
          Ingresa tu número de teléfono para recibir un código por WhatsApp
        </p>
      </div>

      <form onSubmit={onSubmit}>
        <div className="mb-4">
          <label
            htmlFor="phone"
            className="block text-sm font-medium text-gray-700 mb-2"
          >
            Número de teléfono
          </label>
          <input
            id="phone"
            type="tel"
            value={phoneNumber}
            onChange={handleChange}
            onBlur={() => setTouched(true)}
            disabled={loading}
            placeholder="+56 9 1234 5678"
            className={`
              w-full px-4 py-3 border rounded-lg text-lg
              focus:ring-2 focus:ring-blue-500 focus:border-transparent
              disabled:bg-gray-100 disabled:cursor-not-allowed
              ${touched && !isValid ? 'border-red-500' : 'border-gray-300'}
            `}
            autoComplete="tel"
            autoFocus
          />
          {touched && !isValid && (
            <p className="mt-1 text-sm text-red-600">
              Ingresa un número de teléfono válido
            </p>
          )}
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-800">{error}</p>
          </div>
        )}

        <button
          type="submit"
          disabled={loading || !isValid}
          className={`
            w-full py-3 px-4 rounded-lg font-medium text-white
            focus:outline-none focus:ring-2 focus:ring-offset-2
            transition-colors
            ${
              loading || !isValid
                ? 'bg-gray-400 cursor-not-allowed'
                : 'bg-blue-600 hover:bg-blue-700 focus:ring-blue-500'
            }
          `}
        >
          {loading ? (
            <span className="flex items-center justify-center">
              <svg
                className="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </svg>
              Enviando...
            </span>
          ) : (
            'Enviar Código'
          )}
        </button>
      </form>

      <div className="mt-6 text-center text-sm text-gray-500">
        <p>
          Al continuar, recibirás un código de 6 dígitos por WhatsApp
        </p>
      </div>
    </div>
  );
}
```

### Paso 2: Verificación de Código

Crear `src/features/auth/components/CodeVerificationStep.tsx`:

```typescript
import { useEffect, useState, useRef } from 'react';
import { formatDistanceToNow } from 'date-fns';
import { es } from 'date-fns/locale';

interface CodeVerificationStepProps {
  phoneNumber: string;
  code: string;
  onCodeChange: (code: string) => void;
  onSubmit: (e: React.FormEvent) => void;
  onBack: () => void;
  onResend: (e: React.FormEvent) => void;
  loading: boolean;
  error: string | null;
  expiresAt: Date | null;
  retryAfter: number;
}

export function CodeVerificationStep({
  phoneNumber,
  code,
  onCodeChange,
  onSubmit,
  onBack,
  onResend,
  loading,
  error,
  expiresAt,
  retryAfter,
}: CodeVerificationStepProps) {
  const [countdown, setCountdown] = useState(retryAfter);
  const [expiryCountdown, setExpiryCountdown] = useState<string>('');
  const inputsRef = useRef<(HTMLInputElement | null)[]>([]);

  // Countdown for retry
  useEffect(() => {
    if (countdown <= 0) return;

    const timer = setInterval(() => {
      setCountdown((prev) => Math.max(0, prev - 1));
    }, 1000);

    return () => clearInterval(timer);
  }, [countdown]);

  // Countdown for expiry
  useEffect(() => {
    if (!expiresAt) return;

    const updateExpiry = () => {
      const now = new Date();
      const diff = expiresAt.getTime() - now.getTime();

      if (diff <= 0) {
        setExpiryCountdown('Expirado');
      } else {
        const minutes = Math.floor(diff / 60000);
        const seconds = Math.floor((diff % 60000) / 1000);
        setExpiryCountdown(`${minutes}:${seconds.toString().padStart(2, '0')}`);
      }
    };

    updateExpiry();
    const timer = setInterval(updateExpiry, 1000);

    return () => clearInterval(timer);
  }, [expiresAt]);

  const handleCodeInput = (index: number, value: string) => {
    // Only allow digits
    const digit = value.replace(/\D/g, '').slice(-1);

    const newCode = code.split('');
    newCode[index] = digit;
    const updatedCode = newCode.join('').slice(0, 6);

    onCodeChange(updatedCode);

    // Auto-focus next input
    if (digit && index < 5) {
      inputsRef.current[index + 1]?.focus();
    }
  };

  const handleKeyDown = (index: number, e: React.KeyboardEvent) => {
    if (e.key === 'Backspace' && !code[index] && index > 0) {
      inputsRef.current[index - 1]?.focus();
    }
  };

  const handlePaste = (e: React.ClipboardEvent) => {
    e.preventDefault();
    const pastedData = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6);
    onCodeChange(pastedData);

    // Focus last filled input
    const lastIndex = Math.min(pastedData.length, 5);
    inputsRef.current[lastIndex]?.focus();
  };

  const canResend = countdown === 0;
  const isCodeComplete = code.length === 6;

  return (
    <div className="w-full max-w-md mx-auto p-6 bg-white rounded-lg shadow-lg">
      <div className="text-center mb-6">
        <h2 className="text-2xl font-bold text-gray-900">
          Verificar Código
        </h2>
        <p className="mt-2 text-sm text-gray-600">
          Código enviado a
        </p>
        <p className="mt-1 text-lg font-medium text-gray-900">
          {phoneNumber}
        </p>
      </div>

      <form onSubmit={onSubmit}>
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-3 text-center">
            Ingresa el código de 6 dígitos
          </label>

          <div className="flex gap-2 justify-center" onPaste={handlePaste}>
            {[0, 1, 2, 3, 4, 5].map((index) => (
              <input
                key={index}
                ref={(el) => (inputsRef.current[index] = el)}
                type="text"
                inputMode="numeric"
                maxLength={1}
                value={code[index] || ''}
                onChange={(e) => handleCodeInput(index, e.target.value)}
                onKeyDown={(e) => handleKeyDown(index, e)}
                disabled={loading}
                className={`
                  w-12 h-14 text-center text-2xl font-bold
                  border-2 rounded-lg
                  focus:ring-2 focus:ring-blue-500 focus:border-transparent
                  disabled:bg-gray-100 disabled:cursor-not-allowed
                  transition-colors
                  ${
                    error
                      ? 'border-red-500'
                      : code[index]
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-300'
                  }
                `}
                autoFocus={index === 0}
              />
            ))}
          </div>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-800 text-center">{error}</p>
          </div>
        )}

        {expiresAt && (
          <div className="mb-4 text-center">
            <p className="text-sm text-gray-600">
              Código expira en:{' '}
              <span className="font-medium text-gray-900">
                {expiryCountdown}
              </span>
            </p>
          </div>
        )}

        <button
          type="submit"
          disabled={loading || !isCodeComplete}
          className={`
            w-full py-3 px-4 rounded-lg font-medium text-white
            focus:outline-none focus:ring-2 focus:ring-offset-2
            transition-colors mb-3
            ${
              loading || !isCodeComplete
                ? 'bg-gray-400 cursor-not-allowed'
                : 'bg-blue-600 hover:bg-blue-700 focus:ring-blue-500'
            }
          `}
        >
          {loading ? (
            <span className="flex items-center justify-center">
              <svg
                className="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </svg>
              Verificando...
            </span>
          ) : (
            'Verificar'
          )}
        </button>

        <button
          type="button"
          onClick={onBack}
          disabled={loading}
          className="w-full py-2 px-4 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
        >
          Cambiar Número
        </button>
      </form>

      <div className="mt-6 text-center">
        {canResend ? (
          <button
            onClick={onResend}
            disabled={loading}
            className="text-sm text-blue-600 hover:text-blue-700 font-medium"
          >
            Reenviar código
          </button>
        ) : (
          <p className="text-sm text-gray-500">
            ¿No recibiste el código?{' '}
            <span className="font-medium">
              Reenviar en {countdown}s
            </span>
          </p>
        )}
      </div>
    </div>
  );
}
```

---

## 🔒 Protected Route Component

Crear `src/features/auth/components/ProtectedRoute.tsx`:

```typescript
import { Navigate } from 'react-router-dom';
import { AuthStorage } from '../services/phoneAuthService';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const isAuthenticated = AuthStorage.isAuthenticated();

  if (!isAuthenticated) {
    // Redirect to login if not authenticated
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}
```

---

## 🌐 Axios Interceptor (para usar token)

Crear `src/shared/lib/axios.ts`:

```typescript
import axios from 'axios';
import { AuthStorage } from '@/features/auth/services/phoneAuthService';

const API_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor - add token
api.interceptors.request.use(
  (config) => {
    const token = AuthStorage.getAccessToken();

    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor - handle 401
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      AuthStorage.clearAuth();
      window.location.href = '/login';
    }

    return Promise.reject(error);
  }
);
```

---

## 📄 Integración en Rutas

Crear/actualizar `src/app/router.tsx`:

```typescript
import { createBrowserRouter } from 'react-router-dom';
import { PhoneLogin } from '@/features/auth/components/PhoneLogin';
import { ProtectedRoute } from '@/features/auth/components/ProtectedRoute';
import { Dashboard } from '@/pages/Dashboard';

export const router = createBrowserRouter([
  {
    path: '/login',
    element: <PhoneLogin />,
  },
  {
    path: '/dashboard',
    element: (
      <ProtectedRoute>
        <Dashboard />
      </ProtectedRoute>
    ),
  },
  {
    path: '/',
    element: (
      <ProtectedRoute>
        <Dashboard />
      </ProtectedRoute>
    ),
  },
]);
```

---

## ✅ Checklist de Implementación

- [ ] 1. Crear tipos TypeScript
- [ ] 2. Implementar `PhoneAuthService`
- [ ] 3. Implementar `AuthStorage`
- [ ] 4. Crear `PhoneInputStep` component
- [ ] 5. Crear `CodeVerificationStep` component
- [ ] 6. Crear `PhoneLogin` component principal
- [ ] 7. Crear `ProtectedRoute` component
- [ ] 8. Configurar axios interceptor
- [ ] 9. Agregar rutas al router
- [ ] 10. Probar flujo completo
- [ ] 11. Agregar manejo de errores
- [ ] 12. Agregar loading states
- [ ] 13. Agregar validaciones

---

## 🧪 Testing Manual

1. **Request Code**:
   ```
   1. Abrir http://localhost:5173/login
   2. Ingresar número: +56975389973
   3. Click "Enviar Código"
   4. Verificar mensaje en WhatsApp
   ```

2. **Verify Code**:
   ```
   1. Ingresar código de 6 dígitos
   2. Click "Verificar"
   3. Verificar redirección a /dashboard
   4. Verificar token en localStorage
   ```

3. **Protected Route**:
   ```
   1. Logout (limpiar localStorage)
   2. Intentar acceder a /dashboard
   3. Verificar redirección a /login
   ```

---

## 📋 Payloads de Ejemplo

### Request Code

```http
POST http://localhost:8000/api/auth/phone/request-code
Content-Type: application/json

{
  "phone_number": "+56912345678"
}
```

**Response 200**:
```json
{
  "success": true,
  "message": "Código enviado por WhatsApp",
  "expires_at": "2025-11-23T22:05:00Z",
  "retry_after": 60
}
```

### Verify Code

```http
POST http://localhost:8000/api/auth/phone/verify-code
Content-Type: application/json

{
  "phone_number": "+56912345678",
  "code": "123456"
}
```

**Response 200**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "refresh_token": "v1.MR...",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "phone": "+56912345678",
    "email": null,
    "created_at": "2025-11-23T21:40:00.000Z"
  }
}
```

### Use Token in Request

```http
GET http://localhost:8000/api/whatsapp/send/to-phone
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "phone_number": "+56987654321",
  "message": "Hola desde la app!"
}
```

---

¡La guía está completa! Incluye todos los componentes, servicios, tipos y lógica necesaria para implementar el login por WhatsApp en tu frontend React.
