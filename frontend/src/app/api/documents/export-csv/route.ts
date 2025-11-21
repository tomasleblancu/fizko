/**
 * Export Documents as CSV API Route
 *
 * Handles document export with filters for year, months, document types, and movement type
 */

import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@/lib/supabase/server'
import { DocumentsExportService } from '@/services/documents'

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams
    const companyId = searchParams.get('companyId')
    const year = searchParams.get('year')
    const docTypesParam = searchParams.get('docTypes')
    const monthsParam = searchParams.get('months')
    const typeParam = searchParams.get('type')

    // Validate required params
    if (!companyId || !year) {
      return NextResponse.json(
        { error: 'companyId and year are required' },
        { status: 400 }
      )
    }

    // Get authenticated user
    const supabase = await createClient()
    const {
      data: { user },
      error: authError,
    } = await supabase.auth.getUser()

    if (authError || !user) {
      return NextResponse.json(
        { error: 'No autenticado' },
        { status: 401 }
      )
    }

    // Parse optional parameters
    const docTypes = docTypesParam ? docTypesParam.split(',') : undefined
    const months = monthsParam ? monthsParam.split(',').map(m => parseInt(m)) : undefined
    const type = typeParam as 'sale' | 'purchase' | undefined

    // Delegate to service layer
    const csvContent = await DocumentsExportService.exportToCSV({
      companyId,
      year,
      docTypes,
      months,
      type,
    })

    // Return CSV as downloadable file
    return new NextResponse(csvContent, {
      status: 200,
      headers: {
        'Content-Type': 'text/csv; charset=utf-8',
        'Content-Disposition': `attachment; filename="movimientos_${year}.csv"`,
      },
    })
  } catch (error) {
    console.error('[Export CSV API] Error:', error)

    if (error instanceof Error) {
      return NextResponse.json(
        { error: error.message },
        { status: 500 }
      )
    }

    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}
