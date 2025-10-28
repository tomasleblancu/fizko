import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '../contexts/AuthContext';
import { API_BASE_URL } from '../lib/config';
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

export interface ContactCreate {
  rut: string;
  business_name: string;
  trade_name?: string;
  contact_type: 'provider' | 'client' | 'both';
  address?: string;
  phone?: string;
  email?: string;
}

export interface ContactUpdate {
  rut?: string;
  business_name?: string;
  trade_name?: string;
  contact_type?: 'provider' | 'client' | 'both';
  address?: string;
  phone?: string;
  email?: string;
}

/**
 * React Query hook for fetching contacts for a company.
 *
 * Query key: ['home', 'contacts', companyId]
 * Stale time: 5 minutes
 *
 * @param companyId - The company ID to fetch contacts for
 * @returns Query result with contacts array, loading and error states
 *
 * @example
 * ```tsx
 * const { data: contacts = [], isLoading } = useContactsQuery(companyId);
 * ```
 */
export function useContactsQuery(companyId: string | null | undefined) {
  const { session } = useAuth();

  return useQuery({
    queryKey: ['home', 'contacts', companyId],
    queryFn: async (): Promise<Contact[]> => {
      if (!session?.access_token || !companyId) {
        throw new Error('No authenticated session or company ID');
      }

      const response = await apiFetch(`${API_BASE_URL}/contacts?company_id=${companyId}`, {
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch contacts');
      }

      return await response.json();
    },
    enabled: !!session?.access_token && !!companyId,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

/**
 * React Query mutation hook for creating a new contact.
 *
 * Automatically invalidates the contacts query on success.
 *
 * @param companyId - The company ID to create contact for
 * @returns Mutation result with mutate function
 *
 * @example
 * ```tsx
 * const createMutation = useCreateContact(companyId);
 *
 * const handleCreate = async () => {
 *   await createMutation.mutateAsync({
 *     rut: '12345678-9',
 *     business_name: 'Acme Corp',
 *     contact_type: 'client'
 *   });
 * };
 * ```
 */
export function useCreateContact(companyId: string | null | undefined) {
  const { session } = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (contactData: ContactCreate): Promise<Contact> => {
      if (!session?.access_token || !companyId) {
        throw new Error('No authenticated session or company ID');
      }

      const response = await apiFetch(`${API_BASE_URL}/contacts`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ ...contactData, company_id: companyId }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to create contact: ${response.statusText}`);
      }

      return await response.json();
    },
    onSuccess: () => {
      // Invalidate contacts query to refetch
      queryClient.invalidateQueries({
        queryKey: ['home', 'contacts', companyId],
      });
    },
  });
}

/**
 * React Query mutation hook for updating an existing contact.
 *
 * Automatically invalidates the contacts query on success.
 *
 * @param companyId - The company ID
 * @returns Mutation result with mutate function
 *
 * @example
 * ```tsx
 * const updateMutation = useUpdateContact(companyId);
 *
 * const handleUpdate = async () => {
 *   await updateMutation.mutateAsync({
 *     contactId: 'contact-uuid',
 *     data: { phone: '+56912345678' }
 *   });
 * };
 * ```
 */
export function useUpdateContact(companyId: string | null | undefined) {
  const { session } = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ contactId, data }: { contactId: string; data: ContactUpdate }): Promise<Contact> => {
      if (!session?.access_token) {
        throw new Error('No authenticated session');
      }

      const response = await apiFetch(`${API_BASE_URL}/contacts/${contactId}`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to update contact: ${response.statusText}`);
      }

      return await response.json();
    },
    onSuccess: () => {
      // Invalidate contacts query to refetch
      queryClient.invalidateQueries({
        queryKey: ['home', 'contacts', companyId],
      });
    },
  });
}

/**
 * React Query mutation hook for deleting a contact.
 *
 * Automatically invalidates the contacts query on success.
 *
 * @param companyId - The company ID
 * @returns Mutation result with mutate function
 *
 * @example
 * ```tsx
 * const deleteMutation = useDeleteContact(companyId);
 *
 * const handleDelete = async (contactId: string) => {
 *   await deleteMutation.mutateAsync(contactId);
 * };
 * ```
 */
export function useDeleteContact(companyId: string | null | undefined) {
  const { session } = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (contactId: string): Promise<void> => {
      if (!session?.access_token) {
        throw new Error('No authenticated session');
      }

      const response = await apiFetch(`${API_BASE_URL}/contacts/${contactId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to delete contact: ${response.statusText}`);
      }
    },
    onSuccess: () => {
      // Invalidate contacts query to refetch
      queryClient.invalidateQueries({
        queryKey: ['home', 'contacts', companyId],
      });
    },
  });
}
