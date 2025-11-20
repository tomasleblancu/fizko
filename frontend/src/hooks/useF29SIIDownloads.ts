import { useQuery } from '@tanstack/react-query'
import { queryKeys } from '@/lib/query-keys'
import type { F29SIIDownloadsResponse, F29SIIDownloadsParams } from '@/types/f29-sii-downloads'

export function useF29SIIDownloads({
  companyId,
  year,
  month,
}: F29SIIDownloadsParams) {
  return useQuery({
    queryKey: queryKeys.f29SIIDownloads.byCompany(companyId, year, month),
    queryFn: async (): Promise<F29SIIDownloadsResponse> => {
      const params = new URLSearchParams({ companyId })

      if (year) params.append('year', year.toString())
      if (month) params.append('month', month.toString())

      const response = await fetch(`/api/f29-sii-downloads?${params.toString()}`)

      if (!response.ok) {
        throw new Error('Failed to fetch F29 SII downloads')
      }

      return response.json()
    },
    enabled: !!companyId,
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}
