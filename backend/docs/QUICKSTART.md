# Inicio Rápido - SII Integration Service

## Instalación en 3 pasos

```bash
# 1. Navegar al directorio
cd backend-v2

# 2. Instalar dependencias
uv sync

# 3. Iniciar servidor
./start.sh
```

El servidor estará corriendo en: http://localhost:8090

## Documentación API

- **Swagger UI**: http://localhost:8090/docs
- **ReDoc**: http://localhost:8090/redoc

## Test Rápido

Prueba el endpoint de login:

```bash
curl -X POST "http://localhost:8090/api/sii/login" \
  -H "Content-Type: application/json" \
  -d '{
    "rut": "TU_RUT",
    "dv": "TU_DV",
    "password": "TU_PASSWORD"
  }'
```

## Endpoints Principales

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/sii/login` | POST | Verificar credenciales |
| `/api/sii/compras` | POST | Extraer compras (DTEs) |
| `/api/sii/ventas` | POST | Extraer ventas (DTEs) |
| `/api/sii/f29` | POST | Extraer propuesta F29 |
| `/api/sii/boletas-honorarios` | POST | Extraer boletas honorarios |
| `/api/sii/contribuyente` | POST | Info del contribuyente |

## Formato de Request

Todos los endpoints POST requieren:

```json
{
  "rut": "12345678",
  "dv": "9",
  "password": "tu_password",
  "periodo": "202501",  // Solo para endpoints que requieren periodo
  "cookies": []  // OPCIONAL: Reutilizar sesión (ver sección Cookies)
}
```

## Reutilización de Sesiones (Cookies)

Para **evitar logins lentos** en cada request:

```python
import requests

base_url = "http://localhost:8090/api/sii"
creds = {"rut": "12345678", "dv": "9", "password": "tu_pass"}

# 1. Login inicial
login = requests.post(f"{base_url}/login", json=creds).json()
cookies = login["cookies"]  # Guardar cookies

# 2. Reutilizar cookies (sin login!)
compras = requests.post(
    f"{base_url}/compras",
    json={**creds, "periodo": "202501", "cookies": cookies}
).json()

# 3. Actualizar cookies para próximo request
cookies = compras["cookies"]
```

**Beneficio**: 5-10x más rápido al evitar login repetido ⚡

## Notas Importantes

- **RUT**: Sin puntos ni guión (ej: `12345678`)
- **Periodo**: Formato `YYYYMM` (ej: `202501` para enero 2025)
- **Headless**: Por defecto, Chrome corre en modo headless (sin interfaz gráfica)
- **Timeouts**: 30 segundos por defecto

## Troubleshooting

**Error: "command not found: uv"**
```bash
# Instalar uv primero
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Error: "chromedriver not found"**
```bash
# El chromedriver se descarga automáticamente la primera vez
# Si hay problemas, asegúrate de tener Chrome instalado
```

## Documentación Completa

Ver [README.md](README.md) para documentación completa.
