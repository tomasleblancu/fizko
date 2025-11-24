# SII Authentication Edge Function

Esta Edge Function de Supabase maneja el flujo completo de autenticación y onboarding de empresas con el SII.

## Flujo de Autenticación

La función ejecuta los siguientes pasos en orden:

### 1. Normalizar RUT
- Limpia el formato del RUT (remueve puntos y espacios)
- Convierte a formato: `{body}{dv_lowercase}` (ej: "77794858k")
- Extrae RUT body y DV para llamadas al backend

### 2. Autenticar con SII Backend
- Llama al endpoint FastAPI: `POST /api/sii/login`
- Envía credenciales del SII (RUT, DV, contraseña)
- Recibe datos del contribuyente y contraseña encriptada

### 3. Crear o Actualizar Empresa
- Busca empresa existente por RUT normalizado
- **Si no existe:**
  - Crea registro en `companies` con datos del SII
  - Crea registro en `company_tax_info` con actividades económicas
- **Si existe:**
  - Actualiza datos de contacto en `companies`
  - Actualiza `company_tax_info`

### 4. Guardar Credenciales Encriptadas
- Guarda `sii_password` (ya encriptado por backend) en tabla `companies`
- Permite sincronización automática de documentos en el futuro

### 5. Lanzar Tareas de Sincronización (Solo Empresas Nuevas)
- **Documentos SII** (4 tareas en paralelo):
  - Mes actual (offset 0)
  - Mes anterior (offset 1)
  - 2 meses atrás (offset 2)
  - Últimos 12 meses (offset 3-14)
- **Form29** (1 tarea):
  - Sincroniza formularios F29 del año actual
- Las tareas se lanzan de forma asíncrona y no bloquean la respuesta

### 6. Crear o Actualizar Sesión
- Asegura que el usuario tenga un perfil en `profiles`
- Crea o actualiza sesión en `sessions`:
  - Vincula usuario con empresa
  - Guarda cookies del SII para futuros scraping
  - Marca sesión como activa

### 7. Verificar Setup Inicial
- Chequea tabla `company_settings`
- Verifica campo `is_initial_setup_complete`
- Retorna `needs_setup: true` si falta configuración inicial

## Request

```typescript
POST /functions/v1/sii-auth
Authorization: Bearer <USER_JWT_TOKEN>
Content-Type: application/json

{
  "rut": "12.345.678-9",  // Con o sin formato
  "password": "password123"
}
```

## Response

### Éxito (200)
```json
{
  "success": true,
  "company_id": "uuid-empresa",
  "session_id": "uuid-sesion",
  "needs_setup": false,
  "message": "Autenticación exitosa"
}
```

### Error de Autenticación (401)
```json
{
  "success": false,
  "needs_setup": false,
  "error": "Credenciales del SII inválidas"
}
```

### Error de Validación (400)
```json
{
  "success": false,
  "needs_setup": false,
  "error": "RUT y contraseña son requeridos"
}
```

### Error del Servidor (500)
```json
{
  "success": false,
  "needs_setup": false,
  "error": "Error inesperado: <detalle>"
}
```

## Variables de Entorno

La Edge Function requiere las siguientes variables de entorno configuradas en Supabase:

```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
BACKEND_URL=https://fizko-v2-production.up.railway.app  # Backend FastAPI
```

## Deployment

### Desplegar la función a Supabase

```bash
# Desde la raíz del proyecto
cd backend

# Desplegar la función
supabase functions deploy sii-auth --project-ref your-project-ref

# Configurar variables de entorno
supabase secrets set BACKEND_URL=https://fizko-v2-production.up.railway.app --project-ref your-project-ref
```

### Testing Local

```bash
# Iniciar Supabase local
supabase start

# Servir la función localmente
supabase functions serve sii-auth --env-file backend/.env.local

# Test con curl
curl -i --location --request POST 'http://localhost:54321/functions/v1/sii-auth' \
  --header 'Authorization: Bearer YOUR_USER_JWT' \
  --header 'Content-Type: application/json' \
  --data '{"rut":"12345678-9","password":"test123"}'
```

## Dependencias Externas

La función hace llamadas a los siguientes servicios:

1. **Backend FastAPI** (`BACKEND_URL`):
   - `POST /api/sii/login` - Autenticación con SII
   - `POST /api/celery/tasks/launch` - Lanzar tareas de sincronización

2. **Supabase Database**:
   - Tablas: `companies`, `company_tax_info`, `sessions`, `profiles`, `company_settings`

## Logs y Debugging

La función genera logs detallados en cada paso:

```
[SII Auth] Starting authentication for user: <user_id>
[SII Auth] Normalized RUT: <rut>
[SII Auth] Calling backend SII login
[SII Auth] SII authentication successful
[Company] Creating new company with RUT: <rut>
[Company] Company created successfully: <company_id>
[SII Auth] Launching document sync tasks for new company
[Task] Launching sii.sync_documents task
[Task] sii.sync_documents launched with task_id: <task_id>
[Session] Creating/updating session
[Profile] Checking if profile exists for user: <user_id>
[SII Auth] Setup required: <true/false>
```

Ver logs en Supabase Dashboard: **Functions > sii-auth > Logs**

## Seguridad

- **Autenticación requerida**: Valida JWT del usuario antes de procesar
- **Service Role Key**: Usa Service Role para operaciones privilegiadas en DB
- **Contraseñas encriptadas**: Las contraseñas del SII se encriptan en el backend con Fernet/AES-256
- **CORS habilitado**: Permite llamadas desde cualquier origen (ajustar en producción si es necesario)

## Errores Comunes

### "No autenticado"
- Verificar que el JWT sea válido y no haya expirado
- Asegurarse de enviar el header `Authorization: Bearer <token>`

### "Error al autenticar con SII"
- Verificar credenciales del SII
- Revisar que el backend esté disponible (`BACKEND_URL`)
- Verificar logs del backend FastAPI

### "Error al crear empresa"
- Revisar permisos RLS en tabla `companies`
- Verificar que `SUPABASE_SERVICE_ROLE_KEY` esté correctamente configurado

### "Error al crear sesión"
- Verificar que la tabla `profiles` tenga el registro del usuario
- La función intenta crear el perfil automáticamente si no existe

## Performance

- **Tiempo promedio**: 3-5 segundos
  - 2-3s autenticación con SII
  - 1-2s creación de empresa y sesión
  - <1s lanzamiento de tareas (asíncrono)

- **Timeout**: 60 segundos (límite de Edge Functions)

- **Tareas asíncronas**: Las tareas de sincronización se lanzan en background y no afectan el tiempo de respuesta
