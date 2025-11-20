# Acuse de Recibo de Documentos Tributarios

Este documento explica cómo usar el nuevo método `ingresar_aceptacion_reclamo_docs` para realizar acuses de recibo de documentos tributarios electrónicos (DTEs) en el SII.

## Descripción

El método `ingresar_aceptacion_reclamo_docs` permite:
- Aceptar documentos de compra recibidos
- Reclamar documentos con problemas
- Procesar múltiples documentos en una sola operación
- Registrar el acuse de recibo de mercaderías (ERM)

## Códigos de Evento

Los códigos de evento más comunes son:

- **ERM**: Acuse de recibo de mercaderías (aceptación del documento)
- **RCD**: Reclamo por contenido del documento
- **RFP**: Reclamo por falta parcial de mercaderías
- **RFT**: Reclamo por falta total de mercaderías

## Uso Básico

```python
from app.integrations.sii.client import SIIClient

# Credenciales
tax_id = "12345678-9"
password = "tu_clave_sii"

# Documentos a procesar
documentos = [
    {
        "detRutDoc": "76035322",      # RUT del emisor (sin guión)
        "detDvDoc": "1",              # Dígito verificador
        "detTipoDoc": "33",           # Tipo documento (33=Factura)
        "detNroDoc": "22474",         # Número del documento
        "dedCodEvento": "ERM"         # Código evento
    },
    {
        "detRutDoc": "77687339",
        "detDvDoc": "K",
        "detTipoDoc": "33",
        "detNroDoc": "176",
        "dedCodEvento": "ERM"
    }
]

# Ejecutar acuse de recibo
with SIIClient(tax_id=tax_id, password=password) as client:
    client.login()
    resultado = client.ingresar_aceptacion_reclamo_docs(documentos)

    print(f"Eventos procesados: {resultado['eventosOk']}")

    # Ver detalle de cada documento
    for doc in resultado['data']:
        print(f"Doc {doc['detNroDoc']}: {doc['respuesta']}")
```

## Respuesta

El método retorna un diccionario con la siguiente estructura:

```python
{
    "data": [
        {
            "detRutDoc": "76035322",
            "detDvDoc": "1",
            "detTipoDoc": "33",
            "detNroDoc": "22474",
            "dedCodEvento": "ERM",
            "respuesta": "Acuse de recibo realizado",
            "codRespuesta": 0
        },
        # ... más documentos
    ],
    "eventosOk": 10,  # Número de documentos procesados exitosamente
    "metaData": {
        "conversationId": "...",
        "transactionId": "...",
        # ...
    },
    "respEstado": {
        "codRespuesta": 0,
        "msgeRespuesta": null,
        "codError": null
    }
}
```

## Códigos de Respuesta

- **0**: Operación exitosa
- **Otros**: Error en el procesamiento (ver `respuesta` para detalles)

## Ejemplo Completo: Script de Prueba

Se incluye un script de prueba en [test_acuse_recibo.py](./test_acuse_recibo.py):

```bash
# Configurar variables de entorno
export STC_TEST_RUT=12345678-9
export SII_PASSWORD=tu_clave_sii

# Ejecutar prueba
python backend-v2/test_acuse_recibo.py
```

## Validaciones

El método realiza las siguientes validaciones:

1. **Parámetros obligatorios**: Cada documento debe incluir:
   - `detRutDoc`: RUT del emisor (sin guión)
   - `detDvDoc`: Dígito verificador (mayúscula si es 'K')
   - `detTipoDoc`: Código del tipo de documento
   - `detNroDoc`: Número del documento
   - `dedCodEvento`: Código del evento (ERM, RCD, etc.)

2. **Lista no vacía**: Debe incluir al menos un documento

3. **Autenticación**: Requiere sesión activa en el SII

## Manejo de Errores

El método puede lanzar las siguientes excepciones:

- `ValueError`: Parámetros inválidos o campos faltantes
- `ExtractionError`: Error en la comunicación con el SII
- `requests.RequestException`: Error de red

## Reintentos Automáticos

El método incluye reintentos automáticos:
- Por defecto: 3 intentos
- Delay entre intentos: 2 segundos
- Configurable vía parámetro `max_retries`

```python
# Aumentar reintentos a 5
resultado = client.ingresar_aceptacion_reclamo_docs(
    documentos,
    max_retries=5
)
```

## Integración en Backend

### Ejemplo de Endpoint FastAPI

```python
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List

router = APIRouter(prefix="/sii", tags=["sii"])

class DocumentoAcuse(BaseModel):
    detRutDoc: str
    detDvDoc: str
    detTipoDoc: str
    detNroDoc: str
    dedCodEvento: str

class AcuseReciboRequest(BaseModel):
    documentos: List[DocumentoAcuse]

@router.post("/acuse-recibo")
async def realizar_acuse_recibo(
    request: AcuseReciboRequest,
    company_id: str = Depends(get_current_company)
):
    """Realiza acuse de recibo de documentos en el SII"""

    # Obtener credenciales del SII para la empresa
    credentials = await get_sii_credentials(company_id)

    try:
        with SIIClient(
            tax_id=credentials.rut,
            password=credentials.password
        ) as client:
            client.login()

            # Convertir Pydantic models a dicts
            documentos = [doc.dict() for doc in request.documentos]

            resultado = client.ingresar_aceptacion_reclamo_docs(documentos)

            return {
                "success": True,
                "eventos_ok": resultado["eventosOk"],
                "documentos": resultado["data"]
            }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al procesar acuses de recibo: {str(e)}"
        )
```

## Notas Importantes

1. **RUT sin guión**: El campo `detRutDoc` debe ser sin guión (ej: "76035322")
2. **DV en mayúscula**: Si el DV es 'K', debe estar en mayúscula
3. **Autenticación previa**: Debe llamar a `client.login()` antes de usar este método
4. **Sesión válida**: El cliente verifica y refresca la sesión automáticamente
5. **Batch processing**: Puede procesar múltiples documentos en una sola llamada

## Referencias

- Endpoint SII: `https://www4.sii.cl/consdcvinternetui/services/data/facadeService/ingresarAceptacionReclamoDocs`
- Namespace: `cl.sii.sdi.lob.diii.consdcv.data.api.interfaces.FacadeService/ingresarAceptacionReclamoDocs`
