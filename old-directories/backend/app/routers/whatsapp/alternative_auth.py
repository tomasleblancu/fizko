"""
Validación alternativa de webhooks si Kapso no soporta HMAC signature
"""

# OPCIÓN 1: Validar por IP
# Si Kapso siempre envía desde IPs conocidas, podemos usar allowlist
KAPSO_ALLOWED_IPS = [
    "34.211.200.85",  # IP vista en tus logs
    # Añadir más IPs si Kapso usa múltiples
]

def validate_webhook_by_ip(request_ip: str) -> bool:
    """Valida que el webhook venga de una IP permitida"""
    return request_ip in KAPSO_ALLOWED_IPS


# OPCIÓN 2: Validar por token en query string o header
# URL: https://tu-dominio.com/api/whatsapp/webhook?token=SECRET_TOKEN
def validate_webhook_by_token(token: str, expected_token: str) -> bool:
    """Valida usando un token secreto en la URL"""
    return token == expected_token


# OPCIÓN 3: Validar por estructura del payload
# Verificar que el payload tenga la estructura esperada de Kapso
def validate_webhook_payload_structure(data: dict) -> bool:
    """Valida que el payload tenga la estructura de Kapso"""
    required_fields = ["event_type", "conversation_id"]
    return all(field in data for field in required_fields)


# Implementación en whatsapp.py:
"""
from app.routers.whatsapp_alternative_auth import (
    validate_webhook_by_ip,
    KAPSO_ALLOWED_IPS
)

@webhook_router.post("/webhook")
async def handle_webhook(request: Request):
    # Validar por IP
    client_ip = request.client.host if request.client else "unknown"

    if not validate_webhook_by_ip(client_ip):
        logger.warning(f"⚠️ Webhook de IP no permitida: {client_ip}")
        logger.warning(f"⚠️ IPs permitidas: {KAPSO_ALLOWED_IPS}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized IP"
        )

    # Continuar con el procesamiento...
"""
