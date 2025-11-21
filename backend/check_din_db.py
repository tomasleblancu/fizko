"""
Quick check for DIN in database
"""
import asyncio
from app.config.supabase import get_supabase_client


async def check_din():
    """Check if DIN documents are in database"""
    supabase = get_supabase_client()

    # Query directly
    response = supabase._client.table('tax_documents').select('*').eq(
        'company_id', 'ebb912c8-c444-4e9d-8cf6-ec4b73ca00e7'
    ).eq('period', '202510').eq('document_type', 'declaracion_ingreso').execute()

    docs = response.data

    print(f"\n{'='*60}")
    print(f"DIN Documents in Database (October 2025)")
    print(f"{'='*60}")
    print(f"Total: {len(docs)} documents\n")

    if docs:
        for doc in docs:
            print(f"Folio: {doc.get('folio')}")
            print(f"  Tipo: {doc.get('document_type')}")
            print(f"  Emisor: {doc.get('sender_name')} ({doc.get('sender_rut')})")
            print(f"  Fecha: {doc.get('document_date')}")
            print(f"  Neto: ${doc.get('net_amount'):,.0f}")
            print(f"  IVA: ${doc.get('tax_amount'):,.0f}")
            print(f"  Total: ${doc.get('total_amount'):,.0f}")
            print()
    else:
        print("❌ No DIN documents found")

        # Check if there are ANY documents for this company/period
        all_docs = supabase._client.table('tax_documents').select('document_type').eq(
            'company_id', 'ebb912c8-c444-4e9d-8cf6-ec4b73ca00e7'
        ).eq('period', '202510').execute()

        print(f"\nOther document types in October 2025: {len(all_docs.data)} documents")

        # Group by type
        types = {}
        for doc in all_docs.data:
            dt = doc.get('document_type', 'unknown')
            types[dt] = types.get(dt, 0) + 1

        for dt, count in sorted(types.items()):
            print(f"  - {dt}: {count}")


if __name__ == "__main__":
    asyncio.run(check_din())
