import { NextRequest, NextResponse } from 'next/server'
import { F29SIIDownloadsService } from '@/services/tax'

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

    // Delegate to service layer
    const result = await F29SIIDownloadsService.list({
      companyId,
      year: year ? parseInt(year, 10) : undefined,
      month: month ? parseInt(month, 10) : undefined,
    })

    return NextResponse.json(result)
  } catch (error) {
    console.error('[F29 SII Downloads API] Error:', error)

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
