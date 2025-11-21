import { NextRequest, NextResponse } from 'next/server'
import { DocumentsService } from '@/services/documents/documents.service'

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const companyId = searchParams.get('companyId')

    if (!companyId) {
      return NextResponse.json(
        { error: 'Missing required parameter: companyId' },
        { status: 400 }
      )
    }

    const documents = await DocumentsService.list({ companyId })
    return NextResponse.json(documents)
  } catch (error) {
    console.error('[Documents API] Error:', error)

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
