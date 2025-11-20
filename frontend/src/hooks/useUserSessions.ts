"use client";

import { useQuery } from "@tanstack/react-query";
import { createClient } from "@/lib/supabase/client";
import { queryKeys } from "@/lib/query-keys";
import type { SessionWithCompany } from "@/types/database";

export function useUserSessions() {
  const supabase = createClient();

  return useQuery({
    queryKey: queryKeys.sessions.all,
    queryFn: async (): Promise<SessionWithCompany[]> => {
      // Verify session via server-side API to ensure cookies are available
      const sessionResponse = await fetch('/api/auth/session', {
        credentials: 'include',
      });

      if (!sessionResponse.ok) {
        // No valid session - logout and redirect to login
        await supabase.auth.signOut();
        window.location.href = '/auth/login';
        return [];
      }

      const { user } = await sessionResponse.json();

      if (!user) {
        // No user found - logout and redirect
        await supabase.auth.signOut();
        window.location.href = '/auth/login';
        return [];
      }

      // Fetch active sessions with company data and settings
      const { data, error } = await supabase
        .from("sessions")
        .select(
          `
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
        `
        )
        .eq("user_id", user.id)
        .eq("is_active", true)
        .order("last_accessed_at", { ascending: false, nullsFirst: false })
        .order("created_at", { ascending: false });

      if (error) throw error;

      return (data || []).map((session: any) => ({
        ...session,
        company: session.company,
      })) as SessionWithCompany[];
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchOnWindowFocus: true,
  });
}
