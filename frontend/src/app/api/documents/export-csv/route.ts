/**
 * Export Documents as CSV API Route
 *
 * Handles document export with filters for year, months, document types, and movement type
 */

import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@/lib/supabase/server';

interface SalesDocument {
  id: string;
  company_id: string;
  document_type: string;
  folio: number | null;
  issue_date: string;
  recipient_rut: string | null;
  recipient_name: string | null;
  net_amount: number;
  tax_amount: number;
  total_amount: number;
}

interface PurchaseDocument {
  id: string;
  company_id: string;
  document_type: string;
  folio: number | null;
  issue_date: string;
  sender_rut: string | null;
  sender_name: string | null;
  net_amount: number;
  tax_amount: number;
  total_amount: number;
}

interface UnifiedDocument {
  id: string;
  type: 'sale' | 'purchase';
  document_type: string;
  folio: number | null;
  issue_date: string;
  counterparty_rut: string | null;
  counterparty_name: string | null;
  net_amount: number;
  tax_amount: number;
  total_amount: number;
}

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const companyId = searchParams.get('companyId');
    const year = searchParams.get('year');
    const docTypesParam = searchParams.get('docTypes');
    const monthsParam = searchParams.get('months');
    const typeParam = searchParams.get('type'); // 'sale' or 'purchase'

    // Validate required params
    if (!companyId || !year) {
      return NextResponse.json(
        { error: 'companyId and year are required' },
        { status: 400 }
      );
    }

    // Get authenticated user
    const supabase = await createClient();
    const {
      data: { user },
      error: authError,
    } = await supabase.auth.getUser();

    if (authError || !user) {
      return NextResponse.json(
        { error: 'No autenticado' },
        { status: 401 }
      );
    }

    let allDocuments: UnifiedDocument[] = [];

    // Fetch sales documents if not filtered to purchases only
    if (!typeParam || typeParam === 'sale') {
      let salesQuery = supabase
        .from('sales_documents')
        .select('*')
        .eq('company_id', companyId)
        .gte('issue_date', `${year}-01-01`)
        .lte('issue_date', `${year}-12-31`)
        .order('issue_date', { ascending: true });

      // Apply document type filter
      if (docTypesParam) {
        const docTypes = docTypesParam.split(',');
        salesQuery = salesQuery.in('document_type', docTypes);
      }

      const { data: salesData, error: salesError } = await salesQuery;

      if (salesError) {
        console.error('[Export CSV] Sales query error:', salesError);
        return NextResponse.json(
          { error: 'Error al obtener documentos de venta' },
          { status: 500 }
        );
      }

      // Transform sales documents to unified format
      const salesDocuments: UnifiedDocument[] = (salesData || []).map((doc: SalesDocument) => ({
        id: doc.id,
        type: 'sale' as const,
        document_type: doc.document_type,
        folio: doc.folio,
        issue_date: doc.issue_date,
        counterparty_rut: doc.recipient_rut,
        counterparty_name: doc.recipient_name,
        net_amount: doc.net_amount,
        tax_amount: doc.tax_amount,
        total_amount: doc.total_amount,
      }));

      allDocuments = [...allDocuments, ...salesDocuments];
    }

    // Fetch purchase documents if not filtered to sales only
    if (!typeParam || typeParam === 'purchase') {
      let purchasesQuery = supabase
        .from('purchase_documents')
        .select('*')
        .eq('company_id', companyId)
        .gte('issue_date', `${year}-01-01`)
        .lte('issue_date', `${year}-12-31`)
        .order('issue_date', { ascending: true });

      // Apply document type filter
      if (docTypesParam) {
        const docTypes = docTypesParam.split(',');
        purchasesQuery = purchasesQuery.in('document_type', docTypes);
      }

      const { data: purchasesData, error: purchasesError } = await purchasesQuery;

      if (purchasesError) {
        console.error('[Export CSV] Purchases query error:', purchasesError);
        return NextResponse.json(
          { error: 'Error al obtener documentos de compra' },
          { status: 500 }
        );
      }

      // Transform purchase documents to unified format
      const purchaseDocuments: UnifiedDocument[] = (purchasesData || []).map((doc: PurchaseDocument) => ({
        id: doc.id,
        type: 'purchase' as const,
        document_type: doc.document_type,
        folio: doc.folio,
        issue_date: doc.issue_date,
        counterparty_rut: doc.sender_rut,
        counterparty_name: doc.sender_name,
        net_amount: doc.net_amount,
        tax_amount: doc.tax_amount,
        total_amount: doc.total_amount,
      }));

      allDocuments = [...allDocuments, ...purchaseDocuments];
    }

    // Sort by issue date
    allDocuments.sort((a, b) => new Date(a.issue_date).getTime() - new Date(b.issue_date).getTime());

    // Apply month filter in memory if specified
    let filteredDocs = allDocuments;
    if (monthsParam) {
      const months = monthsParam.split(',').map(m => parseInt(m));
      filteredDocs = filteredDocs.filter(doc => {
        const docMonth = new Date(doc.issue_date).getMonth() + 1; // JS months are 0-indexed
        return months.includes(docMonth);
      });
    }

    // Generate CSV
    const headers = [
      'Fecha',
      'Tipo',
      'Tipo Documento',
      'Folio',
      'Contraparte',
      'RUT Contraparte',
      'Monto Neto',
      'IVA',
      'Monto Total',
    ];

    const rows = filteredDocs.map(doc => [
      doc.issue_date,
      doc.type === 'sale' ? 'Venta' : 'Compra',
      doc.document_type,
      doc.folio?.toString() || '',
      doc.counterparty_name || 'Sin nombre',
      doc.counterparty_rut || '',
      doc.net_amount,
      doc.tax_amount,
      doc.total_amount,
    ]);

    // Create CSV content with proper escaping
    const csvContent = [
      headers.join(','),
      ...rows.map(row =>
        row.map(cell => {
          const cellStr = String(cell);
          // Escape commas, quotes, and newlines
          if (cellStr.includes(',') || cellStr.includes('"') || cellStr.includes('\n')) {
            return `"${cellStr.replace(/"/g, '""')}"`;
          }
          return cellStr;
        }).join(',')
      )
    ].join('\n');

    // Add BOM for UTF-8 encoding (Excel compatibility)
    const bom = '\uFEFF';
    const csvWithBom = bom + csvContent;

    // Return CSV as downloadable file
    return new NextResponse(csvWithBom, {
      status: 200,
      headers: {
        'Content-Type': 'text/csv; charset=utf-8',
        'Content-Disposition': `attachment; filename="movimientos_${year}.csv"`,
      },
    });
  } catch (error) {
    console.error('[Export CSV] Unexpected error:', error);
    return NextResponse.json(
      {
        error:
          error instanceof Error ? error.message : 'Error interno del servidor',
      },
      { status: 500 }
    );
  }
}
