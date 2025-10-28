import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';
import type { Company } from '../types/fizko';
import { API_BASE_URL } from '../lib/config';
import { useDashboardCache } from '../contexts/DashboardCacheContext';
import { apiFetch } from '../lib/api-client';

export function useCompany() {
  const { session } = useAuth();
  const cache = useDashboardCache();
  const [company, setCompany] = useState<Company | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchCompany = useCallback(async (skipCache = false) => {
    if (!session?.access_token) {
      setLoading(false);
      return;
    }

    const cacheKey = `companies:${session.user.id}`;

    // Try to get from cache first (stale-while-revalidate)
    if (!skipCache) {
      const cached = cache.get<Company>(cacheKey);
      if (cached) {
        setCompany(cached.data);
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

      const response = await apiFetch(`${API_BASE_URL}/companies`, {
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch companies: ${response.statusText}`);
      }

      const result = await response.json();
      // Get first company from the list or null if empty
      const companyData = result.data && result.data.length > 0 ? result.data[0] : null;

      setCompany(companyData);

      // Update cache
      if (companyData) {
        cache.set(cacheKey, companyData);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch companies');
      setCompany(null);
    } finally {
      setLoading(false);
    }
  }, [session?.access_token, session?.user.id, cache]);

  useEffect(() => {
    fetchCompany();
  }, [fetchCompany]);

  return {
    company,
    loading,
    error,
    refresh: () => fetchCompany(true),
  };
}
