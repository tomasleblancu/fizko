import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';
import type { CalendarEvent, CalendarStats } from '../types/fizko';
import { API_BASE_URL } from '../lib/config';
import { useDashboardCache } from '../contexts/DashboardCacheContext';
import { apiFetch } from '../lib/api-client';

export function useCalendar(companyId: string | null, daysAhead = 30, includeStats = false) {
  const { session } = useAuth();
  const cache = useDashboardCache();
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [stats, setStats] = useState<CalendarStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchCalendarData = useCallback(async (skipCache = false) => {
    if (!session?.access_token || !companyId) {
      setLoading(false);
      return;
    }

    const cacheKey = `calendar:${companyId}:${daysAhead}`;

    // Try to get from cache first (stale-while-revalidate)
    if (!skipCache) {
      const cached = cache.get<{ events: CalendarEvent[]; stats: CalendarStats }>(cacheKey);
      if (cached) {
        setEvents(cached.data.events);
        setStats(cached.data.stats);
        setLoading(false);
        setError(null);

        // If data is fresh, return early
        if (!cached.isStale) {
          return;
        }
        // Otherwise, continue to fetch in background
      }
    }

    try {
      if (!cache.get(cacheKey) || skipCache) {
        setLoading(true);
      }
      setError(null);

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

      const calendarData = {
        events: eventsData.data || [],
        stats: statsData?.data || null,
      };

      setEvents(calendarData.events);
      setStats(calendarData.stats);
      cache.set(cacheKey, calendarData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch calendar data');
      setEvents([]);
      setStats(null);
    } finally {
      setLoading(false);
    }
  }, [session?.access_token, companyId, daysAhead, includeStats, cache]);

  useEffect(() => {
    fetchCalendarData();
  }, [fetchCalendarData]);

  return {
    events,
    stats,
    loading,
    error,
    refresh: () => fetchCalendarData(true),
  };
}
