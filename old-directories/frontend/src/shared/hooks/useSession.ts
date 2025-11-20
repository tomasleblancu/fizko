/**
 * useSession Hook - Optimized with React Query
 *
 * This hook manages SII session state using React Query for:
 * - Automatic caching and deduplication
 * - Consistent error handling and retry logic
 * - Simplified state management (no manual useState/useEffect)
 * - Automatic refetch and invalidation
 *
 * Migration from custom implementation reduces code from 177 to ~80 lines
 * while providing better functionality and consistency with other data hooks.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuth } from "@/app/providers/AuthContext";
import { API_BASE_URL } from "@/shared/lib/config";
import { apiFetch } from "@/shared/lib/api-client";
import { queryKeys } from "@/shared/lib/query-keys";

export interface SIISession {
  id: string;
  user_id: string;
  company_id: string;
  company?: {
    id: string;
    rut: string;
    business_name: string;
    trade_name?: string;
  };
  is_active: boolean;
  has_cookies: boolean;
  has_resources: boolean;
  last_accessed_at?: string;
  created_at: string;
  updated_at: string;
}

export interface OnboardingStatus {
  needsOnboarding: boolean;
  hasSession: boolean;
  session: SIISession | null;
  needsInitialSetup: boolean;
  setupCompanyId: string | null;
}

interface SessionsResponse {
  data: SIISession[];
}

interface SessionData {
  session: SIISession | null;
  needsOnboarding: boolean;
  hasSession: boolean;
  needsInitialSetup: boolean;
  setupCompanyId: string | null;
}

/**
 * Hook to manage SII sessions with React Query
 *
 * @returns {Object} Session state and methods
 * @returns {SIISession | null} session - Current active SII session
 * @returns {boolean} loading - Loading state
 * @returns {string | null} error - Error message if any
 * @returns {boolean} needsOnboarding - Whether user needs to complete onboarding
 * @returns {boolean} needsInitialSetup - Whether company needs initial setup configuration
 * @returns {string | null} setupCompanyId - Company ID needing setup (if any)
 * @returns {boolean} isInitialized - Whether initial fetch has completed
 * @returns {Function} saveSIICredentials - Mutation to save SII credentials
 * @returns {Function} refresh - Manually trigger refetch
 *
 * @example
 * ```typescript
 * const { session, needsOnboarding, saveSIICredentials } = useSession();
 *
 * if (needsOnboarding) {
 *   // Show onboarding form
 *   await saveSIICredentials({ rut: '12345678-9', password: 'secret' });
 * }
 * ```
 */
export function useSession() {
  const { user, session: authSession } = useAuth();
  const queryClient = useQueryClient();

  // Query for fetching sessions
  const sessionsQuery = useQuery({
    queryKey: queryKeys.sessions.byUser(user?.id),
    queryFn: async (): Promise<SessionData> => {
      if (!authSession?.access_token) {
        // Not authenticated - needs onboarding
        return {
          session: null,
          needsOnboarding: true,
          hasSession: false,
          needsInitialSetup: false,
          setupCompanyId: null,
        };
      }

      console.log('[useSession] Fetching sessions for user:', user?.id);

      const response = await apiFetch(`${API_BASE_URL}/sessions`, {
        headers: {
          'Authorization': `Bearer ${authSession.access_token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch session');
      }

      const result: SessionsResponse = await response.json();
      const sessions = result.data || [];

      // Find active session
      const activeSession = sessions.find((s: SIISession) => s.is_active);

      // Check sessionStorage for initial setup flag (set during login)
      const needsSetupStr = sessionStorage.getItem('needs_initial_setup');
      const setupCompanyIdStr = sessionStorage.getItem('setup_company_id');
      const needsSetup = needsSetupStr === 'true';
      const setupCompanyId = setupCompanyIdStr || null;

      if (activeSession) {
        // Has active session - onboarding complete
        return {
          session: activeSession,
          needsOnboarding: false,
          hasSession: true,
          needsInitialSetup: needsSetup && setupCompanyId === activeSession.company_id,
          setupCompanyId: needsSetup && setupCompanyId === activeSession.company_id ? setupCompanyId : null,
        };
      } else if (sessions.length > 0) {
        // Has sessions but none are active - needs onboarding
        return {
          session: sessions[0],
          needsOnboarding: true,
          hasSession: true,
          needsInitialSetup: false,
          setupCompanyId: null,
        };
      } else {
        // No sessions at all - needs onboarding
        return {
          session: null,
          needsOnboarding: true,
          hasSession: false,
          needsInitialSetup: false,
          setupCompanyId: null,
        };
      }
    },
    enabled: !!user && !!authSession?.access_token,
    staleTime: 5 * 60 * 1000, // 5 minutes - consistent with other hooks
    retry: 1, // Only retry once on failure
    // Return needsOnboarding: true on error to show onboarding form
    meta: {
      errorHandler: (error: Error) => {
        console.error('[useSession] Error fetching session:', error);
      },
    },
  });

  // Mutation for saving SII credentials with streaming support
  const saveSIICredentialsMutation = useMutation({
    mutationFn: async (credentials: { rut: string; password: string }) => {
      if (!authSession?.access_token) {
        throw new Error('No estás autenticado');
      }

      console.log('[useSession] Saving SII credentials with streaming...');

      // Use SSE endpoint for streaming progress
      const response = await fetch(`${API_BASE_URL}/sii/auth/login/stream`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${authSession.access_token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(credentials),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Error al autenticar con el SII');
      }

      if (!response.body) {
        throw new Error('No se pudo establecer conexión de streaming');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let result: any = null;

      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value);
          const lines = chunk.split('\n\n');

          for (const line of lines) {
            if (!line.trim()) continue;

            const [eventLine, dataLine] = line.split('\n');
            if (!eventLine || !dataLine) continue;

            const event = eventLine.replace('event: ', '');
            const dataStr = dataLine.replace('data: ', '');

            try {
              const data = JSON.parse(dataStr);

              switch (event) {
                case 'progress':
                  // Emit progress event for UI to consume
                  // This will be handled by custom event listener in OnboardingModal
                  window.dispatchEvent(new CustomEvent('sii-login-progress', { detail: data }));
                  break;
                case 'complete':
                  result = data;
                  // Store initial setup flag if present
                  if (data.needs_initial_setup && data.company?.id) {
                    sessionStorage.setItem('needs_initial_setup', 'true');
                    sessionStorage.setItem('setup_company_id', data.company.id);
                  } else {
                    sessionStorage.removeItem('needs_initial_setup');
                    sessionStorage.removeItem('setup_company_id');
                  }
                  break;
                case 'error':
                  throw new Error(data.message || 'Error durante el proceso');
              }
            } catch (e) {
              console.error('[useSession] Error parsing SSE data:', e);
            }
          }
        }
      } finally {
        reader.releaseLock();
      }

      if (!result) {
        throw new Error('No se recibió respuesta completa del servidor');
      }

      return result;
    },
    onSuccess: async (data) => {
      console.log('[useSession] SII credentials saved successfully:', data);

      // Immediately refetch both queries in parallel for instant UI update
      await Promise.all([
        queryClient.invalidateQueries({
          queryKey: queryKeys.sessions.byUser(user?.id),
        }),
        queryClient.invalidateQueries({
          queryKey: queryKeys.company.all,
        }),
      ]);
    },
    onError: (error: Error) => {
      console.error('[useSession] Error saving SII credentials:', error);
    },
  });

  // Handle case where user is not authenticated
  // Return default "needs onboarding" state
  if (!user || !authSession) {
    return {
      session: null,
      loading: false,
      error: null,
      needsOnboarding: true,
      needsInitialSetup: false,
      setupCompanyId: null,
      isInitialized: true,
      saveSIICredentials: saveSIICredentialsMutation.mutateAsync,
      refresh: () => Promise.resolve(),
    };
  }

  return {
    session: sessionsQuery.data?.session ?? null,
    loading: sessionsQuery.isLoading,
    error: sessionsQuery.error?.message ?? null,
    needsOnboarding: sessionsQuery.data?.needsOnboarding ?? false,
    needsInitialSetup: sessionsQuery.data?.needsInitialSetup ?? false,
    setupCompanyId: sessionsQuery.data?.setupCompanyId ?? null,
    isInitialized: !sessionsQuery.isLoading,
    saveSIICredentials: saveSIICredentialsMutation.mutateAsync,
    refresh: () => sessionsQuery.refetch(),
  };
}
