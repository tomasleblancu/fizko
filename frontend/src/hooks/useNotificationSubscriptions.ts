import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { queryKeys } from '@/lib/query-keys'
import type {
  NotificationSubscriptionsResponse,
  NotificationSubscriptionRequest,
  NotificationSubscriptionUpdateRequest,
  NotificationSubscription,
} from '@/types/notification-subscription'

export function useNotificationSubscriptions(companyId: string) {
  return useQuery({
    queryKey: queryKeys.notificationSubscriptions.byCompany(companyId),
    queryFn: async (): Promise<NotificationSubscriptionsResponse> => {
      const response = await fetch(`/api/notifications/subscriptions?companyId=${companyId}`)

      if (!response.ok) {
        throw new Error('Failed to fetch subscriptions')
      }

      return response.json()
    },
    enabled: !!companyId,
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

export function useCreateSubscription(companyId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (data: NotificationSubscriptionRequest): Promise<{ data: NotificationSubscription }> => {
      const response = await fetch(`/api/notifications/subscriptions?companyId=${companyId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      })

      if (!response.ok) {
        throw new Error('Failed to create subscription')
      }

      return response.json()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.notificationSubscriptions.byCompany(companyId) })
    },
  })
}

export function useUpdateSubscription(companyId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({
      subscriptionId,
      data,
    }: {
      subscriptionId: string
      data: NotificationSubscriptionUpdateRequest
    }): Promise<{ data: NotificationSubscription }> => {
      const response = await fetch(`/api/notifications/subscriptions?subscriptionId=${subscriptionId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      })

      if (!response.ok) {
        throw new Error('Failed to update subscription')
      }

      return response.json()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.notificationSubscriptions.byCompany(companyId) })
    },
  })
}

export function useToggleSubscription(companyId: string) {
  const updateSubscription = useUpdateSubscription(companyId)

  return useMutation({
    mutationFn: async ({
      subscriptionId,
      isEnabled,
    }: {
      subscriptionId: string
      isEnabled: boolean
    }) => {
      return updateSubscription.mutateAsync({
        subscriptionId,
        data: { is_enabled: isEnabled },
      })
    },
  })
}

export function useDeleteSubscription(companyId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (subscriptionId: string): Promise<{ message: string }> => {
      const response = await fetch(`/api/notifications/subscriptions?subscriptionId=${subscriptionId}`, {
        method: 'DELETE',
      })

      if (!response.ok) {
        throw new Error('Failed to delete subscription')
      }

      return response.json()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.notificationSubscriptions.byCompany(companyId) })
    },
  })
}
