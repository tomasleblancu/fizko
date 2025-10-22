# Ejemplos de Uso - RPA v3

Ejemplos prácticos de cómo usar el cliente SII v3.

## 📋 Tabla de Contenidos

1. [Inicio Rápido](#inicio-rápido)
2. [Autenticación](#autenticación)
3. [Contribuyente](#contribuyente)
4. [DTEs](#dtes)
5. [Formularios F29](#formularios-f29)
6. [Casos Avanzados](#casos-avanzados)

---

## Inicio Rápido

### Ejemplo Básico

```python
from apps.sii.rpa_v3 import SIIClient

# Usar context manager (recomendado)
with SIIClient(tax_id="12345678-9", password="mi_password") as client:

    # Obtener datos del contribuyente
    info = client.get_contribuyente()
    print(f"Empresa: {info['razon_social']}")

    # Obtener compras del mes actual
    from datetime import datetime
    periodo = datetime.now().strftime("%Y%m")
    compras = client.get_compras(periodo=periodo)
    print(f"Total compras: {len(compras['data'])}")
```

---

## Autenticación

### Ejemplo 1: Login Simple

```python
from apps.sii.rpa_v3 import SIIClient

with SIIClient(tax_id="12345678-9", password="secret") as client:
    # Login automático al usar cualquier método
    info = client.get_contribuyente()
```

### Ejemplo 2: Login Explícito

```python
with SIIClient(tax_id="12345678-9", password="secret") as client:
    # Login explícito
    success = client.login()

    if success:
        print("✅ Login exitoso")
        cookies = client.get_cookies()
        print(f"Cookies obtenidas: {len(cookies)}")
```

### Ejemplo 3: Forzar Nuevo Login

```python
with SIIClient(tax_id="12345678-9", password="secret") as client:
    # Forzar nuevo login (ignorar cookies guardadas)
    client.login(force_new=True)

    # Continuar con operaciones
    info = client.get_contribuyente()
```

### Ejemplo 4: Verificar Autenticación

```python
with SIIClient(tax_id="12345678-9", password="secret") as client:
    if client.is_authenticated():
        print("✅ Sesión activa")
    else:
        print("⚠️ No autenticado, haciendo login...")
        client.login()
```

### Ejemplo 5: Modo con Navegador Visible (Debug)

```python
# Útil para debugging
with SIIClient(tax_id="12345678-9", password="secret", headless=False) as client:
    # Verás el navegador en acción
    client.login()
```

---

## Contribuyente

### Ejemplo 6: Datos Completos del Contribuyente

```python
with SIIClient(tax_id="12345678-9", password="secret") as client:
    info = client.get_contribuyente()

    # Acceder a todos los campos
    print("=" * 60)
    print("INFORMACIÓN DEL CONTRIBUYENTE")
    print("=" * 60)
    print(f"RUT: {info.get('rut')}")
    print(f"Razón Social: {info.get('razon_social')}")
    print(f"Nombre: {info.get('nombre')}")
    print(f"Dirección: {info.get('direccion')}")
    print(f"Comuna: {info.get('comuna')}")
    print(f"Ciudad: {info.get('ciudad')}")
    print(f"Email: {info.get('email')}")
    print(f"Teléfono: {info.get('telefono')}")
    print(f"Actividad: {info.get('actividad_economica')}")
    print(f"Inicio Actividades: {info.get('fecha_inicio_actividades')}")
```

### Ejemplo 7: Guardar Datos en JSON

```python
import json

with SIIClient(tax_id="12345678-9", password="secret") as client:
    info = client.get_contribuyente()

    # Guardar en archivo JSON
    with open('contribuyente.json', 'w', encoding='utf-8') as f:
        json.dump(info, f, indent=2, ensure_ascii=False)

    print("✅ Datos guardados en contribuyente.json")
```

---

## DTEs

### Ejemplo 8: Compras del Mes Actual

```python
from datetime import datetime

with SIIClient(tax_id="12345678-9", password="secret") as client:
    # Período actual
    periodo = datetime.now().strftime("%Y%m")

    # Obtener facturas de compra
    compras = client.get_compras(periodo=periodo, tipo_doc="33")

    if compras['status'] == 'success':
        print(f"✅ Total documentos: {len(compras['data'])}")

        # Mostrar primeros 5
        for doc in compras['data'][:5]:
            print(f"  - Folio: {doc.get('folio')}, "
                  f"Monto: ${doc.get('monto_total'):,}")
    else:
        print(f"❌ Error: {compras.get('message')}")
```

### Ejemplo 9: Ventas de Varios Períodos

```python
from datetime import datetime, timedelta

with SIIClient(tax_id="12345678-9", password="secret") as client:
    # Últimos 3 meses
    resultados = []

    for i in range(3):
        fecha = datetime.now() - timedelta(days=30 * i)
        periodo = fecha.strftime("%Y%m")

        ventas = client.get_ventas(periodo=periodo)
        resultados.append({
            'periodo': periodo,
            'total_docs': len(ventas.get('data', [])),
            'status': ventas.get('status')
        })

    # Mostrar resumen
    print("RESUMEN VENTAS - ÚLTIMOS 3 MESES")
    for r in resultados:
        print(f"{r['periodo']}: {r['total_docs']} documentos ({r['status']})")
```

### Ejemplo 10: Diferentes Tipos de Documentos

```python
with SIIClient(tax_id="12345678-9", password="secret") as client:
    periodo = "202501"

    tipos = {
        '33': 'Facturas Electrónicas',
        '34': 'Facturas Exentas',
        '39': 'Boletas Electrónicas',
        '61': 'Notas de Crédito'
    }

    for codigo, nombre in tipos.items():
        result = client.get_compras(periodo=periodo, tipo_doc=codigo)
        total = len(result.get('data', []))
        print(f"{nombre} ({codigo}): {total} documentos")
```

### Ejemplo 11: Resumen Completo del Período

```python
with SIIClient(tax_id="12345678-9", password="secret") as client:
    periodo = "202501"

    # Obtener resumen
    resumen = client.get_resumen(periodo=periodo)

    if resumen['status'] == 'success':
        print(f"RESUMEN PERÍODO {periodo}")
        print("=" * 60)

        data = resumen.get('data', {})

        # Compras
        print("\nCOMPRAS:")
        for tipo, info in data.get('compras', {}).items():
            print(f"  Tipo {tipo}: {info['cantidad']} docs, "
                  f"Total: ${info['monto_total']:,}")

        # Ventas
        print("\nVENTAS:")
        for tipo, info in data.get('ventas', {}).items():
            print(f"  Tipo {tipo}: {info['cantidad']} docs, "
                  f"Total: ${info['monto_total']:,}")
```

### Ejemplo 12: Exportar DTEs a CSV

```python
import csv

with SIIClient(tax_id="12345678-9", password="secret") as client:
    periodo = "202501"
    compras = client.get_compras(periodo=periodo)

    if compras['status'] == 'success':
        # Guardar en CSV
        with open(f'compras_{periodo}.csv', 'w', newline='', encoding='utf-8') as f:
            if compras['data']:
                writer = csv.DictWriter(f, fieldnames=compras['data'][0].keys())
                writer.writeheader()
                writer.writerows(compras['data'])

        print(f"✅ Exportadas {len(compras['data'])} compras a CSV")
```

---

## Formularios F29

### Ejemplo 13: Lista de F29 del Año

```python
with SIIClient(tax_id="12345678-9", password="secret") as client:
    anio = "2024"

    formularios = client.get_f29_lista(anio=anio)

    print(f"FORMULARIOS F29 - AÑO {anio}")
    print("=" * 60)

    for form in formularios:
        print(f"Folio: {form.get('folio')}")
        print(f"  Período: {form.get('periodo')}")
        print(f"  Tipo: {form.get('tipo')}")
        print(f"  Estado: {form.get('estado')}")
        print(f"  Fecha: {form.get('fecha_presentacion')}")
        print()
```

### Ejemplo 14: Buscar F29 Específico

```python
with SIIClient(tax_id="12345678-9", password="secret") as client:
    # Buscar por folio
    formularios = client.get_f29_lista(anio="2024", folio="123456")

    if formularios:
        form = formularios[0]
        print(f"✅ F29 encontrado:")
        print(f"   Folio: {form.get('folio')}")
        print(f"   Período: {form.get('periodo')}")
    else:
        print("❌ F29 no encontrado")
```

### Ejemplo 15: Detalles Completos de F29

```python
with SIIClient(tax_id="12345678-9", password="secret") as client:
    folio = "123456"

    detalle = client.get_f29_detalle(folio=folio)

    if detalle['status'] == 'success':
        print(f"DETALLE F29 - FOLIO {folio}")
        print("=" * 60)
        print(f"Período: {detalle.get('periodo')}")
        print(f"Total campos: {detalle.get('total_campos')}")
        print(f"Total subtablas: {detalle.get('total_subtablas')}")
        print()

        # Mostrar primeros campos
        print("CAMPOS EXTRAÍDOS (primeros 10):")
        for campo in detalle.get('campos_extraidos', [])[:10]:
            print(f"  [{campo['codigo']}] {campo['nombre']}: {campo['valor']}")
```

### Ejemplo 16: Exportar F29 a JSON

```python
import json

with SIIClient(tax_id="12345678-9", password="secret") as client:
    folio = "123456"
    detalle = client.get_f29_detalle(folio=folio)

    # Guardar en JSON
    filename = f'f29_{folio}.json'
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(detalle, f, indent=2, ensure_ascii=False)

    print(f"✅ F29 {folio} guardado en {filename}")
```

---

## Casos Avanzados

### Ejemplo 17: Manejo de Errores

```python
from apps.sii.rpa_v3 import SIIClient, AuthenticationError, ExtractionError

try:
    with SIIClient(tax_id="12345678-9", password="secret") as client:
        # Intentar operaciones
        info = client.get_contribuyente()
        compras = client.get_compras(periodo="202501")

except AuthenticationError as e:
    print(f"❌ Error de autenticación: {e}")
    print("   Verifica tus credenciales")

except ExtractionError as e:
    print(f"❌ Error extrayendo datos: {e}")
    print(f"   Recurso: {e.resource}")

except Exception as e:
    print(f"❌ Error general: {e}")
    import traceback
    traceback.print_exc()
```

### Ejemplo 18: Logging Detallado

```python
import logging

# Configurar logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Ahora verás logs detallados
with SIIClient(tax_id="12345678-9", password="secret") as client:
    info = client.get_contribuyente()
```

### Ejemplo 19: Procesamiento Batch

```python
def procesar_contribuyente(tax_id, password):
    """Procesa todos los datos de un contribuyente"""

    with SIIClient(tax_id=tax_id, password=password) as client:
        resultados = {}

        # 1. Contribuyente
        print(f"📊 Procesando {tax_id}...")
        resultados['contribuyente'] = client.get_contribuyente()

        # 2. DTEs del mes
        from datetime import datetime
        periodo = datetime.now().strftime("%Y%m")

        resultados['compras'] = client.get_compras(periodo=periodo)
        resultados['ventas'] = client.get_ventas(periodo=periodo)

        # 3. F29 del año
        anio = str(datetime.now().year)
        resultados['f29'] = client.get_f29_lista(anio=anio)

        return resultados

# Procesar múltiples contribuyentes
contribuyentes = [
    ("12345678-9", "password1"),
    ("98765432-1", "password2"),
]

for tax_id, password in contribuyentes:
    try:
        datos = procesar_contribuyente(tax_id, password)
        print(f"✅ {tax_id} procesado exitosamente")
    except Exception as e:
        print(f"❌ {tax_id} falló: {e}")
```

### Ejemplo 20: Comparación Mensual

```python
from datetime import datetime, timedelta

def comparar_meses(tax_id, password, meses=3):
    """Compara DTEs de los últimos N meses"""

    with SIIClient(tax_id=tax_id, password=password) as client:
        comparacion = []

        for i in range(meses):
            fecha = datetime.now() - timedelta(days=30 * i)
            periodo = fecha.strftime("%Y%m")

            compras = client.get_compras(periodo=periodo)
            ventas = client.get_ventas(periodo=periodo)

            comparacion.append({
                'periodo': periodo,
                'compras': len(compras.get('data', [])),
                'ventas': len(ventas.get('data', []))
            })

        # Mostrar comparación
        print("COMPARACIÓN MENSUAL")
        print("=" * 50)
        print(f"{'Período':<10} {'Compras':<10} {'Ventas':<10}")
        print("-" * 50)

        for mes in comparacion:
            print(f"{mes['periodo']:<10} {mes['compras']:<10} {mes['ventas']:<10}")

        return comparacion

# Ejecutar
comparar_meses("12345678-9", "secret", meses=6)
```

---

## 💡 Tips

1. **Usa context manager**: Asegura cierre automático de recursos
2. **Verifica `status`**: Siempre revisa el status en resultados de DTEs
3. **Maneja excepciones**: Captura errores específicos para mejor debugging
4. **Logging**: Habilita logs para entender el flujo
5. **Headless=False**: Usa para debugging visual

---

**Más ejemplos en:** [README.md](README.md)
