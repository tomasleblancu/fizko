/**
 * Database query functions for tax documents
 */

import type { SupabaseClient } from "jsr:@supabase/supabase-js@2";
import type { Document, GeneratedForm29, Form29SiiDownload } from "./types.ts";
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

/**
 * Get generated Form29 for the period
 *
 * @param supabase - Supabase client
 * @param companyId - Company UUID
 * @param periodYear - Period year
 * @param periodMonth - Period month
 * @returns Generated Form29 or null
 */
export async function getGeneratedF29(
  supabase: SupabaseClient,
  companyId: string,
  periodYear: number,
  periodMonth: number
): Promise<GeneratedForm29 | null> {
  const { data, error } = await supabase
    .from("form29")
    .select("*")
    .eq("company_id", companyId)
    .eq("period_year", periodYear)
    .eq("period_month", periodMonth)
    .neq("status", "cancelled")
    .order("revision_number", { ascending: false })
    .order("created_at", { ascending: false })
    .limit(1);

  if (error || !data || data.length === 0) {
    return null;
  }

  const form = data[0];

  return {
    id: form.id,
    company_id: form.company_id,
    period_year: form.period_year,
    period_month: form.period_month,
    total_sales: form.total_sales,
    taxable_sales: form.taxable_sales,
    exempt_sales: form.exempt_sales,
    sales_tax: form.sales_tax,
    total_purchases: form.total_purchases,
    taxable_purchases: form.taxable_purchases,
    purchases_tax: form.purchases_tax,
    iva_to_pay: form.iva_to_pay,
    iva_credit: form.iva_credit,
    net_iva: form.net_iva,
    status: form.status,
    extra_data: form.extra_data as Record<string, any> | null,
    submitted_at: form.submission_date,
    created_at: form.created_at,
    updated_at: form.updated_at,
  };
}

/**
 * Get Form29 SII Download for the period
 * Returns the "Vigente" (current) F29 from SII for the specified period
 *
 * @param supabase - Supabase client
 * @param companyId - Company UUID
 * @param periodYear - Period year
 * @param periodMonth - Period month
 * @returns Form29 SII Download or null
 */
export async function getForm29SiiDownload(
  supabase: SupabaseClient,
  companyId: string,
  periodYear: number,
  periodMonth: number
): Promise<Form29SiiDownload | null> {
  const { data, error } = await supabase
    .from("form29_sii_downloads")
    .select("*")
    .eq("company_id", companyId)
    .eq("period_year", periodYear)
    .eq("period_month", periodMonth)
    .eq("status", "Vigente")
    .order("created_at", { ascending: false })
    .limit(1);

  if (error || !data || data.length === 0) {
    return null;
  }

  const download = data[0];

  return {
    id: download.id,
    company_id: download.company_id,
    form29_id: download.form29_id,
    sii_folio: download.sii_folio,
    sii_id_interno: download.sii_id_interno,
    period_year: download.period_year,
    period_month: download.period_month,
    period_display: download.period_display,
    contributor_rut: download.contributor_rut,
    submission_date: download.submission_date,
    status: download.status,
    amount_cents: download.amount_cents,
    pdf_storage_url: download.pdf_storage_url,
    pdf_download_status: download.pdf_download_status,
    pdf_download_error: download.pdf_download_error,
    pdf_downloaded_at: download.pdf_downloaded_at,
    extra_data: download.extra_data as Record<string, any> | null,
    created_at: download.created_at,
    updated_at: download.updated_at,
  };
}
