import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'
import type { Database } from '@/types/database'
import {
  TaxSummary,
  SALES_POSITIVE_TYPES,
  SALES_CREDIT_TYPES,
  PURCHASES_POSITIVE_TYPES,
  PURCHASES_CREDIT_TYPES,
} from '@/types/tax'

// Types for database rows
type SalesDocumentRow = { total_amount: number; tax_amount: number }
type PurchaseDocumentRow = { total_amount: number; tax_amount: number }
type HonorariosReceiptRow = { recipient_retention: number }
type Form29Row = Database['public']['Tables']['form29']['Row']
type Form29SiiDownloadRow = Database['public']['Tables']['form29_sii_downloads']['Row']

// Create Supabase client for server-side operations
// Using publishable key with RLS for security
function getSupabaseClient() {
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
  const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY!

  return createClient<Database>(supabaseUrl, supabaseKey)
}

/**
 * Parse period string (YYYY-MM) or default to current month
 */
function parsePeriod(period?: string): { start: Date; end: Date } {
  let year: number
  let month: number

  if (period) {
    const parts = period.split('-')
    if (parts.length !== 2) {
      throw new Error('Invalid period format. Use YYYY-MM')
    }
    year = parseInt(parts[0], 10)
    month = parseInt(parts[1], 10)

    if (isNaN(year) || isNaN(month) || month < 1 || month > 12) {
      throw new Error('Invalid period format. Use YYYY-MM')
    }
  } else {
    const now = new Date()
    year = now.getFullYear()
    month = now.getMonth() + 1
  }

  const periodStart = new Date(year, month - 1, 1)
  const periodEnd = month === 12
    ? new Date(year + 1, 0, 1)
    : new Date(year, month, 1)

  return { start: periodStart, end: periodEnd }
}

/**
 * Calculate sales revenue and IVA collected
 */
async function calculateSales(
  supabase: ReturnType<typeof getSupabaseClient>,
  companyId: string,
  periodStart: Date,
  periodEnd: Date
): Promise<{ totalRevenue: number; ivaCollected: number }> {
  // Query positive documents
  const { data: positiveData, error: positiveError } = await supabase
    .from('sales_documents')
    .select('total_amount, tax_amount')
    .eq('company_id', companyId)
    .gte('issue_date', periodStart.toISOString().split('T')[0])
    .lt('issue_date', periodEnd.toISOString().split('T')[0])
    .in('document_type', [...SALES_POSITIVE_TYPES]) as { data: SalesDocumentRow[] | null; error: any }

  if (positiveError) throw positiveError

  // Query credit notes
  const { data: creditData, error: creditError } = await supabase
    .from('sales_documents')
    .select('total_amount, tax_amount')
    .eq('company_id', companyId)
    .gte('issue_date', periodStart.toISOString().split('T')[0])
    .lt('issue_date', periodEnd.toISOString().split('T')[0])
    .in('document_type', [...SALES_CREDIT_TYPES]) as { data: SalesDocumentRow[] | null; error: any }

  if (creditError) throw creditError

  // Calculate totals
  const positiveTotal = positiveData?.reduce((sum, doc) => sum + doc.total_amount, 0) || 0
  const positiveTax = positiveData?.reduce((sum, doc) => sum + doc.tax_amount, 0) || 0
  const creditTotal = creditData?.reduce((sum, doc) => sum + doc.total_amount, 0) || 0
  const creditTax = creditData?.reduce((sum, doc) => sum + doc.tax_amount, 0) || 0

  return {
    totalRevenue: positiveTotal - creditTotal,
    ivaCollected: positiveTax - creditTax,
  }
}

/**
 * Calculate purchase expenses and IVA paid
 */
async function calculatePurchases(
  supabase: ReturnType<typeof getSupabaseClient>,
  companyId: string,
  periodStart: Date,
  periodEnd: Date
): Promise<{ totalExpenses: number; ivaPaid: number }> {
  // Query positive documents
  const { data: positiveData, error: positiveError } = await supabase
    .from('purchase_documents')
    .select('total_amount, tax_amount')
    .eq('company_id', companyId)
    .gte('issue_date', periodStart.toISOString().split('T')[0])
    .lt('issue_date', periodEnd.toISOString().split('T')[0])
    .in('document_type', [...PURCHASES_POSITIVE_TYPES]) as { data: PurchaseDocumentRow[] | null; error: any }

  if (positiveError) throw positiveError

  // Query credit notes
  const { data: creditData, error: creditError } = await supabase
    .from('purchase_documents')
    .select('total_amount, tax_amount')
    .eq('company_id', companyId)
    .gte('issue_date', periodStart.toISOString().split('T')[0])
    .lt('issue_date', periodEnd.toISOString().split('T')[0])
    .in('document_type', [...PURCHASES_CREDIT_TYPES]) as { data: PurchaseDocumentRow[] | null; error: any }

  if (creditError) throw creditError

  // Calculate totals
  const positiveTotal = positiveData?.reduce((sum, doc) => sum + doc.total_amount, 0) || 0
  const positiveTax = positiveData?.reduce((sum, doc) => sum + doc.tax_amount, 0) || 0
  const creditTotal = creditData?.reduce((sum, doc) => sum + doc.total_amount, 0) || 0
  const creditTax = creditData?.reduce((sum, doc) => sum + doc.tax_amount, 0) || 0

  return {
    totalExpenses: positiveTotal - creditTotal,
    ivaPaid: positiveTax - creditTax,
  }
}

/**
 * Get previous month credit from Form29
 */
async function getPreviousMonthCredit(
  supabase: ReturnType<typeof getSupabaseClient>,
  companyId: string,
  periodStart: Date
): Promise<number | null> {
  const prevYear = periodStart.getMonth() === 0 ? periodStart.getFullYear() - 1 : periodStart.getFullYear()
  const prevMonth = periodStart.getMonth() === 0 ? 12 : periodStart.getMonth()

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
    .maybeSingle() as { data: { net_iva: number } | null; error: any }

  if (draftData && draftData.net_iva < 0) {
    return Math.abs(draftData.net_iva)
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
    .maybeSingle() as { data: { extra_data: any } | null; error: any }

  if (siiData?.extra_data) {
    const extraData = siiData.extra_data as any
    const f29Data = extraData?.f29_data || {}
    const codes = f29Data?.codes || {}
    const code077 = codes['077'] || {}
    const remanente = code077?.value

    if (remanente !== null && remanente !== undefined) {
      return Number(remanente)
    }
  }

  return null
}

/**
 * Calculate PPM (0.125% of net revenue)
 */
function calculatePPM(netRevenue: number): number | null {
  if (netRevenue > 0) {
    return netRevenue * 0.00125 // 0.125%
  }
  return null
}

/**
 * Get retención from honorarios receipts
 */
async function getRetencion(
  supabase: ReturnType<typeof getSupabaseClient>,
  companyId: string,
  periodStart: Date,
  periodEnd: Date
): Promise<number | null> {
  const { data, error } = await supabase
    .from('honorarios_receipts')
    .select('recipient_retention')
    .eq('company_id', companyId)
    .eq('receipt_type', 'received')
    .gte('issue_date', periodStart.toISOString().split('T')[0])
    .lt('issue_date', periodEnd.toISOString().split('T')[0]) as { data: HonorariosReceiptRow[] | null; error: any }

  if (error) {
    console.error('Error fetching honorarios receipts:', error)
    return null
  }

  const total = data?.reduce((sum, receipt) => sum + receipt.recipient_retention, 0) || 0
  return total > 0 ? total : null
}

/**
 * Get generated Form29 for the period
 */
async function getGeneratedF29(
  supabase: ReturnType<typeof getSupabaseClient>,
  companyId: string,
  periodYear: number,
  periodMonth: number
) {
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
    .single() as { data: Form29Row | null; error: any }

  if (!data) return null

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
  }
}

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams
    const companyId = searchParams.get('companyId')
    const period = searchParams.get('period') || undefined

    if (!companyId) {
      return NextResponse.json(
        { error: 'companyId is required' },
        { status: 400 }
      )
    }

    // Parse period
    const { start: periodStart, end: periodEnd } = parsePeriod(period)

    // Initialize Supabase client
    const supabase = getSupabaseClient()

    // Verify company exists
    const { data: company, error: companyError } = await supabase
      .from('companies')
      .select('id')
      .eq('id', companyId)
      .single() as { data: { id: string } | null; error: any }

    if (companyError || !company) {
      return NextResponse.json(
        { error: 'Company not found' },
        { status: 404 }
      )
    }

    // Calculate all components in parallel
    const [
      { totalRevenue, ivaCollected },
      { totalExpenses, ivaPaid },
      previousMonthCredit,
      retencion,
    ] = await Promise.all([
      calculateSales(supabase, companyId, periodStart, periodEnd),
      calculatePurchases(supabase, companyId, periodStart, periodEnd),
      getPreviousMonthCredit(supabase, companyId, periodStart),
      getRetencion(supabase, companyId, periodStart, periodEnd),
    ])

    // Calculate derived values
    const netIva = ivaCollected - ivaPaid
    const netRevenue = totalRevenue - ivaCollected
    const ppm = calculatePPM(netRevenue)
    const impuestoTrabajadores = null // TODO: Implement when payroll system exists

    // Calculate monthly tax following Chilean tax formula
    const ivaBalance = ivaCollected - ivaPaid - (previousMonthCredit || 0)
    const ivaAPagar = Math.max(0, ivaBalance)

    let monthlyTax = ivaAPagar
    if (ppm && ppm > 0) monthlyTax += ppm
    if (retencion && retencion > 0) monthlyTax += retencion
    if (impuestoTrabajadores && impuestoTrabajadores > 0) monthlyTax += impuestoTrabajadores

    // Get generated Form29
    const generatedF29 = await getGeneratedF29(
      supabase,
      companyId,
      periodStart.getFullYear(),
      periodStart.getMonth() + 1
    )

    // Generate summary ID
    const summaryId = `${companyId}-${periodStart.getFullYear()}-${String(periodStart.getMonth() + 1).padStart(2, '0')}`

    const summary: TaxSummary = {
      id: summaryId,
      company_id: companyId,
      period_start: periodStart.toISOString(),
      period_end: periodEnd.toISOString(),
      total_revenue: totalRevenue,
      total_expenses: totalExpenses,
      iva_collected: ivaCollected,
      iva_paid: ivaPaid,
      net_iva: netIva,
      income_tax: 0, // TODO: Implement
      previous_month_credit: previousMonthCredit,
      ppm,
      retencion,
      impuesto_trabajadores: impuestoTrabajadores,
      monthly_tax: monthlyTax,
      generated_f29: generatedF29,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }

    return NextResponse.json(summary)
  } catch (error) {
    console.error('Error calculating tax summary:', error)

    if (error instanceof Error) {
      return NextResponse.json(
        { error: error.message },
        { status: 400 }
      )
    }

    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}
