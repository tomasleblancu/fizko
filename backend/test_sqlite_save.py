"""
Script de prueba para verificar que SQLiteSession funciona correctamente
con el formato de mensajes assistant que usamos.
"""
import os
import sys
from agents import SQLiteSession

def test_sqlite_notification_save():
    """
    Prueba guardar un contexto de notificación en SQLite
    usando el mismo formato que sending_service.py
    """
    # Path de prueba
    test_session_file = "backend/app/sessions/test_notifications.db"
    test_conversation_id = "test-conv-12345"

    # Limpiar DB de prueba si existe
    if os.path.exists(test_session_file):
        os.remove(test_session_file)
        print(f"🗑️  Removed old test database")

    # Crear sesión SQLite
    session = SQLiteSession(test_conversation_id, test_session_file)

    # Simular contexto de notificación
    notification_context = """<notification_context>
I sent you a reminder about:

📅 Event: Pago de IVA
Due: 12/11/2025
Status: Pending
Description: Declaración y pago de IVA mensual

Sent message: Hola! Te recordamos que el pago de IVA vence el 12/11/2025.
</notification_context>"""

    # Formato que usamos en sending_service.py
    assistant_message = {
        "role": "assistant",
        "content": [
            {
                "type": "output_text",
                "text": notification_context
            }
        ]
    }

    print(f"📝 Saving notification context to SQLite...")
    print(f"   Conversation ID: {test_conversation_id}")
    print(f"   Session file: {test_session_file}\n")

    # Guardar
    try:
        current_history = session.load()
        print(f"✅ Current history loaded: {len(current_history)} messages")

        current_history.append(assistant_message)
        session.store(current_history)

        print(f"✅ Message saved successfully!\n")

        # Verificar que se guardó
        reloaded_history = session.load()
        print(f"✅ Reloaded history: {len(reloaded_history)} messages")

        if len(reloaded_history) > 0:
            last_msg = reloaded_history[-1]
            print(f"\n📋 Last message:")
            print(f"   Role: {last_msg.get('role')}")
            print(f"   Content type: {type(last_msg.get('content'))}")

            if isinstance(last_msg.get('content'), list) and len(last_msg['content']) > 0:
                content_part = last_msg['content'][0]
                text = content_part.get('text', '')
                print(f"   Text preview: {text[:100]}...")

                # Verificar que contiene el marcador de notificación
                if "<notification_context>" in text:
                    print(f"\n✅ SUCCESS: Notification context marker found!")
                else:
                    print(f"\n❌ ERROR: Notification context marker NOT found")
            else:
                print(f"\n❌ ERROR: Content format unexpected")
                print(f"   Content: {last_msg.get('content')}")

        # Verificar en la DB directamente
        print(f"\n📊 Checking SQLite database directly...")
        import sqlite3
        conn = sqlite3.connect(test_session_file)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM agent_messages WHERE session_id = ?", (test_conversation_id,))
        count = cursor.fetchone()[0]
        print(f"   Messages in DB: {count}")

        cursor.execute("SELECT message_data FROM agent_messages WHERE session_id = ?", (test_conversation_id,))
        row = cursor.fetchone()
        if row:
            import json
            data = json.loads(row[0])
            print(f"   Stored role: {data.get('role')}")
            if "<notification_context>" in str(data):
                print(f"   ✅ Notification context found in raw DB data!")
            else:
                print(f"   ⚠️  Notification context NOT in raw DB data")

        conn.close()

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

    print(f"\n" + "=" * 80)
    print(f"Test completed successfully!")
    print(f"=" * 80)
    return True

if __name__ == "__main__":
    success = test_sqlite_notification_save()
    sys.exit(0 if success else 1)
