# API Documentation - SII Integration Service

Documentación completa de la API REST para integración con el Servicio de Impuestos Internos (SII) de Chile.

## 📋 Tabla de Contenidos

- [Información General](#información-general)
- [Autenticación y Cookies](#autenticación-y-cookies)
- [Endpoints](#endpoints)
  - [Health Check](#health-check)
  - [Login](#login)
  - [Compras (Purchases)](#compras-purchases)
  - [Ventas (Sales)](#ventas-sales)
  - [Formulario 29 (F29)](#formulario-29-f29)
  - [Boletas de Honorarios](#boletas-de-honorarios)
  - [Información del Contribuyente](#información-del-contribuyente)
- [Ejemplos de Uso](#ejemplos-de-uso)
- [Manejo de Errores](#manejo-de-errores)
- [Optimización con Cookies](#optimización-con-cookies)

---

## Información General

**Base URL:** `http://localhost:8090/api/sii`

**Versión:** 2.0.0

**Content-Type:** `application/json`

**Sin Autenticación:** Este servicio NO requiere tokens de autenticación. Solo necesitas las credenciales del SII.

---

## Autenticación y Cookies

### 🔑 Credenciales Requeridas

Para todos los endpoints (excepto `/health`), necesitas:

| Campo | Tipo | Descripción | Ejemplo |
|-------|------|-------------|---------|
| `rut` | string | RUT sin puntos ni guión | `"77794858"` |
| `dv` | string | Dígito verificador | `"K"` |
| `password` | string | Contraseña del SII | `"MiPassword123"` |

### 🍪 Sistema de Cookies (Opcional pero Recomendado)

**Ventaja:** Reutilizar sesiones evita logins repetidos, mejorando la velocidad **5-10x**.

**Cómo funciona:**
1. El primer request (login o cualquier endpoint) retorna cookies
2. Guardas las cookies
3. Envías las cookies en requests subsecuentes
4. El sistema reutiliza la sesión sin hacer login nuevamente

**Formato de cookies:**
```json
{
  "cookies": [
    {
      "domain": ".sii.cl",
      "name": "CSESSIONID",
      "value": "E55R4XVF30UG9",
      "path": "/",
      "secure": true,
      "httpOnly": false,
      "sameSite": "Strict"
    }
    // ... más cookies
  ]
}
```

---

## Endpoints

### Health Check

**Endpoint:** `GET /api/sii/health`

**Descripción:** Verifica que el servicio esté funcionando.

**Sin parámetros requeridos**

#### Ejemplo de Request

```bash
curl http://localhost:8090/api/sii/health
```

#### Ejemplo de Response (200 OK)

```json
{
  "status": "healthy",
  "service": "SII Integration Service",
  "version": "2.0.0",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

### Login

**Endpoint:** `POST /api/sii/login`

**Descripción:** Prueba las credenciales del SII sin extraer datos. Útil para validar credenciales y obtener cookies para reutilización.

#### Request Body

```json
{
  "rut": "77794858",
  "dv": "K",
  "password": "SiiPfufl574@#",
  "cookies": []  // Opcional: cookies de sesión anterior
}
```

#### Ejemplo de Request

```bash
curl -X POST http://localhost:8090/api/sii/login \
  -H "Content-Type: application/json" \
  -d '{
    "rut": "77794858",
    "dv": "K",
    "password": "SiiPfufl574@#"
  }'
```

#### Ejemplo de Response (200 OK)

```json
{
  "success": true,
  "message": "Login exitoso",
  "session_active": true,
  "cookies": [
    {
      "domain": ".sii.cl",
      "name": "TOKEN",
      "value": "E55R4XVF30UG9",
      "path": "/",
      "secure": true,
      "httpOnly": false,
      "sameSite": "Strict"
    }
    // ... 12-16 cookies en total
  ]
}
```

#### Errores Comunes

**401 Unauthorized** - Credenciales inválidas
```json
{
  "detail": "Error de autenticación: Credenciales inválidas"
}
```

**500 Internal Server Error** - Error inesperado
```json
{
  "detail": "Error inesperado: [mensaje de error]"
}
```

---

### Compras (Purchases)

**Endpoint:** `POST /api/sii/compras`

**Descripción:** Extrae los documentos de compras (DTEs recibidos) para un periodo tributario específico.

#### Request Body

```json
{
  "rut": "77794858",
  "dv": "K",
  "password": "SiiPfufl574@#",
  "periodo": "202411",  // Formato: YYYYMM
  "cookies": []  // Opcional: reutilizar sesión
}
```

#### Parámetros

| Campo | Tipo | Requerido | Descripción | Ejemplo |
|-------|------|-----------|-------------|---------|
| `rut` | string | ✅ | RUT sin puntos ni guión | `"77794858"` |
| `dv` | string | ✅ | Dígito verificador | `"K"` |
| `password` | string | ✅ | Contraseña del SII | `"password123"` |
| `periodo` | string | ✅ | Periodo tributario YYYYMM | `"202411"` |
| `cookies` | array | ❌ | Cookies de sesión previa | `[{...}]` |

#### Ejemplo de Request

**Sin cookies (primera vez):**
```bash
curl -X POST http://localhost:8090/api/sii/compras \
  -H "Content-Type: application/json" \
  -d '{
    "rut": "77794858",
    "dv": "K",
    "password": "SiiPfufl574@#",
    "periodo": "202411"
  }'
```

**Con cookies (reutilización de sesión):**
```bash
curl -X POST http://localhost:8090/api/sii/compras \
  -H "Content-Type: application/json" \
  -d '{
    "rut": "77794858",
    "dv": "K",
    "password": "SiiPfufl574@#",
    "periodo": "202411",
    "cookies": [
      {
        "domain": ".sii.cl",
        "name": "TOKEN",
        "value": "E55R4XVF30UG9",
        "path": "/",
        "secure": true
      }
    ]
  }'
```

#### Ejemplo de Response (200 OK)

```json
{
  "success": true,
  "periodo": "202411",
  "tipo": "compras",
  "total_documentos": 11,
  "documentos": {
    "status": "success",
    "data": [
      {
        "detRutDoc": 77398220,
        "detDvDoc": "1",
        "detRznSoc": "MercadoLibre Chile Ltda.",
        "detNroDoc": 6454081,
        "detFchDoc": "29/11/2024",
        "detMntNeto": 4526490,
        "detMntIVA": 860033,
        "detMntTotal": 5386523,
        "detTipoDoc": 33,
        "detFecRecepcion": "30/11/2024 11:09:31"
        // ... más campos del documento
      }
      // ... más documentos
    ],
    "extraction_method": "api_direct",
    "periodo_tributario": "202411",
    "estado_contab": "REGISTRO",
    "timestamp": "2025-11-19T01:01:10.799885"
  },
  "cookies": [
    // Cookies actualizadas para próximos requests
  ]
}
```

#### Campos de Documento de Compra

| Campo | Descripción |
|-------|-------------|
| `detRutDoc` | RUT del emisor (proveedor) |
| `detDvDoc` | DV del emisor |
| `detRznSoc` | Razón social del emisor |
| `detNroDoc` | Número del documento (folio) |
| `detFchDoc` | Fecha de emisión del documento |
| `detFecRecepcion` | Fecha de recepción en SII |
| `detTipoDoc` | Tipo de documento (33=Factura, 34=Factura Exenta, etc.) |
| `detMntNeto` | Monto neto (sin IVA) |
| `detMntIVA` | Monto del IVA |
| `detMntTotal` | Monto total del documento |
| `detMntExe` | Monto exento |
| `detEventoReceptor` | Estado del documento (P=Pagado, A=Aceptado) |

#### Errores Comunes

**401 Unauthorized** - Error de autenticación
```json
{
  "detail": "Error de autenticación: Credenciales inválidas"
}
```

**422 Unprocessable Entity** - Error al extraer datos
```json
{
  "detail": "Error al extraer datos: Periodo no encontrado"
}
```

---

### Ventas (Sales)

**Endpoint:** `POST /api/sii/ventas`

**Descripción:** Extrae los documentos de ventas (DTEs emitidos) para un periodo tributario específico.

#### Request Body

```json
{
  "rut": "77794858",
  "dv": "K",
  "password": "SiiPfufl574@#",
  "periodo": "202411",
  "cookies": []  // Opcional
}
```

#### Parámetros

Mismos parámetros que el endpoint de [Compras](#compras-purchases).

#### Ejemplo de Request

```bash
curl -X POST http://localhost:8090/api/sii/ventas \
  -H "Content-Type: application/json" \
  -d '{
    "rut": "77794858",
    "dv": "K",
    "password": "SiiPfufl574@#",
    "periodo": "202411",
    "cookies": []
  }'
```

#### Ejemplo de Response (200 OK)

```json
{
  "success": true,
  "periodo": "202411",
  "tipo": "ventas",
  "total_documentos": 5,
  "documentos": {
    "status": "success",
    "data": [
      {
        "detRutDoc": 76063352,
        "detDvDoc": "6",
        "detRznSoc": "MAS RELAX S.A.",
        "detNroDoc": 118,
        "detFchDoc": "21/11/2024",
        "detMntNeto": 1640800,
        "detMntIVA": 311752,
        "detMntTotal": 1952552,
        "detTipoDoc": 33,
        "detFecRecepcion": "21/11/2024 23:10:27"
        // ... más campos
      }
      // ... más documentos
    ],
    "extraction_method": "api_direct",
    "periodo_tributario": "202411",
    "timestamp": "2025-11-19T01:01:14.904995"
  },
  "cookies": [
    // Cookies actualizadas
  ]
}
```

#### Campos de Documento de Venta

Similares a compras, con algunas diferencias:

| Campo | Descripción |
|-------|-------------|
| `detRutDoc` | RUT del receptor (cliente) |
| `detDvDoc` | DV del receptor |
| `detRznSoc` | Razón social del receptor |
| `detNroDoc` | Número del documento (folio) |
| `detFchDoc` | Fecha de emisión |
| `detMntNeto` | Monto neto |
| `detMntIVA` | Monto IVA |
| `detMntTotal` | Monto total |
| `detTipoDoc` | Tipo de documento |

---

### Formulario 29 (F29)

**Endpoint:** `POST /api/sii/f29`

**Descripción:** Obtiene la propuesta del Formulario 29 (declaración mensual de IVA) para un periodo específico.

#### Request Body

```json
{
  "rut": "77794858",
  "dv": "K",
  "password": "SiiPfufl574@#",
  "periodo": "202411",
  "cookies": []  // Opcional
}
```

#### Ejemplo de Request

```bash
curl -X POST http://localhost:8090/api/sii/f29 \
  -H "Content-Type: application/json" \
  -d '{
    "rut": "77794858",
    "dv": "K",
    "password": "SiiPfufl574@#",
    "periodo": "202411"
  }'
```

#### Ejemplo de Response (200 OK)

```json
{
  "success": true,
  "periodo": "202411",
  "tipo": "f29_propuesta",
  "data": {
    "periodo": "202411",
    "total_ventas": 1952552,
    "total_compras": 7400000,
    "debito_fiscal": 311752,
    "credito_fiscal": 1406000,
    "iva_por_pagar": 0,
    "remanente": 1094248,
    "codigos": {
      "115": 1640800,    // Ventas netas
      "116": 0,          // Exportaciones
      "152": 311752,     // Débito fiscal
      "504": 4797963,    // Compras netas con derecho a crédito
      "506": 911613,     // Crédito fiscal
      // ... más códigos del F29
    },
    "detalles": {
      "ventas": {
        "neto": 1640800,
        "exento": 0,
        "iva": 311752,
        "total": 1952552
      },
      "compras": {
        "neto": 4797963,
        "iva": 911613,
        "total": 5709576
      }
    }
  },
  "cookies": [
    // Cookies actualizadas
  ]
}
```

#### Códigos Importantes del F29

| Código | Descripción |
|--------|-------------|
| 115 | Ventas y servicios netos |
| 116 | Exportaciones |
| 152 | Débito fiscal (IVA de ventas) |
| 504 | Compras netas con derecho a crédito |
| 506 | Crédito fiscal (IVA de compras) |
| 65 | IVA a pagar |
| 89 | Remanente crédito fiscal mes siguiente |

---

### Boletas de Honorarios

**Endpoint:** `POST /api/sii/boletas-honorarios`

**Descripción:** Obtiene las boletas de honorarios emitidas en un periodo.

#### Request Body

```json
{
  "rut": "77794858",
  "dv": "K",
  "password": "SiiPfufl574@#",
  "periodo": "202411",
  "cookies": []  // Opcional
}
```

#### Ejemplo de Request

```bash
curl -X POST http://localhost:8090/api/sii/boletas-honorarios \
  -H "Content-Type: application/json" \
  -d '{
    "rut": "77794858",
    "dv": "K",
    "password": "SiiPfufl574@#",
    "periodo": "202411"
  }'
```

#### Ejemplo de Response (200 OK)

```json
{
  "success": true,
  "periodo": "202411",
  "tipo": "boletas_honorarios",
  "total_boletas": 3,
  "data": [
    {
      "numero_boleta": 1,
      "fecha_emision": "15/11/2024",
      "rut_receptor": "12345678-9",
      "razon_social_receptor": "Empresa Cliente SpA",
      "monto_bruto": 1000000,
      "retencion": 115000,
      "monto_liquido": 885000,
      "descripcion": "Servicios profesionales noviembre 2024"
    }
    // ... más boletas
  ],
  "cookies": [
    // Cookies actualizadas
  ]
}
```

#### Campos de Boleta de Honorarios

| Campo | Descripción |
|-------|-------------|
| `numero_boleta` | Número correlativo de la boleta |
| `fecha_emision` | Fecha de emisión |
| `rut_receptor` | RUT del cliente |
| `razon_social_receptor` | Nombre/razón social del cliente |
| `monto_bruto` | Monto bruto (honorario antes de retención) |
| `retencion` | Retención de impuesto (11.5%) |
| `monto_liquido` | Monto líquido a pagar |
| `descripcion` | Descripción del servicio |

---

### Información del Contribuyente

**Endpoint:** `POST /api/sii/contribuyente`

**Descripción:** Obtiene la información del contribuyente desde el SII.

#### Request Body

```json
{
  "rut": "77794858",
  "dv": "K",
  "password": "SiiPfufl574@#",
  "cookies": []  // Opcional
}
```

**Nota:** No requiere `periodo` ya que obtiene información general del contribuyente.

#### Ejemplo de Request

```bash
curl -X POST http://localhost:8090/api/sii/contribuyente \
  -H "Content-Type: application/json" \
  -d '{
    "rut": "77794858",
    "dv": "K",
    "password": "SiiPfufl574@#"
  }'
```

#### Ejemplo de Response (200 OK)

```json
{
  "success": true,
  "tipo": "contribuyente",
  "data": {
    "rut": "77794858-K",
    "razon_social": "MI EMPRESA SPA",
    "nombre_fantasia": "Mi Empresa",
    "actividades_economicas": [
      {
        "codigo": 620200,
        "glosa": "Actividades de consultores en informática",
        "categoria": "PRIMERA"
      }
    ],
    "direccion": {
      "calle": "AV. LIBERTADOR BERNARDO O'HIGGINS",
      "numero": "1234",
      "comuna": "SANTIAGO",
      "ciudad": "SANTIAGO"
    },
    "email": "contacto@miempresa.cl",
    "telefono": "+56912345678",
    "regimen_tributario": "Renta Efectiva con Contabilidad Completa",
    "inicio_actividades": "01/01/2020",
    "estado": "ACTIVO"
  },
  "cookies": [
    // Cookies actualizadas
  ]
}
```

#### Campos de Información del Contribuyente

| Campo | Descripción |
|-------|-------------|
| `rut` | RUT completo con DV |
| `razon_social` | Razón social oficial |
| `nombre_fantasia` | Nombre comercial (si aplica) |
| `actividades_economicas` | Lista de actividades registradas en SII |
| `direccion` | Domicilio comercial |
| `email` | Email registrado en SII |
| `telefono` | Teléfono de contacto |
| `regimen_tributario` | Régimen tributario aplicable |
| `inicio_actividades` | Fecha de inicio de actividades |
| `estado` | Estado actual (ACTIVO, SUSPENDIDO, etc.) |

---

## Ejemplos de Uso

### Ejemplo 1: Login Simple

```python
import requests

url = "http://localhost:8090/api/sii/login"
data = {
    "rut": "77794858",
    "dv": "K",
    "password": "SiiPfufl574@#"
}

response = requests.post(url, json=data)
result = response.json()

if result["success"]:
    print(f"✅ Login exitoso")
    print(f"Cookies recibidas: {len(result['cookies'])}")
    # Guardar cookies para reutilizar
    cookies = result["cookies"]
else:
    print(f"❌ Login fallido: {result.get('message')}")
```

### Ejemplo 2: Flujo Completo con Reutilización de Cookies

```python
import requests

class SIIServiceClient:
    def __init__(self, rut: str, dv: str, password: str):
        self.base_url = "http://localhost:8090/api/sii"
        self.rut = rut
        self.dv = dv
        self.password = password
        self.cookies = None

    def _make_request(self, endpoint: str, **extra_data):
        """Hacer request reutilizando cookies."""
        data = {
            "rut": self.rut,
            "dv": self.dv,
            "password": self.password,
            **extra_data
        }

        # Agregar cookies si existen
        if self.cookies:
            data["cookies"] = self.cookies

        response = requests.post(f"{self.base_url}/{endpoint}", json=data)
        result = response.json()

        # Actualizar cookies para próximos requests
        if "cookies" in result:
            self.cookies = result["cookies"]

        return result

    def login(self):
        """Login inicial."""
        return self._make_request("login")

    def get_compras(self, periodo: str):
        """Obtener compras de un periodo."""
        return self._make_request("compras", periodo=periodo)

    def get_ventas(self, periodo: str):
        """Obtener ventas de un periodo."""
        return self._make_request("ventas", periodo=periodo)

    def get_f29(self, periodo: str):
        """Obtener F29 de un periodo."""
        return self._make_request("f29", periodo=periodo)

    def get_boletas_honorarios(self, periodo: str):
        """Obtener boletas de honorarios."""
        return self._make_request("boletas-honorarios", periodo=periodo)

    def get_contribuyente_info(self):
        """Obtener información del contribuyente."""
        return self._make_request("contribuyente")


# Uso
client = SIIServiceClient(
    rut="77794858",
    dv="K",
    password="SiiPfufl574@#"
)

# 1. Login (opcional, pero recomendado para obtener cookies)
print("1. Login...")
login_result = client.login()
print(f"   ✅ {len(client.cookies)} cookies guardadas\n")

# 2. Obtener compras (reutiliza cookies)
print("2. Obteniendo compras...")
compras = client.get_compras(periodo="202411")
compras_data = compras["documentos"]["data"]
print(f"   ✅ {len(compras_data)} compras obtenidas\n")

# 3. Obtener ventas (reutiliza cookies actualizadas)
print("3. Obteniendo ventas...")
ventas = client.get_ventas(periodo="202411")
ventas_data = ventas["documentos"]["data"]
print(f"   ✅ {len(ventas_data)} ventas obtenidas\n")

# 4. Obtener F29 (reutiliza cookies)
print("4. Obteniendo F29...")
f29 = client.get_f29(periodo="202411")
print(f"   ✅ F29 obtenido: IVA a pagar = ${f29['data'].get('iva_por_pagar', 0):,}\n")

# 5. Info del contribuyente
print("5. Obteniendo info del contribuyente...")
info = client.get_contribuyente_info()
print(f"   ✅ Razón social: {info['data']['razon_social']}")
```

### Ejemplo 3: JavaScript/TypeScript (Frontend)

```typescript
class SIIClient {
  private baseUrl = 'http://localhost:8090/api/sii';
  private cookies: any[] | null = null;

  constructor(
    private rut: string,
    private dv: string,
    private password: string
  ) {}

  private async makeRequest(endpoint: string, extraData: any = {}) {
    const data = {
      rut: this.rut,
      dv: this.dv,
      password: this.password,
      ...extraData,
    };

    // Agregar cookies si existen
    if (this.cookies) {
      data.cookies = this.cookies;
    }

    const response = await fetch(`${this.baseUrl}/${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });

    const result = await response.json();

    // Actualizar cookies
    if (result.cookies) {
      this.cookies = result.cookies;
    }

    return result;
  }

  async login() {
    return this.makeRequest('login');
  }

  async getCompras(periodo: string) {
    return this.makeRequest('compras', { periodo });
  }

  async getVentas(periodo: string) {
    return this.makeRequest('ventas', { periodo });
  }

  async getF29(periodo: string) {
    return this.makeRequest('f29', { periodo });
  }

  async getBoletasHonorarios(periodo: string) {
    return this.makeRequest('boletas-honorarios', { periodo });
  }

  async getContribuyenteInfo() {
    return this.makeRequest('contribuyente');
  }
}

// Uso
const client = new SIIClient('77794858', 'K', 'SiiPfufl574@#');

// Obtener compras
const compras = await client.getCompras('202411');
console.log(`Compras: ${compras.documentos.data.length}`);

// Obtener ventas (reutiliza cookies automáticamente)
const ventas = await client.getVentas('202411');
console.log(`Ventas: ${ventas.documentos.data.length}`);
```

### Ejemplo 4: React Hook

```typescript
import { useState } from 'react';

interface UseTaxSummaryParams {
  rut: string;
  dv: string;
  password: string;
  periodo: string;
}

export function useTaxSummary({ rut, dv, password, periodo }: UseTaxSummaryParams) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<any>(null);
  const [cookies, setCookies] = useState<any[] | null>(null);

  const fetchTaxData = async () => {
    setLoading(true);
    setError(null);

    try {
      const baseUrl = 'http://localhost:8090/api/sii';
      const baseData = { rut, dv, password, cookies };

      // 1. Obtener compras
      const comprasRes = await fetch(`${baseUrl}/compras`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...baseData, periodo }),
      });
      const compras = await comprasRes.json();

      // Actualizar cookies
      if (compras.cookies) setCookies(compras.cookies);

      // 2. Obtener ventas (con cookies actualizadas)
      const ventasRes = await fetch(`${baseUrl}/ventas`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...baseData, periodo, cookies: compras.cookies }),
      });
      const ventas = await ventasRes.json();

      if (ventas.cookies) setCookies(ventas.cookies);

      // 3. Obtener F29
      const f29Res = await fetch(`${baseUrl}/f29`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...baseData, periodo, cookies: ventas.cookies }),
      });
      const f29 = await f29Res.json();

      setData({
        compras: compras.documentos.data,
        ventas: ventas.documentos.data,
        f29: f29.data,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error desconocido');
    } finally {
      setLoading(false);
    }
  };

  return { data, loading, error, fetchTaxData };
}
```

---

## Manejo de Errores

### Códigos de Estado HTTP

| Código | Descripción | Causa Común |
|--------|-------------|-------------|
| 200 | OK | Request exitoso |
| 401 | Unauthorized | Credenciales inválidas |
| 422 | Unprocessable Entity | Error en extracción de datos (periodo inválido, etc.) |
| 500 | Internal Server Error | Error inesperado del servidor |

### Errores Comunes y Soluciones

#### Error 401: Credenciales Inválidas

```json
{
  "detail": "Error de autenticación: Credenciales inválidas"
}
```

**Soluciones:**
- Verificar RUT (sin puntos ni guión)
- Verificar dígito verificador
- Verificar contraseña del SII
- Probar login manual en misiir.sii.cl

#### Error 422: Periodo No Encontrado

```json
{
  "detail": "Error al extraer datos: Periodo no encontrado"
}
```

**Soluciones:**
- Verificar formato del periodo (debe ser YYYYMM)
- Verificar que existan documentos en ese periodo
- Usar periodos recientes (últimos 12 meses)

#### Error 500: Timeout del Driver

```json
{
  "detail": "Error inesperado: Timeout al cargar página"
}
```

**Soluciones:**
- Reintentar el request
- Verificar conexión a internet
- El SII puede estar lento, esperar unos minutos

#### Cookies Expiradas

Si las cookies expiran, el servicio automáticamente hace login nuevamente. Sin embargo, si experimentas errores:

**Solución:** Obtener cookies frescas haciendo login nuevamente:
```python
# Resetear cookies y hacer login nuevo
client.cookies = None
client.login()
```

---

## Optimización con Cookies

### ⚡ Mejores Prácticas

#### 1. Login Inicial + Reutilización

```python
# ✅ RECOMENDADO
client = SIIServiceClient(rut, dv, password)
client.login()  # Login inicial

# Todos estos reutilizan la misma sesión (RÁPIDO)
compras = client.get_compras("202411")
ventas = client.get_ventas("202411")
f29 = client.get_f29("202411")
```

#### 2. Guardar Cookies en Storage

```typescript
// Guardar cookies en localStorage
const saveCookies = (cookies: any[]) => {
  localStorage.setItem('sii_cookies', JSON.stringify(cookies));
  localStorage.setItem('sii_cookies_timestamp', Date.now().toString());
};

// Cargar cookies si son recientes (menos de 2 horas)
const loadCookies = (): any[] | null => {
  const cookies = localStorage.getItem('sii_cookies');
  const timestamp = localStorage.getItem('sii_cookies_timestamp');

  if (!cookies || !timestamp) return null;

  const age = Date.now() - parseInt(timestamp);
  const TWO_HOURS = 2 * 60 * 60 * 1000;

  if (age > TWO_HOURS) {
    // Cookies muy viejas, eliminar
    localStorage.removeItem('sii_cookies');
    localStorage.removeItem('sii_cookies_timestamp');
    return null;
  }

  return JSON.parse(cookies);
};
```

#### 3. Actualizar Cookies Progresivamente

```python
# Las cookies se actualizan en cada request
# Siempre usa las cookies más recientes

cookies = login()["cookies"]           # Cookies v1
cookies = get_compras(cookies)["cookies"]  # Cookies v2 (actualizadas)
cookies = get_ventas(cookies)["cookies"]   # Cookies v3 (actualizadas)
```

### 📊 Comparación de Rendimiento

| Escenario | Sin Cookies | Con Cookies | Mejora |
|-----------|-------------|-------------|--------|
| Login | ~5-8 seg | ~5-8 seg | - |
| Compras | ~8-12 seg | ~2-3 seg | **4x más rápido** |
| Ventas | ~8-12 seg | ~2-3 seg | **4x más rápido** |
| F29 | ~10-15 seg | ~3-5 seg | **3x más rápido** |
| **Total 4 requests** | **~35-45 seg** | **~12-19 seg** | **~3x más rápido** |

### 🎯 Tips de Optimización

1. **Siempre reutiliza cookies** entre requests del mismo flujo
2. **Actualiza cookies** después de cada request
3. **No guardes cookies por más de 2-3 horas** (pueden expirar)
4. **Maneja errores de sesión** haciendo login nuevamente si es necesario
5. **Usa requests en paralelo** solo si son para periodos diferentes (no comparten sesión)

---

## Consideraciones Técnicas

### Tiempos de Respuesta

| Endpoint | Sin Cookies | Con Cookies |
|----------|-------------|-------------|
| `/login` | 5-8 seg | 5-8 seg |
| `/compras` | 8-12 seg | 2-3 seg |
| `/ventas` | 8-12 seg | 2-3 seg |
| `/f29` | 10-15 seg | 3-5 seg |
| `/boletas-honorarios` | 8-12 seg | 2-3 seg |
| `/contribuyente` | 5-8 seg | 1-2 seg |

**Nota:** Los tiempos dependen de la velocidad del SII y la cantidad de datos.

### Limitaciones

- **Sin autenticación JWT:** No hay sistema de usuarios/tokens
- **Sin base de datos:** No se persisten datos (servicio stateless)
- **Scraping en tiempo real:** Cada request accede al SII en vivo
- **Cookies expiran:** Las sesiones del SII expiran después de ~2-3 horas
- **Sin rate limiting:** Evita hacer requests muy frecuentes al SII

### Seguridad

- **HTTPS en producción:** Usa HTTPS para proteger credenciales
- **No almacenar passwords:** Solo guarda cookies, nunca passwords
- **Validar RUT:** Valida formato antes de enviar
- **Timeout de 30 segundos:** Los requests no esperan indefinidamente

---

## Soporte y Troubleshooting

### Logs del Servidor

El servidor registra información útil:

```bash
# Ver logs en tiempo real
tail -f logs/sii_service.log
```

### Depuración

Para debugging, ejecuta el servidor con logs detallados:

```bash
# Backend con logs detallados
uvicorn app.main:app --reload --port 8090 --log-level debug
```

### Reporte de Problemas

Si encuentras problemas:

1. **Verifica credenciales** en misiir.sii.cl manualmente
2. **Revisa logs** del servidor
3. **Prueba con curl** para aislar el problema
4. **Verifica periodo** (formato YYYYMM)
5. **Reinicia el servicio** si es necesario

---

## Changelog

### v2.0.0 (Actual)
- ✅ Servicio stateless sin base de datos
- ✅ Sistema de reutilización de cookies
- ✅ Todos los endpoints funcionando
- ✅ Documentación completa

---

**Última actualización:** Noviembre 2025

**Versión del documento:** 1.0.0
