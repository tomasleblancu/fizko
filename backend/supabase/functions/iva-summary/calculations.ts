/**
 * IVA calculation functions
 */

import type { SupabaseClient } from "jsr:@supabase/supabase-js@2";
import type { Document, IvaSummary } from "./types.ts";
import { calculatePPM, calculatePeriodRange } from "./helpers.ts";
import {
  getDocuments,
  getPreviousMonthCredit,
  getRetencion,
  getReverseChargeWithholding,
  getGeneratedF29,
  getForm29SiiDownload,
} from "./documents.ts";

/**
 * Document types for sales (positive transactions)
 */
const SALES_POSITIVE_TYPES = [
  "factura_venta",
  "boleta",
  "boleta_exenta",
  "factura_exenta",
  "comprobante_pago",
  "liquidacion_factura",
  "nota_debito_venta",
];

/**
 * Document types for sales credits (negative transactions)
 */
const SALES_CREDIT_TYPES = ["nota_credito_venta"];

/**
 * Document types for purchases (positive transactions)
 */
const PURCHASES_POSITIVE_TYPES = [
  "factura_compra",
  "factura_exenta_compra",
  "liquidacion_factura",
  "nota_debito_compra",
  "declaracion_ingreso",
];

/**
 * Document types for purchase credits (negative transactions)
 */
const PURCHASES_CREDIT_TYPES = ["nota_credito_compra"];

/**
 * Calculate sales totals
 */
export function calculateSalesTotals(
  salesPositive: Document[],
  salesCredits: Document[]
): {
  totalRevenue: number;
  ivaCollected: number;
  overdueIvaFromSales: number;
  netRevenue: number;
} {
  // Positive sales
  const salesPositiveTotal = salesPositive.reduce(
    (sum, doc) => sum + (doc.total_amount || 0),
    0
  );
  const salesPositiveTax = salesPositive.reduce(
    (sum, doc) => sum + (doc.tax_amount || 0),
    0
  );
  const salesPositiveOverdue = salesPositive.reduce(
    (sum, doc) => sum + (doc.overdue_iva_credit || 0),
    0
  );
  // For PPM: exclude documents with overdue_iva_credit
  const salesPositiveNet = salesPositive
    .filter((doc) => !(doc.overdue_iva_credit || 0) > 0)
    .reduce((sum, doc) => sum + (doc.net_amount || 0), 0);

  // Credit notes (subtract)
  const salesCreditTotal = salesCredits.reduce(
    (sum, doc) => sum + (doc.total_amount || 0),
    0
  );
  const salesCreditTax = salesCredits.reduce(
    (sum, doc) => sum + (doc.tax_amount || 0),
    0
  );
  const salesCreditOverdue = salesCredits.reduce(
    (sum, doc) => sum + (doc.overdue_iva_credit || 0),
    0
  );
  // For PPM: exclude credit notes with overdue_iva_credit
  const salesCreditNet = salesCredits
    .filter((doc) => !(doc.overdue_iva_credit || 0) > 0)
    .reduce((sum, doc) => sum + (doc.net_amount || 0), 0);

  // Calculate totals
  const totalRevenue = salesPositiveTotal - salesCreditTotal;
  const ivaCollected = salesPositiveTax - salesCreditTax;
  const overdueIvaFromSales = salesPositiveOverdue + salesCreditOverdue;
  const netRevenue = salesPositiveNet - salesCreditNet;

  return {
    totalRevenue,
    ivaCollected,
    overdueIvaFromSales,
    netRevenue,
  };
}

/**
 * Calculate purchases totals
 */
export function calculatePurchasesTotals(
  purchasesPositive: Document[],
  purchasesCredits: Document[]
): {
  totalExpenses: number;
  ivaPaid: number;
  overdueIvaFromPurchases: number;
} {
  // Positive purchases
  const purchasesPositiveTotal = purchasesPositive.reduce(
    (sum, doc) => sum + (doc.total_amount || 0),
    0
  );
  const purchasesPositiveTax = purchasesPositive.reduce(
    (sum, doc) => sum + (doc.tax_amount || 0),
    0
  );
  const purchasesPositiveOverdue = purchasesPositive.reduce(
    (sum, doc) => sum + (doc.overdue_iva_credit || 0),
    0
  );

  // Credit notes (subtract)
  const purchasesCreditTotal = purchasesCredits.reduce(
    (sum, doc) => sum + (doc.total_amount || 0),
    0
  );
  const purchasesCreditTax = purchasesCredits.reduce(
    (sum, doc) => sum + (doc.tax_amount || 0),
    0
  );
  const purchasesCreditOverdue = purchasesCredits.reduce(
    (sum, doc) => sum + (doc.overdue_iva_credit || 0),
    0
  );

  // Calculate totals
  const totalExpenses = purchasesPositiveTotal - purchasesCreditTotal;
  const ivaPaid = purchasesPositiveTax - purchasesCreditTax;
  const overdueIvaFromPurchases =
    purchasesPositiveOverdue + purchasesCreditOverdue;

  return {
    totalExpenses,
    ivaPaid,
    overdueIvaFromPurchases,
  };
}

/**
 * Calculate complete IVA summary for a company and period
 *
 * @param supabase - Supabase client
 * @param companyId - Company UUID
 * @param periodStart - Period start date (YYYY-MM-DD) or null for all dates
 * @param periodEnd - Period end date (YYYY-MM-DD) or null for all dates
 * @returns Complete IVA summary
 */
export async function calculateIvaSummary(
  supabase: SupabaseClient,
  companyId: string,
  periodStart: string | null,
  periodEnd: string | null
): Promise<IvaSummary> {
  // Get sales documents
  const salesPositive = await getDocuments(
    supabase,
    "sales_documents",
    companyId,
    SALES_POSITIVE_TYPES,
    periodStart,
    periodEnd,
    ["tax_amount", "total_amount", "net_amount", "overdue_iva_credit"]
  );

  const salesCredits = await getDocuments(
    supabase,
    "sales_documents",
    companyId,
    SALES_CREDIT_TYPES,
    periodStart,
    periodEnd,
    ["tax_amount", "total_amount", "net_amount", "overdue_iva_credit"]
  );

  // Calculate sales totals
  const {
    totalRevenue,
    ivaCollected,
    overdueIvaFromSales,
    netRevenue,
  } = calculateSalesTotals(salesPositive, salesCredits);

  // Get purchase documents
  const purchasesPositive = await getDocuments(
    supabase,
    "purchase_documents",
    companyId,
    PURCHASES_POSITIVE_TYPES,
    periodStart,
    periodEnd,
    ["tax_amount", "total_amount", "overdue_iva_credit"]
  );

  const purchasesCredits = await getDocuments(
    supabase,
    "purchase_documents",
    companyId,
    PURCHASES_CREDIT_TYPES,
    periodStart,
    periodEnd,
    ["tax_amount", "total_amount", "overdue_iva_credit"]
  );

  // Calculate purchase totals
  const {
    totalExpenses,
    ivaPaid,
    overdueIvaFromPurchases,
  } = calculatePurchasesTotals(purchasesPositive, purchasesCredits);

  // Calculate totals
  const overdueIvaCredit = overdueIvaFromSales + overdueIvaFromPurchases;
  const netIva = ivaCollected - ivaPaid;

  // Get additional data
  const previousMonthCredit = await getPreviousMonthCredit(
    supabase,
    companyId,
    periodStart
  );
  const ppm = calculatePPM(netRevenue);
  const retencion = await getRetencion(
    supabase,
    companyId,
    periodStart,
    periodEnd
  );
  const reverseChargeWithholding = await getReverseChargeWithholding(
    supabase,
    companyId,
    periodStart,
    periodEnd
  );

  // Get period year and month for F29 queries
  let periodYear: number;
  let periodMonth: number;
  if (periodStart) {
    const [yearStr, monthStr] = periodStart.split("-");
    periodYear = parseInt(yearStr);
    periodMonth = parseInt(monthStr);
  } else {
    const now = new Date();
    periodYear = now.getFullYear();
    periodMonth = now.getMonth() + 1;
  }

  // Get F29 data
  const generatedF29 = await getGeneratedF29(
    supabase,
    companyId,
    periodYear,
    periodMonth
  );
  const form29SiiDownload = await getForm29SiiDownload(
    supabase,
    companyId,
    periodYear,
    periodMonth
  );

  // Calculate monthly tax following Chilean tax formula
  const ivaBalance = ivaCollected - ivaPaid - (previousMonthCredit || 0);
  const ivaAPagar = Math.max(0, ivaBalance);

  let monthlyTax = ivaAPagar;
  monthlyTax += overdueIvaCredit; // Always add overdue IVA
  if (ppm && ppm > 0) monthlyTax += ppm;
  if (retencion && retencion > 0) monthlyTax += retencion;
  if (reverseChargeWithholding && reverseChargeWithholding > 0)
    monthlyTax += reverseChargeWithholding;

  // Generate summary ID
  const summaryId = `${companyId}-${periodYear}-${
    String(periodMonth).padStart(2, "0")
  }`;

  // Build result with timestamps
  const now = new Date().toISOString();

  return {
    id: summaryId,
    company_id: companyId,
    period_start: periodStart
      ? `${periodStart}T00:00:00.000Z`
      : now,
    period_end: periodEnd
      ? `${periodEnd}T00:00:00.000Z`
      : now,
    total_revenue: totalRevenue,
    total_expenses: totalExpenses,
    iva_collected: ivaCollected,
    iva_paid: ivaPaid,
    net_iva: netIva,
    income_tax: 0, // TODO: Implement when income tax is calculated
    previous_month_credit: previousMonthCredit > 0 ? previousMonthCredit : null,
    overdue_iva_credit: overdueIvaCredit,
    ppm: ppm > 0 ? ppm : null,
    retencion: retencion > 0 ? retencion : null,
    reverse_charge_withholding: reverseChargeWithholding > 0
      ? reverseChargeWithholding
      : null,
    impuesto_trabajadores: null, // TODO: Implement when payroll exists
    monthly_tax: monthlyTax,
    generated_f29: generatedF29,
    form29_sii_download: form29SiiDownload,
    created_at: now,
    updated_at: now,
  };
}
