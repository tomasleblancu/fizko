"""
Test script to verify accounting_date logic in parsers
"""

from app.services.sii.parsers import parse_purchase_document, parse_sales_document

# Test data for DIN document (should use issue_date)
din_doc = {
    'detNroDoc': 123456,
    'detRutDoc': '12345678-9',
    'detRznSoc': 'Proveedor Test',
    'detFchDoc': '2025-01-15',
    'detFecRecepcion': '2025-01-20',  # Different from issue_date
    'detMntNeto': 100000,
    'detMntIVA': 19000,
    'detMntTotal': 119000
}

# Test data for regular purchase (should use reception_date)
factura_doc = {
    'detNroDoc': 789012,
    'detRutDoc': '87654321-0',
    'detRznSoc': 'Otro Proveedor',
    'detFchDoc': '2025-01-15',
    'detFecRecepcion': '2025-01-20',  # Different from issue_date
    'detMntNeto': 200000,
    'detMntIVA': 38000,
    'detMntTotal': 238000
}

# Test data for sales document (should use issue_date)
sales_doc = {
    'detNroDoc': 456789,
    'detRutDoc': '11111111-1',
    'detRznSoc': 'Cliente Test',
    'detFchDoc': '2025-01-15',
    'detFecRecepcion': '2025-01-20',  # Different from issue_date
    'detMntNeto': 300000,
    'detMntIVA': 57000,
    'detMntTotal': 357000
}

company_id = 'test-company-id'

print("\n" + "="*80)
print("TESTING ACCOUNTING_DATE LOGIC")
print("="*80)

# Test DIN document
print("\n1. DIN Document (tipo_doc=914):")
print("-" * 80)
result_din = parse_purchase_document(company_id, din_doc, '914', 'REGISTRO')
print(f"   Document Type: {result_din['document_type']}")
print(f"   Issue Date: {result_din['issue_date']}")
print(f"   Reception Date: {result_din['reception_date']}")
print(f"   Accounting Date: {result_din['accounting_date']}")
print(f"   ✅ PASS" if result_din['accounting_date'] == result_din['issue_date'] else f"   ❌ FAIL - Expected issue_date")

# Test regular purchase (Factura)
print("\n2. Purchase Invoice (tipo_doc=33):")
print("-" * 80)
result_factura = parse_purchase_document(company_id, factura_doc, '33', 'REGISTRO')
print(f"   Document Type: {result_factura['document_type']}")
print(f"   Issue Date: {result_factura['issue_date']}")
print(f"   Reception Date: {result_factura['reception_date']}")
print(f"   Accounting Date: {result_factura['accounting_date']}")
print(f"   ✅ PASS" if result_factura['accounting_date'] == result_factura['reception_date'] else f"   ❌ FAIL - Expected reception_date")

# Test sales document
print("\n3. Sales Invoice (tipo_doc=33):")
print("-" * 80)
result_sales = parse_sales_document(company_id, sales_doc, '33')
print(f"   Document Type: {result_sales['document_type']}")
print(f"   Issue Date: {result_sales['issue_date']}")
print(f"   Reception Date: {result_sales['reception_date']}")
print(f"   Accounting Date: {result_sales['accounting_date']}")
print(f"   ✅ PASS" if result_sales['accounting_date'] == result_sales['issue_date'] else f"   ❌ FAIL - Expected issue_date")

print("\n" + "="*80)
print("TEST SUMMARY")
print("="*80)

all_pass = (
    result_din['accounting_date'] == result_din['issue_date'] and
    result_factura['accounting_date'] == result_factura['reception_date'] and
    result_sales['accounting_date'] == result_sales['issue_date']
)

if all_pass:
    print("✅ ALL TESTS PASSED")
else:
    print("❌ SOME TESTS FAILED")

print("="*80 + "\n")
