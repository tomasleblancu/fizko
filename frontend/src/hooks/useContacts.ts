import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { API_BASE_URL } from '../lib/config';
import { useDashboardCache } from '../contexts/DashboardCacheContext';
import { apiFetch } from '../lib/api-client';

export interface Contact {
  id: string;
  rut: string;
  business_name: string;
  trade_name?: string;
  contact_type: 'provider' | 'client' | 'both';
  address?: string;
  phone?: string;
  email?: string;
  created_at: string;
  updated_at: string;
}

export function useContacts(companyId: string | null | undefined) {
  const { session } = useAuth();
  const cache = useDashboardCache();
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchContacts = useCallback(async (skipCache = false) => {
    if (!session?.access_token || !companyId) {
      setLoading(false);
      return;
    }

    const cacheKey = `contacts:${companyId}`;

    // Try to get from cache first (stale-while-revalidate)
    if (!skipCache) {
      const cached = cache.get<Contact[]>(cacheKey);
      if (cached) {
        setContacts(cached.data);
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

      const response = await apiFetch(`${API_BASE_URL}/contacts?company_id=${companyId}`, {
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch contacts');
      }

      const data = await response.json();
      setContacts(data);
      cache.set(cacheKey, data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error loading contacts');
      setContacts([]);
    } finally {
      setLoading(false);
    }
  }, [session?.access_token, companyId, cache]);

  useEffect(() => {
    fetchContacts();
  }, [fetchContacts]);

  return {
    contacts,
    loading,
    error,
    refresh: () => fetchContacts(true),
  };
}
