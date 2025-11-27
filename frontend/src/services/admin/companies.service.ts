import { createServiceClient } from '@/lib/supabase/server'
import type { Database } from '@/types/database'

export type Company = Database['public']['Tables']['companies']['Row']

export interface CompanyWithStats extends Company {
  users_count?: number
  sessions_count?: number
  last_activity?: string | null
}

export interface UserSession {
  id: string
  user_id: string
  is_active: boolean
  last_accessed_at: string | null
  created_at: string
  profile: {
    email: string
    name: string | null
    lastname: string | null
  }
}

export interface CompanyDetail extends CompanyWithStats {
  sessions?: UserSession[]
}

export class AdminCompaniesService {
  /**
   * List all companies with basic stats
   */
  static async listAll(): Promise<CompanyWithStats[]> {
    const supabase = createServiceClient()

    // Get all companies
    const { data: companies, error } = await supabase
      .from('companies')
      .select(`
        *,
        sessions(count),
        profiles:sessions(user_id)
      `)
      .order('created_at', { ascending: false })

    if (error) {
      console.error('[AdminCompaniesService] Error fetching companies:', error)
      throw new Error(`Failed to fetch companies: ${error.message}`)
    }

    // Process data to add stats
    const companiesWithStats: CompanyWithStats[] = companies.map((company: any) => {
      // Get unique user IDs from sessions
      const uniqueUserIds = new Set(
        company.profiles?.map((p: any) => p.user_id) || []
      )

      return {
        id: company.id,
        rut: company.rut,
        business_name: company.business_name,
        trade_name: company.trade_name,
        address: company.address,
        phone: company.phone,
        email: company.email,
        created_at: company.created_at,
        updated_at: company.updated_at,
        sii_password: company.sii_password,
        users_count: uniqueUserIds.size,
        sessions_count: company.sessions?.[0]?.count || 0,
      }
    })

    return companiesWithStats
  }

  /**
   * Get company by ID with detailed information
   */
  static async getById(companyId: string): Promise<CompanyDetail | null> {
    const supabase = createServiceClient()

    const { data: company, error } = await supabase
      .from('companies')
      .select(`
        *,
        sessions(
          id,
          user_id,
          is_active,
          last_accessed_at,
          created_at
        )
      `)
      .eq('id', companyId)
      .single()

    if (error) {
      if (error.code === 'PGRST116') {
        return null
      }
      console.error('[AdminCompaniesService] Error fetching company:', error)
      throw new Error(`Failed to fetch company: ${error.message}`)
    }

    // Fetch profiles separately for each unique user_id
    const userIds = [...new Set(company.sessions?.map((s: any) => s.user_id) || [])]
    const { data: profiles, error: profilesError } = await supabase
      .from('profiles')
      .select('id, email, name, lastname')
      .in('id', userIds)

    if (profilesError) {
      console.error('[AdminCompaniesService] Error fetching profiles:', profilesError)
      // Continue without profiles data
    }

    // Create a map of profiles by id
    const profilesMap = new Map(
      (profiles || []).map(p => [p.id, p])
    )

    // Get unique users
    const uniqueUserIds = new Set(
      company.sessions?.map((s: any) => s.user_id) || []
    )

    // Get last activity
    const lastActivity = company.sessions?.reduce((latest: string | null, session: any) => {
      if (!session.last_accessed_at) return latest
      if (!latest) return session.last_accessed_at
      return session.last_accessed_at > latest ? session.last_accessed_at : latest
    }, null)

    // Transform sessions to match UserSession interface
    const sessions: UserSession[] = (company.sessions || []).map((s: any) => {
      const profile = profilesMap.get(s.user_id)
      return {
        id: s.id,
        user_id: s.user_id,
        is_active: s.is_active,
        last_accessed_at: s.last_accessed_at,
        created_at: s.created_at,
        profile: {
          email: profile?.email || '',
          name: profile?.name || null,
          lastname: profile?.lastname || null,
        }
      }
    })

    return {
      id: company.id,
      rut: company.rut,
      business_name: company.business_name,
      trade_name: company.trade_name,
      address: company.address,
      phone: company.phone,
      email: company.email,
      created_at: company.created_at,
      updated_at: company.updated_at,
      sii_password: company.sii_password,
      users_count: uniqueUserIds.size,
      sessions_count: company.sessions?.length || 0,
      last_activity: lastActivity,
      sessions,
    }
  }
}
