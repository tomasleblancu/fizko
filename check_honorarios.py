#!/usr/bin/env python3
"""
Check honorarios receipt data in database.
"""
from dotenv import load_dotenv
load_dotenv("backend-v2/.env")

from supabase import create_client
import os

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_KEY")

client = create_client(supabase_url, supabase_key)

# Query honorarios receipt
response = client.table("honorarios_receipts").select("*").eq("folio", 15).execute()

if response.data:
    receipt = response.data[0]
    print("=" * 60)
    print("📋 Boleta de Honorarios #15")
    print("=" * 60)
    print(f"Receipt Type: {receipt.get('receipt_type')}")
    print(f"Issuer RUT: {receipt.get('issuer_rut')}")
    print(f"Issuer Name: {receipt.get('issuer_name')}")
    print(f"Recipient RUT: {receipt.get('recipient_rut')}")
    print(f"Recipient Name: {receipt.get('recipient_name')}")
    print(f"Gross Amount: ${receipt.get('gross_amount'):,.0f}")
    print(f"Issuer Retention: ${receipt.get('issuer_retention'):,.0f}")
    print(f"Recipient Retention: ${receipt.get('recipient_retention'):,.0f}")
    print(f"Net Amount: ${receipt.get('net_amount'):,.0f}")
    print(f"Status: {receipt.get('status')}")
    print(f"Issue Date: {receipt.get('issue_date')}")
    print("=" * 60)
else:
    print("❌ No receipt found with folio 15")
