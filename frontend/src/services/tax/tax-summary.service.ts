/**
 * Tax Summary Service
 *
 * Handles tax summary calculations including:
 * - Sales and purchases aggregation
 * - IVA calculations (collected vs paid)
 * - PPM (Pagos Provisionales Mensuales) calculations
 * - Honorarios retention calculations
 * - Previous month credit retrieval
 * - Monthly tax formula for Chilean tax system
 */

import { createServiceClient } from '@/lib/supabase/server';
import type { Database } from '@/types/database';
import type { TaxSummary } from '@/types/tax';
import {
  SALES_POSITIVE_TYPES,
  SALES_CREDIT_TYPES,
  PURCHASES_POSITIVE_TYPES,
  PURCHASES_CREDIT_TYPES,
} from '@/types/tax';

type SalesDocumentRow = { total_amount: number; tax_amount: number; overdue_iva_credit: number; net_amount: number };
type PurchaseDocumentRow = { total_amount: number; tax_amount: number; overdue_iva_credit: number };
type HonorariosReceiptRow = { recipient_retention: number };
type Form29Row = Database['public']['Tables']['form29']['Row'];
type Form29SiiDownloadRow = Database['public']['Tables']['form29_sii_downloads']['Row'];

export class TaxSummaryService {
  /**
   * Calculate comprehensive tax summary for a company and period
   *
   * @param companyId - Company UUID
   * @param period - Period in YYYY-MM format (optional, defaults to current month)
   * @returns Complete tax summary with all calculations
   */
  static async calculateSummary(
    companyId: string,
    period?: string
  ): Promise<TaxSummary> {
    console.log(`[Tax Summary Service] Calculating summary for company ${companyId}, period ${period || 'current'}`);

    const supabase = createServiceClient();

    // Verify company exists
    const { data: company, error: companyError } = await supabase
      .from('companies')
      .select('id')
      .eq('id', companyId)
      .single();

    if (companyError || !company) {
      throw new Error('Company not found');
    }

    // Parse period
    const { start: periodStart, end: periodEnd, year: periodYear, month: periodMonth } =
      this.parsePeriod(period);

    // Calculate all components in parallel
    const [
      { totalRevenue, ivaCollected, overdueIvaFromSales, netRevenue },
      { totalExpenses, ivaPaid, overdueIvaFromPurchases },
      previousMonthCredit,
      retencion,
      reverseChargeWithholding,
    ] = await Promise.all([
      this.calculateSales(companyId, periodStart, periodEnd),
      this.calculatePurchases(companyId, periodStart, periodEnd),
      this.getPreviousMonthCredit(companyId, periodStart),
      this.getRetencion(companyId, periodStart, periodEnd),
      this.getReverseChargeWithholding(companyId, periodStart, periodEnd),
    ]);

    // Calculate derived values
    const netIva = ivaCollected - ivaPaid;
    // netRevenue now comes from calculateSales (excluding documents with overdue)
    const ppm = this.calculatePPM(netRevenue);
    const impuestoTrabajadores = null; // TODO: Implement when payroll system exists

    // Calculate overdue IVA credit (net effect)
    // Sales overdue IVA: reduces your credit (negative effect) = add to tax
    // Purchases overdue IVA: can't claim this credit (negative effect) = add to tax
    const overdueIvaCredit = overdueIvaFromSales + overdueIvaFromPurchases;

    // Calculate monthly tax following Chilean tax formula
    const ivaBalance = ivaCollected - ivaPaid - (previousMonthCredit || 0);
    const ivaAPagar = Math.max(0, ivaBalance);

    let monthlyTax = ivaAPagar;
    monthlyTax += overdueIvaCredit; // Always add overdue IVA (can be positive or negative)
    if (ppm && ppm > 0) monthlyTax += ppm;
    if (retencion && retencion > 0) monthlyTax += retencion;
    if (reverseChargeWithholding && reverseChargeWithholding > 0) monthlyTax += reverseChargeWithholding;
    if (impuestoTrabajadores && impuestoTrabajadores > 0) monthlyTax += impuestoTrabajadores;

    // Get generated Form29
    const generatedF29 = await this.getGeneratedF29(companyId, periodYear, periodMonth);

    // Generate summary ID
    const summaryId = `${companyId}-${periodYear}-${String(periodMonth).padStart(2, '0')}`;

    const summary: TaxSummary = {
      id: summaryId,
      company_id: companyId,
      period_start: `${periodStart}T00:00:00.000Z`,
      period_end: `${periodEnd}T00:00:00.000Z`,
      total_revenue: totalRevenue,
      total_expenses: totalExpenses,
      iva_collected: ivaCollected,
      iva_paid: ivaPaid,
      net_iva: netIva,
      income_tax: 0, // TODO: Implement
      previous_month_credit: previousMonthCredit,
      overdue_iva_credit: overdueIvaCredit,
      ppm,
      retencion,
      reverse_charge_withholding: reverseChargeWithholding,
      impuesto_trabajadores: impuestoTrabajadores,
      monthly_tax: monthlyTax,
      generated_f29: generatedF29,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    console.log('[Tax Summary Service] Summary calculated successfully');

    return summary;
  }

  /**
   * Calculate sales revenue and IVA collected
   * Uses accounting_date for tax recognition
   *
   * Note: overdue_iva_credit in SALES documents represents IVA credit LOST (you can't claim it)
   * So it REDUCES your effective IVA credit (negative effect)
   */
  private static async calculateSales(
    companyId: string,
    periodStart: string,
    periodEnd: string
  ): Promise<{ totalRevenue: number; ivaCollected: number; overdueIvaFromSales: number; netRevenue: number }> {
    const supabase = createServiceClient();

    // Query positive documents using accounting_date
    const { data: positiveData, error: positiveError } = await supabase
      .from('sales_documents')
      .select('total_amount, tax_amount, overdue_iva_credit, net_amount')
      .eq('company_id', companyId)
      .gte('accounting_date', periodStart)
      .lt('accounting_date', periodEnd)
      .in('document_type', [...SALES_POSITIVE_TYPES]) as { data: SalesDocumentRow[] | null; error: any };

    if (positiveError) throw positiveError;

    // Query credit notes using accounting_date
    const { data: creditData, error: creditError } = await supabase
      .from('sales_documents')
      .select('total_amount, tax_amount, overdue_iva_credit, net_amount')
      .eq('company_id', companyId)
      .gte('accounting_date', periodStart)
      .lt('accounting_date', periodEnd)
      .in('document_type', [...SALES_CREDIT_TYPES]) as { data: SalesDocumentRow[] | null; error: any };

    if (creditError) throw creditError;

    // Calculate totals
    const positiveTotal = positiveData?.reduce((sum, doc) => sum + doc.total_amount, 0) || 0;
    const positiveTax = positiveData?.reduce((sum, doc) => sum + doc.tax_amount, 0) || 0;
    const positiveOverdue = positiveData?.reduce((sum, doc) => sum + (doc.overdue_iva_credit || 0), 0) || 0;

    // For PPM calculation: exclude documents with overdue_iva_credit
    // If a document has overdue, it means it's "out of time" and shouldn't affect the tax base
    const positiveNet = positiveData?.reduce(
      (sum, doc) => sum + ((doc.overdue_iva_credit || 0) > 0 ? 0 : (doc.net_amount || 0)),
      0
    ) || 0;

    const creditTotal = creditData?.reduce((sum, doc) => sum + doc.total_amount, 0) || 0;
    const creditTax = creditData?.reduce((sum, doc) => sum + doc.tax_amount, 0) || 0;
    const creditOverdue = creditData?.reduce((sum, doc) => sum + (doc.overdue_iva_credit || 0), 0) || 0;

    // For PPM calculation: exclude credit notes with overdue_iva_credit
    const creditNet = creditData?.reduce(
      (sum, doc) => sum + ((doc.overdue_iva_credit || 0) > 0 ? 0 : (doc.net_amount || 0)),
      0
    ) || 0;

    return {
      totalRevenue: positiveTotal - creditTotal,
      ivaCollected: positiveTax - creditTax,
      // Overdue IVA: ALWAYS adds to tax burden (can't be recovered)
      // Both positive docs AND credit notes increase the burden
      overdueIvaFromSales: positiveOverdue + creditOverdue,
      netRevenue: positiveNet - creditNet,
    };
  }

  /**
   * Calculate purchase expenses and IVA paid
   * Uses accounting_date for tax recognition
   *
   * Note: overdue_iva_credit in PURCHASE documents represents IVA credit you CAN'T CLAIM
   * So it INCREASES your tax burden (positive effect on tax owed)
   */
  private static async calculatePurchases(
    companyId: string,
    periodStart: string,
    periodEnd: string
  ): Promise<{ totalExpenses: number; ivaPaid: number; overdueIvaFromPurchases: number }> {
    const supabase = createServiceClient();

    // Query positive documents using accounting_date
    const { data: positiveData, error: positiveError } = await supabase
      .from('purchase_documents')
      .select('total_amount, tax_amount, overdue_iva_credit')
      .eq('company_id', companyId)
      .gte('accounting_date', periodStart)
      .lt('accounting_date', periodEnd)
      .in('document_type', [...PURCHASES_POSITIVE_TYPES]) as { data: PurchaseDocumentRow[] | null; error: any };

    if (positiveError) throw positiveError;

    // Query credit notes using accounting_date
    const { data: creditData, error: creditError } = await supabase
      .from('purchase_documents')
      .select('total_amount, tax_amount, overdue_iva_credit')
      .eq('company_id', companyId)
      .gte('accounting_date', periodStart)
      .lt('accounting_date', periodEnd)
      .in('document_type', [...PURCHASES_CREDIT_TYPES]) as { data: PurchaseDocumentRow[] | null; error: any };

    if (creditError) throw creditError;

    // Calculate totals
    const positiveTotal = positiveData?.reduce((sum, doc) => sum + doc.total_amount, 0) || 0;
    const positiveTax = positiveData?.reduce((sum, doc) => sum + doc.tax_amount, 0) || 0;
    const positiveOverdue = positiveData?.reduce((sum, doc) => sum + (doc.overdue_iva_credit || 0), 0) || 0;

    const creditTotal = creditData?.reduce((sum, doc) => sum + doc.total_amount, 0) || 0;
    const creditTax = creditData?.reduce((sum, doc) => sum + doc.tax_amount, 0) || 0;
    const creditOverdue = creditData?.reduce((sum, doc) => sum + (doc.overdue_iva_credit || 0), 0) || 0;

    return {
      totalExpenses: positiveTotal - creditTotal,
      ivaPaid: positiveTax - creditTax,
      // Overdue IVA: ALWAYS adds to tax burden (can't be claimed)
      // Both positive docs AND credit notes increase the burden
      overdueIvaFromPurchases: positiveOverdue + creditOverdue,
    };
  }

  /**
   * Get previous month credit from Form29
   * Checks both form29 table (drafts) and form29_sii_downloads (SII data)
   */
  private static async getPreviousMonthCredit(
    companyId: string,
    periodStart: string
  ): Promise<number | null> {
    const supabase = createServiceClient();

    // Parse periodStart (YYYY-MM-DD format)
    const [year, month] = periodStart.split('-').map(Number);
    const prevYear = month === 1 ? year - 1 : year;
    const prevMonth = month === 1 ? 12 : month - 1;

    // First: Check Form29 drafts for saved/paid forms
    const { data: draftData } = await supabase
      .from('form29')
      .select('net_iva')
      .eq('company_id', companyId)
      .eq('period_year', prevYear)
      .eq('period_month', prevMonth)
      .in('status', ['saved', 'paid'])
      .order('created_at', { ascending: false })
      .limit(1)
      .maybeSingle() as { data: { net_iva: number } | null; error: any };

    if (draftData && draftData.net_iva < 0) {
      return Math.abs(draftData.net_iva);
    }

    // Fallback: Query Form29 SII downloads for "Vigente" forms
    const { data: siiData } = await supabase
      .from('form29_sii_downloads')
      .select('extra_data')
      .eq('company_id', companyId)
      .eq('period_year', prevYear)
      .eq('period_month', prevMonth)
      .eq('status', 'Vigente')
      .order('created_at', { ascending: false })
      .limit(1)
      .maybeSingle() as { data: { extra_data: any } | null; error: any };

    if (siiData?.extra_data) {
      const extraData = siiData.extra_data as any;
      const f29Data = extraData?.f29_data || {};
      const codes = f29Data?.codes || {};
      const code077 = codes['077'] || {};
      const remanente = code077?.value;

      if (remanente !== null && remanente !== undefined) {
        return Number(remanente);
      }
    }

    return null;
  }

  /**
   * Calculate PPM (Pagos Provisionales Mensuales)
   * PPM = 0.125% of net revenue (only if positive)
   */
  private static calculatePPM(netRevenue: number): number | null {
    if (netRevenue > 0) {
      return netRevenue * 0.00125; // 0.125%
    }
    return null;
  }

  /**
   * Get retención from honorarios receipts (received)
   */
  private static async getRetencion(
    companyId: string,
    periodStart: string,
    periodEnd: string
  ): Promise<number | null> {
    const supabase = createServiceClient();

    const { data, error } = await supabase
      .from('honorarios_receipts')
      .select('recipient_retention')
      .eq('company_id', companyId)
      .eq('receipt_type', 'received')
      .gte('issue_date', periodStart)
      .lt('issue_date', periodEnd) as { data: HonorariosReceiptRow[] | null; error: any };

    if (error) {
      console.error('[Tax Summary Service] Error fetching honorarios receipts:', error);
      return null;
    }

    const total = data?.reduce((sum, receipt) => sum + receipt.recipient_retention, 0) || 0;
    return total > 0 ? total : null;
  }

  /**
   * Get Reverse Charge Withholding from purchase documents with code 46
   * This is when the buyer pays the seller's IVA obligation (Retención Cambio de Sujeto)
   */
  private static async getReverseChargeWithholding(
    companyId: string,
    periodStart: string,
    periodEnd: string
  ): Promise<number | null> {
    const supabase = createServiceClient();

    const { data, error } = await supabase
      .from('purchase_documents')
      .select('tax_amount')
      .eq('company_id', companyId)
      .eq('document_type_code', '46')
      .gte('accounting_date', periodStart)
      .lt('accounting_date', periodEnd) as { data: { tax_amount: number }[] | null; error: any };

    if (error) {
      console.error('[Tax Summary Service] Error fetching código 46 documents:', error);
      return null;
    }

    const total = data?.reduce((sum, doc) => sum + doc.tax_amount, 0) || 0;
    return total > 0 ? total : null;
  }

  /**
   * Get generated Form29 for the period
   */
  private static async getGeneratedF29(
    companyId: string,
    periodYear: number,
    periodMonth: number
  ) {
    const supabase = createServiceClient();

    const { data } = await supabase
      .from('form29')
      .select('*')
      .eq('company_id', companyId)
      .eq('period_year', periodYear)
      .eq('period_month', periodMonth)
      .neq('status', 'cancelled')
      .order('revision_number', { ascending: false })
      .order('created_at', { ascending: false })
      .limit(1)
      .single() as { data: Form29Row | null; error: any };

    if (!data) return null;

    return {
      id: data.id,
      company_id: data.company_id,
      period_year: data.period_year,
      period_month: data.period_month,
      total_sales: data.total_sales,
      taxable_sales: data.taxable_sales,
      exempt_sales: data.exempt_sales,
      sales_tax: data.sales_tax,
      total_purchases: data.total_purchases,
      taxable_purchases: data.taxable_purchases,
      purchases_tax: data.purchases_tax,
      iva_to_pay: data.iva_to_pay,
      iva_credit: data.iva_credit,
      net_iva: data.net_iva,
      status: data.status,
      extra_data: data.extra_data as Record<string, any> | null,
      submitted_at: data.submission_date,
      created_at: data.created_at,
      updated_at: data.updated_at,
    };
  }

  /**
   * Parse period string (YYYY-MM) or default to current month
   * Returns ISO date strings (YYYY-MM-DD) to avoid timezone issues
   */
  private static parsePeriod(period?: string): {
    start: string;
    end: string;
    year: number;
    month: number;
  } {
    let year: number;
    let month: number;

    if (period) {
      const parts = period.split('-');
      if (parts.length !== 2) {
        throw new Error('Invalid period format. Use YYYY-MM');
      }
      year = parseInt(parts[0], 10);
      month = parseInt(parts[1], 10);

      if (isNaN(year) || isNaN(month) || month < 1 || month > 12) {
        throw new Error('Invalid period format. Use YYYY-MM');
      }
    } else {
      const now = new Date();
      year = now.getFullYear();
      month = now.getMonth() + 1;
    }

    // Return ISO date strings directly to avoid timezone conversion issues
    const periodStart = `${year}-${String(month).padStart(2, '0')}-01`;
    const periodEnd = month === 12
      ? `${year + 1}-01-01`
      : `${year}-${String(month + 1).padStart(2, '0')}-01`;

    return { start: periodStart, end: periodEnd, year, month };
  }
}
