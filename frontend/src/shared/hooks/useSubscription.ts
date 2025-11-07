/**
 * Hook to fetch and manage subscription information
 */

import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@/app/providers/AuthContext";
import { apiFetch } from "@/shared/lib/api-client";
import { queryKeys } from "@/shared/lib/query-keys";
import type { SubscriptionInfo } from "@/shared/types/subscription";

export function useSubscription() {
  const { session } = useAuth();

  return useQuery({
    queryKey: queryKeys.subscription.current,
    queryFn: async (): Promise<SubscriptionInfo | null> => {
      if (!session?.access_token) {
        return null;
      }

      try {
        const response = await apiFetch("/api/subscriptions/current", {
          headers: {
            Authorization: `Bearer ${session.access_token}`,
          },
        });

        if (!response.ok) {
          // No subscription or error - return null instead of throwing
          return null;
        }

        return response.json();
      } catch (error) {
        console.error("Failed to fetch subscription:", error);
        return null;
      }
    },
    enabled: !!session?.access_token,
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: false, // Don't retry on error - just return null
  });
}

/**
 * Hook to check if user has an active subscription
 */
export function useHasActiveSubscription() {
  const { data: subscription, isLoading } = useSubscription();

  const hasActiveSubscription =
    subscription &&
    (subscription.status === "trialing" || subscription.status === "active");

  return {
    hasActiveSubscription: !!hasActiveSubscription,
    isLoading,
    subscription,
  };
}

/**
 * Hook to check if user is in trial period
 */
export function useIsInTrial() {
  const { data: subscription } = useSubscription();

  const isInTrial =
    subscription &&
    subscription.status === "trialing" &&
    subscription.is_trial === true;

  return {
    isInTrial: !!isInTrial,
    trialEndsAt: subscription?.trial_end,
    subscription,
  };
}
