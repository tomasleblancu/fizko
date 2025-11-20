import { useQuery } from '@tanstack/react-query'
import { queryKeys } from '@/lib/query-keys'
import type { F29FormsResponse, F29FormsParams } from '@/types/f29'

export function useF29Forms({
  companyId,
  formType,
  year,
  month,
}: F29FormsParams) {
  return useQuery({
    queryKey: queryKeys.f29.byCompany(companyId, year, month),
    queryFn: async (): Promise<F29FormsResponse> => {
      const params = new URLSearchParams({ companyId })

      if (formType) params.append('formType', formType)
      if (year) params.append('year', year.toString())
      if (month) params.append('month', month.toString())

      const response = await fetch(`/api/f29?${params.toString()}`)

      if (!response.ok) {
        throw new Error('Failed to fetch F29 forms')
      }

      return response.json()
    },
    enabled: !!companyId,
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}
