# RPA v3 - Inicio Rápido

Guía de 5 minutos para empezar a usar RPA v3.

---

## 🚀 En 30 Segundos

```python
from apps.sii.rpa_v3 import SIIClient

with SIIClient(tax_id="12345678-9", password="tu_password") as client:
    # Obtener datos
    info = client.get_contribuyente()
    compras = client.get_compras(periodo="202501")

    print(f"Empresa: {info['razon_social']}")
    print(f"Compras: {len(compras['data'])} documentos")
```

**Eso es todo.** Una clase, un context manager, todo funciona.

---

## 📋 Requisitos Previos

1. **Credenciales SII válidas**
   - RUT del contribuyente
   - Contraseña del portal SII

2. **Django configurado**
   - Modelo `SIISession` migrado
   - Settings configurados

3. **Chrome/Chromedriver instalado**
   - Chrome o Chromium
   - Chromedriver compatible

---

## 🎯 Las 4 Operaciones Principales

### 1. Contribuyente

```python
with SIIClient(tax_id="12345678-9", password="secret") as client:
    info = client.get_contribuyente()

    print(info['razon_social'])  # Nombre empresa
    print(info['email'])         # Email
    print(info['direccion'])     # Dirección
```

### 2. DTEs de Compra

```python
with SIIClient(tax_id="12345678-9", password="secret") as client:
    compras = client.get_compras(periodo="202501", tipo_doc="33")

    for doc in compras['data']:
        print(f"Folio {doc['folio']}: ${doc['monto_total']}")
```

### 3. DTEs de Venta

```python
with SIIClient(tax_id="12345678-9", password="secret") as client:
    ventas = client.get_ventas(periodo="202501")

    print(f"Total ventas: {len(ventas['data'])}")
```

### 4. Formularios F29

```python
with SIIClient(tax_id="12345678-9", password="secret") as client:
    # Lista de F29
    formularios = client.get_f29_lista(anio="2024")

    # Detalle específico
    detalle = client.get_f29_detalle(folio="123456")
```

---

## 🧪 Probar Instalación

### Opción 1: Quick Test

```bash
# Configurar credenciales
export SII_TEST_RUT="12345678-9"
export SII_TEST_PASSWORD="tu_password"

# Ejecutar test rápido
cd fizko_django/apps/sii/rpa_v3/tests
python quick_test.py
```

**Salida esperada:**
```
==================== RPA v3 - QUICK TEST ====================
RUT: 12345678-9
Headless: True
=============================================================

🔐 TEST 1: Login
   ✅ Login: True

🍪 TEST 2: Cookies
   ✅ Total cookies: 15

📊 TEST 3: Contribuyente
   ✅ RUT: 12345678-9
   ✅ Razón Social: MI EMPRESA LTDA
   ✅ Email: contacto@empresa.cl

📥 TEST 4: Compras DTEs
   ✅ Status: success
   ✅ Total docs: 25
   ✅ Method: api_valid_cookies

📤 TEST 5: Ventas DTEs
   ✅ Status: success
   ✅ Total docs: 50
   ✅ Method: api_valid_cookies

📋 TEST 6: F29 Lista
   ✅ Total F29: 12
   ✅ Primer folio: 123456

==================== ✅ TODOS LOS TESTS PASARON ====================
```

### Opción 2: Pytest

```bash
pytest apps/sii/rpa_v3/tests/test_real_extraction.py \
    --rut="12345678-9" \
    --password="tu_password" \
    -v -s
```

---

## ⚙️ Configuración Común

### Modo Headless

```python
# Con ventana visible (debugging)
client = SIIClient(tax_id="...", password="...", headless=False)

# Sin ventana (producción, por defecto)
client = SIIClient(tax_id="...", password="...", headless=True)
```

### Logging

```python
import logging

# Ver todos los logs
logging.basicConfig(level=logging.DEBUG)

# Solo errores
logging.basicConfig(level=logging.ERROR)
```

### Período Dinámico

```python
from datetime import datetime

# Período actual
periodo = datetime.now().strftime("%Y%m")
compras = client.get_compras(periodo=periodo)

# Mes anterior
from dateutil.relativedelta import relativedelta
mes_anterior = (datetime.now() - relativedelta(months=1)).strftime("%Y%m")
compras = client.get_compras(periodo=mes_anterior)
```

---

## 🔧 Debugging

### Ver el Navegador

```python
# Modo visual
with SIIClient(tax_id="...", password="...", headless=False) as client:
    client.login()  # Verás el navegador abrirse
    # ... resto del código
```

### Logs Detallados

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Ahora verás logs detallados de todo el proceso
```

### Guardar Screenshots

```python
with SIIClient(tax_id="...", password="...", headless=False) as client:
    client.login()

    # Acceder al driver directamente
    client._driver.take_screenshot("screenshot.png")
```

---

## ❌ Troubleshooting

### Error: "Credenciales inválidas"

```python
# Verificar credenciales
print(f"RUT: {tax_id}")
print(f"Password length: {len(password)}")

# Intentar login manual en navegador visible
client = SIIClient(tax_id="...", password="...", headless=False)
```

### Error: "Chrome not found"

```bash
# Verificar Chrome instalado
which google-chrome
which chromium

# Configurar path manualmente
export CHROME_BINARY_PATH="/usr/bin/chromium"
```

### Error: "No module named 'apps.sii.rpa_v3'"

```python
# Asegurar que Django está configurado
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fizko_django.settings')
django.setup()

# Luego importar
from apps.sii.rpa_v3 import SIIClient
```

### DTEs retornan vacío

```python
# Normal si no hay documentos en el período
compras = client.get_compras(periodo="202501")

if compras['status'] == 'success':
    if len(compras['data']) == 0:
        print("Sin documentos en este período")
    else:
        print(f"Encontrados {len(compras['data'])} documentos")
```

---

## 📚 Siguiente Paso

Una vez que el quick test funcione, revisa:

1. **[README.md](README.md)** - Documentación completa de la API
2. **[EXAMPLES.md](EXAMPLES.md)** - 20 ejemplos prácticos
3. **[tests/](tests/)** - Ver más ejemplos de uso

---

## 💡 Tips Rápidos

1. **Siempre usa context manager** (`with`)
2. **Verifica `status`** en resultados de DTEs
3. **F29 es más lento** (requiere login fresco)
4. **Cookies se reutilizan** (~70% más rápido)
5. **Headless=False para debug**

---

¿Listo? ¡Empieza a extraer datos! 🚀
