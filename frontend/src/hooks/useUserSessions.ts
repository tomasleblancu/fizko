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

      // Fetch active sessions via internal API route
      const sessionsResponse = await fetch('/api/sessions', {
        credentials: 'include',
      });

      if (!sessionsResponse.ok) {
        throw new Error('Failed to fetch sessions');
      }

      const { data } = await sessionsResponse.json();
      return data as SessionWithCompany[];
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchOnWindowFocus: true,
  });
}
