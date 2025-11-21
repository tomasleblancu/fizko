"use client";

import { useQuery } from "@tanstack/react-query";
import { useMemo, useState, useCallback } from "react";
import { queryKeys } from "@/lib/query-keys";
import { getTimestamp } from "@/shared/lib/date-utils";
import type { DocumentWithType } from "@/types/database";

interface UseInfiniteCompanyDocumentsOptions {
  companyId: string;
  pageSize?: number;
}

const DEFAULT_PAGE_SIZE = 50;

export function useInfiniteCompanyDocuments({
  companyId,
  pageSize = DEFAULT_PAGE_SIZE
}: UseInfiniteCompanyDocumentsOptions) {
  const [displayedCount, setDisplayedCount] = useState(pageSize);

  // Fetch ALL documents once and cache them via internal API
  const { data: allDocuments, isLoading } = useQuery({
    queryKey: companyId ? queryKeys.documents.byCompany(companyId) : ['documents', 'empty'],
    queryFn: async (): Promise<DocumentWithType[]> => {
      const response = await fetch(`/api/documents?companyId=${companyId}`, {
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error('Failed to fetch documents');
      }

      const { data } = await response.json();
      return data as DocumentWithType[];
    },
    enabled: !!companyId,
    staleTime: 2 * 60 * 1000, // 2 minutes
    refetchOnWindowFocus: true,
  });

  // Client-side pagination
  const paginatedData = useMemo(() => {
    if (!allDocuments) return null;

    const documents = allDocuments.slice(0, displayedCount);
    const hasMore = displayedCount < allDocuments.length;

    return {
      pages: [{ documents }], // Wrap in pages structure for compatibility
      documents, // Flat array of displayed documents
      hasMore,
    };
  }, [allDocuments, displayedCount]);

  const fetchNextPage = useCallback(() => {
    if (!allDocuments) return;
    setDisplayedCount(prev => Math.min(prev + pageSize, allDocuments.length));
  }, [allDocuments, pageSize]);

  const hasNextPage = paginatedData?.hasMore ?? false;
  const isFetchingNextPage = false; // No actual fetching, just displaying more

  return {
    data: paginatedData,
    isLoading,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  };
}
