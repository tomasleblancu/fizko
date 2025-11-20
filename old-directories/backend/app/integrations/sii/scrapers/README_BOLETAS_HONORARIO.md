# Boletas de Honorarios Scraper

Scraper especializado para obtener boletas de honorarios desde el portal del SII.

## Características

- ✅ Obtiene boletas de honorarios por período (mes/año)
- ✅ Extrae datos completos de cada boleta
- ✅ Calcula totales agregados automáticamente
- ✅ Maneja paginación automáticamente
- ✅ Usa el endpoint oficial de la Propuesta F29 del SII

## Uso Básico

```python
from app.integrations.sii.client import SIIClient

# Inicializar cliente SII (requiere autenticación previa)
sii_client = SIIClient()

# Autenticar con certificado digital
sii_client.autenticar_con_certificado(rut="12345678-9")

# Obtener boletas de honorarios
resultado = sii_client.obtener_boletas_honorarios(
    mes="10",
    anio="2025"
)

# Acceder a las boletas
for boleta in resultado['boletas']:
    print(f"Boleta #{boleta['numero_boleta']}")
    print(f"  Receptor: {boleta['nombre_receptor']}")
    print(f"  Monto Bruto: ${boleta['honorarios_brutos']:,}")
    print(f"  Retención: ${boleta['retencion_receptor']:,}")
    print(f"  Monto Líquido: ${boleta['honorarios_liquidos']:,}")

# Acceder a totales
print(f"\nTotales del período:")
print(f"  Total Bruto: ${resultado['totales']['honorarios_bruto']:,}")
print(f"  Total Retenciones: ${resultado['totales']['honorarios_retencion_receptor']:,}")
print(f"  Total Líquido: ${resultado['totales']['honorarios_liquido']:,}")
```

## Obtener Todas las Páginas

Si hay muchas boletas, el SII las pagina. Puedes obtener todas las páginas automáticamente:

```python
# Obtiene automáticamente todas las páginas
resultado = sii_client.obtener_boletas_honorarios_todas_paginas(
    mes="10",
    anio="2025"
)

print(f"Total de boletas: {len(resultado['boletas'])}")
```

## Estructura de Datos

### Boleta

```python
{
    'numero_boleta': 1844,                          # Número de la boleta
    'estado': 'VIG',                                # Estado: VIG (Vigente), ANU (Anulada)
    'fecha_boleta': '29-10-2025',                   # Fecha de emisión
    'fecha_emision': '29-10-2025 17:16',           # Fecha y hora de emisión
    'usuario_emision': 'RAUL MARCELO CARCEY RIVERA', # Nombre del emisor
    'sociedad_profesional': False,                  # True si es sociedad profesional
    'rut_receptor': '77794858',                     # RUT del receptor
    'nombre_receptor': 'COMERCIAL ATAL SPA',        # Nombre del receptor
    'honorarios_brutos': 116959,                    # Monto bruto
    'retencion_emisor': 0,                          # Retención del emisor
    'retencion_receptor': 16959,                    # Retención del receptor (10.75%)
    'honorarios_liquidos': 100000,                  # Monto líquido
    'manual': False                                 # True si fue ingreso manual
}
```

### Totales

```python
{
    'honorarios_bruto': 116959,                     # Suma total honorarios brutos
    'honorarios_retencion_emisor': 0,               # Suma total retención emisor
    'honorarios_retencion_receptor': 16959,         # Suma total retención receptor
    'honorarios_liquido': 100000,                   # Suma total honorarios líquidos
    'total_registros': 1,                           # Total de boletas
    'bhep': False                                   # Boleta de Honorarios Electrónica de Pago
}
```

### Paginación

```python
{
    'pagina_actual': 1,                             # Página actual
    'total_paginas': 1,                             # Total de páginas disponibles
    'tam_pagina': 10                                # Cantidad de registros por página
}
```

## Endpoint del SII

El scraper utiliza el endpoint oficial:

```
POST https://www4.sii.cl/propuestaf29ui/services/data/riacFacadeService/getBoletasHonorario
```

### Payload

```json
{
    "metaData": {
        "namespace": "cl.sii.sdi.lob.iva.propuestaf29.data.api.interfaces.RiacFacadeService/getBoletasHonorario",
        "conversationId": "XXXXXXXXXX",
        "transactionId": "uuid-v4"
    },
    "data": {
        "rutContribuyente": "77794858",
        "dv": "K",
        "mes": "10",
        "anno": "2025",
        "paginaActual": 1
    }
}
```

## Manejo de Errores

El scraper maneja automáticamente:

- ✅ Validación de parámetros (mes, año)
- ✅ Detección automática del RUT de la empresa
- ✅ Reintentos en caso de errores de red
- ✅ Manejo de respuestas con errores del SII
- ✅ Validación de formato de respuesta

```python
try:
    resultado = sii_client.obtener_boletas_honorarios(mes="10", anio="2025")
except ValueError as e:
    print(f"Parámetros inválidos: {e}")
except ScrapingException as e:
    print(f"Error obteniendo boletas: {e}")
```

## Requisitos

- ✅ Sesión autenticada en el SII (certificado digital)
- ✅ Selenium WebDriver activo
- ✅ Cookies de sesión válidas

## Integración con el Sistema

El scraper está integrado en el `SIIClient`:

```python
# En app/integrations/sii/client.py

def obtener_boletas_honorarios(self, mes: str, anio: str) -> Dict[str, Any]:
    """Obtiene boletas de honorarios para un período"""
    scraper = BoletasHonorarioScraper(self.driver)
    return scraper.obtener_boletas(mes=mes, anio=anio)

def obtener_boletas_honorarios_todas_paginas(self, mes: str, anio: str) -> Dict[str, Any]:
    """Obtiene todas las páginas de boletas"""
    scraper = BoletasHonorarioScraper(self.driver)
    return scraper.obtener_todas_las_paginas(mes=mes, anio=anio)
```

## Casos de Uso

### 1. Validar Boletas de un Mes

```python
# Obtener boletas de octubre 2025
resultado = sii_client.obtener_boletas_honorarios(mes="10", anio="2025")

# Verificar que todas las boletas estén vigentes
boletas_invalidas = [
    b for b in resultado['boletas']
    if b['estado'] != 'VIG'
]

if boletas_invalidas:
    print(f"⚠️ {len(boletas_invalidas)} boletas no vigentes")
```

### 2. Calcular Total de Impuestos Retenidos

```python
resultado = sii_client.obtener_boletas_honorarios(mes="10", anio="2025")

total_retenido = resultado['totales']['honorarios_retencion_receptor']
print(f"Total retenido en el mes: ${total_retenido:,}")
```

### 3. Exportar a CSV

```python
import csv

resultado = sii_client.obtener_boletas_honorarios_todas_paginas(
    mes="10",
    anio="2025"
)

with open('boletas_honorarios.csv', 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=resultado['boletas'][0].keys())
    writer.writeheader()
    writer.writerows(resultado['boletas'])
```

## Notas Técnicas

1. **Detección del RUT**: El scraper intenta detectar el RUT de la empresa desde:
   - HTML de la página actual
   - localStorage del navegador
   - sessionStorage del navegador

2. **IDs de Transacción**: Cada petición genera:
   - `conversationId`: String alfanumérico de 10 caracteres
   - `transactionId`: UUID v4

3. **Paginación**: El SII pagina los resultados de 10 en 10 por defecto

4. **Retenciones**: La retención del receptor es típicamente el 10.75% del monto bruto

5. **Estados de Boletas**:
   - `VIG`: Vigente
   - `ANU`: Anulada

## Testing

```python
# Test básico
def test_obtener_boletas():
    client = SIIClient()
    client.autenticar_con_certificado(rut="12345678-9")

    resultado = client.obtener_boletas_honorarios(mes="10", anio="2025")

    assert 'boletas' in resultado
    assert 'totales' in resultado
    assert 'paginacion' in resultado
    assert len(resultado['boletas']) > 0
```
