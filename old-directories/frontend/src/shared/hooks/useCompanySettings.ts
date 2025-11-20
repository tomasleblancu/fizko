/**
 * useCompanySettings Hook
 *
 * Manages company business settings and configuration.
 * Handles fetching and updating company operational settings
 * (employees, imports, exports, lease contracts).
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuth } from "@/app/providers/AuthContext";
import { API_BASE_URL } from "@/shared/lib/config";
import { apiFetch } from "@/shared/lib/api-client";
import { queryKeys } from "@/shared/lib/query-keys";

export interface CompanySettings {
  id?: string;
  company_id: string;
  has_formal_employees: boolean | null;
  has_imports: boolean | null;
  has_exports: boolean | null;
  has_lease_contracts: boolean | null;
  has_bank_loans: boolean | null;
  business_description: string | null;
  is_initial_setup_complete: boolean;
  initial_setup_completed_at: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface CompanySettingsUpdate {
  has_formal_employees?: boolean | null;
  has_imports?: boolean | null;
  has_exports?: boolean | null;
  has_lease_contracts?: boolean | null;
  has_bank_loans?: boolean | null;
  business_description?: string | null;
}

interface CompanySettingsResponse {
  data: CompanySettings;
  message?: string;
}

/**
 * Hook to manage company settings
 *
 * @param companyId - UUID of the company
 * @returns {Object} Settings state and methods
 * @returns {CompanySettings | null} settings - Current company settings
 * @returns {boolean} loading - Loading state
 * @returns {string | null} error - Error message if any
 * @returns {Function} updateSettings - Mutation to update settings
 * @returns {Function} refetch - Manually trigger refetch
 *
 * @example
 * ```typescript
 * const { settings, updateSettings, loading } = useCompanySettings(companyId);
 *
 * // Update settings
 * await updateSettings.mutateAsync({
 *   has_formal_employees: true,
 *   has_imports: false,
 * });
 * ```
 */
export function useCompanySettings(companyId: string | null) {
  const { session: authSession } = useAuth();
  const queryClient = useQueryClient();

  // Query for fetching settings
  const settingsQuery = useQuery({
    queryKey: queryKeys.companySettings.byId(companyId || ''),
    queryFn: async (): Promise<CompanySettings | null> => {
      if (!authSession?.access_token || !companyId) {
        return null;
      }

      console.log('[useCompanySettings] Fetching settings for company:', companyId);

      const response = await apiFetch(`${API_BASE_URL}/companies/${companyId}/settings`, {
        headers: {
          'Authorization': `Bearer ${authSession.access_token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        // If 404, return default empty settings (not an error)
        if (response.status === 404) {
          return {
            company_id: companyId,
            has_formal_employees: null,
            has_imports: null,
            has_exports: null,
            has_lease_contracts: null,
            has_bank_loans: null,
            business_description: null,
            is_initial_setup_complete: false,
            initial_setup_completed_at: null,
          };
        }
        throw new Error('Failed to fetch company settings');
      }

      const result: CompanySettingsResponse = await response.json();
      return result.data;
    },
    enabled: !!companyId && !!authSession?.access_token,
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 1,
  });

  // Mutation for updating settings
  const updateSettingsMutation = useMutation({
    mutationFn: async (data: CompanySettingsUpdate): Promise<CompanySettings> => {
      if (!authSession?.access_token || !companyId) {
        throw new Error('No estás autenticado o no se especificó la empresa');
      }

      console.log('[useCompanySettings] Updating settings:', data);

      const response = await apiFetch(`${API_BASE_URL}/companies/${companyId}/settings`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${authSession.access_token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Error al guardar configuración');
      }

      const result: CompanySettingsResponse = await response.json();
      return result.data;
    },
    onSuccess: async (data) => {
      console.log('[useCompanySettings] Settings updated successfully:', data);

      // Invalidate queries to refetch updated data
      await queryClient.invalidateQueries({
        queryKey: queryKeys.companySettings.byId(companyId || ''),
      });

      // Also invalidate company query in case it affects other data
      await queryClient.invalidateQueries({
        queryKey: queryKeys.company.all,
      });
    },
    onError: (error: Error) => {
      console.error('[useCompanySettings] Error updating settings:', error);
    },
  });

  // Handle case where company ID is not provided
  if (!companyId) {
    return {
      settings: null,
      loading: false,
      error: null,
      updateSettings: updateSettingsMutation,
      refetch: () => Promise.resolve({ data: null } as any),
    };
  }

  return {
    settings: settingsQuery.data ?? null,
    loading: settingsQuery.isLoading,
    error: settingsQuery.error?.message ?? null,
    updateSettings: updateSettingsMutation,
    refetch: () => settingsQuery.refetch(),
  };
}
