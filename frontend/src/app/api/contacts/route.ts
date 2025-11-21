import { NextRequest, NextResponse } from 'next/server'
import type { ContactType } from '@/types/contacts'
import { ContactsService } from '@/services/contacts'

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams
    const companyId = searchParams.get('companyId')
    const contactType = searchParams.get('contactType') as ContactType | null

    if (!companyId) {
      return NextResponse.json(
        { error: 'companyId is required' },
        { status: 400 }
      )
    }

    // Delegate to service layer
    const contacts = await ContactsService.list({
      companyId,
      contactType: contactType || undefined,
    })

    return NextResponse.json(contacts)
  } catch (error) {
    console.error('[Contacts API] Error:', error)

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
