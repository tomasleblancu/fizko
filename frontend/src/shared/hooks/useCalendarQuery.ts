import { useQuery } from '@tanstack/react-query';
import { useAuth } from "@/app/providers/AuthContext";
import { useCompanyContext } from "@/app/providers/CompanyContext";
import type { CalendarEvent, CalendarStats } from "@/shared/types/fizko";
import { API_BASE_URL } from "@/shared/lib/config";
import { apiFetch } from "@/shared/lib/api-client";
import { queryKeys } from "@/shared/lib/query-keys";

interface CalendarData {
  events: CalendarEvent[];
  stats: CalendarStats | null;
}

/**
 * React Query hook for fetching calendar events for the selected company.
 *
 * Uses CompanyContext to get the currently selected company ID.
 * Query key: ['home', 'calendar', companyId, daysAhead, includeStats]
 * Stale time: 5 minutes
 *
 * @param daysAhead - Number of days ahead to fetch events (default: 30)
 * @param includeStats - Whether to include calendar statistics (default: false)
 * @param enabled - Whether the query should run (default: true)
 * @returns Query result with events and optionally stats, loading and error states
 *
 * @example
 * ```tsx
 * // Fetch events for next 30 days
 * const { data, isLoading } = useCalendarQuery();
 * const events = data?.events || [];
 *
 * // Fetch events with statistics
 * const { data } = useCalendarQuery(30, true);
 * const stats = data?.stats;
 * ```
 */
export function useCalendarQuery(
  daysAhead: number = 30,
  includeStats: boolean = false,
  enabled: boolean = true
) {
  const { session } = useAuth();
  const { selectedCompanyId } = useCompanyContext();

  return useQuery({
    queryKey: ['home', 'calendar', selectedCompanyId, daysAhead, includeStats],
    queryFn: async (): Promise<CalendarData> => {
      if (!session?.access_token) {
        throw new Error('No authenticated session');
      }

      // Fetch events (and optionally stats) in parallel for better performance
      const eventsUrl = `${API_BASE_URL}/calendar/events/upcoming?days_ahead=${daysAhead}&company_id=${selectedCompanyId}`;

      let eventsData;
      let statsData = null;

      if (includeStats) {
        const statsUrl = `${API_BASE_URL}/calendar/stats?company_id=${selectedCompanyId}`;
        const [eventsResponse, statsResponse] = await Promise.all([
          apiFetch(eventsUrl, {
            headers: {
              'Authorization': `Bearer ${session.access_token}`,
              'Content-Type': 'application/json',
            },
          }),
          apiFetch(statsUrl, {
            headers: {
              'Authorization': `Bearer ${session.access_token}`,
              'Content-Type': 'application/json',
            },
          }),
        ]);

        if (!eventsResponse.ok) {
          throw new Error(`Failed to fetch calendar events: ${eventsResponse.statusText}`);
        }

        if (!statsResponse.ok) {
          throw new Error(`Failed to fetch calendar stats: ${statsResponse.statusText}`);
        }

        [eventsData, statsData] = await Promise.all([
          eventsResponse.json(),
          statsResponse.json(),
        ]);
      } else {
        // Only fetch events
        const eventsResponse = await apiFetch(eventsUrl, {
          headers: {
            'Authorization': `Bearer ${session.access_token}`,
            'Content-Type': 'application/json',
          },
        });

        if (!eventsResponse.ok) {
          throw new Error(`Failed to fetch calendar events: ${eventsResponse.statusText}`);
        }

        eventsData = await eventsResponse.json();
      }

      return {
        events: eventsData.data || [],
        stats: statsData?.data || null,
      };
    },
    enabled: !!session?.access_token && !!selectedCompanyId && enabled,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}
