import { createServiceClient } from '@/lib/supabase/server'
import type { SessionWithCompany } from '@/types/database'

export interface ListSessionsParams {
  userId: string
}

export interface ListSessionsResponse {
  data: SessionWithCompany[]
}

export class SessionsService {
  /**
   * List active sessions for a user with company data and settings
   */
  static async list(params: ListSessionsParams): Promise<ListSessionsResponse> {
    const supabase = createServiceClient()

    const { data, error } = await supabase
      .from('sessions')
      .select(`
        *,
        company:companies (
          id,
          rut,
          business_name,
          trade_name,
          address,
          phone,
          email,
          created_at,
          updated_at,
          settings:company_settings (
            id,
            is_initial_setup_complete,
            has_formal_employees,
            has_imports,
            has_exports,
            has_lease_contracts,
            has_bank_loans,
            business_description
          )
        )
      `)
      .eq('user_id', params.userId)
      .eq('is_active', true)
      .order('last_accessed_at', { ascending: false, nullsFirst: false })
      .order('created_at', { ascending: false })

    if (error) {
      console.error('[SessionsService] Error fetching sessions:', error)
      throw new Error(`Failed to fetch sessions: ${error.message}`)
    }

    // Transform data to ensure proper typing
    const sessions: SessionWithCompany[] = (data || []).map((session: any) => ({
      ...session,
      company: session.company,
    }))

    return { data: sessions }
  }
}
