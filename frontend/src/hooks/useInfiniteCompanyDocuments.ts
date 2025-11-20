"use client";

import { useInfiniteQuery } from "@tanstack/react-query";
import { createClient } from "@/lib/supabase/client";
import { queryKeys } from "@/lib/query-keys";
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

  return useInfiniteQuery({
    queryKey: companyId ? queryKeys.documents.byCompany(companyId) : ['documents', 'empty'],
    queryFn: async ({ pageParam = 0 }): Promise<{
      documents: DocumentWithType[];
      nextCursor: number | undefined;
      hasMore: boolean;
    }> => {
      const offset = pageParam;

      // Fetch sales documents with pagination
      const { data: salesData, error: salesError, count: salesCount } = await supabase
        .from("sales_documents")
        .select("*", { count: 'exact' })
        .eq("company_id", companyId)
        .order("issue_date", { ascending: false })
        .range(offset, offset + pageSize - 1);

      if (salesError) throw salesError;

      // Fetch purchase documents with pagination
      const { data: purchasesData, error: purchasesError, count: purchasesCount } = await supabase
        .from("purchase_documents")
        .select("*", { count: 'exact' })
        .eq("company_id", companyId)
        .order("issue_date", { ascending: false })
        .range(offset, offset + pageSize - 1);

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
      const allDocuments = [...salesDocuments, ...purchaseDocuments].sort(
        (a, b) => new Date(b.issue_date).getTime() - new Date(a.issue_date).getTime()
      );

      // Calculate if there are more documents
      const totalCount = (salesCount || 0) + (purchasesCount || 0);
      const hasMore = offset + allDocuments.length < totalCount;
      const nextCursor = hasMore ? offset + pageSize : undefined;

      return {
        documents: allDocuments,
        nextCursor,
        hasMore,
      };
    },
    getNextPageParam: (lastPage) => lastPage.nextCursor,
    initialPageParam: 0,
    enabled: !!companyId,
    staleTime: 2 * 60 * 1000, // 2 minutes
    refetchOnWindowFocus: true,
  });
}
