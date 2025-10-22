import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';
import type { TaxSummary } from '../types/fizko';
import { API_BASE_URL } from '../lib/config';
import { useDashboardCache } from '../contexts/DashboardCacheContext';

export function useTaxSummary(companyId: string | null, period?: string) {
  const { session } = useAuth();
  const cache = useDashboardCache();
  const [taxSummary, setTaxSummary] = useState<TaxSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchTaxSummary = useCallback(async (skipCache = false) => {
    if (!session?.access_token || !companyId) {
      setLoading(false);
      return;
    }

    const cacheKey = `tax-summary:${companyId}:${period || 'default'}`;

    // Try to get from cache first (stale-while-revalidate)
    if (!skipCache) {
      const cached = cache.get<TaxSummary | null>(cacheKey);
      if (cached) {
        setTaxSummary(cached.data);
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

      const params = new URLSearchParams();
      if (period) {
        params.append('period', period);
      }

      const url = `${API_BASE_URL}/tax-summary/${companyId}${params.toString() ? `?${params.toString()}` : ''}`;

      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        // 404 is expected for new companies without tax data yet
        if (response.status === 404) {
          setTaxSummary(null);
          setError(null);
          cache.set(cacheKey, null);
          return;
        }
        throw new Error(`Failed to fetch tax summary: ${response.statusText}`);
      }

      const data = await response.json();
      setTaxSummary(data);
      cache.set(cacheKey, data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch tax summary');
      setTaxSummary(null);
    } finally {
      setLoading(false);
    }
  }, [session?.access_token, companyId, period, cache]);

  useEffect(() => {
    fetchTaxSummary();
  }, [fetchTaxSummary]);

  return {
    taxSummary,
    loading,
    error,
    refresh: () => fetchTaxSummary(true),
  };
}
