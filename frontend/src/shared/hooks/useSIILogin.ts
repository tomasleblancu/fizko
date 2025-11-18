import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '@/app/providers/AuthContext';
import { API_BASE_URL } from '@/shared/lib/config';

interface SIILoginRequest {
  rut: string;
  password: string;
}

interface SIILoginResponse {
  success: boolean;
  message: string;
  company: {
    id: string;
    rut: string;
    business_name: string;
    trade_name?: string;
  };
  company_tax_info: any;
  session: any;
  contribuyente_info: any;
  needs_initial_setup: boolean;
}

/**
 * Hook for SII login to add a new company to the user's account.
 *
 * This mutation:
 * 1. Authenticates with SII using RUT and password
 * 2. Creates/updates company in the database
 * 3. Creates a new session for the user with that company
 * 4. Triggers background sync tasks
 *
 * After successful login, you should:
 * - Invalidate sessions query to refresh company list
 * - Update selected company in CompanyContext
 * - Reload the page or navigate to setup
 *
 * @example
 * ```tsx
 * const { mutateAsync: loginToSII, isPending } = useSIILogin();
 *
 * const handleLogin = async () => {
 *   try {
 *     const result = await loginToSII({
 *       rut: '12345678-9',
 *       password: 'mypassword'
 *     });
 *     console.log('Company added:', result.company);
 *   } catch (error) {
 *     console.error('Login failed:', error);
 *   }
 * };
 * ```
 */
export function useSIILogin() {
  const { session } = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (credentials: SIILoginRequest): Promise<SIILoginResponse> => {
      if (!session?.access_token) {
        throw new Error('No authenticated session');
      }

      const response = await fetch(`${API_BASE_URL}/sii/auth/login`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(credentials),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to login to SII: ${response.statusText}`);
      }

      return await response.json();
    },
    onSuccess: () => {
      // Invalidate sessions query to refetch and update company list
      queryClient.invalidateQueries({
        queryKey: ['sessions'],
      });
    },
  });
}
