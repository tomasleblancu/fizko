import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'
import type { Database } from '@/types/database'
import type { Person, PersonStatus } from '@/types/personnel'

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

    // Initialize Supabase client
    const supabase = getSupabaseClient()

    // Build query
    let query = supabase
      .from('people')
      .select('*', { count: 'exact' })
      .eq('company_id', companyId)

    // Apply optional status filter
    if (status) {
      query = query.eq('status', status)
    }

    // Apply optional search filter
    if (search) {
      query = query.or(`first_name.ilike.%${search}%,last_name.ilike.%${search}%,rut.ilike.%${search}%`)
    }

    // Apply pagination
    const from = (page - 1) * pageSize
    const to = from + pageSize - 1
    query = query.range(from, to)

    // Order by last name, first name
    query = query.order('last_name', { ascending: true })
      .order('first_name', { ascending: true })

    // Execute query
    const { data: people, error, count } = await query

    if (error) {
      console.error('Error fetching people:', error)
      return NextResponse.json(
        { error: 'Failed to fetch people' },
        { status: 500 }
      )
    }

    // Transform to response format
    const response: Person[] = (people || []).map((person) => ({
      id: person.id,
      company_id: person.company_id,
      rut: person.rut,
      first_name: person.first_name,
      last_name: person.last_name,
      email: person.email,
      phone: person.phone,
      birth_date: person.birth_date,
      position_title: person.position_title,
      contract_type: person.contract_type as any,
      hire_date: person.hire_date,
      base_salary: Number(person.base_salary),
      afp_provider: person.afp_provider,
      afp_percentage: person.afp_percentage ? Number(person.afp_percentage) : null,
      health_provider: person.health_provider,
      health_plan: person.health_plan,
      health_percentage: person.health_percentage ? Number(person.health_percentage) : null,
      health_fixed_amount: person.health_fixed_amount ? Number(person.health_fixed_amount) : null,
      bank_name: person.bank_name,
      bank_account_type: person.bank_account_type as any,
      bank_account_number: person.bank_account_number,
      status: person.status as PersonStatus,
      termination_date: person.termination_date,
      termination_reason: person.termination_reason,
      notes: person.notes,
      photo_url: person.photo_url,
      created_at: person.created_at,
      updated_at: person.updated_at,
    }))

    return NextResponse.json({
      data: response,
      total: count || 0,
      page,
      page_size: pageSize,
    })
  } catch (error) {
    console.error('Error in personnel API route:', error)

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
