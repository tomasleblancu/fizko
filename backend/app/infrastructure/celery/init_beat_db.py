"""
Initialize Celery Beat database tables.

This script creates the necessary tables for sqlalchemy-celery-beat
in the specified schema. Run this once before starting celery-beat.

Usage:
    python -m app.infrastructure.celery.init_beat_db
"""
import os
from sqlalchemy import create_engine, text
from sqlalchemy_celery_beat.models import ModelBase
from sqlalchemy_celery_beat.session import SessionManager

def init_beat_database():
    """Create Celery Beat tables in the database."""
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        print("❌ DATABASE_URL not set")
        return False

    print(f"📊 Initializing Celery Beat database...")
    print(f"   Database: {database_url.split('@')[1] if '@' in database_url else 'hidden'}")

    try:
        # Create engine
        engine = create_engine(database_url)

        # Create schema if it doesn't exist
        schema = "celery_schema"
        with engine.connect() as conn:
            conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
            conn.commit()
            print(f"✅ Schema '{schema}' ready")

        # Create session manager and prepare models
        session_manager = SessionManager()
        engine, Session = session_manager.create_session(
            database_url,
            schema=schema
        )

        # Create all tables
        session_manager.prepare_models(engine, schema=schema)
        print(f"✅ Tables created in schema '{schema}'")

        # List created tables
        with engine.connect() as conn:
            result = conn.execute(text(f"""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = '{schema}'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result]
            print(f"\n📋 Created tables ({len(tables)}):")
            for table in tables:
                print(f"   - {table}")

        return True

    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    success = init_beat_database()
    exit(0 if success else 1)
