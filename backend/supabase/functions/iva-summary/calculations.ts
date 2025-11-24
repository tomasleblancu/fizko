/**
 * IVA calculation functions
 */

import type { SupabaseClient } from "jsr:@supabase/supabase-js@2";
import type { Document, IvaSummary } from "./types.ts";
import { calculatePPM } from "./helpers.ts";
import {
  getDocuments,
  getPreviousMonthCredit,
  getRetencion,
  getReverseChargeWithholding,
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
 * Calculate sales totals (débito fiscal)
 */
export function calculateSalesTotals(
  salesPositive: Document[],
  salesCredits: Document[]
): {
  debitoFiscal: number;
  netRevenue: number;
  overdueIvaFromSales: number;
  salesCount: number;
} {
  // Positive sales
  const salesPositiveTax = salesPositive.reduce(
    (sum, doc) => sum + (doc.tax_amount || 0),
    0
  );
  const salesPositiveOverdue = salesPositive.reduce(
    (sum, doc) => sum + (doc.overdue_iva_credit || 0),
    0
  );
  const salesPositiveNet = salesPositive
    .filter((doc) => !(doc.overdue_iva_credit || 0) > 0)
    .reduce((sum, doc) => sum + (doc.net_amount || 0), 0);

  // Credit notes (subtract)
  const salesCreditTax = salesCredits.reduce(
    (sum, doc) => sum + (doc.tax_amount || 0),
    0
  );
  const salesCreditOverdue = salesCredits.reduce(
    (sum, doc) => sum + (doc.overdue_iva_credit || 0),
    0
  );
  const salesCreditNet = salesCredits
    .filter((doc) => !(doc.overdue_iva_credit || 0) > 0)
    .reduce((sum, doc) => sum + (doc.net_amount || 0), 0);

  // Calculate totals
  const debitoFiscal = salesPositiveTax - salesCreditTax;
  const netRevenue = salesPositiveNet - salesCreditNet;
  const overdueIvaFromSales = salesPositiveOverdue + salesCreditOverdue;
  const salesCount = salesPositive.length + salesCredits.length;

  return {
    debitoFiscal,
    netRevenue,
    overdueIvaFromSales,
    salesCount,
  };
}

/**
 * Calculate purchases totals (crédito fiscal)
 */
export function calculatePurchasesTotals(
  purchasesPositive: Document[],
  purchasesCredits: Document[]
): {
  creditoFiscal: number;
  overdueIvaFromPurchases: number;
  purchasesCount: number;
} {
  // Positive purchases
  const purchasesPositiveTax = purchasesPositive.reduce(
    (sum, doc) => sum + (doc.tax_amount || 0),
    0
  );
  const purchasesPositiveOverdue = purchasesPositive.reduce(
    (sum, doc) => sum + (doc.overdue_iva_credit || 0),
    0
  );

  // Credit notes (subtract)
  const purchasesCreditTax = purchasesCredits.reduce(
    (sum, doc) => sum + (doc.tax_amount || 0),
    0
  );
  const purchasesCreditOverdue = purchasesCredits.reduce(
    (sum, doc) => sum + (doc.overdue_iva_credit || 0),
    0
  );

  // Calculate totals
  const creditoFiscal = purchasesPositiveTax - purchasesCreditTax;
  const overdueIvaFromPurchases =
    purchasesPositiveOverdue + purchasesCreditOverdue;
  const purchasesCount = purchasesPositive.length + purchasesCredits.length;

  return {
    creditoFiscal,
    overdueIvaFromPurchases,
    purchasesCount,
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
    debitoFiscal,
    netRevenue,
    overdueIvaFromSales,
    salesCount,
  } = calculateSalesTotals(salesPositive, salesCredits);

  // Get purchase documents
  const purchasesPositive = await getDocuments(
    supabase,
    "purchase_documents",
    companyId,
    PURCHASES_POSITIVE_TYPES,
    periodStart,
    periodEnd,
    ["tax_amount", "overdue_iva_credit"]
  );

  const purchasesCredits = await getDocuments(
    supabase,
    "purchase_documents",
    companyId,
    PURCHASES_CREDIT_TYPES,
    periodStart,
    periodEnd,
    ["tax_amount", "overdue_iva_credit"]
  );

  // Calculate purchase totals
  const {
    creditoFiscal,
    overdueIvaFromPurchases,
    purchasesCount,
  } = calculatePurchasesTotals(purchasesPositive, purchasesCredits);

  // Calculate totals
  const overdueIvaCredit = overdueIvaFromSales + overdueIvaFromPurchases;
  const balance = debitoFiscal - creditoFiscal;

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

  // Build result
  return {
    debito_fiscal: debitoFiscal,
    credito_fiscal: creditoFiscal,
    balance: balance,
    previous_month_credit: previousMonthCredit,
    overdue_iva_credit: overdueIvaCredit,
    ppm: ppm,
    retencion: retencion,
    reverse_charge_withholding: reverseChargeWithholding,
    sales_count: salesCount,
    purchases_count: purchasesCount,
  };
}
