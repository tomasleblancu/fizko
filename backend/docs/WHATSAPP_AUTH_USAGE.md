```javascript
// 1. Request Verification Code
async function requestVerificationCode(phoneNumber) {
  const response = await fetch('http://localhost:8000/api/auth/phone/request-code', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      phone_number: phoneNumber  // e.g., "+56912345678"
    })
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail);
  }

  const data = await response.json();
  // {
  //   "success": true,
  //   "message": "Código enviado por WhatsApp",
  //   "expires_at": "2025-11-23T22:05:00Z",
  //   "retry_after": 60
  // }

  return data;
}

// 2. Verify Code
async function verifyCode(phoneNumber, code) {
  const response = await fetch('http://localhost:8000/api/auth/phone/verify-code', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      phone_number: phoneNumber,
      code: code  // 6-digit code
    })
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail);
  }

  const data = await response.json();
  // {
  //   "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  //   "token_type": "bearer",
  //   "expires_in": 3600,
  //   "refresh_token": "v1.MR...",
  //   "user": {
  //     "id": "uuid-here",
  //     "phone": "+56912345678",
  //     "email": null,
  //     "created_at": "2025-11-23T21:40:00Z"
  //   }
  // }

  // Save token to localStorage/secure storage
  localStorage.setItem('access_token', data.access_token);
  localStorage.setItem('refresh_token', data.refresh_token);

  return data;
}

// 3. Use token in subsequent requests
async function makeAuthenticatedRequest(endpoint) {
  const token = localStorage.getItem('access_token');

  const response = await fetch(`http://localhost:8000${endpoint}`, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    }
  });

  return response.json();
}
```

## 🎯 Ejemplo Completo: React Component

```typescript
// LoginWithPhone.tsx

import { useState } from 'react';

type AuthStep = 'phone' | 'code' | 'authenticated';

export function LoginWithPhone() {
  const [step, setStep] = useState<AuthStep>('phone');
  const [phoneNumber, setPhoneNumber] = useState('+56');
  const [code, setCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [expiresAt, setExpiresAt] = useState<string | null>(null);

  const handleRequestCode = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await fetch('http://localhost:8000/api/auth/phone/request-code', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone_number: phoneNumber })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail);
      }

      const data = await response.json();
      setExpiresAt(data.expires_at);
      setStep('code');

    } catch (err: any) {
      setError(err.message || 'Error al enviar código');
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyCode = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await fetch('http://localhost:8000/api/auth/phone/verify-code', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          phone_number: phoneNumber,
          code: code
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail);
      }

      const data = await response.json();

      // Save tokens
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('refresh_token', data.refresh_token);
      localStorage.setItem('user', JSON.stringify(data.user));

      setStep('authenticated');

      // Redirect to dashboard
      window.location.href = '/dashboard';

    } catch (err: any) {
      setError(err.message || 'Código inválido');
    } finally {
      setLoading(false);
    }
  };

  if (step === 'phone') {
    return (
      <div className="login-container">
        <h2>Iniciar Sesión</h2>
        <p>Ingresa tu número de teléfono para recibir un código por WhatsApp</p>

        <form onSubmit={handleRequestCode}>
          <input
            type="tel"
            placeholder="+56 9 1234 5678"
            value={phoneNumber}
            onChange={(e) => setPhoneNumber(e.target.value)}
            disabled={loading}
            required
          />

          {error && <div className="error">{error}</div>}

          <button type="submit" disabled={loading}>
            {loading ? 'Enviando...' : 'Enviar Código'}
          </button>
        </form>
      </div>
    );
  }

  if (step === 'code') {
    return (
      <div className="login-container">
        <h2>Verificar Código</h2>
        <p>Ingresa el código de 6 dígitos que recibiste por WhatsApp</p>
        <p className="phone-number">{phoneNumber}</p>

        <form onSubmit={handleVerifyCode}>
          <input
            type="text"
            placeholder="000000"
            value={code}
            onChange={(e) => setCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
            disabled={loading}
            maxLength={6}
            pattern="[0-9]{6}"
            required
            autoFocus
          />

          {error && <div className="error">{error}</div>}

          <button type="submit" disabled={loading || code.length !== 6}>
            {loading ? 'Verificando...' : 'Verificar'}
          </button>

          <button
            type="button"
            onClick={() => setStep('phone')}
            disabled={loading}
            className="secondary"
          >
            Cambiar Número
          </button>
        </form>

        {expiresAt && (
          <p className="expiry-info">
            Código expira en: {new Date(expiresAt).toLocaleTimeString()}
          </p>
        )}
      </div>
    );
  }

  return null;
}
```

## 🧪 Testing con cURL

### 1. Request Code

```bash
# Solicitar código
curl -X POST "http://localhost:8000/api/auth/phone/request-code" \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+56975389973"
  }'

# Response:
# {
#   "success": true,
#   "message": "Código enviado por WhatsApp",
#   "expires_at": "2025-11-23T22:05:00Z",
#   "retry_after": 60
# }
```

### 2. Verify Code

```bash
# Verificar código
curl -X POST "http://localhost:8000/api/auth/phone/verify-code" \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+56975389973",
    "code": "123456"
  }'

# Response (success):
# {
#   "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
#   "token_type": "bearer",
#   "expires_in": 3600,
#   "refresh_token": "v1.MR...",
#   "user": {
#     "id": "550e8400-e29b-41d4-a716-446655440000",
#     "phone": "+56975389973",
#     "email": null,
#     "created_at": "2025-11-23T21:40:00.000Z"
#   }
# }

# Response (error - invalid code):
# {
#   "detail": "Código incorrecto. Te quedan 2 intentos."
# }
```

### 3. Use Token

```bash
# Usar token en request autenticado
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

curl "http://localhost:8000/api/whatsapp/send/to-phone" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+56912345678",
    "message": "Hola desde la app!"
  }'
```

## 🔧 Variables de Entorno Requeridas

Agregar a `backend/.env`:

```bash
# Supabase (obligatorias)
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_ROLE_KEY=eyJ...  # IMPORTANTE: Service role para crear usuarios
SUPABASE_JWT_SECRET=your-jwt-secret

# WhatsApp (obligatorias)
KAPSO_API_TOKEN=sk_...
KAPSO_PROJECT_ID=proj_...

# Phone Auth (opcionales - tienen defaults)
PHONE_VERIFICATION_CODE_EXPIRY_MINUTES=5
PHONE_VERIFICATION_MAX_ATTEMPTS=3
PHONE_VERIFICATION_COOLDOWN_SECONDS=60
```

## 📋 Setup Checklist

### 1. Aplicar Migración de Base de Datos

```bash
# Opción A: Via Supabase Dashboard
# 1. Ve a SQL Editor en Supabase Dashboard
# 2. Copia el contenido de:
#    backend/supabase/migrations/20251123213739_phone_verification_codes.sql
# 3. Ejecuta el SQL

# Opción B: Via Supabase CLI
cd backend
supabase migration up
```

### 2. Configurar Variables de Entorno

```bash
# Copiar .env.example a .env
cp backend/.env.example backend/.env

# Editar .env y agregar:
# - SUPABASE_SERVICE_ROLE_KEY (obtener de Supabase Dashboard > Settings > API)
# - KAPSO_API_TOKEN
# - Otros valores de configuración
```

### 3. Verificar Instalación

```bash
# Iniciar backend
cd backend
./dev.sh

# En otra terminal, verificar endpoints
curl http://localhost:8000/

# Debe retornar:
# {
#   "service": "SII Integration Service",
#   "version": "2.0.0",
#   "status": "running",
#   "features": {
#     ...
#     "authentication": true
#   }
# }
```

### 4. Probar Flujo Completo

```bash
# 1. Asegúrate de tener conversación activa con tu número de prueba
# 2. Request code
curl -X POST "http://localhost:8000/api/auth/phone/request-code" \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+56975389973"}'

# 3. Revisa WhatsApp para obtener el código
# 4. Verify code
curl -X POST "http://localhost:8000/api/auth/phone/verify-code" \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+56975389973", "code": "CODIGO_RECIBIDO"}'

# 5. Usar token retornado en requests autenticados
```

## ⚠️ Limitaciones y Soluciones

### 1. "No active conversation found"

**Problema**: El usuario no tiene conversación activa de WhatsApp con Fizko.

**Solución**:
- Opción A: Usuario inicia conversación enviando cualquier mensaje a Fizko
- Opción B: Enviar template de WhatsApp Business (requiere template aprobado)
- Opción C: Fallback a SMS (requiere integración adicional)

### 2. "Code expired"

**Problema**: Código expiró (5 minutos).

**Solución**: Solicitar nuevo código.

### 3. "Too many attempts"

**Problema**: Usuario excedió 3 intentos de verificación.

**Solución**: Solicitar nuevo código.

### 4. "Rate limit exceeded"

**Problema**: Usuario solicitó múltiples códigos en corto tiempo.

**Solución**: Esperar 60 segundos antes de solicitar otro código.

## 🔒 Seguridad

### Mejores Prácticas

1. **Almacenar tokens de forma segura**:
   ```typescript
   // ✅ BUENO: Usar httpOnly cookies (server-side)
   // ✅ BUENO: Usar secure storage en mobile
   // ⚠️  ACEPTABLE: localStorage (solo si no hay alternativa)
   // ❌ MALO: sessionStorage para refresh tokens
   ```

2. **Validar formato de números**:
   ```typescript
   // Siempre usar E.164 format
   const phoneRegex = /^\+[1-9]\d{1,14}$/;
   if (!phoneRegex.test(phoneNumber)) {
     throw new Error('Invalid phone number format');
   }
   ```

3. **Manejar expiración de tokens**:
   ```typescript
   // Interceptor para refrescar token automáticamente
   axios.interceptors.response.use(
     response => response,
     async error => {
       if (error.response?.status === 401) {
         // Token expired - refresh
         const refreshToken = localStorage.getItem('refresh_token');
         // ... refresh logic
       }
       return Promise.reject(error);
     }
   );
   ```

4. **Limpiar datos sensibles**:
   ```typescript
   // Al logout
   function logout() {
     localStorage.removeItem('access_token');
     localStorage.removeItem('refresh_token');
     localStorage.removeItem('user');
     window.location.href = '/login';
   }
   ```

## 📊 Monitoreo

### Logs a Revisar

```bash
# Ver logs de autenticación
cd backend
tail -f logs/auth.log | grep "phone"

# Buscar intentos fallidos
grep "Invalid code" logs/auth.log

# Ver rate limiting
grep "Rate limit" logs/auth.log
```

### Métricas Importantes

- Tasa de éxito de verificación
- Tiempo promedio entre request y verify
- Número de códigos expirados
- Intentos fallidos por código

## 🚀 Próximos Pasos

1. **Implementar en Frontend**:
   - Crear componente de login
   - Agregar manejo de errores
   - Implementar UI de código de verificación

2. **Mejoras de Seguridad**:
   - Rate limiting por IP (usar Redis)
   - Device fingerprinting
   - Geolocation validation

3. **UX Enhancements**:
   - Auto-submit código cuando se llena
   - Countdown timer para expiración
   - Reenvío de código con cooldown visual

4. **Monitoring**:
   - Alertas para tasa de fallo alta
   - Dashboard de métricas de autenticación
   - Logs estructurados

## 📚 Referencias

- [Arquitectura Completa](./WHATSAPP_AUTH_ARCHITECTURE.md)
- [Migración SQL](./supabase/migrations/20251123213739_phone_verification_codes.sql)
- [Supabase Auth](https://supabase.com/docs/guides/auth)
- [WhatsApp Integration](./app/routers/whatsapp/README.md)
