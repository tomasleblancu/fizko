"use client";

import { useQuery } from "@tanstack/react-query";
import { queryKeys } from "@/lib/query-keys";
import type { PersonListResponse, PersonStatus } from "@/types/personnel";

interface UsePersonnelOptions {
  companyId: string;
  status?: PersonStatus;
  search?: string;
  page?: number;
  pageSize?: number;
}

/**
 * Hook to fetch personnel (people/employees) for a company
 *
 * Fetches all employees for a company with optional filtering and pagination.
 *
 * @param companyId - Company UUID
 * @param status - Optional filter by status (active, inactive, terminated)
 * @param search - Optional search by name or RUT
 * @param page - Page number (default 1)
 * @param pageSize - Items per page (default 50)
 */
export function usePersonnel({
  companyId,
  status,
  search,
  page = 1,
  pageSize = 50,
}: UsePersonnelOptions) {
  return useQuery({
    queryKey: queryKeys.personnel.byCompany(companyId, status, search, page),
    queryFn: async (): Promise<PersonListResponse> => {
      const params = new URLSearchParams({
        companyId,
        page: page.toString(),
        pageSize: pageSize.toString(),
      });

      if (status) {
        params.append('status', status);
      }

      if (search) {
        params.append('search', search);
      }

      const response = await fetch(`/api/personnel?${params.toString()}`);

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to fetch personnel');
      }

      return response.json();
    },
    enabled: !!companyId,
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchOnWindowFocus: true,
  });
}
