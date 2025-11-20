import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'
import type { Database } from '@/types/database'
import type { F29Form, F29Status, FormType } from '@/types/f29'

// Create Supabase client for server-side operations
function getSupabaseClient() {
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
  const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY!

  return createClient<Database>(supabaseUrl, supabaseKey)
}

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams
    const companyId = searchParams.get('companyId')
    const formType = searchParams.get('formType') as FormType | null
    const year = searchParams.get('year')
    const month = searchParams.get('month')

    if (!companyId) {
      return NextResponse.json(
        { error: 'companyId is required' },
        { status: 400 }
      )
    }

    // Initialize Supabase client
    const supabase = getSupabaseClient()

    // Build query
    let query = supabase
      .from('form29')
      .select('*', { count: 'exact' })
      .eq('company_id', companyId)
      .order('period_year', { ascending: false })
      .order('period_month', { ascending: false })

    // Apply optional year filter
    if (year) {
      query = query.eq('period_year', parseInt(year, 10))
    }

    // Apply optional month filter
    if (month) {
      query = query.eq('period_month', parseInt(month, 10))
    }

    // Execute query
    const { data: forms, error, count } = await query

    if (error) {
      console.error('Error fetching F29 forms:', error)
      return NextResponse.json(
        { error: 'Failed to fetch F29 forms' },
        { status: 500 }
      )
    }

    // Transform to response format with type assertion
    const response: F29Form[] = (forms || []).map((form: any) => ({
      id: form.id,
      company_id: form.company_id,
      period_year: form.period_year,
      period_month: form.period_month,
      total_sales: Number(form.total_sales),
      taxable_sales: Number(form.taxable_sales),
      exempt_sales: Number(form.exempt_sales),
      sales_tax: Number(form.sales_tax),
      total_purchases: Number(form.total_purchases),
      taxable_purchases: Number(form.taxable_purchases),
      purchases_tax: Number(form.purchases_tax),
      iva_to_pay: Number(form.iva_to_pay),
      iva_credit: Number(form.iva_credit),
      net_iva: Number(form.net_iva),
      status: form.status as F29Status,
      revision_number: form.revision_number,
      submission_date: form.submission_date,
      extra_data: form.extra_data as Record<string, any> | null,
      created_at: form.created_at,
      updated_at: form.updated_at,
    }))

    return NextResponse.json({
      data: response,
      total: count || 0,
    })
  } catch (error) {
    console.error('Error in F29 API route:', error)

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
