import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'
import type { Database } from '@/types/database'
import type { F29SIIDownload, SIIFormStatus, PDFDownloadStatus } from '@/types/f29-sii-downloads'

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
      .from('form29_sii_downloads')
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
    const { data: downloads, error, count } = await query

    if (error) {
      console.error('Error fetching F29 SII downloads:', error)
      return NextResponse.json(
        { error: 'Failed to fetch F29 SII downloads' },
        { status: 500 }
      )
    }

    // Transform to response format with type assertion
    const response: F29SIIDownload[] = (downloads || []).map((download: any) => ({
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
      status: download.status as SIIFormStatus,
      amount_cents: Number(download.amount_cents),
      pdf_storage_url: download.pdf_storage_url,
      pdf_download_status: download.pdf_download_status as PDFDownloadStatus,
      pdf_download_error: download.pdf_download_error,
      pdf_downloaded_at: download.pdf_downloaded_at,
      extra_data: download.extra_data as Record<string, any> | null,
      created_at: download.created_at,
      updated_at: download.updated_at,
    }))

    return NextResponse.json({
      data: response,
      total: count || 0,
    })
  } catch (error) {
    console.error('Error in F29 SII downloads API route:', error)

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
