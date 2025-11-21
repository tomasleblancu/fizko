import { NextRequest, NextResponse } from 'next/server'
import type { CompanySettingsRequest } from '@/types/company-settings'
import { CompanyService } from '@/services/company'

export async function GET(
  request: NextRequest,
  context: { params: Promise<{ companyId: string }> }
) {
  try {
    const { companyId } = await context.params

    // Delegate to service layer
    const settings = await CompanyService.getSettings(companyId)

    return NextResponse.json({
      data: settings,
      message: settings.id ? undefined : 'No settings found, using defaults'
    })
  } catch (error) {
    console.error('[Company Settings API] GET Error:', error)

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

export async function POST(
  request: NextRequest,
  context: { params: Promise<{ companyId: string }> }
) {
  try {
    const { companyId } = await context.params
    const body: CompanySettingsRequest = await request.json()

    // Delegate to service layer
    const settings = await CompanyService.upsertSettings(companyId, body)

    return NextResponse.json({
      data: settings,
      message: 'Settings saved successfully'
    })
  } catch (error) {
    console.error('[Company Settings API] POST Error:', error)

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
