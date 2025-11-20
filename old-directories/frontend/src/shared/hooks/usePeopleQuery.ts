import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuth } from "@/app/providers/AuthContext";
import { useCompanyContext } from "@/app/providers/CompanyContext";
import type { Person, PersonCreate, PersonUpdate, PersonListResponse } from "@/shared/types/fizko";
import { API_BASE_URL } from "@/shared/lib/config";
import { apiFetch } from "@/shared/lib/api-client";
import { queryKeys } from "@/shared/lib/query-keys";

export type { Person };

interface UsePeopleOptions {
  status?: 'active' | 'inactive' | 'terminated';
  search?: string;
  page?: number;
  pageSize?: number;
}

/**
 * React Query hook for fetching people/personnel for the selected company.
 *
 * Uses CompanyContext to get the currently selected company ID.
 * Query key: ['home', 'people', companyId, status, search, page, pageSize]
 * Stale time: 3 minutes
 *
 * @param options - Query options (status filter, search, pagination)
 * @returns Query result with people array, total count, loading and error states
 *
 * @example
 * ```tsx
 * // Fetch all active people
 * const { data, isLoading } = usePeopleQuery({ status: 'active' });
 * const people = data?.people || [];
 * const total = data?.total || 0;
 *
 * // With search and pagination
 * const { data } = usePeopleQuery({
 *   search: 'juan',
 *   page: 2,
 *   pageSize: 20
 * });
 * ```
 */
export function usePeopleQuery(options: UsePeopleOptions = {}) {
  const { session } = useAuth();
  const { selectedCompanyId } = useCompanyContext();
  const {
    status,
    search,
    page = 1,
    pageSize = 50,
  } = options;

  return useQuery({
    queryKey: ['home', 'people', selectedCompanyId, status, search, page, pageSize],
    queryFn: async (): Promise<{ people: Person[]; total: number }> => {
      if (!session?.access_token) {
        throw new Error('No authenticated session');
      }

      // Build query params
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: pageSize.toString(),
      });

      if (status) {
        params.append('status', status);
      }

      if (search) {
        params.append('search', search);
      }

      if (selectedCompanyId) {
        params.append('company_id', selectedCompanyId);
      }

      const url = `${API_BASE_URL}/personnel/people/?${params.toString()}`;

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

      return {
        people: data.data,
        total: data.total,
      };
    },
    enabled: !!session?.access_token && !!selectedCompanyId,
    staleTime: 3 * 60 * 1000, // 3 minutes
  });
}

/**
 * React Query mutation hook for creating a new person.
 *
 * Uses CompanyContext to get the currently selected company ID.
 * Automatically invalidates the people query on success.
 *
 * @returns Mutation result with mutate function
 *
 * @example
 * ```tsx
 * const createMutation = useCreatePerson();
 *
 * const handleCreate = async () => {
 *   await createMutation.mutateAsync({
 *     rut: '12345678-9',
 *     first_name: 'Juan',
 *     last_name: 'Pérez',
 *     email: 'juan@example.com'
 *   });
 * };
 * ```
 */
export function useCreatePerson() {
  const { session } = useAuth();
  const { selectedCompanyId } = useCompanyContext();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (personData: PersonCreate): Promise<Person> => {
      if (!session?.access_token) {
        throw new Error('No authentication token available');
      }

      const url = `${API_BASE_URL}/personnel/people/`;

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

      return await response.json();
    },
    onSuccess: () => {
      // Invalidate all people queries for this company
      queryClient.invalidateQueries({
        queryKey: ['home', 'people', selectedCompanyId],
      });
    },
  });
}

/**
 * React Query mutation hook for updating an existing person.
 *
 * Uses CompanyContext to get the currently selected company ID.
 * Uses optimistic updates for instant UI feedback.
 *
 * @returns Mutation result with mutate function
 *
 * @example
 * ```tsx
 * const updateMutation = useUpdatePerson();
 *
 * const handleUpdate = async () => {
 *   await updateMutation.mutateAsync({
 *     personId: 'person-uuid',
 *     data: { email: 'newemail@example.com' }
 *   });
 * };
 * ```
 */
export function useUpdatePerson() {
  const { session } = useAuth();
  const { selectedCompanyId } = useCompanyContext();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ personId, data }: { personId: string; data: PersonUpdate }): Promise<Person> => {
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
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to update person: ${response.statusText}`);
      }

      return await response.json();
    },
    // Optimistic update
    onMutate: async ({ personId, data }) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({
        queryKey: ['home', 'people', selectedCompanyId],
      });

      // Snapshot previous values for all affected queries
      const previousQueries: Array<{ queryKey: any[]; data: any }> = [];

      queryClient.getQueryCache().findAll({
        queryKey: ['home', 'people', selectedCompanyId],
      }).forEach((query) => {
        const queryData = query.state.data as { people: Person[]; total: number } | undefined;
        if (queryData) {
          previousQueries.push({
            queryKey: query.queryKey,
            data: queryData,
          });

          // Optimistically update the person in the list
          queryClient.setQueryData(query.queryKey, {
            ...queryData,
            people: queryData.people.map((person) =>
              person.id === personId
                ? { ...person, ...data }
                : person
            ),
          });
        }
      });

      // Also update single person query if it exists
      const personQueryKey = ['home', 'person', personId];
      const previousPerson = queryClient.getQueryData<Person>(personQueryKey);
      if (previousPerson) {
        previousQueries.push({
          queryKey: personQueryKey,
          data: previousPerson,
        });
        queryClient.setQueryData(personQueryKey, { ...previousPerson, ...data });
      }

      return { previousQueries };
    },
    // On error, rollback
    onError: (_err, _variables, context) => {
      if (context?.previousQueries) {
        context.previousQueries.forEach(({ queryKey, data }) => {
          queryClient.setQueryData(queryKey, data);
        });
      }
    },
    // On success, update with server response
    onSuccess: (updatedPerson, { personId }) => {
      // Update all people lists
      queryClient.getQueryCache().findAll({
        queryKey: ['home', 'people', selectedCompanyId],
      }).forEach((query) => {
        const queryData = query.state.data as { people: Person[]; total: number } | undefined;
        if (queryData) {
          queryClient.setQueryData(query.queryKey, {
            ...queryData,
            people: queryData.people.map((person) =>
              person.id === personId ? updatedPerson : person
            ),
          });
        }
      });

      // Update single person query
      queryClient.setQueryData(['home', 'person', personId], updatedPerson);
    },
  });
}

/**
 * React Query mutation hook for deleting a person.
 *
 * Uses CompanyContext to get the currently selected company ID.
 * Uses optimistic updates for instant UI feedback.
 *
 * @returns Mutation result with mutate function
 *
 * @example
 * ```tsx
 * const deleteMutation = useDeletePerson();
 *
 * const handleDelete = async (personId: string) => {
 *   await deleteMutation.mutateAsync(personId);
 * };
 * ```
 */
export function useDeletePerson() {
  const { session } = useAuth();
  const { selectedCompanyId } = useCompanyContext();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (personId: string): Promise<void> => {
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
    },
    // Optimistic update - remove from cache immediately
    onMutate: async (personId) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({
        queryKey: ['home', 'people', selectedCompanyId],
      });

      // Snapshot previous values for all affected queries
      const previousQueries: Array<{ queryKey: any[]; data: any }> = [];

      queryClient.getQueryCache().findAll({
        queryKey: ['home', 'people', selectedCompanyId],
      }).forEach((query) => {
        const queryData = query.state.data as { people: Person[]; total: number } | undefined;
        if (queryData) {
          previousQueries.push({
            queryKey: query.queryKey,
            data: queryData,
          });

          // Optimistically remove the person from the list
          queryClient.setQueryData(query.queryKey, {
            ...queryData,
            people: queryData.people.filter((person) => person.id !== personId),
            total: queryData.total - 1,
          });
        }
      });

      return { previousQueries };
    },
    // On error, rollback
    onError: (_err, _personId, context) => {
      if (context?.previousQueries) {
        context.previousQueries.forEach(({ queryKey, data }) => {
          queryClient.setQueryData(queryKey, data);
        });
      }
    },
    // On success, just ensure the person is removed (already done optimistically)
    onSuccess: (_, personId) => {
      // Remove from single person query cache
      queryClient.removeQueries({
        queryKey: ['home', 'person', personId],
      });
    },
  });
}

/**
 * React Query query hook for fetching a single person by ID.
 *
 * Query key: ['home', 'person', personId]
 * Stale time: 5 minutes
 *
 * @param personId - The person ID to fetch
 * @returns Query result with person data, loading and error states
 *
 * @example
 * ```tsx
 * const { data: person, isLoading } = usePersonQuery('person-uuid');
 * ```
 */
export function usePersonQuery(personId: string | null) {
  const { session } = useAuth();

  return useQuery({
    queryKey: ['home', 'person', personId],
    queryFn: async (): Promise<Person> => {
      if (!session?.access_token || !personId) {
        throw new Error('No authenticated session or person ID');
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
    },
    enabled: !!session?.access_token && !!personId,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}
