import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'
import type { Database } from '@/types/database'
import type { CompanySettings, CompanySettingsRequest } from '@/types/company-settings'

// Type for company_settings row from database
type CompanySettingsRow = Database['public']['Tables']['company_settings']['Row']

function getSupabaseClient() {
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
  const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY!

  return createClient<Database>(supabaseUrl, supabaseKey)
}

export async function GET(
  request: NextRequest,
  context: { params: Promise<{ companyId: string }> }
) {
  try {
    const { companyId } = await context.params
    const supabase = getSupabaseClient()

    const { data: settings, error } = await supabase
      .from('company_settings')
      .select('*')
      .eq('company_id', companyId)
      .single() as { data: CompanySettingsRow | null; error: any }

    if (error && error.code !== 'PGRST116') { // Not found is ok
      console.error('Error fetching company settings:', error)
      return NextResponse.json(
        { error: 'Failed to fetch company settings' },
        { status: 500 }
      )
    }

    // If no settings exist, return default values
    if (!settings) {
      const defaultSettings: CompanySettings = {
        id: '',
        company_id: companyId,
        has_formal_employees: null,
        has_imports: null,
        has_exports: null,
        has_lease_contracts: null,
        has_bank_loans: null,
        business_description: null,
        is_initial_setup_complete: false,
        initial_setup_completed_at: null,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }
      return NextResponse.json({
        data: defaultSettings,
        message: 'No settings found, using defaults'
      })
    }

    const response: CompanySettings = {
      id: settings.id,
      company_id: settings.company_id,
      has_formal_employees: settings.has_formal_employees,
      has_imports: settings.has_imports,
      has_exports: settings.has_exports,
      has_lease_contracts: settings.has_lease_contracts,
      has_bank_loans: settings.has_bank_loans,
      business_description: settings.business_description,
      is_initial_setup_complete: settings.is_initial_setup_complete,
      initial_setup_completed_at: settings.initial_setup_completed_at,
      created_at: settings.created_at,
      updated_at: settings.updated_at,
    }

    return NextResponse.json({ data: response })
  } catch (error) {
    console.error('Error in company settings GET:', error)
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
    const supabase = getSupabaseClient()
    const body: CompanySettingsRequest = await request.json()

    // Check if settings already exist
    const { data: existing } = await supabase
      .from('company_settings')
      .select('id, is_initial_setup_complete')
      .eq('company_id', companyId)
      .single() as { data: { id: string; is_initial_setup_complete: boolean } | null; error: any }

    const hasAnyField = Object.values(body).some(val => val !== null && val !== undefined)
    const shouldMarkSetupComplete = !existing?.is_initial_setup_complete && hasAnyField

    const updateData = { ...body } as Record<string, any>
    if (shouldMarkSetupComplete) {
      updateData.is_initial_setup_complete = true
      updateData.initial_setup_completed_at = new Date().toISOString()
    }

    let result: CompanySettingsRow
    if (existing) {
      // Update existing - Using any cast to bypass Supabase type inference issue
      const { data, error } = await (supabase as any)
        .from('company_settings')
        .update(updateData)
        .eq('company_id', companyId)
        .select()
        .single()

      if (error) throw error
      result = data
    } else {
      // Create new - Using any cast to bypass Supabase type inference issue
      const { data, error } = await (supabase as any)
        .from('company_settings')
        .insert({
          company_id: companyId,
          ...updateData,
        })
        .select()
        .single()

      if (error) throw error
      result = data
    }

    const response: CompanySettings = {
      id: result.id,
      company_id: result.company_id,
      has_formal_employees: result.has_formal_employees,
      has_imports: result.has_imports,
      has_exports: result.has_exports,
      has_lease_contracts: result.has_lease_contracts,
      has_bank_loans: result.has_bank_loans,
      business_description: result.business_description,
      is_initial_setup_complete: result.is_initial_setup_complete,
      initial_setup_completed_at: result.initial_setup_completed_at,
      created_at: result.created_at,
      updated_at: result.updated_at,
    }

    return NextResponse.json({
      data: response,
      message: 'Settings saved successfully'
    })
  } catch (error) {
    console.error('Error in company settings POST:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}
