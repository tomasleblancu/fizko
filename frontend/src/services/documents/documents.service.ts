import { createServiceClient } from '@/lib/supabase/server'
import type { SalesDocument, PurchaseDocument, DocumentWithType } from '@/types/database'

export interface ListDocumentsParams {
  companyId: string
}

export interface ListDocumentsResponse {
  data: DocumentWithType[]
}

export class DocumentsService {
  /**
   * List all sales and purchase documents for a company
   * Returns a unified array sorted by issue_date (most recent first)
   */
  static async list(params: ListDocumentsParams): Promise<ListDocumentsResponse> {
    const supabase = createServiceClient()

    // Fetch ALL sales documents
    const { data: salesData, error: salesError } = await supabase
      .from('sales_documents')
      .select('*')
      .eq('company_id', params.companyId)
      .order('issue_date', { ascending: false })

    if (salesError) {
      console.error('[DocumentsService] Error fetching sales documents:', salesError)
      throw new Error(`Failed to fetch sales documents: ${salesError.message}`)
    }

    // Fetch ALL purchase documents
    const { data: purchasesData, error: purchasesError } = await supabase
      .from('purchase_documents')
      .select('*')
      .eq('company_id', params.companyId)
      .order('issue_date', { ascending: false })

    if (purchasesError) {
      console.error('[DocumentsService] Error fetching purchase documents:', purchasesError)
      throw new Error(`Failed to fetch purchase documents: ${purchasesError.message}`)
    }

    // Transform sales documents to unified format
    const salesDocuments: DocumentWithType[] = (salesData || []).map((doc: SalesDocument) => ({
      ...doc,
      type: 'sale' as const,
      counterparty_rut: doc.recipient_rut,
      counterparty_name: doc.recipient_name,
    }))

    // Transform purchase documents to unified format
    const purchaseDocuments: DocumentWithType[] = (purchasesData || []).map((doc: PurchaseDocument) => ({
      ...doc,
      type: 'purchase' as const,
      counterparty_rut: doc.sender_rut,
      counterparty_name: doc.sender_name,
    }))

    // Combine and sort by issue_date (timestamp comparison for proper sorting)
    const getTimestamp = (dateStr: string) => new Date(dateStr).getTime()
    const allDocuments = [...salesDocuments, ...purchaseDocuments].sort(
      (a, b) => getTimestamp(b.issue_date) - getTimestamp(a.issue_date)
    )

    return { data: allDocuments }
  }
}
