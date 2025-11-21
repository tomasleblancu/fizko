import { NextRequest, NextResponse } from 'next/server'
import { TaxSummaryService } from '@/services/tax'

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

    // Delegate to service layer
    const summary = await TaxSummaryService.calculateSummary(companyId, period)

    return NextResponse.json(summary)
  } catch (error) {
    console.error('[Tax Summary API] Error:', error)

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
