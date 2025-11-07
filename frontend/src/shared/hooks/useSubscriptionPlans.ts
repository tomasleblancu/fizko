/**
 * Hook to fetch subscription plans
 *
 * Plans are precached in Home component for instant loading
 */

import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/shared/lib/api-client";
import { queryKeys } from "@/shared/lib/query-keys";
import type { SubscriptionPlan } from "@/shared/types/subscription";

export function useSubscriptionPlans() {
  return useQuery({
    queryKey: queryKeys.subscription.plans,
    queryFn: async (): Promise<SubscriptionPlan[]> => {
      const response = await apiFetch("/api/subscriptions/plans");

      if (!response.ok) {
        throw new Error("Failed to fetch subscription plans");
      }

      const data = await response.json();
      return data.plans || [];
    },
    staleTime: 10 * 60 * 1000, // 10 minutes - plans don't change often
    gcTime: 30 * 60 * 1000, // Keep in cache for 30 minutes
  });
}
