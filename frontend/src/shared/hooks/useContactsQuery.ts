import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuth } from "@/app/providers/AuthContext";
import { useCompanyContext } from "@/app/providers/CompanyContext";
import { API_BASE_URL } from "@/shared/lib/config";
import { apiFetch } from "@/shared/lib/api-client";
import { queryKeys } from "@/shared/lib/query-keys";

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
 * React Query hook for fetching contacts for the selected company.
 *
 * Uses CompanyContext to get the currently selected company ID.
 * Query key: ['home', 'contacts', companyId]
 * Stale time: 5 minutes
 *
 * @returns Query result with contacts array, loading and error states
 *
 * @example
 * ```tsx
 * const { data: contacts = [], isLoading } = useContactsQuery();
 * ```
 */
export function useContactsQuery() {
  const { session } = useAuth();
  const { selectedCompanyId } = useCompanyContext();

  return useQuery({
    queryKey: queryKeys.contacts.byCompany(selectedCompanyId || ''),
    queryFn: async (): Promise<Contact[]> => {
      if (!session?.access_token) {
        throw new Error('No authenticated session');
      }

      const response = await apiFetch(`${API_BASE_URL}/contacts?company_id=${selectedCompanyId}`, {
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
    enabled: !!session?.access_token && !!selectedCompanyId,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

/**
 * React Query mutation hook for creating a new contact.
 *
 * Uses CompanyContext to get the currently selected company ID.
 * Automatically invalidates the contacts query on success.
 *
 * @returns Mutation result with mutate function
 *
 * @example
 * ```tsx
 * const createMutation = useCreateContact();
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
export function useCreateContact() {
  const { session } = useAuth();
  const { selectedCompanyId } = useCompanyContext();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (contactData: ContactCreate): Promise<Contact> => {
      if (!session?.access_token || !selectedCompanyId) {
        throw new Error('No authenticated session or company ID');
      }

      const response = await apiFetch(`${API_BASE_URL}/contacts`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ ...contactData, company_id: selectedCompanyId }),
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
        queryKey: queryKeys.contacts.byCompany(selectedCompanyId || ''),
      });
    },
  });
}

/**
 * React Query mutation hook for updating an existing contact.
 *
 * Uses CompanyContext to get the currently selected company ID.
 * Automatically invalidates the contacts query on success.
 *
 * @returns Mutation result with mutate function
 *
 * @example
 * ```tsx
 * const updateMutation = useUpdateContact();
 *
 * const handleUpdate = async () => {
 *   await updateMutation.mutateAsync({
 *     contactId: 'contact-uuid',
 *     data: { phone: '+56912345678' }
 *   });
 * };
 * ```
 */
export function useUpdateContact() {
  const { session } = useAuth();
  const { selectedCompanyId } = useCompanyContext();
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
        queryKey: queryKeys.contacts.byCompany(selectedCompanyId || ''),
      });
    },
  });
}

/**
 * React Query mutation hook for deleting a contact.
 *
 * Uses CompanyContext to get the currently selected company ID.
 * Automatically invalidates the contacts query on success.
 *
 * @returns Mutation result with mutate function
 *
 * @example
 * ```tsx
 * const deleteMutation = useDeleteContact();
 *
 * const handleDelete = async (contactId: string) => {
 *   await deleteMutation.mutateAsync(contactId);
 * };
 * ```
 */
export function useDeleteContact() {
  const { session } = useAuth();
  const { selectedCompanyId } = useCompanyContext();
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
        queryKey: queryKeys.contacts.byCompany(selectedCompanyId || ''),
      });
    },
  });
}
