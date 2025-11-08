"""
Script para limpiar memorias huérfanas en Mem0.

Cuando se borran memorias de company_brain pero no de Mem0,
quedan memorias duplicadas. Este script busca y borra las huérfanas.
"""
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

async def clean_mem0_orphans():
    """Clean orphan memories from Mem0."""
    from app.config.database import get_db
    from app.db.models import CompanyBrain
    from app.infrastructure.mem0_client import get_mem0_client
    from sqlalchemy import select

    company_id = "628771e2-6912-4e7f-8bb9-ff69f7d334e3"
    company_entity_id = f"company_{company_id}"

    async with get_db() as db:
        # Get all subscription memories from DB
        result = await db.execute(
            select(CompanyBrain).where(
                CompanyBrain.company_id == company_id,
                CompanyBrain.slug.like("company_subscription%")
            )
        )
        db_memories = result.scalars().all()

        print(f"📊 Memorias en company_brain:")
        db_memory_ids = set()
        for mem in db_memories:
            print(f"  - {mem.slug}: {mem.memory_id}")
            print(f"    Content: {mem.content[:80]}...")
            db_memory_ids.add(mem.memory_id)

        print(f"\n🔍 Buscando memorias en Mem0...")

        # Get all memories from Mem0
        mem0 = get_mem0_client()

        try:
            # Get all memories for this company
            mem0_memories = await mem0.get_all(user_id=company_entity_id)

            print(f"\n📊 Memorias en Mem0 ({len(mem0_memories)} total):")

            orphans = []
            for mem in mem0_memories:
                mem_id = mem.get("id")
                content = mem.get("memory", "")
                metadata = mem.get("metadata", {})

                is_subscription = (
                    "subscription" in metadata.get("slug", "").lower() or
                    "suscripción" in content.lower() or
                    "plan" in content.lower()
                )

                if is_subscription:
                    is_orphan = mem_id not in db_memory_ids
                    status = "🔴 HUÉRFANA" if is_orphan else "✅ OK"
                    print(f"  {status} ID: {mem_id}")
                    print(f"    Content: {content[:80]}...")
                    print(f"    Slug: {metadata.get('slug', 'N/A')}")

                    if is_orphan:
                        orphans.append(mem_id)

            if orphans:
                print(f"\n⚠️  Encontradas {len(orphans)} memorias huérfanas")
                print("¿Borrar memorias huérfanas? (y/n): ", end="")
                response = input().strip().lower()

                if response == "y":
                    for mem_id in orphans:
                        print(f"  🗑️  Borrando {mem_id}...")
                        await mem0.delete(memory_id=mem_id)
                    print(f"✅ {len(orphans)} memorias huérfanas borradas")
                else:
                    print("❌ Cancelado")
            else:
                print("\n✅ No hay memorias huérfanas")

        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(clean_mem0_orphans())
