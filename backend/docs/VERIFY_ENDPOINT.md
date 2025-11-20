# Endpoint de Verificación de Credenciales SII

Documentación completa del endpoint `/api/sii/verify` - Verificación de credenciales y extracción completa de información del contribuyente.

## 🎯 Propósito

Este endpoint permite:
- ✅ **Verificar credenciales** del SII sin guardar nada en base de datos
- 📊 **Extraer información completa** del contribuyente
- 🍪 **Reutilizar sesiones** mediante cookies
- ⚡ **Optimizar rendimiento** evitando logins repetidos

**Diferencias con otros endpoints:**
- `/login`: Solo valida credenciales y retorna cookies básicas
- `/contribuyente`: Requiere login previo, extrae info del contribuyente
- `/verify`: **Todo en uno** - verifica + extrae + retorna cookies

---

## 📋 Especificación del Endpoint

### Request

**Endpoint:** `POST /api/sii/verify`

**Headers:**
```
Content-Type: application/json
```

**Body:**
```json
{
  "rut": "77794858",
  "dv": "K",
  "password": "SiiPfufl574@#",
  "cookies": []  // Opcional: cookies de sesión anterior
}
```

#### Parámetros

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `rut` | string | ✅ | RUT sin puntos ni guión (ej: "77794858") |
| `dv` | string | ✅ | Dígito verificador (ej: "K") |
| `password` | string | ✅ | Contraseña del SII |
| `cookies` | array | ❌ | Cookies de sesión existentes (opcional) |

---

### Response

**Status Code:** `200 OK`

**Body:**
```json
{
  "success": true,
  "message": "Credenciales verificadas exitosamente",
  "contribuyente_info": {
    "rut": "77794858-K",
    "razon_social": "MI EMPRESA SPA",
    "nombre_fantasia": "Mi Empresa",
    "actividades_economicas": [
      {
        "codigo": 620200,
        "glosa": "Actividades de consultores en informática",
        "categoria": "PRIMERA",
        "afecta_iva": true
      }
    ],
    "direccion": {
      "calle": "AV. LIBERTADOR BERNARDO O'HIGGINS",
      "numero": "1234",
      "comuna": "SANTIAGO",
      "ciudad": "SANTIAGO",
      "region": "REGIÓN METROPOLITANA"
    },
    "contacto": {
      "email": "contacto@miempresa.cl",
      "telefono": "+56912345678",
      "telefono_movil": "+56987654321"
    },
    "regimen_tributario": {
      "codigo": "14A",
      "descripcion": "Renta Efectiva con Contabilidad Completa",
      "categoria": "PRIMERA CATEGORÍA"
    },
    "representantes_legales": [
      {
        "rut": "12345678-9",
        "nombre": "JUAN PÉREZ GONZÁLEZ",
        "cargo": "REPRESENTANTE LEGAL"
      }
    ],
    "sucursales": [
      {
        "codigo": "001",
        "direccion": "CALLE FALSA 123",
        "comuna": "PROVIDENCIA"
      }
    ],
    "estado": "ACTIVO",
    "inicio_actividades": "2020-01-15",
    "termino_giro": null,
    "capital_efectivo": 50000000,
    "capital_propio": 50000000,
    "tipo_contribuyente": "PERSONA JURÍDICA",
    "categoria_tributaria": "GRAN CONTRIBUYENTE",
    "archivador_electronico": true,
    "facturacion_electronica": true,
    "autorizacion_imprenta": false
  },
  "cookies": [
    {
      "domain": ".sii.cl",
      "name": "TOKEN",
      "value": "E55R4XVF30UG9",
      "path": "/",
      "secure": true,
      "httpOnly": false,
      "sameSite": "Strict",
      "expiry": 1700000000
    }
    // ... más cookies (12-16 en total)
  ],
  "session_refreshed": true,
  "extraction_method": "scraping",
  "timestamp": "2025-11-19T10:30:45.123456"
}
```

---

## 📊 Estructura de Datos Retornados

### 1. `contribuyente_info` (Dict)

Información completa del contribuyente extraída del perfil SII:

#### Campos Básicos

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `rut` | string | RUT completo con DV (ej: "77794858-K") |
| `razon_social` | string | Razón social oficial del contribuyente |
| `nombre_fantasia` | string | Nombre comercial (si aplica) |
| `estado` | string | Estado actual (ACTIVO, SUSPENDIDO, TÉRMINO DE GIRO) |
| `tipo_contribuyente` | string | PERSONA JURÍDICA, PERSONA NATURAL, etc. |

#### Actividades Económicas

```python
"actividades_economicas": [
    {
        "codigo": 620200,  # Código actividad económica
        "glosa": "Actividades de consultores en informática",  # Descripción
        "categoria": "PRIMERA",  # Categoría tributaria
        "afecta_iva": true  # Si está afecto a IVA
    }
]
```

#### Dirección

```python
"direccion": {
    "calle": str,  # Nombre de calle/avenida
    "numero": str,  # Número
    "depto_oficina": str | null,  # Depto/Oficina (opcional)
    "comuna": str,  # Comuna
    "ciudad": str,  # Ciudad
    "region": str  # Región
}
```

#### Contacto

```python
"contacto": {
    "email": str,  # Email principal
    "email_secundario": str | null,  # Email secundario (opcional)
    "telefono": str,  # Teléfono fijo
    "telefono_movil": str | null  # Teléfono móvil (opcional)
}
```

#### Régimen Tributario

```python
"regimen_tributario": {
    "codigo": str,  # Código del régimen (ej: "14A")
    "descripcion": str,  # Descripción del régimen
    "categoria": str  # Categoría (PRIMERA, SEGUNDA, etc.)
}
```

#### Representantes Legales

```python
"representantes_legales": [
    {
        "rut": str,  # RUT del representante
        "nombre": str,  # Nombre completo
        "cargo": str  # Cargo (REPRESENTANTE LEGAL, GERENTE, etc.)
    }
]
```

#### Sucursales

```python
"sucursales": [
    {
        "codigo": str,  # Código de sucursal
        "direccion": str,  # Dirección completa
        "comuna": str,  # Comuna
        "telefono": str | null  # Teléfono (opcional)
    }
]
```

#### Otros Campos

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `inicio_actividades` | string | Fecha inicio actividades (YYYY-MM-DD) |
| `termino_giro` | string\|null | Fecha término de giro (si aplica) |
| `capital_efectivo` | number\|null | Capital efectivo declarado |
| `capital_propio` | number\|null | Capital propio declarado |
| `categoria_tributaria` | string | GRAN CONTRIBUYENTE, PYME, etc. |
| `archivador_electronico` | boolean | Si usa archivador electrónico |
| `facturacion_electronica` | boolean | Si emite facturas electrónicas |
| `autorizacion_imprenta` | boolean | Si tiene autorización de imprenta |

### 2. `cookies` (List[Dict])

Array de cookies de sesión para reutilización:

```python
{
    "domain": str,  # Dominio (ej: ".sii.cl")
    "name": str,  # Nombre de la cookie (ej: "TOKEN")
    "value": str,  # Valor de la cookie
    "path": str,  # Path (ej: "/")
    "secure": bool,  # Si es HTTPS only
    "httpOnly": bool,  # Si es HTTP only
    "sameSite": str,  # Política SameSite ("Strict", "Lax", "None")
    "expiry": int  # Timestamp de expiración
}
```

### 3. Metadatos

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `success` | boolean | True si la verificación fue exitosa |
| `message` | string | Mensaje descriptivo del resultado |
| `session_refreshed` | boolean | True si se hizo login nuevo, False si reutilizó sesión |
| `extraction_method` | string | Método usado ("scraping", "api", etc.) |
| `timestamp` | string | Timestamp ISO 8601 de la extracción |

---

## 🚀 Ejemplos de Uso

### Ejemplo 1: Verificación Simple (Python)

```python
import requests

url = "http://localhost:8090/api/sii/verify"
data = {
    "rut": "77794858",
    "dv": "K",
    "password": "SiiPfufl574@#"
}

response = requests.post(url, json=data)
result = response.json()

if result["success"]:
    print(f"✅ Verificación exitosa")
    print(f"Razón Social: {result['contribuyente_info']['razon_social']}")
    print(f"RUT: {result['contribuyente_info']['rut']}")
    print(f"Actividades: {len(result['contribuyente_info']['actividades_economicas'])}")
    print(f"Cookies guardadas: {len(result['cookies'])}")

    # Guardar cookies para reutilizar
    cookies = result["cookies"]
else:
    print(f"❌ Error: {result.get('message')}")
```

### Ejemplo 2: Cliente con Reutilización de Cookies

```python
class SIIVerifier:
    def __init__(self, rut: str, dv: str, password: str):
        self.rut = rut
        self.dv = dv
        self.password = password
        self.cookies = None
        self.base_url = "http://localhost:8090/api/sii"

    def verify(self):
        """Verificar credenciales y guardar cookies"""
        data = {
            "rut": self.rut,
            "dv": self.dv,
            "password": self.password
        }

        # Agregar cookies si existen
        if self.cookies:
            data["cookies"] = self.cookies

        response = requests.post(f"{self.base_url}/verify", json=data)
        result = response.json()

        if result["success"]:
            # Actualizar cookies para próximos requests
            self.cookies = result["cookies"]
            return result["contribuyente_info"]
        else:
            raise Exception(f"Verificación fallida: {result.get('message')}")

    def get_info(self):
        """Obtener info usando cookies existentes (rápido)"""
        return self.verify()


# Uso
verifier = SIIVerifier(
    rut="77794858",
    dv="K",
    password="SiiPfufl574@#"
)

# Primera vez (hace login completo)
info1 = verifier.verify()
print(f"Primera verificación: {info1['razon_social']}")

# Segunda vez (reutiliza cookies, mucho más rápido)
info2 = verifier.get_info()
print(f"Segunda verificación: {info2['razon_social']}")
```

### Ejemplo 3: TypeScript/React

```typescript
interface ContribuyenteInfo {
  rut: string;
  razon_social: string;
  nombre_fantasia?: string;
  actividades_economicas: Array<{
    codigo: number;
    glosa: string;
    categoria: string;
    afecta_iva: boolean;
  }>;
  direccion: {
    calle: string;
    numero: string;
    comuna: string;
    ciudad: string;
    region: string;
  };
  contacto: {
    email: string;
    telefono: string;
  };
  estado: string;
  // ... más campos
}

interface VerifyResponse {
  success: boolean;
  message: string;
  contribuyente_info: ContribuyenteInfo;
  cookies: any[];
  session_refreshed: boolean;
  extraction_method: string;
  timestamp: string;
}

async function verifySIICredentials(
  rut: string,
  dv: string,
  password: string,
  cookies?: any[]
): Promise<VerifyResponse> {
  const response = await fetch('http://localhost:8090/api/sii/verify', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ rut, dv, password, cookies }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Verification failed');
  }

  return response.json();
}

// Uso
const result = await verifySIICredentials('77794858', 'K', 'password');
console.log('Razón Social:', result.contribuyente_info.razon_social);
console.log('Actividades:', result.contribuyente_info.actividades_economicas);

// Guardar cookies para próximas verificaciones
localStorage.setItem('sii_cookies', JSON.stringify(result.cookies));
```

### Ejemplo 4: React Hook

```typescript
import { useState } from 'react';

export function useSIIVerification() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [contribuyente, setContribuyente] = useState<ContribuyenteInfo | null>(null);
  const [cookies, setCookies] = useState<any[]>([]);

  const verify = async (rut: string, dv: string, password: string) => {
    setLoading(true);
    setError(null);

    try {
      // Intentar con cookies guardadas primero
      const savedCookies = localStorage.getItem('sii_cookies');
      const cookiesToUse = savedCookies ? JSON.parse(savedCookies) : [];

      const response = await fetch('http://localhost:8090/api/sii/verify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          rut,
          dv,
          password,
          cookies: cookiesToUse,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Verification failed');
      }

      const result = await response.json();

      // Guardar datos
      setContribuyente(result.contribuyente_info);
      setCookies(result.cookies);

      // Persistir cookies
      localStorage.setItem('sii_cookies', JSON.stringify(result.cookies));

      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const clearCookies = () => {
    setCookies([]);
    localStorage.removeItem('sii_cookies');
  };

  return {
    verify,
    clearCookies,
    loading,
    error,
    contribuyente,
    cookies,
    hasCookies: cookies.length > 0,
  };
}

// Uso en componente
function VerifyCredentials() {
  const { verify, loading, error, contribuyente, hasCookies } = useSIIVerification();

  const handleVerify = async () => {
    try {
      await verify('77794858', 'K', 'password');
      console.log('Verificación exitosa!');
    } catch (err) {
      console.error('Error:', err);
    }
  };

  return (
    <div>
      <button onClick={handleVerify} disabled={loading}>
        {loading ? 'Verificando...' : 'Verificar Credenciales'}
      </button>

      {hasCookies && <p>✅ Sesión activa (usando cookies)</p>}

      {error && <p style={{ color: 'red' }}>Error: {error}</p>}

      {contribuyente && (
        <div>
          <h3>{contribuyente.razon_social}</h3>
          <p>RUT: {contribuyente.rut}</p>
          <p>Estado: {contribuyente.estado}</p>
        </div>
      )}
    </div>
  );
}
```

---

## ⚠️ Manejo de Errores

### Error 401: Credenciales Inválidas

```json
{
  "detail": "Error de autenticación: Credenciales inválidas"
}
```

**Causas:**
- RUT o contraseña incorrectos
- Cuenta bloqueada en el SII
- Problemas de conexión con el SII

**Solución:**
- Verificar credenciales en misiir.sii.cl manualmente
- Verificar que el RUT esté en formato correcto (sin puntos ni guión)
- Verificar que la contraseña sea correcta

### Error 422: Error en Extracción

```json
{
  "detail": "Error al extraer información del contribuyente: Timeout en scraping"
}
```

**Causas:**
- El SII está lento o no responde
- Timeout durante scraping
- Cambios en la estructura del sitio SII

**Solución:**
- Reintentar el request
- Verificar conexión a internet
- Esperar unos minutos y volver a intentar

### Error 500: Error Inesperado

```json
{
  "detail": "Error inesperado: Internal server error"
}
```

**Causas:**
- Error interno del servicio
- Driver de Selenium no disponible
- Recursos insuficientes

**Solución:**
- Revisar logs del servidor
- Reiniciar el servicio
- Verificar que Chromedriver esté disponible

---

## ⚡ Rendimiento

### Tiempos de Respuesta

| Escenario | Tiempo | Descripción |
|-----------|--------|-------------|
| **Primera vez (sin cookies)** | 7-10 seg | Login completo + extracción |
| **Con cookies válidas** | 2-4 seg | Solo verificación + extracción |
| **Con cookies expiradas** | 7-10 seg | Re-login + extracción |

### Comparación con otros endpoints

| Endpoint | Sin Cookies | Con Cookies | Datos Retornados |
|----------|-------------|-------------|------------------|
| `/login` | 5-8 seg | 5-8 seg | Solo cookies |
| `/contribuyente` | 5-8 seg | 1-2 seg | Info contribuyente |
| **`/verify`** | **7-10 seg** | **2-4 seg** | **Todo: verificación + info completa + cookies** |

### Optimización

**Mejores prácticas:**

1. **Siempre reutiliza cookies:**
   ```python
   # ✅ BUENO
   result1 = verify(cookies=None)  # Primera vez
   result2 = verify(cookies=result1["cookies"])  # Rápido
   ```

2. **Guarda cookies en storage:**
   ```typescript
   localStorage.setItem('sii_cookies', JSON.stringify(cookies));
   ```

3. **Invalida cookies después de 2-3 horas:**
   ```python
   # Cookies del SII expiran después de ~2-3 horas
   if time.time() - last_verify > 7200:  # 2 horas
       cookies = None  # Forzar nuevo login
   ```

---

## 🔒 Seguridad

**Recomendaciones:**

1. **NUNCA almacenes passwords en localStorage/cookies**
   ```javascript
   // ❌ MAL
   localStorage.setItem('sii_password', password);

   // ✅ BIEN
   localStorage.setItem('sii_cookies', JSON.stringify(cookies));
   ```

2. **Usa HTTPS en producción**
   ```
   https://tu-api.com/api/sii/verify
   ```

3. **Valida RUT en el cliente antes de enviar**
   ```typescript
   function validateRUT(rut: string, dv: string): boolean {
     // Implementar algoritmo de validación de RUT
     // ...
   }
   ```

4. **Implementa rate limiting en producción**
   - Máximo 10 requests por minuto por IP
   - Previene ataques de fuerza bruta

---

## 📝 Notas Importantes

1. **No hay persistencia:** Este endpoint NO guarda nada en base de datos
2. **Stateless:** Cada request es independiente
3. **Cookies opcionales:** Puedes omitir cookies, pero será más lento
4. **Información completa:** Retorna TODA la info disponible del contribuyente
5. **Timeout:** Máximo 30 segundos por request

---

## 🆚 Comparación con otros Endpoints

| Feature | `/login` | `/contribuyente` | **`/verify`** |
|---------|----------|------------------|--------------|
| Verifica credenciales | ✅ | ❌ | ✅ |
| Retorna cookies | ✅ | ✅ | ✅ |
| Extrae info completa | ❌ | ✅ | ✅ |
| Requiere login previo | ❌ | ✅ | ❌ |
| Tiempo (sin cookies) | 5-8s | 5-8s | 7-10s |
| Tiempo (con cookies) | 5-8s | 1-2s | 2-4s |
| **Uso recomendado** | Solo validar | Obtener info | **Todo en uno** |

---

**Última actualización:** Noviembre 2025

**Versión del documento:** 1.0.0
