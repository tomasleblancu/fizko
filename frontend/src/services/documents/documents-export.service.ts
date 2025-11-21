/**
 * Documents Export Service
 *
 * Handles document export operations:
 * - Export sales and purchase documents to CSV
 * - Handles pagination to avoid 1000-row Supabase limit
 * - Unified document format
 * - CSV generation with UTF-8 BOM for Excel compatibility
 */

import { createServiceClient } from '@/lib/supabase/server';
import { getTimestamp, getMonth } from '@/shared/lib/date-utils';

interface UnifiedDocument {
  id: string;
  type: 'sale' | 'purchase';
  document_type: string;
  folio: number | null;
  issue_date: string;
  reception_date: string | null;
  accounting_date: string | null;
  counterparty_rut: string | null;
  counterparty_name: string | null;
  net_amount: number;
  tax_amount: number;
  total_amount: number;
}

export interface ExportDocumentsParams {
  companyId: string;
  year: string;
  docTypes?: string[]; // Array of document type codes
  months?: number[]; // Array of month numbers (1-12)
  type?: 'sale' | 'purchase'; // Filter by movement type
}

export class DocumentsExportService {
  /**
   * Export documents to CSV format
   *
   * Fetches all documents with pagination to avoid limits,
   * filters by parameters, and generates CSV with UTF-8 BOM.
   *
   * @param params - Export parameters
   * @returns CSV content as string with BOM
   */
  static async exportToCSV(params: ExportDocumentsParams): Promise<string> {
    console.log(`[Documents Export Service] Exporting documents for company ${params.companyId}, year ${params.year}`);

    let allDocuments: UnifiedDocument[] = [];

    // Fetch sales documents if not filtered to purchases only
    if (!params.type || params.type === 'sale') {
      const salesDocs = await this.fetchSalesDocuments(params);
      allDocuments = [...allDocuments, ...salesDocs];
    }

    // Fetch purchase documents if not filtered to sales only
    if (!params.type || params.type === 'purchase') {
      const purchaseDocs = await this.fetchPurchaseDocuments(params);
      allDocuments = [...allDocuments, ...purchaseDocs];
    }

    // Sort by issue date
    allDocuments.sort((a, b) => getTimestamp(a.issue_date) - getTimestamp(b.issue_date));

    // Apply month filter in memory if specified
    let filteredDocs = allDocuments;
    if (params.months && params.months.length > 0) {
      filteredDocs = filteredDocs.filter(doc => {
        const docMonth = getMonth(doc.issue_date);
        return params.months!.includes(docMonth);
      });
    }

    console.log(`[Documents Export Service] Exporting ${filteredDocs.length} documents`);

    // Generate CSV
    return this.generateCSV(filteredDocs, params.year);
  }

  /**
   * Fetch all sales documents with pagination
   */
  private static async fetchSalesDocuments(
    params: ExportDocumentsParams
  ): Promise<UnifiedDocument[]> {
    const supabase = createServiceClient();
    let salesData: any[] = [];
    let page = 0;
    const pageSize = 1000;
    let hasMore = true;

    while (hasMore) {
      let salesQuery = supabase
        .from('sales_documents')
        .select('*')
        .eq('company_id', params.companyId)
        .gte('issue_date', `${params.year}-01-01`)
        .lte('issue_date', `${params.year}-12-31`)
        .order('issue_date', { ascending: true })
        .range(page * pageSize, (page + 1) * pageSize - 1);

      // Apply document type filter
      if (params.docTypes && params.docTypes.length > 0) {
        salesQuery = salesQuery.in('document_type', params.docTypes);
      }

      const { data: pageData, error: salesError } = await salesQuery;

      if (salesError) {
        console.error('[Documents Export Service] Sales query error:', salesError);
        throw new Error(`Error fetching sales documents: ${salesError.message}`);
      }

      if (pageData && pageData.length > 0) {
        salesData = [...salesData, ...pageData];
        hasMore = pageData.length === pageSize;
        page++;
      } else {
        hasMore = false;
      }
    }

    // Transform sales documents to unified format
    return salesData.map((doc: any): UnifiedDocument => ({
      id: doc.id,
      type: 'sale',
      document_type: doc.document_type,
      folio: doc.folio,
      issue_date: doc.issue_date,
      reception_date: doc.reception_date || null,
      accounting_date: doc.accounting_date || null,
      counterparty_rut: doc.recipient_rut,
      counterparty_name: doc.recipient_name,
      net_amount: Number(doc.net_amount) || 0,
      tax_amount: Number(doc.tax_amount) || 0,
      total_amount: Number(doc.total_amount) || 0,
    }));
  }

  /**
   * Fetch all purchase documents with pagination
   */
  private static async fetchPurchaseDocuments(
    params: ExportDocumentsParams
  ): Promise<UnifiedDocument[]> {
    const supabase = createServiceClient();
    let purchasesData: any[] = [];
    let page = 0;
    const pageSize = 1000;
    let hasMore = true;

    while (hasMore) {
      let purchasesQuery = supabase
        .from('purchase_documents')
        .select('*')
        .eq('company_id', params.companyId)
        .gte('issue_date', `${params.year}-01-01`)
        .lte('issue_date', `${params.year}-12-31`)
        .order('issue_date', { ascending: true })
        .range(page * pageSize, (page + 1) * pageSize - 1);

      // Apply document type filter
      if (params.docTypes && params.docTypes.length > 0) {
        purchasesQuery = purchasesQuery.in('document_type', params.docTypes);
      }

      const { data: pageData, error: purchasesError } = await purchasesQuery;

      if (purchasesError) {
        console.error('[Documents Export Service] Purchases query error:', purchasesError);
        throw new Error(`Error fetching purchase documents: ${purchasesError.message}`);
      }

      if (pageData && pageData.length > 0) {
        purchasesData = [...purchasesData, ...pageData];
        hasMore = pageData.length === pageSize;
        page++;
      } else {
        hasMore = false;
      }
    }

    // Transform purchase documents to unified format
    return purchasesData.map((doc: any): UnifiedDocument => ({
      id: doc.id,
      type: 'purchase',
      document_type: doc.document_type,
      folio: doc.folio,
      issue_date: doc.issue_date,
      reception_date: doc.reception_date || null,
      accounting_date: doc.accounting_date || null,
      counterparty_rut: doc.sender_rut,
      counterparty_name: doc.sender_name,
      net_amount: Number(doc.net_amount) || 0,
      tax_amount: Number(doc.tax_amount) || 0,
      total_amount: Number(doc.total_amount) || 0,
    }));
  }

  /**
   * Generate CSV content from documents
   *
   * Includes UTF-8 BOM for Excel compatibility
   */
  private static generateCSV(documents: UnifiedDocument[], year: string): string {
    const headers = [
      'Fecha',
      'Fecha Recepción',
      'Fecha Contable',
      'Tipo',
      'Tipo Documento',
      'Folio',
      'Contraparte',
      'RUT Contraparte',
      'Monto Neto',
      'IVA',
      'Monto Total',
    ];

    const rows = documents.map(doc => [
      doc.issue_date,
      doc.reception_date || '',
      doc.accounting_date || '',
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
    return bom + csvContent;
  }
}
