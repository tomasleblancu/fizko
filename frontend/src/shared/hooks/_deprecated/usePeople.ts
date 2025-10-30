import { useState, useEffect, useCallback } from 'react';
import { useAuth } from "@/app/providers/AuthContext";
import type { Person, PersonCreate, PersonUpdate, PersonListResponse } from "@/shared/types/fizko";
import { API_BASE_URL } from "@/shared/lib/config";
import { useDashboardCache } from "@/app/providers/DashboardCacheContext";
import { apiFetch } from "@/shared/lib/api-client";

export type { Person };

interface UsePeopleOptions {
  status?: 'active' | 'inactive' | 'terminated';
  search?: string;
  page?: number;
  pageSize?: number;
}

export function usePeople(companyId: string | null, options: UsePeopleOptions = {}) {
  const { session } = useAuth();
  const cache = useDashboardCache();
  const [people, setPeople] = useState<Person[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const {
    status,
    search,
    page = 1,
    pageSize = 50,
  } = options;

  const fetchPeople = useCallback(async (skipCache = false) => {
    if (!session?.access_token || !companyId) {
      setLoading(false);
      return;
    }

    const cacheKey = `people:${companyId}:${status || 'all'}:${search || ''}:${page}:${pageSize}`;

    // Try to get from cache first (stale-while-revalidate)
    if (!skipCache) {
      const cached = cache.get<PersonListResponse>(cacheKey);
      if (cached) {
        setPeople(cached.data.data);
        setTotal(cached.data.total);
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

      // Build query params
      const params = new URLSearchParams({
        company_id: companyId,
        page: page.toString(),
        page_size: pageSize.toString(),
      });

      if (status) {
        params.append('status', status);
      }

      if (search) {
        params.append('search', search);
      }

      const url = `${API_BASE_URL}/personnel/people?${params.toString()}`;

      const response = await apiFetch(url, {
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch people: ${response.statusText}`);
      }

      const data: PersonListResponse = await response.json();

      setPeople(data.data);
      setTotal(data.total);
      cache.set(cacheKey, data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch people');
      setPeople([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, [session?.access_token, companyId, status, search, page, pageSize, cache]);

  useEffect(() => {
    fetchPeople();
  }, [fetchPeople]);

  const createPerson = useCallback(async (personData: PersonCreate): Promise<Person> => {
    if (!session?.access_token) {
      throw new Error('No authentication token available');
    }

    const url = `${API_BASE_URL}/personnel/people`;

    const response = await apiFetch(url, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${session.access_token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(personData),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Failed to create person: ${response.statusText}`);
    }

    const newPerson: Person = await response.json();

    // Invalidate cache and refetch
    await fetchPeople(true);

    return newPerson;
  }, [session?.access_token, fetchPeople]);

  const updatePerson = useCallback(async (personId: string, personData: PersonUpdate): Promise<Person> => {
    if (!session?.access_token) {
      throw new Error('No authentication token available');
    }

    const url = `${API_BASE_URL}/personnel/people/${personId}`;

    const response = await apiFetch(url, {
      method: 'PATCH',
      headers: {
        'Authorization': `Bearer ${session.access_token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(personData),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Failed to update person: ${response.statusText}`);
    }

    const updatedPerson: Person = await response.json();

    // Invalidate cache and refetch
    await fetchPeople(true);

    return updatedPerson;
  }, [session?.access_token, fetchPeople]);

  const deletePerson = useCallback(async (personId: string): Promise<void> => {
    if (!session?.access_token) {
      throw new Error('No authentication token available');
    }

    const url = `${API_BASE_URL}/personnel/people/${personId}`;

    const response = await apiFetch(url, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${session.access_token}`,
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Failed to delete person: ${response.statusText}`);
    }

    // Invalidate cache and refetch
    await fetchPeople(true);
  }, [session?.access_token, fetchPeople]);

  const getPerson = useCallback(async (personId: string): Promise<Person> => {
    if (!session?.access_token) {
      throw new Error('No authentication token available');
    }

    const url = `${API_BASE_URL}/personnel/people/${personId}`;

    const response = await apiFetch(url, {
      headers: {
        'Authorization': `Bearer ${session.access_token}`,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Failed to fetch person: ${response.statusText}`);
    }

    return await response.json();
  }, [session?.access_token]);

  return {
    people,
    total,
    loading,
    error,
    refresh: () => fetchPeople(true),
    createPerson,
    updatePerson,
    deletePerson,
    getPerson,
  };
}
