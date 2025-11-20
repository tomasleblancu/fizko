"use client";

import { useQuery } from "@tanstack/react-query";
import { queryKeys } from "@/lib/query-keys";
import type { Contact, ContactType } from "@/types/contacts";

interface UseContactsOptions {
  companyId: string;
  contactType?: ContactType;
}

/**
 * Hook to fetch contacts for a company
 *
 * Fetches all contacts (providers and/or clients) for a company.
 * Can be filtered by contact type.
 *
 * @param companyId - Company UUID
 * @param contactType - Optional filter by contact type (provider, client, both)
 */
export function useContacts({ companyId, contactType }: UseContactsOptions) {
  return useQuery({
    queryKey: queryKeys.contacts.byCompany(companyId, contactType),
    queryFn: async (): Promise<Contact[]> => {
      const params = new URLSearchParams({ companyId });
      if (contactType) {
        params.append('contactType', contactType);
      }

      const response = await fetch(`/api/contacts?${params.toString()}`);

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to fetch contacts');
      }

      return response.json();
    },
    enabled: !!companyId,
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchOnWindowFocus: true,
  });
}
