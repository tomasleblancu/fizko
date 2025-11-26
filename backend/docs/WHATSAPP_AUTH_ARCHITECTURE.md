# Arquitectura de Autenticación por WhatsApp (OTP)

## 📋 Resumen

Sistema de autenticación sin contraseña (passwordless) usando códigos de verificación enviados por WhatsApp.

## 🏗️ Arquitectura General

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React)                          │
│  ┌──────────────────┐      ┌──────────────────┐            │
│  │  LoginPhoneForm  │ ──►  │  VerifyCodeForm  │            │
│  └──────────────────┘      └──────────────────┘            │
└────────┬──────────────────────────┬───────────────────────┘
         │                          │
         ▼                          ▼
┌─────────────────────────────────────────────────────────────┐
│              Backend (FastAPI)                               │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Auth Router (app/routers/auth/)                     │  │
│  │  ├─ POST /api/auth/phone/request-code               │  │
│  │  └─ POST /api/auth/phone/verify-code                │  │
│  └──────────────────────────────────────────────────────┘  │
│         │                          │                        │
│         ▼                          ▼                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Phone Auth Service                                  │  │
│  │  ├─ generate_verification_code()                     │  │
│  │  ├─ send_code_via_whatsapp()                         │  │
│  │  ├─ verify_code()                                    │  │
│  │  └─ create_or_get_user()                            │  │
│  └──────────────────────────────────────────────────────┘  │
│         │                          │                        │
│         ▼                          ▼                        │
│  ┌──────────────┐    ┌─────────────────┐                  │
│  │  WhatsApp    │    │  Supabase Auth  │                  │
│  │  Service     │    │  Admin API      │                  │
│  └──────────────┘    └─────────────────┘                  │
└────────┬──────────────────────┬──────────────────────────┘
         │                      │
         ▼                      ▼
┌──────────────────┐   ┌─────────────────────────┐
│  Kapso WhatsApp  │   │  Supabase PostgreSQL    │
│  API             │   │  ├─ profiles            │
└──────────────────┘   │  ├─ phone_verification  │
                       │  │    _codes             │
                       └─────────────────────────┘
```

## 📊 Modelo de Datos

### 1. Tabla: `phone_verification_codes`

```sql
CREATE TABLE phone_verification_codes (
    id UUID PRIMARY KEY,
    phone_number TEXT NOT NULL,          -- E.164 format: +56912345678
    code TEXT NOT NULL,                   -- 6-digit code
    created_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,               -- Typical: 5-10 minutes
    verified_at TIMESTAMPTZ,              -- NULL if not verified
    attempts INTEGER DEFAULT 0,           -- Failed verification attempts
    max_attempts INTEGER DEFAULT 3,       -- Max allowed attempts
    metadata JSONB                        -- Extra info (IP, user agent, etc.)
);
```

**Índices**:
- `idx_phone_verification_codes_phone` - Búsqueda por número
- `idx_phone_verification_codes_active` - Códigos activos (no verificados, no expirados)
- `idx_phone_verification_codes_expires` - Cleanup de códigos expirados

### 2. Tabla: `profiles` (existente)

Campos relevantes para autenticación por teléfono:
```sql
profiles:
  - id UUID (Supabase auth.users.id)
  - phone TEXT (número de teléfono en E.164)
  - email TEXT (opcional)
  - created_at TIMESTAMPTZ
```

## 🔄 Flujo de Autenticación

### Fase 1: Request Code

```
1. Frontend → POST /api/auth/phone/request-code
   Body: { phone_number: "+56912345678" }

2. Backend:
   a. Normaliza número (+56912345678)
   b. Valida formato E.164
   c. Genera código aleatorio (6 dígitos)
   d. Guarda en phone_verification_codes (expires_at = now + 5min)
   e. Envía código por WhatsApp
   f. Retorna { success: true, expires_at: "..." }

3. WhatsApp:
   - Busca conversación activa con ese número
   - Envía mensaje: "Tu código de verificación es: 123456"
```

### Fase 2: Verify Code

```
1. Frontend → POST /api/auth/phone/verify-code
   Body: { phone_number: "+56912345678", code: "123456" }

2. Backend:
   a. Busca código activo para ese número
   b. Verifica que no esté expirado
   c. Verifica attempts < max_attempts
   d. Compara código (timing-safe comparison)

   Si código es INCORRECTO:
     - Incrementa attempts
     - Retorna error { error: "invalid_code", attempts_remaining: 2 }

   Si código es CORRECTO:
     e. Marca código como verified (verified_at = now)
     f. Busca/crea usuario en profiles
     g. Genera JWT token de Supabase
     h. Retorna { access_token, refresh_token, user }
```

## 🔐 Seguridad

### Rate Limiting

**Por Número de Teléfono**:
- Máximo 3 solicitudes de código por hora por número
- Máximo 3 intentos de verificación por código

**Por IP**:
- Máximo 10 solicitudes de código por hora
- Máximo 20 intentos de verificación por hora

### Validaciones

1. **Formato de número**: E.164 format (+[country][number])
2. **Timing-safe comparison**: Previene timing attacks
3. **Expiración de códigos**: 5-10 minutos
4. **Cleanup automático**: Borrar códigos expirados cada hora

### Prevención de Abuso

- Códigos de un solo uso (marcados como verified)
- Límite de intentos por código (3)
- Cooldown entre solicitudes (60 segundos)
- Logging de intentos fallidos

## 📂 Estructura de Archivos

```
backend/app/
├── routers/
│   └── auth/
│       ├── __init__.py
│       ├── main.py                    # Router principal
│       ├── schemas.py                 # Request/Response models
│       └── phone.py                   # Endpoints de autenticación por teléfono
│
├── services/
│   └── auth/
│       ├── __init__.py
│       ├── phone_auth_service.py      # Lógica de negocio OTP
│       └── supabase_auth_service.py   # Interacción con Supabase Auth
│
├── repositories/
│   └── verification_codes.py         # Data access para códigos
│
└── core/
    └── security.py                    # Utilidades de seguridad (generar códigos, etc.)
```

## 🔌 Endpoints API

### 1. Request Verification Code

```http
POST /api/auth/phone/request-code
Content-Type: application/json

{
  "phone_number": "+56912345678"
}
```

**Response (200 OK)**:
```json
{
  "success": true,
  "message": "Código enviado por WhatsApp",
  "expires_at": "2025-11-23T21:45:00Z",
  "retry_after": 60
}
```

**Response (429 Too Many Requests)**:
```json
{
  "detail": "Too many requests. Try again in 45 seconds."
}
```

**Response (400 Bad Request)**:
```json
{
  "detail": "Invalid phone number format. Use E.164 format: +56912345678"
}
```

### 2. Verify Code

```http
POST /api/auth/phone/verify-code
Content-Type: application/json

{
  "phone_number": "+56912345678",
  "code": "123456"
}
```

**Response (200 OK)**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "refresh_token": "v1.MR...",
  "user": {
    "id": "uuid-here",
    "phone": "+56912345678",
    "email": null,
    "created_at": "2025-11-23T21:40:00Z"
  }
}
```

**Response (400 Bad Request - Invalid Code)**:
```json
{
  "error": "invalid_code",
  "message": "Código incorrecto",
  "attempts_remaining": 2
}
```

**Response (400 Bad Request - Expired)**:
```json
{
  "error": "code_expired",
  "message": "El código ha expirado. Solicita uno nuevo."
}
```

**Response (400 Bad Request - Too Many Attempts)**:
```json
{
  "error": "max_attempts_exceeded",
  "message": "Demasiados intentos fallidos. Solicita un nuevo código."
}
```

## 🎯 Integración con Supabase Auth

### Crear Usuario en Supabase

```python
from supabase import create_client

# Usar Admin API para crear usuario sin email
supabase_admin = create_client(
    supabase_url,
    service_role_key  # Service role key (no anon key)
)

# Crear usuario
user_response = supabase_admin.auth.admin.create_user({
    "phone": "+56912345678",
    "phone_confirmed": True,  # Ya verificado por OTP
    "user_metadata": {
        "verified_via": "whatsapp_otp"
    }
})

# Generar JWT token
token = supabase_admin.auth.admin.generate_link({
    "type": "magiclink",
    "email": f"{phone_number}@fizko.temp"  # Email temporal
})
```

**Alternativa**: Usar `signInWithPassword` con teléfono como username y código como password (un solo uso).

## 🧪 Testing

### Unit Tests

```python
# tests/unit/services/test_phone_auth_service.py

async def test_generate_verification_code():
    service = PhoneAuthService()
    code = service._generate_code()
    assert len(code) == 6
    assert code.isdigit()

async def test_verify_code_success():
    # Mock database con código válido
    result = await service.verify_code("+56912345678", "123456")
    assert result.success is True

async def test_verify_code_expired():
    # Mock código expirado
    with pytest.raises(CodeExpiredError):
        await service.verify_code("+56912345678", "123456")
```

### Integration Tests

```python
# tests/integration/test_phone_auth_flow.py

async def test_full_auth_flow(client: AsyncClient):
    # 1. Request code
    response = await client.post(
        "/api/auth/phone/request-code",
        json={"phone_number": "+56975389973"}
    )
    assert response.status_code == 200

    # 2. Get code from database (in test env)
    code = await get_latest_verification_code("+56975389973")

    # 3. Verify code
    response = await client.post(
        "/api/auth/phone/verify-code",
        json={"phone_number": "+56975389973", "code": code}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
```

## 📱 Formato de Mensajes WhatsApp

### Mensaje de Verificación

```
🔐 Código de Verificación Fizko

Tu código es: 123456

Este código expira en 5 minutos.

No compartas este código con nadie.
```

### Configuración de Template (Opcional)

Si usas templates de WhatsApp Business:

```json
{
  "name": "verification_code",
  "language": "es_CL",
  "components": [
    {
      "type": "body",
      "parameters": [
        {"type": "text", "text": "{{1}}"}  // Código
      ]
    }
  ]
}
```

## 🔧 Variables de Entorno

```bash
# .env

# Supabase (ya existentes)
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=...
SUPABASE_SERVICE_ROLE_KEY=...  # NUEVO: Para crear usuarios
SUPABASE_JWT_SECRET=...

# WhatsApp (ya existentes)
KAPSO_API_TOKEN=...
KAPSO_PROJECT_ID=...

# Phone Auth (nuevos)
PHONE_VERIFICATION_CODE_EXPIRY_MINUTES=5
PHONE_VERIFICATION_MAX_ATTEMPTS=3
PHONE_VERIFICATION_RATE_LIMIT_PER_HOUR=3
PHONE_VERIFICATION_COOLDOWN_SECONDS=60
```

## 🚀 Deployment Checklist

- [ ] Aplicar migración de `phone_verification_codes`
- [ ] Configurar `SUPABASE_SERVICE_ROLE_KEY`
- [ ] Implementar rate limiting (Redis o in-memory)
- [ ] Configurar Celery task para cleanup de códigos expirados
- [ ] Configurar monitoring para intentos fallidos
- [ ] Agregar logging de eventos de autenticación
- [ ] Testear flujo completo en staging

## 🔍 Monitoreo y Alertas

### Métricas a Trackear

1. **Tasa de éxito de verificación**: % de códigos verificados correctamente
2. **Tiempo promedio de verificación**: Desde solicitud hasta verificación
3. **Intentos fallidos**: Alertar si > 50% de intentos fallan
4. **Códigos expirados sin verificar**: Indica UX problems

### Logs Importantes

```python
# Request code
logger.info(f"Verification code requested for {phone_number}")

# Code sent
logger.info(f"Code sent via WhatsApp to {phone_number}")

# Verification failed
logger.warning(f"Invalid code attempt for {phone_number} ({attempts}/{max_attempts})")

# Verification success
logger.info(f"User authenticated via phone: {user_id}")
```

## 📋 Próximos Pasos / Mejoras Futuras

1. **Refresh tokens**: Implementar refresh token rotation
2. **Remember device**: Permitir "recordar este dispositivo" por 30 días
3. **Fallback SMS**: Si WhatsApp falla, enviar por SMS
4. **Two-factor auth**: Opcional para usuarios que quieran más seguridad
5. **Biometrics**: Integración con Face ID / Touch ID en móvil
6. **Phone number change**: Flujo para cambiar número verificado

## 🔗 Referencias

- [Supabase Auth Admin API](https://supabase.com/docs/reference/javascript/auth-admin-api)
- [WhatsApp Business API - Templates](https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates)
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [E.164 Phone Number Format](https://en.wikipedia.org/wiki/E.164)
