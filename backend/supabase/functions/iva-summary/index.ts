import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "jsr:@supabase/supabase-js@2";

// Types for document data
interface Document {
  tax_amount: number | null;
  total_amount: number | null;
  net_amount: number | null;
  overdue_iva_credit: number | null;
}

interface IvaSummary {
  debito_fiscal: number;
  credito_fiscal: number;
  balance: number;
  previous_month_credit: number;
  overdue_iva_credit: number;
  ppm: number;
  retencion: number;
  reverse_charge_withholding: number;
  sales_count: number;
  purchases_count: number;
}

// Helper: Calculate date range from period string (YYYY-MM)
function calculatePeriodRange(period: string | null): [string | null, string | null] {
  if (!period) return [null, null];

  const [yearStr, monthStr] = period.split("-");
  const year = parseInt(yearStr);
  const month = parseInt(monthStr);

  const periodStart = `${year}-${month.toString().padStart(2, "0")}-01`;

  let periodEnd: string;
  if (month === 12) {
    periodEnd = `${year + 1}-01-01`;
  } else {
    periodEnd = `${year}-${(month + 1).toString().padStart(2, "0")}-01`;
  }

  return [periodStart, periodEnd];
}

// Helper: Calculate PPM (0.125% of net revenue)
function calculatePPM(netRevenue: number): number {
  return netRevenue > 0 ? netRevenue * 0.00125 : 0;
}

// Helper: Get documents with filters
async function getDocuments(
  supabase: any,
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

// Helper: Get previous month credit from F29
async function getPreviousMonthCredit(
  supabase: any,
  companyId: string,
  periodStart: string | null
): Promise<number> {
  if (!periodStart) return 0;

  const [yearStr, monthStr] = periodStart.split("-");
  let year = parseInt(yearStr);
  let month = parseInt(monthStr);

  // Calculate previous month
  if (month === 1) {
    year -= 1;
    month = 12;
  } else {
    month -= 1;
  }

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
    if (extraData?.f29_data?.codes?.["077"]?.value !== undefined) {
      return parseFloat(extraData.f29_data.codes["077"].value);
    }
  }

  return 0;
}

// Helper: Get retención from honorarios receipts
async function getRetencion(
  supabase: any,
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

// Helper: Get reverse charge withholding (código 46)
async function getReverseChargeWithholding(
  supabase: any,
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

// Main handler
Deno.serve(async (req: Request) => {
  // CORS headers
  const corsHeaders = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers":
      "authorization, x-client-info, apikey, content-type",
  };

  // Handle CORS preflight
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }

  try {
    // Get auth token
    const authHeader = req.headers.get("Authorization");
    if (!authHeader) {
      return new Response(
        JSON.stringify({ error: "Missing authorization header" }),
        {
          status: 401,
          headers: { ...corsHeaders, "Content-Type": "application/json" },
        }
      );
    }

    // Initialize Supabase client
    const supabaseUrl = Deno.env.get("SUPABASE_URL")!;
    const supabaseAnonKey = Deno.env.get("SUPABASE_ANON_KEY")!;

    const supabase = createClient(supabaseUrl, supabaseAnonKey, {
      global: {
        headers: { Authorization: authHeader },
      },
    });

    // Verify user is authenticated
    const {
      data: { user },
      error: userError,
    } = await supabase.auth.getUser();

    if (userError || !user) {
      return new Response(JSON.stringify({ error: "Unauthorized" }), {
        status: 401,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      });
    }

    // Parse request body
    const { company_id, period } = await req.json();

    if (!company_id) {
      return new Response(
        JSON.stringify({ error: "company_id is required" }),
        {
          status: 400,
          headers: { ...corsHeaders, "Content-Type": "application/json" },
        }
      );
    }

    // Calculate date range
    const [periodStart, periodEnd] = calculatePeriodRange(period || null);

    // Get sales documents
    const salesPositive = await getDocuments(
      supabase,
      "sales_documents",
      company_id,
      [
        "factura_venta",
        "boleta",
        "boleta_exenta",
        "factura_exenta",
        "comprobante_pago",
        "liquidacion_factura",
        "nota_debito_venta",
      ],
      periodStart,
      periodEnd,
      ["tax_amount", "total_amount", "net_amount", "overdue_iva_credit"]
    );

    const salesCredits = await getDocuments(
      supabase,
      "sales_documents",
      company_id,
      ["nota_credito_venta"],
      periodStart,
      periodEnd,
      ["tax_amount", "total_amount", "net_amount", "overdue_iva_credit"]
    );

    // Calculate sales totals
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

    const debitoFiscal = salesPositiveTax - salesCreditTax;
    const netRevenue = salesPositiveNet - salesCreditNet;
    const overdueIvaFromSales = salesPositiveOverdue + salesCreditOverdue;

    // Get purchase documents
    const purchasesPositive = await getDocuments(
      supabase,
      "purchase_documents",
      company_id,
      [
        "factura_compra",
        "factura_exenta_compra",
        "liquidacion_factura",
        "nota_debito_compra",
        "declaracion_ingreso",
      ],
      periodStart,
      periodEnd,
      ["tax_amount", "overdue_iva_credit"]
    );

    const purchasesCredits = await getDocuments(
      supabase,
      "purchase_documents",
      company_id,
      ["nota_credito_compra"],
      periodStart,
      periodEnd,
      ["tax_amount", "overdue_iva_credit"]
    );

    // Calculate purchase totals
    const purchasesPositiveTax = purchasesPositive.reduce(
      (sum, doc) => sum + (doc.tax_amount || 0),
      0
    );
    const purchasesPositiveOverdue = purchasesPositive.reduce(
      (sum, doc) => sum + (doc.overdue_iva_credit || 0),
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

    const creditoFiscal = purchasesPositiveTax - purchasesCreditTax;
    const overdueIvaFromPurchases =
      purchasesPositiveOverdue + purchasesCreditOverdue;

    // Calculate totals
    const overdueIvaCredit = overdueIvaFromSales + overdueIvaFromPurchases;
    const balance = debitoFiscal - creditoFiscal;

    // Get additional data
    const previousMonthCredit = await getPreviousMonthCredit(
      supabase,
      company_id,
      periodStart
    );
    const ppm = calculatePPM(netRevenue);
    const retencion = await getRetencion(
      supabase,
      company_id,
      periodStart,
      periodEnd
    );
    const reverseChargeWithholding = await getReverseChargeWithholding(
      supabase,
      company_id,
      periodStart,
      periodEnd
    );

    // Build response
    const result: IvaSummary = {
      debito_fiscal: debitoFiscal,
      credito_fiscal: creditoFiscal,
      balance: balance,
      previous_month_credit: previousMonthCredit,
      overdue_iva_credit: overdueIvaCredit,
      ppm: ppm,
      retencion: retencion,
      reverse_charge_withholding: reverseChargeWithholding,
      sales_count: salesPositive.length + salesCredits.length,
      purchases_count: purchasesPositive.length + purchasesCredits.length,
    };

    return new Response(JSON.stringify(result), {
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  } catch (error) {
    console.error("Error in iva-summary function:", error);
    return new Response(
      JSON.stringify({
        error: error instanceof Error ? error.message : "Unknown error",
      }),
      {
        status: 500,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      }
    );
  }
});
