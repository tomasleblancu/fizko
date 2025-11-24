/**
 * Database query functions for tax documents
 */

import type { SupabaseClient } from "jsr:@supabase/supabase-js@2";
import type { Document } from "./types.ts";
import { calculatePreviousMonth } from "./helpers.ts";

/**
 * Get documents from sales or purchase tables with filters
 *
 * @param supabase - Supabase client
 * @param table - Table name (sales_documents or purchase_documents)
 * @param companyId - Company UUID
 * @param documentTypes - Array of document type codes to filter
 * @param periodStart - Period start date (YYYY-MM-DD) or null for all dates
 * @param periodEnd - Period end date (YYYY-MM-DD) or null for all dates
 * @param fields - Fields to select from the table
 * @returns Array of documents
 */
export async function getDocuments(
  supabase: SupabaseClient,
  table: string,
  companyId: string,
  documentTypes: string[],
  periodStart: string | null,
  periodEnd: string | null,
  fields: string[]
): Promise<Document[]> {
  let query = supabase
    .from(table)
    .select(fields.join(", "))
    .eq("company_id", companyId)
    .in("document_type", documentTypes);

  if (periodStart && periodEnd) {
    query = query
      .gte("accounting_date", periodStart)
      .lt("accounting_date", periodEnd);
  }

  const { data, error } = await query;

  if (error) {
    console.error(`Error fetching ${table}:`, error);
    return [];
  }

  return data || [];
}

/**
 * Get previous month credit from F29 forms
 * Checks both form29 drafts and form29_sii_downloads
 *
 * @param supabase - Supabase client
 * @param companyId - Company UUID
 * @param periodStart - Current period start date (YYYY-MM-DD)
 * @returns Previous month credit amount (0 if not found)
 */
export async function getPreviousMonthCredit(
  supabase: SupabaseClient,
  companyId: string,
  periodStart: string | null
): Promise<number> {
  if (!periodStart) return 0;

  const [year, month] = calculatePreviousMonth(periodStart);

  // Check form29 drafts first
  const { data: draftData, error: draftError } = await supabase
    .from("form29")
    .select("net_iva")
    .eq("company_id", companyId)
    .eq("period_year", year)
    .eq("period_month", month)
    .in("status", ["saved", "paid"])
    .order("created_at", { ascending: false })
    .limit(1);

  if (!draftError && draftData && draftData.length > 0) {
    const netIva = draftData[0].net_iva;
    if (netIva !== null && netIva < 0) {
      return Math.abs(netIva);
    }
  }

  // Fallback to form29_sii_downloads
  const { data: siiData, error: siiError } = await supabase
    .from("form29_sii_downloads")
    .select("extra_data")
    .eq("company_id", companyId)
    .eq("period_year", year)
    .eq("period_month", month)
    .eq("status", "Vigente")
    .order("created_at", { ascending: false })
    .limit(1);

  if (!siiError && siiData && siiData.length > 0) {
    const extraData = siiData[0].extra_data;
    // Code 077 in F29 is "Remanente de crédito fiscal del mes anterior"
    if (extraData?.f29_data?.codes?.["077"]?.value !== undefined) {
      return parseFloat(extraData.f29_data.codes["077"].value);
    }
  }

  return 0;
}

/**
 * Get retención (withholding) from honorarios receipts
 *
 * @param supabase - Supabase client
 * @param companyId - Company UUID
 * @param periodStart - Period start date (YYYY-MM-DD) or null for all dates
 * @param periodEnd - Period end date (YYYY-MM-DD) or null for all dates
 * @returns Total retención amount
 */
export async function getRetencion(
  supabase: SupabaseClient,
  companyId: string,
  periodStart: string | null,
  periodEnd: string | null
): Promise<number> {
  let query = supabase
    .from("honorarios_receipts")
    .select("recipient_retention")
    .eq("company_id", companyId)
    .eq("receipt_type", "received");

  if (periodStart && periodEnd) {
    query = query.gte("issue_date", periodStart).lt("issue_date", periodEnd);
  }

  const { data, error } = await query;

  if (error || !data) {
    console.error("Error fetching retención:", error);
    return 0;
  }

  const total = data.reduce(
    (sum: number, receipt: any) => sum + (receipt.recipient_retention || 0),
    0
  );

  return total;
}

/**
 * Get reverse charge withholding (código 46)
 * Document type code 46 is "Facturas de compra con retención total"
 *
 * @param supabase - Supabase client
 * @param companyId - Company UUID
 * @param periodStart - Period start date (YYYY-MM-DD) or null for all dates
 * @param periodEnd - Period end date (YYYY-MM-DD) or null for all dates
 * @returns Total reverse charge withholding amount
 */
export async function getReverseChargeWithholding(
  supabase: SupabaseClient,
  companyId: string,
  periodStart: string | null,
  periodEnd: string | null
): Promise<number> {
  let query = supabase
    .from("purchase_documents")
    .select("tax_amount")
    .eq("company_id", companyId)
    .eq("document_type_code", "46");

  if (periodStart && periodEnd) {
    query = query
      .gte("accounting_date", periodStart)
      .lt("accounting_date", periodEnd);
  }

  const { data, error } = await query;

  if (error || !data) {
    console.error("Error fetching reverse charge:", error);
    return 0;
  }

  const total = data.reduce(
    (sum: number, doc: any) => sum + (doc.tax_amount || 0),
    0
  );

  return total;
}
