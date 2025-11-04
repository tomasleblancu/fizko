# SII STC Integration (Sin Autenticación)

Integración para consultas públicas del SII sin necesidad de autenticación.

## 🎯 Características

- ✅ **Sin autenticación**: No requiere credenciales de usuario
- ✅ **Interceptación de reCAPTCHA**: Captura automática del token rresp
- ✅ **Consulta de proveedores**: Valida estado de proveedores y documentos tributarios
- ✅ **Selenium-wire**: Intercepta requests HTTP para capturar tokens
- ✅ **API REST**: Endpoint listo para usar desde frontend

## 📦 Arquitectura

```
┌─────────────────────────────────────────────────────┐
│  FastAPI Router                                      │
│  └─ POST /api/stc/consultar-documento               │
└──────────────────┬──────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────┐
│  STCClient                                           │
│  ├─ prepare() - Navega, captura cookies y token     │
│  └─ consultar_documento() - Consulta API SII        │
└──────────────────┬──────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────┐
│  Core Components                                     │
│  ├─ STCDriver (selenium-wire)                       │
│  │  └─ Intercepta requests HTTP                     │
│  └─ RecaptchaInterceptor                            │
│     └─ Extrae token rresp                           │
└─────────────────────────────────────────────────────┘
```

## 🚀 Uso Rápido

### Desde Python

```python
from app.integrations.sii_stc import STCClient

# Uso básico
with STCClient() as client:
    # Preparar (navegar, capturar cookies y token)
    client.prepare()

    # Consultar documento
    result = client.consultar_documento(
        rut="77794858",
        dv="K"
    )

    print(result)
```

### Uso con auto_prepare

```python
from app.integrations.sii_stc import STCClient

# Auto-prepare ejecuta prepare() automáticamente
with STCClient() as client:
    result = client.consultar_documento(
        rut="77794858",
        dv="K",
        auto_prepare=True  # Default
    )
```

### Modo no-headless (debugging)

```python
with STCClient(headless=False) as client:
    # Verás el navegador abrirse
    result = client.consultar_documento(
        rut="77794858",
        dv="K"
    )
```

## 🌐 API REST

### Endpoint: Consultar Documento

**POST** `/api/stc/consultar-documento`

**Body:**
```json
{
  "rut": "77794858",
  "dv": "K",
  "headless": true,
  "recaptcha_timeout": 15,
  "query_timeout": 15
}
```

**Response:**
```json
{
  "success": true,
  "message": "Consulta exitosa",
  "data": {
    // Resultado de la API del SII
  },
  "rut": "77794858",
  "dv": "K"
}
```

**Errores:**
- `408`: Timeout esperando reCAPTCHA o consulta
- `422`: Error validando reCAPTCHA
- `500`: Error en la consulta

### Ejemplo con curl

```bash
curl -X POST "http://localhost:8089/api/stc/consultar-documento" \
  -H "Content-Type: application/json" \
  -d '{
    "rut": "77794858",
    "dv": "K"
  }'
```

### Ejemplo con JavaScript/TypeScript

```typescript
const consultarDocumento = async (rut: string, dv: string) => {
  const response = await fetch('/api/stc/consultar-documento', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ rut, dv }),
  });

  if (!response.ok) {
    throw new Error(`Error: ${response.status}`);
  }

  return response.json();
};

// Uso
try {
  const result = await consultarDocumento('77794858', 'K');
  console.log('Resultado:', result);
} catch (error) {
  console.error('Error:', error);
}
```

## 🧪 Testing

### Test Rápido

```bash
cd backend

# Con parámetros por defecto
python -m app.integrations.sii_stc.tests.test_quick

# Con RUT personalizado
STC_TEST_RUT=77794858 STC_TEST_DV=K python -m app.integrations.sii_stc.tests.test_quick

# Sin headless (para debugging)
STC_HEADLESS=false python -m app.integrations.sii_stc.tests.test_quick
```

### Pytest (futuro)

```bash
pytest app/integrations/sii_stc/tests/ -v
```

## 🔧 Configuración

### Variables de entorno

No se requieren variables de entorno. La integración funciona "out of the box".

### Configuración personalizada

```python
custom_config = {
    'timeout': 30,
    'window_size': '1920,1080'
}

with STCClient(headless=True, custom_config=custom_config) as client:
    result = client.consultar_documento(rut="77794858", dv="K")
```

### Timeouts

```python
with STCClient() as client:
    # Timeout para reCAPTCHA
    client.prepare(recaptcha_timeout=20)

    # Timeout para consulta
    result = client.consultar_documento(
        rut="77794858",
        dv="K",
        timeout=15
    )
```

## 📊 Flujo Técnico

### 1. Preparación (prepare)

```
1. Iniciar Selenium-wire Chrome driver
2. Navegar a https://www2.sii.cl/stc/noauthz/consulta
3. Esperar carga de página (5s)
4. Capturar cookies del navegador
5. Interceptar request a recaptcha/enterprise/reload
6. Extraer token rresp de la respuesta
7. Almacenar cookies y token en memoria
```

### 2. Consulta (consultar_documento)

```
1. Validar que tenemos cookies y token (auto_prepare si no)
2. Preparar payload:
   {
     "rut": "77794858",
     "dv": "K",
     "reAction": "consultaSTC",
     "reToken": "<rresp_token>"
   }
3. Convertir cookies de Selenium a formato requests
4. POST a https://www2.sii.cl/app/stc/recurso/v1/consulta/getConsultaData/
5. Retornar respuesta JSON
```

## 🔍 Interceptación de reCAPTCHA

### Cómo funciona

1. **selenium-wire** actúa como proxy entre Selenium y el navegador
2. Cuando la página carga, reCAPTCHA hace un request a:
   ```
   https://www.google.com/recaptcha/enterprise/reload?k=6Lc_DPAqAAAAAB7QWxHsaPDNxLLOUj9VkiuAXRYP
   ```
3. La respuesta tiene el formato:
   ```
   )
   ]
   }'
   ["rresp","<TOKEN>",1]
   ```
4. El `RecaptchaInterceptor` parsea esta respuesta y extrae el token
5. El token se usa en el payload de la consulta

### Debugging de reCAPTCHA

```python
from app.integrations.sii_stc import STCClient

with STCClient(headless=False) as client:
    client.prepare()

    # Ver cookies capturadas
    cookies = client.get_cookies()
    print(f"Cookies: {len(cookies)}")

    # Ver token capturado
    token = client.get_recaptcha_token()
    print(f"Token: {token[:30]}...")

    # Verificar si está preparado
    print(f"Preparado: {client.is_prepared()}")
```

## 🐛 Troubleshooting

### Error: "No reCAPTCHA request found"

**Causa**: El request de reCAPTCHA no se interceptó a tiempo.

**Solución**:
1. Aumentar `recaptcha_timeout`:
   ```python
   client.prepare(recaptcha_timeout=30)
   ```
2. Ejecutar en modo no-headless para verificar que la página carga:
   ```python
   client = STCClient(headless=False)
   ```
3. Verificar conexión a internet

### Error: "selenium-wire not found"

**Causa**: selenium-wire no está instalado.

**Solución**:
```bash
cd backend
uv pip install selenium-wire
```

### Error: "ChromeDriver not found"

**Causa**: ChromeDriver no está en el PATH.

**Solución**:
- macOS: `brew install chromedriver`
- Linux: Instalar desde [chromedriver downloads](https://chromedriver.chromium.org/)

### Consulta falla con 403 o 401

**Causa**: El token reCAPTCHA expiró o las cookies no son válidas.

**Solución**:
1. Llamar `prepare()` nuevamente para obtener cookies/token frescos
2. No reutilizar el cliente por mucho tiempo (token expira)

## 📝 Estructura de Archivos

```
app/integrations/sii_stc/
├── __init__.py              # Exports públicos
├── client.py                # STCClient principal
├── config.py                # Configuración y URLs
├── exceptions.py            # Excepciones custom
├── README.md               # Esta documentación
│
├── core/                   # Componentes core
│   ├── __init__.py
│   ├── driver.py           # Selenium-wire driver
│   └── recaptcha_interceptor.py  # Interceptor de reCAPTCHA
│
└── tests/                  # Tests
    ├── __init__.py
    └── test_quick.py       # Test rápido
```

## 🆚 Diferencias con integración SII principal

| Característica | SII (Auth) | SII STC (Public) |
|----------------|------------|------------------|
| Autenticación | Requiere credenciales | Sin auth |
| Cookies | Guardadas en DB | Solo en memoria |
| Selenium | Normal | Selenium-wire |
| reCAPTCHA | No | Sí (interceptado) |
| Scope | Por empresa | Agnóstico |
| Persistencia | Sí (DB) | No |

## 🚧 Limitaciones

1. **No persistencia**: Los datos no se guardan en DB
2. **Tiempo de ejecución**: ~10-15s por consulta (navegador + reCAPTCHA)
3. **Dependencia de UI**: Si el SII cambia la página, puede romperse
4. **Rate limiting**: No implementado (usar con cuidado)
5. **Token expira**: El token reCAPTCHA expira después de unos minutos

## 🔮 Mejoras Futuras

- [ ] Cache de tokens reCAPTCHA (con expiración)
- [ ] Pool de drivers pre-inicializados
- [ ] Rate limiting configurable
- [ ] Retry automático con backoff
- [ ] Métricas de performance
- [ ] Validación de RUT antes de consultar
- [ ] Tests con mocking

## 📞 Soporte

Para problemas o preguntas:
1. Revisar esta documentación
2. Ejecutar test rápido con debugging: `STC_HEADLESS=false python -m app.integrations.sii_stc.tests.test_quick`
3. Verificar logs en consola

---

**Versión:** 1.0.0
**Fecha:** 2025-01-04
**Dependencias:** selenium-wire, selenium, requests
