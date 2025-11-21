"use client";

import { useQuery } from "@tanstack/react-query";
import { useMemo, useState, useCallback } from "react";
import { createClient } from "@/lib/supabase/client";
import { queryKeys } from "@/lib/query-keys";
import { getTimestamp } from "@/shared/lib/date-utils";
import type { SalesDocument, PurchaseDocument, DocumentWithType } from "@/types/database";

interface UseInfiniteCompanyDocumentsOptions {
  companyId: string;
  pageSize?: number;
}

const DEFAULT_PAGE_SIZE = 50;

export function useInfiniteCompanyDocuments({
  companyId,
  pageSize = DEFAULT_PAGE_SIZE
}: UseInfiniteCompanyDocumentsOptions) {
  const supabase = createClient();
  const [displayedCount, setDisplayedCount] = useState(pageSize);

  // Fetch ALL documents once and cache them
  const { data: allDocuments, isLoading } = useQuery({
    queryKey: companyId ? queryKeys.documents.byCompany(companyId) : ['documents', 'empty'],
    queryFn: async (): Promise<DocumentWithType[]> => {
      // Fetch ALL sales documents
      const { data: salesData, error: salesError } = await supabase
        .from("sales_documents")
        .select("*")
        .eq("company_id", companyId)
        .order("issue_date", { ascending: false });

      if (salesError) throw salesError;

      // Fetch ALL purchase documents
      const { data: purchasesData, error: purchasesError } = await supabase
        .from("purchase_documents")
        .select("*")
        .eq("company_id", companyId)
        .order("issue_date", { ascending: false });

      if (purchasesError) throw purchasesError;

      // Transform sales documents to unified format
      const salesDocuments: DocumentWithType[] = (salesData || []).map((doc: SalesDocument) => ({
        ...doc,
        type: 'sale' as const,
        counterparty_rut: doc.recipient_rut,
        counterparty_name: doc.recipient_name,
      }));

      // Transform purchase documents to unified format
      const purchaseDocuments: DocumentWithType[] = (purchasesData || []).map((doc: PurchaseDocument) => ({
        ...doc,
        type: 'purchase' as const,
        counterparty_rut: doc.sender_rut,
        counterparty_name: doc.sender_name,
      }));

      // Combine and sort by issue_date
      return [...salesDocuments, ...purchaseDocuments].sort(
        (a, b) => getTimestamp(b.issue_date) - getTimestamp(a.issue_date)
      );
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
