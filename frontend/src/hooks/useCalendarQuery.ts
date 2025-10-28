import { useQuery } from '@tanstack/react-query';
import { useAuth } from '../contexts/AuthContext';
import type { CalendarEvent, CalendarStats } from '../types/fizko';
import { API_BASE_URL } from '../lib/config';
import { apiFetch } from '../lib/api-client';

interface CalendarData {
  events: CalendarEvent[];
  stats: CalendarStats | null;
}

/**
 * React Query hook for fetching calendar events for a company.
 *
 * Query key: ['home', 'calendar', companyId, daysAhead]
 * Stale time: 5 minutes
 *
 * @param companyId - The company ID to fetch calendar for
 * @param daysAhead - Number of days ahead to fetch events (default: 30)
 * @param includeStats - Whether to include calendar statistics (default: false)
 * @returns Query result with events and optionally stats, loading and error states
 *
 * @example
 * ```tsx
 * // Fetch events for next 30 days
 * const { data, isLoading } = useCalendarQuery(companyId);
 * const events = data?.events || [];
 *
 * // Fetch events with statistics
 * const { data } = useCalendarQuery(companyId, 30, true);
 * const stats = data?.stats;
 * ```
 */
export function useCalendarQuery(
  companyId: string | null,
  daysAhead: number = 30,
  includeStats: boolean = false
) {
  const { session } = useAuth();

  return useQuery({
    queryKey: ['home', 'calendar', companyId, daysAhead, includeStats],
    queryFn: async (): Promise<CalendarData> => {
      if (!session?.access_token || !companyId) {
        throw new Error('No authenticated session or company ID');
      }

      // Fetch events (and optionally stats) in parallel for better performance
      const eventsUrl = `${API_BASE_URL}/calendar/events/upcoming?company_id=${companyId}&days_ahead=${daysAhead}`;

      let eventsData;
      let statsData = null;

      if (includeStats) {
        const statsUrl = `${API_BASE_URL}/calendar/stats?company_id=${companyId}`;
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
    enabled: !!session?.access_token && !!companyId,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}
