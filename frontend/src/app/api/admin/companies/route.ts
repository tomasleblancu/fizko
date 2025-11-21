import { NextRequest, NextResponse } from 'next/server'
import { AdminCompaniesService } from '@/services/admin/companies.service'

export async function GET(request: NextRequest) {
  try {
    const companies = await AdminCompaniesService.listAll()
    return NextResponse.json({ data: companies })
  } catch (error) {
    console.error('[Admin Companies API] Error:', error)

    if (error instanceof Error) {
      // Check if it's an authorization error
      if (error.message.includes('Unauthorized') || error.message.includes('Forbidden')) {
        return NextResponse.json(
          { error: error.message },
          { status: error.message.includes('Unauthorized') ? 401 : 403 }
        )
      }

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
