import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'
import type { Database } from '@/types/database'
import type { Contact, ContactType } from '@/types/contacts'

// Type for contacts row from database
type ContactRow = Database['public']['Tables']['contacts']['Row']

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
    const contactType = searchParams.get('contactType') as ContactType | null

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
      .from('contacts')
      .select('*')
      .eq('company_id', companyId)
      .order('business_name', { ascending: true })

    // Apply optional contact type filter
    if (contactType) {
      query = query.eq('contact_type', contactType)
    }

    // Execute query
    const { data: contacts, error } = await query as { data: ContactRow[] | null; error: any }

    if (error) {
      console.error('Error fetching contacts:', error)
      return NextResponse.json(
        { error: 'Failed to fetch contacts' },
        { status: 500 }
      )
    }

    // Transform to response format
    const response: Contact[] = (contacts || []).map((contact) => ({
      id: contact.id,
      rut: contact.rut,
      business_name: contact.business_name,
      trade_name: contact.trade_name,
      contact_type: contact.contact_type as ContactType,
      address: contact.address,
      phone: contact.phone,
      email: contact.email,
      created_at: contact.created_at,
      updated_at: contact.updated_at,
    }))

    return NextResponse.json(response)
  } catch (error) {
    console.error('Error in contacts API route:', error)

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
