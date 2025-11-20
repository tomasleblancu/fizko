import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { queryKeys } from '@/lib/query-keys'
import type { ProfileResponse, ProfileUpdateRequest } from '@/types/profile'

export function useProfile(userId: string) {
  return useQuery({
    queryKey: queryKeys.profile.byUser(userId),
    queryFn: async (): Promise<ProfileResponse> => {
      const response = await fetch(`/api/profile?userId=${userId}`)

      if (!response.ok) {
        throw new Error('Failed to fetch profile')
      }

      return response.json()
    },
    enabled: !!userId,
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

export function useUpdateProfile(userId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (data: ProfileUpdateRequest): Promise<ProfileResponse> => {
      const response = await fetch(`/api/profile?userId=${userId}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      })

      if (!response.ok) {
        throw new Error('Failed to update profile')
      }

      return response.json()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.profile.byUser(userId) })
    },
  })
}
