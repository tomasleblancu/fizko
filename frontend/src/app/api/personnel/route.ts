import { NextRequest, NextResponse } from 'next/server'
import type { PersonStatus } from '@/types/personnel'
import { PersonnelService } from '@/services/personnel'

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams
    const companyId = searchParams.get('companyId')
    const status = searchParams.get('status') as PersonStatus | null
    const search = searchParams.get('search')
    const page = parseInt(searchParams.get('page') || '1', 10)
    const pageSize = parseInt(searchParams.get('pageSize') || '50', 10)

    if (!companyId) {
      return NextResponse.json(
        { error: 'companyId is required' },
        { status: 400 }
      )
    }

    // Delegate to service layer
    const result = await PersonnelService.list({
      companyId,
      status: status || undefined,
      search: search || undefined,
      page,
      pageSize,
    })

    return NextResponse.json(result)
  } catch (error) {
    console.error('[Personnel API] Error:', error)

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
