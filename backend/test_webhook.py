#!/usr/bin/env python3
"""
Script de testing para el webhook de Kapso
Uso: python test_webhook.py [--with-signature]
"""
import requests
import json
import hmac
import hashlib
import sys
import os

# Configuración
WEBHOOK_URL = "http://localhost:8000/api/whatsapp/webhook"
WEBHOOK_SECRET = os.getenv("KAPSO_WEBHOOK_SECRET", "test-secret-key")

# Payload de ejemplo
payload = {
    "event_type": "message.received",
    "conversation_id": "test-conv-123",
    "message_id": "test-msg-456",
    "timestamp": "2025-10-26T10:30:00Z",
    "payload": {
        "from": "+56912345678",
        "to": "+56987654321",
        "content": "Hola, este es un mensaje de prueba",
        "message_type": "text",
        "timestamp": "2025-10-26T10:30:00Z",
        "contact": {
            "id": "contact-123",
            "phone_number": "+56912345678",
            "display_name": "Juan Pérez (Test)"
        }
    }
}

def generate_signature(payload_str: str, secret: str) -> str:
    """Genera firma HMAC-SHA256"""
    return hmac.new(
        secret.encode('utf-8'),
        payload_str.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

def test_webhook_without_signature():
    """Test sin firma - solo funciona si KAPSO_WEBHOOK_SECRET no está configurado"""
    print("\n" + "="*70)
    print("TEST 1: Webhook SIN firma")
    print("="*70)

    payload_str = json.dumps(payload)

    try:
        response = requests.post(
            WEBHOOK_URL,
            headers={"Content-Type": "application/json"},
            data=payload_str,
            timeout=10
        )

        print(f"\n✅ Status Code: {response.status_code}")
        print(f"📦 Response: {json.dumps(response.json(), indent=2)}")

        if response.status_code == 200:
            print("\n✅ TEST PASÓ: Webhook aceptado sin firma")
            print("   Esto significa que KAPSO_WEBHOOK_SECRET NO está configurado")
        elif response.status_code == 401:
            print("\n⚠️  TEST FALLÓ: Webhook rechazado (401 Unauthorized)")
            print("   Esto significa que KAPSO_WEBHOOK_SECRET está configurado")
            print("   Ejecuta: python test_webhook.py --with-signature")

    except requests.exceptions.ConnectionError:
        print("\n❌ Error: No se puede conectar al servidor")
        print("   ¿Está el servidor corriendo en http://localhost:8000?")
        print("   Ejecuta: uvicorn app.main:app --reload")
    except Exception as e:
        print(f"\n❌ Error: {e}")

def test_webhook_with_signature():
    """Test con firma HMAC"""
    print("\n" + "="*70)
    print("TEST 2: Webhook CON firma HMAC-SHA256")
    print("="*70)

    payload_str = json.dumps(payload)
    signature = generate_signature(payload_str, WEBHOOK_SECRET)

    print(f"\n📝 Secret: {WEBHOOK_SECRET}")
    print(f"🔐 Firma: {signature}")

    try:
        response = requests.post(
            WEBHOOK_URL,
            headers={
                "Content-Type": "application/json",
                "X-Kapso-Signature": signature
            },
            data=payload_str,
            timeout=10
        )

        print(f"\n✅ Status Code: {response.status_code}")
        print(f"📦 Response: {json.dumps(response.json(), indent=2)}")

        if response.status_code == 200:
            print("\n✅ TEST PASÓ: Webhook aceptado con firma válida")
        elif response.status_code == 401:
            print("\n❌ TEST FALLÓ: Firma rechazada (401 Unauthorized)")
            print("   Verifica que KAPSO_WEBHOOK_SECRET en .env coincida con el secreto usado")

    except requests.exceptions.ConnectionError:
        print("\n❌ Error: No se puede conectar al servidor")
        print("   ¿Está el servidor corriendo en http://localhost:8000?")
        print("   Ejecuta: uvicorn app.main:app --reload")
    except Exception as e:
        print(f"\n❌ Error: {e}")

def test_webhook_with_wrong_signature():
    """Test con firma incorrecta"""
    print("\n" + "="*70)
    print("TEST 3: Webhook con firma INCORRECTA (debe fallar)")
    print("="*70)

    payload_str = json.dumps(payload)
    wrong_signature = "abc123def456invalid"  # Firma falsa

    try:
        response = requests.post(
            WEBHOOK_URL,
            headers={
                "Content-Type": "application/json",
                "X-Kapso-Signature": wrong_signature
            },
            data=payload_str,
            timeout=10
        )

        print(f"\n✅ Status Code: {response.status_code}")

        if response.status_code == 401:
            print("✅ TEST PASÓ: Firma incorrecta rechazada correctamente")
        else:
            print(f"⚠️  ADVERTENCIA: Se esperaba 401, pero se obtuvo {response.status_code}")

    except requests.exceptions.ConnectionError:
        print("\n❌ Error: No se puede conectar al servidor")
    except Exception as e:
        print(f"\n❌ Error: {e}")

def main():
    print("\n" + "="*70)
    print("🧪 TEST SUITE - Webhook de Kapso WhatsApp")
    print("="*70)
    print(f"URL: {WEBHOOK_URL}")

    if "--with-signature" in sys.argv:
        # Tests con firma
        test_webhook_with_signature()
        test_webhook_with_wrong_signature()
    else:
        # Test sin firma
        test_webhook_without_signature()

    print("\n" + "="*70)
    print("Tests completados")
    print("="*70)
    print("\nOpciones:")
    print("  python test_webhook.py                    # Test sin firma")
    print("  python test_webhook.py --with-signature   # Test con firma HMAC")
    print()

if __name__ == "__main__":
    main()
