# Supabase Edge Functions

Este directorio contiene las Edge Functions de Supabase para Fizko.

## Funciones Disponibles

### `iva-summary`
Calcula el resumen de IVA para un período específico.

**Endpoint:** `https://oppvraaktawbidyfjhmy.supabase.co/functions/v1/iva-summary`

**Autenticación:** Requiere JWT token válido

**Parámetros:**
- `period` (query param): Período en formato YYYY-MM (ej: "2024-01")
- `company_id` (query param): ID de la compañía

**Ejemplo:**
```bash
curl -i --location --request GET \
  'https://oppvraaktawbidyfjhmy.supabase.co/functions/v1/iva-summary?period=2024-01&company_id=123' \
  --header 'Authorization: Bearer YOUR_JWT_TOKEN'
```

## Desarrollo Local

### Iniciar Funciones Localmente

```bash
cd backend
supabase functions serve
```

Las funciones estarán disponibles en `http://localhost:54321/functions/v1/`

### Probar una Función

```bash
# Con curl
curl -i --location --request GET \
  'http://localhost:54321/functions/v1/iva-summary?period=2024-01&company_id=123' \
  --header 'Authorization: Bearer YOUR_JWT_TOKEN'

# O usar el script de prueba incluido
cd supabase/functions/iva-summary
./test.sh
```

## Deploy a Producción

### Deploy de una Función Específica

```bash
cd backend
supabase functions deploy iva-summary --project-ref oppvraaktawbidyfjhmy
```

### Deploy de Todas las Funciones

```bash
cd backend
supabase functions deploy --project-ref oppvraaktawbidyfjhmy
```

## Configuración

### deno.json
El archivo `deno.json` configura Deno para manejar dependencias automáticamente:

```json
{
  "nodeModulesDir": "auto",
  "compilerOptions": {
    "allowJs": true,
    "lib": ["deno.window"],
    "strict": true
  },
  "imports": {
    "@supabase/supabase-js": "jsr:@supabase/supabase-js@^2",
    "@supabase/functions-js": "jsr:@supabase/functions-js@^2"
  }
}
```

La opción `"nodeModulesDir": "auto"` permite a Deno instalar automáticamente las dependencias de npm necesarias.

### config.toml
Configuración de funciones en `supabase/config.toml`:

```toml
[functions.iva-summary]
verify_jwt = true
```

## Solución de Problemas

### Error: "Could not find a matching package"

Si ves este error:
```
Error: failed to create the graph
Caused by:
    Could not find a matching package for 'npm:@supabase/realtime-js@2.15.5'
```

**Solución:** Asegúrate de que existe `deno.json` con `"nodeModulesDir": "auto"` en el directorio `functions/`.

### Error: "verify_jwt is not supported"

Si ves este error al hacer deploy:
```
Warning: verify_jwt is not supported for remote functions, skipping...
```

Esto es normal - la verificación JWT se configura en el dashboard de Supabase, no en el config.toml local.

### Regenerar lock file

Si las dependencias están desactualizadas:
```bash
cd backend/supabase/functions
deno cache --reload */index.ts
```

## Estructura de Archivos

```
functions/
├── deno.json           # Configuración de Deno
├── .gitignore          # Archivos a ignorar
├── README.md           # Esta documentación
└── iva-summary/        # Función de resumen IVA
    ├── index.ts        # Código principal
    ├── README.md       # Documentación específica
    ├── example-usage.ts # Ejemplos de uso
    └── test.sh         # Script de prueba
```

## Variables de Entorno

Las funciones tienen acceso automático a:
- `SUPABASE_URL` - URL del proyecto Supabase
- `SUPABASE_ANON_KEY` - Clave pública anon
- `SUPABASE_SERVICE_ROLE_KEY` - Clave de servicio (bypass RLS)

Puedes agregar variables adicionales en el dashboard de Supabase:
1. Ve a **Project Settings** → **Edge Functions**
2. Agrega variables en la sección **Secrets**

## Recursos

- [Documentación de Edge Functions](https://supabase.com/docs/guides/functions)
- [Deno Deploy](https://deno.com/deploy/docs)
- [Supabase CLI](https://supabase.com/docs/guides/cli)
