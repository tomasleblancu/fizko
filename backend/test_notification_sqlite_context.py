"""
Script de prueba para verificar que el contexto de notificaciones
se guarda correctamente en SQLite.
"""
import sqlite3
import os

# Path a la base de datos SQLite
sessions_db_path = "backend/app/sessions/whatsapp_agent_sessions.db"

def check_notification_context(conversation_id: str):
    """
    Verifica si una conversación tiene contexto de notificación guardado en SQLite.

    Args:
        conversation_id: UUID de la conversación a verificar
    """
    if not os.path.exists(sessions_db_path):
        print(f"❌ Database not found: {sessions_db_path}")
        return

    conn = sqlite3.connect(sessions_db_path)
    cursor = conn.cursor()

    # Verificar si existe la sesión
    cursor.execute(
        "SELECT session_id, created_at, updated_at FROM agent_sessions WHERE session_id = ?",
        (conversation_id,)
    )
    session = cursor.fetchone()

    if not session:
        print(f"⚠️ Session not found for conversation: {conversation_id}")
        conn.close()
        return

    print(f"✅ Session found: {session[0]}")
    print(f"   Created: {session[1]}")
    print(f"   Updated: {session[2]}\n")

    # Obtener mensajes
    cursor.execute(
        """
        SELECT id, created_at, message_data
        FROM agent_messages
        WHERE session_id = ?
        ORDER BY id
        """,
        (conversation_id,)
    )
    messages = cursor.fetchall()

    if not messages:
        print(f"⚠️ No messages found")
        conn.close()
        return

    print(f"📊 Total messages: {len(messages)}\n")

    # Buscar mensajes con contexto de notificación
    import json
    notification_contexts = []

    for msg_id, created_at, message_data in messages:
        try:
            data = json.loads(message_data)
            role = data.get("role")
            content = data.get("content", "")

            # Detectar contexto de notificación
            if role == "assistant" and "<notification_context>" in str(content):
                notification_contexts.append({
                    "id": msg_id,
                    "created_at": created_at,
                    "content": content[:200] + "..." if len(str(content)) > 200 else content
                })

        except json.JSONDecodeError:
            continue

    if notification_contexts:
        print(f"✅ Found {len(notification_contexts)} notification context(s):\n")
        for ctx in notification_contexts:
            print(f"Message ID: {ctx['id']}")
            print(f"Created: {ctx['created_at']}")
            print(f"Content preview: {ctx['content']}\n")
    else:
        print(f"⚠️ No notification contexts found in SQLite")
        print(f"\nAll messages:")
        for msg_id, created_at, message_data in messages:
            try:
                data = json.loads(message_data)
                role = data.get("role", "unknown")
                content_preview = str(data.get("content", ""))[:100]
                print(f"  [{msg_id}] {role}: {content_preview}...")
            except:
                print(f"  [{msg_id}] [parse error]")

    conn.close()

if __name__ == "__main__":
    # Ejemplo de uso
    test_conversation_id = "957701ec-c25f-4783-a8b4-1c4c75965929"

    print("=" * 80)
    print("Testing SQLite Notification Context")
    print("=" * 80)
    print(f"Conversation ID: {test_conversation_id}\n")

    check_notification_context(test_conversation_id)
    print("\n" + "=" * 80)
