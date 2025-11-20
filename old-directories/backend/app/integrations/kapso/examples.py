"""
Ejemplos de uso de la integración de Kapso
NOTA: Este archivo es solo para referencia, no ejecutar directamente
"""
import asyncio
import os
from typing import Optional

from app.integrations.kapso import KapsoClient
from app.integrations.kapso.models import MessageType
from app.services.whatsapp import WhatsAppService


# =============================================================================
# Ejemplo 1: Enviar notificación de documento tributario
# =============================================================================

async def example_send_tax_document_notification():
    """
    Envía una notificación cuando un nuevo documento tributario llega.
    """
    service = WhatsAppService(
        api_token=os.getenv("KAPSO_API_TOKEN"),
    )

    # Datos del documento (ejemplo)
    document_data = {
        "folio": "12345",
        "tipo": "Factura Electrónica",
        "monto": 150000,
        "emisor": "Empresa ABC",
        "fecha": "2025-10-26",
    }

    user_phone = "+56912345678"
    whatsapp_config_id = os.getenv("KAPSO_WHATSAPP_CONFIG_ID")

    # Opción 1: Usar plantilla (recomendado para iniciar conversación)
    result = await service.send_template(
        phone_number=user_phone,
        template_name="nuevo_documento_tributario",
        template_params=[
            document_data["tipo"],
            document_data["folio"],
            f"${document_data['monto']:,}",
        ],
        whatsapp_config_id=whatsapp_config_id,
    )

    print(f"✅ Notificación enviada: {result}")


# =============================================================================
# Ejemplo 2: Chat conversacional con el usuario
# =============================================================================

async def example_conversational_chat():
    """
    Ejemplo de chat conversacional con botones interactivos.
    """
    service = WhatsAppService(
        api_token=os.getenv("KAPSO_API_TOKEN"),
    )

    conversation_id = "conv-123"  # ID de conversación activa

    # Enviar mensaje con botones
    await service.send_interactive(
        conversation_id=conversation_id,
        interactive_type="button",
        body_text="¿Qué te gustaría hacer hoy?",
        header_text="Menú Principal",
        footer_text="Selecciona una opción",
        buttons=[
            {"id": "view_documents", "title": "Ver documentos"},
            {"id": "tax_summary", "title": "Resumen fiscal"},
            {"id": "help", "title": "Ayuda"},
        ],
    )


# =============================================================================
# Ejemplo 3: Enviar resumen fiscal mensual con PDF
# =============================================================================

async def example_send_tax_summary_with_pdf():
    """
    Envía resumen fiscal con documento PDF adjunto.
    """
    service = WhatsAppService(
        api_token=os.getenv("KAPSO_API_TOKEN"),
    )

    conversation_id = "conv-123"

    # 1. Enviar mensaje de contexto
    await service.send_text(
        conversation_id=conversation_id,
        message="📊 Tu resumen fiscal de octubre está listo",
    )

    # 2. Enviar PDF
    await service.send_media(
        conversation_id=conversation_id,
        media_url="https://storage.fizko.ai/reports/resumen-octubre.pdf",
        media_type=MessageType.DOCUMENT,
        filename="Resumen_Fiscal_Octubre_2025.pdf",
        caption="Resumen fiscal del mes de octubre 2025",
    )

    # 3. Enviar mensaje de seguimiento
    await service.send_text(
        conversation_id=conversation_id,
        message="¿Necesitas ayuda para interpretar estos datos?",
    )


# =============================================================================
# Ejemplo 4: Búsqueda y contexto de contacto
# =============================================================================

async def example_search_and_get_context():
    """
    Busca un contacto y obtiene su historial.
    """
    service = WhatsAppService(
        api_token=os.getenv("KAPSO_API_TOKEN"),
    )

    # Buscar contacto
    contacts = await service.search_contacts(query="Juan")

    if contacts.get("nodes"):
        contact = contacts["nodes"][0]
        contact_id = contact["id"]

        # Obtener historial completo
        history = await service.get_contact_history(
            identifier=contact_id,
            message_limit=50,
        )

        print(f"📱 Contacto: {contact['display_name']}")
        print(f"💬 Mensajes recientes: {len(history.get('messages', []))}")

        # Añadir nota al contacto
        await service.add_note_to_contact(
            contact_identifier=contact_id,
            note="Cliente interesado en servicios contables",
            label="seguimiento_comercial",
        )


# =============================================================================
# Ejemplo 5: Webhook handler - Procesamiento de mensajes entrantes
# =============================================================================

async def example_webhook_message_received(webhook_data: dict):
    """
    Procesa un mensaje recibido desde el webhook de Kapso.

    Args:
        webhook_data: Payload del webhook
    """
    service = WhatsAppService(
        api_token=os.getenv("KAPSO_API_TOKEN"),
    )

    event_type = webhook_data.get("event_type")

    if event_type == "message.received":
        conversation_id = webhook_data["conversation_id"]
        message_content = webhook_data["payload"]["content"]
        sender_phone = webhook_data["payload"]["from"]

        print(f"📥 Mensaje recibido de {sender_phone}: {message_content}")

        # Marcar como leído
        await service.mark_as_read(conversation_id=conversation_id)

        # Lógica de negocio: responder según el contenido
        if "documento" in message_content.lower():
            await service.send_text(
                conversation_id=conversation_id,
                message="Para ver tus documentos, ingresa a https://app.fizko.ai/documentos",
            )

        elif "ayuda" in message_content.lower():
            await service.send_interactive(
                conversation_id=conversation_id,
                interactive_type="list",
                body_text="¿En qué puedo ayudarte?",
                header_text="Centro de Ayuda",
                sections=[
                    {
                        "title": "Documentos",
                        "rows": [
                            {"id": "ver_facturas", "title": "Ver facturas"},
                            {"id": "ver_boletas", "title": "Ver boletas"},
                        ],
                    },
                    {
                        "title": "Reportes",
                        "rows": [
                            {"id": "resumen_fiscal", "title": "Resumen fiscal"},
                            {"id": "libro_ventas", "title": "Libro de ventas"},
                        ],
                    },
                ],
            )


# =============================================================================
# Ejemplo 6: Gestión de bandeja de entrada
# =============================================================================

async def example_inbox_management():
    """
    Gestiona la bandeja de entrada de conversaciones activas.
    """
    service = WhatsAppService(
        api_token=os.getenv("KAPSO_API_TOKEN"),
    )

    whatsapp_config_id = os.getenv("KAPSO_WHATSAPP_CONFIG_ID")

    # Obtener conversaciones activas
    inbox = await service.get_inbox(
        whatsapp_config_id=whatsapp_config_id,
        limit=50,
        status="active",
    )

    conversations = inbox.get("conversations", [])

    print(f"📬 Conversaciones activas: {len(conversations)}")

    for conv in conversations:
        conversation_id = conv["id"]
        phone = conv["phone_number"]
        last_message = conv.get("last_message", {})

        print(f"\n💬 {phone}")
        print(f"   Último mensaje: {last_message.get('content', 'N/A')}")

        # Si no hay actividad reciente, enviar recordatorio
        # (implementar lógica de tiempo aquí)
        # await service.send_text(...)


# =============================================================================
# Ejemplo 7: Enviar recordatorio de vencimiento F29
# =============================================================================

async def example_send_f29_reminder():
    """
    Envía recordatorio de vencimiento de F29.
    """
    service = WhatsAppService(
        api_token=os.getenv("KAPSO_API_TOKEN"),
    )

    users_to_notify = [
        {"phone": "+56912345678", "name": "Juan Pérez"},
        {"phone": "+56987654321", "name": "María González"},
    ]

    whatsapp_config_id = os.getenv("KAPSO_WHATSAPP_CONFIG_ID")

    for user in users_to_notify:
        # Usar plantilla de recordatorio
        result = await service.send_template(
            phone_number=user["phone"],
            template_name="recordatorio_f29",
            template_params=[
                user["name"],
                "12",  # día de vencimiento
                "noviembre",  # mes
            ],
            whatsapp_config_id=whatsapp_config_id,
        )

        print(f"✅ Recordatorio enviado a {user['name']}: {result}")


# =============================================================================
# Ejemplo 8: Obtener y listar plantillas disponibles
# =============================================================================

async def example_list_templates():
    """
    Lista todas las plantillas disponibles.
    """
    service = WhatsAppService(
        api_token=os.getenv("KAPSO_API_TOKEN"),
    )

    templates = await service.list_templates()

    print("📋 Plantillas disponibles:")
    for template in templates.get("nodes", []):
        print(f"  - {template['name']} ({template['language']})")
        print(f"    Estado: {template['status']}")
        print(f"    Categoría: {template.get('category', 'N/A')}")


# =============================================================================
# Ejemplo 9: Búsqueda de mensajes
# =============================================================================

async def example_search_messages():
    """
    Busca mensajes que contengan cierta palabra.
    """
    service = WhatsAppService(
        api_token=os.getenv("KAPSO_API_TOKEN"),
    )

    # Buscar mensajes que mencionen "factura"
    results = await service.search_messages(
        query="factura",
        limit=20,
    )

    messages = results.get("nodes", [])
    print(f"🔍 Encontrados {len(messages)} mensajes con 'factura'")

    for msg in messages:
        print(f"  - {msg.get('snippet', msg.get('content', ''))}")


# =============================================================================
# Ejemplo 10: Health check
# =============================================================================

async def example_health_check():
    """
    Verifica el estado del servicio Kapso.
    """
    service = WhatsAppService(
        api_token=os.getenv("KAPSO_API_TOKEN"),
    )

    health = await service.health_check()

    print(f"🏥 Estado del servicio: {health['status']}")
    if health["status"] == "healthy":
        print(f"   Tiempo de respuesta: {health.get('response_time', 'N/A')}s")


# =============================================================================
# Ejecutar ejemplos
# =============================================================================

if __name__ == "__main__":
    # Ejemplo de ejecución
    # asyncio.run(example_send_tax_document_notification())
    # asyncio.run(example_conversational_chat())
    # asyncio.run(example_send_tax_summary_with_pdf())
    # asyncio.run(example_search_and_get_context())
    # asyncio.run(example_inbox_management())
    # asyncio.run(example_send_f29_reminder())
    # asyncio.run(example_list_templates())
    # asyncio.run(example_search_messages())
    # asyncio.run(example_health_check())

    print("⚠️ Este archivo es solo de referencia. Descomenta el ejemplo que quieras ejecutar.")
