"use client";

import { useQuery } from "@tanstack/react-query";
import { queryKeys } from "@/lib/query-keys";
import type { UpcomingEventsResponse } from "@/types/calendar";

interface UseUpcomingEventsOptions {
  companyId: string;
  daysAhead?: number;
}

/**
 * Hook to fetch upcoming calendar events for a company
 *
 * Fetches tax calendar events within the specified days ahead window.
 * Events are filtered by company and date range, sorted by due date ascending.
 *
 * @param companyId - Company UUID
 * @param daysAhead - Number of days to look ahead (defaults to 30)
 */
export function useUpcomingEvents({ companyId, daysAhead = 30 }: UseUpcomingEventsOptions) {
  return useQuery({
    queryKey: queryKeys.calendar.upcoming(companyId, daysAhead),
    queryFn: async (): Promise<UpcomingEventsResponse> => {
      const params = new URLSearchParams({
        companyId,
        daysAhead: daysAhead.toString()
      });

      const response = await fetch(`/api/calendar/upcoming?${params.toString()}`);

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to fetch calendar events');
      }

      return response.json();
    },
    enabled: !!companyId,
    staleTime: 5 * 60 * 1000, // 5 minutes - calendar events change less frequently
    refetchOnWindowFocus: true,
  });
}
