import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { queryKeys } from '@/lib/query-keys'
import type {
  NotificationPreferences,
  NotificationPreferencesRequest,
} from '@/types/notification-subscription'

export function useNotificationPreferences(userId: string, companyId?: string) {
  return useQuery({
    queryKey: queryKeys.notificationPreferences.byUser(userId, companyId),
    queryFn: async (): Promise<{ data: NotificationPreferences }> => {
      const params = new URLSearchParams({ userId })
      if (companyId) {
        params.append('companyId', companyId)
      }

      const response = await fetch(`/api/notifications/preferences?${params}`)

      if (!response.ok) {
        throw new Error('Failed to fetch notification preferences')
      }

      return response.json()
    },
    enabled: !!userId,
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

export function useUpdateNotificationPreferences(userId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (data: NotificationPreferencesRequest): Promise<{
      data: NotificationPreferences
      message: string
    }> => {
      const response = await fetch(`/api/notifications/preferences?userId=${userId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      })

      if (!response.ok) {
        throw new Error('Failed to update notification preferences')
      }

      return response.json()
    },
    onSuccess: (_, variables) => {
      // Invalidate both with and without companyId to ensure all queries refresh
      queryClient.invalidateQueries({
        queryKey: queryKeys.notificationPreferences.byUser(userId, variables.company_id)
      })
      queryClient.invalidateQueries({
        queryKey: queryKeys.notificationPreferences.byUser(userId)
      })
    },
  })
}
