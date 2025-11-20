import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@/lib/supabase/server';
import type { ActiveSessionsResponse } from '@/types/sii';

export async function GET(request: NextRequest) {
  try {
    const supabase = await createClient();
    const {
      data: { user },
      error: authError,
    } = await supabase.auth.getUser();

    if (authError || !user) {
      return NextResponse.json({
        hasActiveSessions: false,
        sessions: [],
      } as ActiveSessionsResponse);
    }

    // Fetch active sessions with company and settings data
    const { data: sessions, error: sessionsError } = await supabase
      .from('sessions')
      .select(
        `
        *,
        company:companies (
          id,
          rut,
          business_name,
          trade_name,
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
      `
      )
      .eq('user_id', user.id)
      .eq('is_active', true)
      .order('last_accessed_at', { ascending: false });

    if (sessionsError) {
      console.error('[Verify Session] Error fetching sessions:', sessionsError);
      return NextResponse.json(
        {
          hasActiveSessions: false,
          sessions: [],
          error: sessionsError.message,
        } as ActiveSessionsResponse,
        { status: 500 }
      );
    }

    return NextResponse.json({
      hasActiveSessions: (sessions?.length || 0) > 0,
      sessions: sessions || [],
    } as ActiveSessionsResponse);
  } catch (error) {
    console.error('[Verify Session] Unexpected error:', error);
    return NextResponse.json(
      {
        hasActiveSessions: false,
        sessions: [],
        error: error instanceof Error ? error.message : 'Error interno',
      } as ActiveSessionsResponse,
      { status: 500 }
    );
  }
}
