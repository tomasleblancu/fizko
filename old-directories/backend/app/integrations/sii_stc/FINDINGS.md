# Hallazgos de la Integración STC

## 🔍 Problema Encontrado

Durante las pruebas de la integración STC, se descubrió que **reCAPTCHA no se carga automáticamente** en el portal STC del SII (`https://www2.sii.cl/stc/noauthz/consulta`).

### Evidencia

- ✅ El navegador se conecta correctamente al portal
- ✅ La página carga completamente (assets, CSS, JS)
- ❌ No aparece ningún request a `recaptcha/enterprise/reload`
- ❌ Timeout después de 20 segundos esperando el token reCAPTCHA

### Logs Observados

```
2025-11-04 15:42:14 - Navigating to: https://www2.sii.cl/stc/noauthz/consulta
2025-11-04 15:42:14 - Capturing response: https://www2.sii.cl/stc/noauthz/consulta 200 OK
2025-11-04 15:42:14 - [Loading assets...]
2025-11-04 15:42:20 - Captured 1 cookies
2025-11-04 15:42:20 - Waiting for reCAPTCHA token...
2025-11-04 15:42:40 - ❌ No reCAPTCHA request found after 20s
```

## 💡 Posibles Causas

1. **reCAPTCHA carga bajo demanda**: El SII puede cargar reCAPTCHA solo cuando el usuario:
   - Hace click en el botón "Consultar"
   - Completa el formulario
   - Interactúa con algún elemento específico

2. **reCAPTCHA v3 (invisible)**: Si usa reCAPTCHA v3, el comportamiento es diferente:
   - Se ejecuta en background sin UI visible
   - El token se obtiene mediante JavaScript, no HTTP
   - No hay request interceptable a `recaptcha/enterprise/reload`

3. **Detección de automatización**: El sitio puede detectar que estamos usando Selenium y:
   - No cargar reCAPTCHA
   - Cargar una versión diferente
   - Bloquear la funcionalidad

## 🛠️ Solución Alternativa: Usar Request Directo con Token Manual

Dado que interceptar reCAPTCHA automáticamente es complejo, propongo una solución más simple:

### Opción A: Sin reCAPTCHA (Si es posible)

Intentar hacer la consulta directamente sin token reCAPTCHA para ver si el endpoint lo requiere realmente.

```python
# Payload sin reToken
payload = {
    "rut": "77794858",
    "dv": "K",
    "reAction": "consultaSTC"
    # "reToken": ""  # Omitir o vacío
}
```

### Opción B: Token Manual del Usuario

Permitir que el usuario obtenga el token manualmente:

1. Usuario visita `https://www2.sii.cl/stc/noauthz/consulta` en su navegador
2. Abre DevTools → Network
3. Hace click en "Consultar"
4. Copia el `reToken` del payload del request
5. Lo pasa al endpoint API

```python
# API acepta token manual
POST /api/stc/consultar-documento
{
  "rut": "77794858",
  "dv": "K",
  "recaptcha_token": "03AFcWeA..."  # Token manual
}
```

### Opción C: Scraping Completo con Selenium

En lugar de interceptar el token, hacer todo el flujo con Selenium:

1. Navegar al portal
2. Llenar el formulario (RUT, DV)
3. Hacer click en "Consultar"
4. Esperar y capturar la respuesta del navegador
5. Parsear el HTML resultante

```python
# Llenar formulario
rut_field.send_keys("77794858")
dv_field.send_keys("K")
submit_button.click()

# Esperar resultado
time.sleep(5)

# Parsear respuesta
result_html = driver.page_source
# Extraer datos del HTML
```

## 📋 Recomendación

**Opción B (Token Manual)** es la más práctica por ahora:

### Ventajas:
- ✅ Simple de implementar
- ✅ No depende de interceptación compleja
- ✅ Funciona con cualquier tipo de reCAPTCHA
- ✅ El usuario tiene control total
- ✅ Útil para testing y validación

### Desventajas:
- ❌ Requiere intervención manual del usuario
- ❌ Token expira después de ~2 minutos
- ❌ No es completamente automatizado

### Implementación:

1. Crear endpoint que acepta token manual:
```python
@router.post("/consultar-documento-manual")
async def consultar_documento_manual(
    rut: str,
    dv: str,
    recaptcha_token: str  # Token obtenido manualmente
):
    # Hacer request directo sin Selenium
    response = requests.post(
        "https://www2.sii.cl/app/stc/recurso/v1/consulta/getConsultaData/",
        json={
            "rut": rut,
            "dv": dv,
            "reAction": "consultaSTC",
            "reToken": recaptcha_token
        }
    )
    return response.json()
```

2. Documentar cómo obtener el token:
   - Abrir DevTools
   - Network tab
   - Hacer consulta en el portal
   - Copiar token del request

## 🔮 Futuro: Investigación Adicional

Para hacer la automatización completamente:

1. **Investigar reCAPTCHA v3**: Si es v3, necesitamos approach diferente
2. **Analizar JavaScript del sitio**: Ver cómo genera el token
3. **Probar con navegador real**: Usar herramientas como Puppeteer/Playwright
4. **Considerar servicios de terceros**: 2Captcha, Anti-Captcha, etc. (costo adicional)

## 📝 Código Actual

El código actual está implementado y funcionará **SI** reCAPTCHA se carga:
- ✅ Driver con selenium-wire
- ✅ Interceptor de requests
- ✅ Parser de token rresp
- ✅ Cliente completo

Solo necesita que reCAPTCHA se cargue en la página.

## 🎯 Próximos Pasos

1. **Probar Opción A**: Intentar sin token para ver si es realmente necesario
2. **Implementar Opción B**: Endpoint con token manual como fallback
3. **Investigar más**: Analizar JavaScript del sitio para entender reCAPTCHA
4. **Documentar workaround**: Guía para usuarios sobre cómo obtener token manual

---

**Fecha**: 2025-11-04
**Estado**: Investigación en curso
**Código**: Listo para usar (requiere que reCAPTCHA se cargue)
