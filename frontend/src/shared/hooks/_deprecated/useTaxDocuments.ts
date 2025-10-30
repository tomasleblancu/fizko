import { useState, useEffect, useCallback } from 'react';
import { useAuth } from "@/app/providers/AuthContext";
import type { TaxDocument } from "@/shared/types/fizko";
import { API_BASE_URL } from "@/shared/lib/config";
import { useDashboardCache } from "@/app/providers/DashboardCacheContext";
import { apiFetch } from "@/shared/lib/api-client";

export function useTaxDocuments(companyId: string | null, limit: number = 10, period?: string) {
  const { session } = useAuth();
  const cache = useDashboardCache();
  const [documents, setDocuments] = useState<TaxDocument[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDocuments = useCallback(async (skipCache = false) => {
    if (!session?.access_token || !companyId) {
      setLoading(false);
      return;
    }

    const cacheKey = `tax-documents:${companyId}:${limit}:${period || 'default'}`;

    // Try to get from cache first (stale-while-revalidate)
    if (!skipCache) {
      const cached = cache.get<TaxDocument[]>(cacheKey);
      if (cached) {
        setDocuments(cached.data);
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
      params.append('limit', limit.toString());
      if (period) {
        params.append('period', period);
      }

      const url = `${API_BASE_URL}/tax-documents/${companyId}?${params.toString()}`;

      const response = await apiFetch(url, {
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        // 404 is expected for new companies without documents yet
        if (response.status === 404) {
          setDocuments([]);
          setError(null);
          cache.set(cacheKey, []);
          return;
        }
        throw new Error(`Failed to fetch tax documents: ${response.statusText}`);
      }

      const data = await response.json();
      setDocuments(data);
      cache.set(cacheKey, data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch tax documents');
      setDocuments([]);
    } finally {
      setLoading(false);
    }
  }, [session?.access_token, companyId, limit, period, cache]);

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  return {
    documents,
    loading,
    error,
    refresh: () => fetchDocuments(true),
  };
}
