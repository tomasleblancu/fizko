"""
WhatsApp session cleanup tasks.

Maneja la limpieza de sesiones SQLite antiguas para reducir el consumo de contexto
en conversaciones de WhatsApp.
"""
import logging
import sqlite3
from datetime import timedelta
from pathlib import Path

from app.infrastructure.celery import celery_app
from app.utils import format_for_sqlite, now

logger = logging.getLogger(__name__)


@celery_app.task(name="whatsapp.cleanup_old_sessions")
def cleanup_old_sessions(threshold_hours: int = 1) -> dict:
    """
    Limpia sesiones de WhatsApp que no han tenido actividad en las últimas N horas.

    Esta tarea:
    1. Lee el archivo SQLite de sesiones de WhatsApp
    2. Identifica sesiones con updated_at > threshold_hours
    3. Elimina todos los mensajes asociados a esas sesiones
    4. Elimina las sesiones antiguas

    Args:
        threshold_hours: Horas de inactividad antes de limpiar (default: 1)

    Returns:
        dict: Resultado con estadísticas de limpieza
            {
                "success": bool,
                "sessions_deleted": int,
                "messages_deleted": int,
                "threshold_hours": int,
                "error": str (opcional)
            }
    """
    try:
        # Path al archivo SQLite de sesiones de WhatsApp
        # __file__ está en: backend/app/infrastructure/celery/tasks/whatsapp/cleanup.py
        # Queremos: backend/app/sessions/whatsapp_agent_sessions.db
        # Subimos 5 niveles: whatsapp/ -> tasks/ -> celery/ -> infrastructure/ -> app/
        sessions_db_path = Path(__file__).parent.parent.parent.parent.parent / "sessions" / "whatsapp_agent_sessions.db"

        if not sessions_db_path.exists():
            logger.warning(f"⚠️ Sessions database not found at {sessions_db_path}")
            return {
                "success": False,
                "sessions_deleted": 0,
                "messages_deleted": 0,
                "threshold_hours": threshold_hours,
                "error": "Database file not found"
            }

        logger.info(f"🧹 Starting session cleanup (threshold: {threshold_hours}h)")
        logger.info(f"   Database: {sessions_db_path}")

        # Conectar a SQLite
        conn = sqlite3.connect(str(sessions_db_path))
        cursor = conn.cursor()

        # Calcular el timestamp límite
        # IMPORTANTE: SQLite guarda timestamps en formato local sin timezone
        # Usamos la timezone configurada de la aplicación (America/Santiago)
        current_time = now()
        threshold_time = current_time - timedelta(hours=threshold_hours)
        # Formato SQLite: 'YYYY-MM-DD HH:MM:SS' (sin timezone)
        threshold_str = format_for_sqlite(threshold_time)
        current_str = format_for_sqlite(current_time)

        logger.info(f"   Cutoff time: {threshold_str} (America/Santiago)")
        logger.info(f"   Current time: {current_str} (America/Santiago)")

        # 1. Encontrar sesiones antiguas
        cursor.execute(
            """
            SELECT session_id, updated_at
            FROM agent_sessions
            WHERE updated_at < ?
            """,
            (threshold_str,)
        )
        old_sessions = cursor.fetchall()

        if not old_sessions:
            logger.info("✅ No old sessions to clean up")
            conn.close()
            return {
                "success": True,
                "sessions_deleted": 0,
                "messages_deleted": 0,
                "threshold_hours": threshold_hours,
            }

        session_ids = [s[0] for s in old_sessions]
        logger.info(f"📊 Found {len(session_ids)} old session(s) to delete")

        # 2. Contar mensajes que se van a eliminar (para stats)
        placeholders = ",".join("?" * len(session_ids))
        cursor.execute(
            f"""
            SELECT COUNT(*)
            FROM agent_messages
            WHERE session_id IN ({placeholders})
            """,
            session_ids
        )
        messages_count = cursor.fetchone()[0]

        logger.info(f"📊 Will delete {messages_count} message(s)")

        # 3. Eliminar mensajes (CASCADE debería hacerlo, pero lo hacemos explícito)
        cursor.execute(
            f"""
            DELETE FROM agent_messages
            WHERE session_id IN ({placeholders})
            """,
            session_ids
        )

        # 4. Eliminar sesiones
        cursor.execute(
            f"""
            DELETE FROM agent_sessions
            WHERE session_id IN ({placeholders})
            """,
            session_ids
        )

        # Commit y cerrar
        conn.commit()
        conn.close()

        logger.info(f"✅ Cleanup completed:")
        logger.info(f"   Sessions deleted: {len(session_ids)}")
        logger.info(f"   Messages deleted: {messages_count}")

        return {
            "success": True,
            "sessions_deleted": len(session_ids),
            "messages_deleted": messages_count,
            "threshold_hours": threshold_hours,
        }

    except Exception as e:
        logger.error(f"❌ Error cleaning up sessions: {e}", exc_info=True)
        return {
            "success": False,
            "sessions_deleted": 0,
            "messages_deleted": 0,
            "threshold_hours": threshold_hours,
            "error": str(e)
        }
