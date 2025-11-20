import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { queryKeys } from '@/lib/query-keys'
import type { CompanySettingsResponse, CompanySettingsRequest } from '@/types/company-settings'

export function useCompanySettings(companyId: string) {
  return useQuery({
    queryKey: queryKeys.companySettings.byCompany(companyId),
    queryFn: async (): Promise<CompanySettingsResponse> => {
      const response = await fetch(`/api/companies/${companyId}/settings`)

      if (!response.ok) {
        throw new Error('Failed to fetch company settings')
      }

      return response.json()
    },
    enabled: !!companyId,
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

export function useUpdateCompanySettings(companyId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (data: CompanySettingsRequest): Promise<CompanySettingsResponse> => {
      const response = await fetch(`/api/companies/${companyId}/settings`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      })

      if (!response.ok) {
        throw new Error('Failed to update company settings')
      }

      return response.json()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.companySettings.byCompany(companyId) })
    },
  })
}
