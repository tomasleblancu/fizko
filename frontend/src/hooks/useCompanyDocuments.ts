"use client";

import { useQuery } from "@tanstack/react-query";
import { createClient } from "@/lib/supabase/client";
import { queryKeys } from "@/lib/query-keys";
import { getTimestamp } from "@/shared/lib/date-utils";
import type { SalesDocument, PurchaseDocument, DocumentWithType } from "@/types/database";

interface UseCompanyDocumentsOptions {
  companyId: string;
  limit?: number;
}

export function useCompanyDocuments({ companyId, limit = 50 }: UseCompanyDocumentsOptions) {
  const supabase = createClient();

  return useQuery({
    queryKey: queryKeys.documents.byCompany(companyId),
    queryFn: async (): Promise<DocumentWithType[]> => {
      // Fetch sales documents
      const { data: salesData, error: salesError } = await supabase
        .from("sales_documents")
        .select("*")
        .eq("company_id", companyId)
        .order("issue_date", { ascending: false })
        .limit(limit);

      if (salesError) throw salesError;

      // Fetch purchase documents
      const { data: purchasesData, error: purchasesError } = await supabase
        .from("purchase_documents")
        .select("*")
        .eq("company_id", companyId)
        .order("issue_date", { ascending: false })
        .limit(limit);

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
        (a, b) => getTimestamp(b.issue_date) - getTimestamp(a.issue_date)
      );

      return allDocuments.slice(0, limit);
    },
    enabled: !!companyId,
    staleTime: 2 * 60 * 1000, // 2 minutes
    refetchOnWindowFocus: true,
  });
}
