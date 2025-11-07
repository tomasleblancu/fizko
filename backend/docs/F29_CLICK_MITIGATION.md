# Mitigación de errores ElementClickInterceptedException en extracción F29

## Problema identificado

Durante la extracción de formularios F29, ocasionalmente ocurre el error:

```
ElementClickInterceptedException: Element <button>...</button> is not clickable at point (640, 279).
Other element would receive the click: <div class="gw-par-negrita">...</div>
```

Este error ocurre específicamente en el paso de **volver a la tabla principal** después de extraer el `codInt` del formulario.

## Causa raíz

El portal del SII utiliza **Google Web Toolkit (GWT)** que genera overlays dinámicos que pueden interceptar clicks. El flujo de extracción es:

1. Click en "Ver" para ver detalles del formulario ✅
2. Click en "Formulario Compacto" para abrir PDF y extraer `codInt` de la URL ✅
3. **Click en "Volver" para regresar a la tabla** ❌ **← Aquí ocurre el error**

El problema se manifiesta cuando:
- Un overlay de carga (`gw-par-negrita`, modales, etc.) no se ha ocultado completamente
- La animación de transición de página aún está en progreso
- El botón "Volver" no está completamente visible/clickable

## Solución implementada

Se implementó un sistema de **6 estrategias progresivas** con reintentos en [f29_scraper.py:830-969](backend/app/integrations/sii/scrapers/f29_scraper.py#L830-L969):

### Estrategia 1: Espera adaptativa
```python
wait_time = 1.5 + (attempt * 0.5)  # Aumentar tiempo en cada reintento
time.sleep(wait_time)
```
Da más tiempo para que la página se estabilice en reintentos subsecuentes.

### Estrategia 2: Múltiples selectores
```python
volver_selectors = [
    "//button[contains(text(), 'Volver')]",
    "//button[contains(@class, 'gw-button') and contains(text(), 'Volver')]",
    "//*[contains(text(), 'Volver') and (name()='button' or name()='a')]"
]
```
Intenta encontrar el botón con diferentes XPath para mayor robustez.

### Estrategia 3: Detección y cierre de overlays
```python
overlay_selectors = [
    "//div[contains(@class, 'gw-par-negrita')]",  # El div específico del error
    "//div[contains(@class, 'modal')]",
    "//div[contains(@class, 'overlay')]",
    "//div[contains(@class, 'loading')]"
]

for overlay in overlays:
    if overlay.is_displayed():
        driver.execute_script("arguments[0].style.display = 'none';", overlay)
```
Detecta y oculta explícitamente overlays que bloquean el click.

### Estrategia 4: Scroll y espera de clickability
```python
driver.execute_script(
    "arguments[0].scrollIntoView({block: 'center', inline: 'center'});",
    volver_btn
)

volver_btn = WebDriverWait(driver, 3).until(
    EC.element_to_be_clickable(volver_btn)
)
```
Asegura que el elemento esté visible y sea clickable antes de interactuar.

### Estrategia 5: Click progresivo
- **Intentos 1-3**: Click normal de Selenium
- **Intentos 4-5**: JavaScript click directo (más robusto)

```python
if attempt < 3:
    volver_btn.click()
else:
    driver.execute_script("arguments[0].click();", volver_btn)
```

### Estrategia 6: Navegación alternativa (último recurso)
Si todos los clicks fallan, usa métodos alternativos de navegación:

```python
# Opción A: History back
driver.execute_script("window.history.back();")

# Opción B: Navegación directa a URL de búsqueda
driver.navigate_to(SEARCH_URL)
```

## Impacto de la mejora

### Antes
- **3 reintentos** con estrategia básica
- Falla completa si el overlay persiste
- Error crítico que detiene el procesamiento del folio

### Después
- **5 reintentos** con 6 estrategias progresivas
- Detección y cierre proactivo de overlays
- Navegación alternativa si todo falla
- **Error no crítico**: El formulario ya fue procesado y guardado con su `codInt`

### Logging mejorado
```
🔙 Click normal exitoso en 'Volver' (intento 1)
⚠️ Click bloqueado (intento 2/5): Element click intercepted...
⚠️ Overlay detectado, intentando ocultar: //div[contains(@class, 'gw-par-negrita')]
🔙 JavaScript click exitoso en 'Volver' (intento 4)
✅ Navegación con history.back() exitosa
```

## Resultado

Este error ya **no detiene el procesamiento** de formularios F29. El sistema:

1. ✅ Extrae correctamente el `codInt` antes del error
2. ✅ Guarda el formulario con todos sus datos
3. ⚠️ Intenta múltiples estrategias para volver a la tabla
4. ℹ️ Si todas fallan, registra warning pero continúa con el siguiente folio

**El error se convirtió de crítico a informativo**, manteniendo la extracción exitosa del dato más importante (`codInt` para descarga de PDF).

## Monitoreo

Para verificar la efectividad de las mejoras, monitorear en logs:

```bash
# Contar éxitos de click en primer intento
grep "🔙 Click normal exitoso en 'Volver' (intento 1)" logs.txt | wc -l

# Contar casos que requirieron JavaScript click
grep "JavaScript click exitoso" logs.txt | wc -l

# Contar casos que requirieron navegación alternativa
grep "history.back() exitosa" logs.txt | wc -l

# Verificar si hay folios que fallaron completamente
grep "Error al volver a tabla principal" logs.txt
```

## Mejoras futuras (opcional)

Si el error persiste con frecuencia, considerar:

1. **Rediseñar flujo**: Extraer `codInt` sin necesidad de navegar (parse directo desde tabla)
2. **Headless optimizado**: Usar opciones de Chrome que deshabiliten animaciones GWT
3. **Timeout dinámico**: Ajustar tiempos según latencia de red detectada
4. **Batch processing**: Agrupar extracciones en lotes para minimizar navegación
