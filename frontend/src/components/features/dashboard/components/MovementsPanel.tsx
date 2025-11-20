/**
 * Movements Panel Component
 * Displays tax documents with expandable table view and filters
 */

import React from "react";
import {
  Receipt,
  Download,
  X,
  Maximize2,
  ArrowUpRight,
  ArrowDownLeft,
  Calendar,
} from "lucide-react";
import { ChateableWrapper } from "@/components/ui/ChateableWrapper";

interface Document {
  id: string;
  type: "sale" | "purchase";
  document_type: string;
  folio: string | number | null;
  counterparty_name: string | null;
  total_amount: number;
  tax_amount: number;
  issue_date: string;
}

interface GroupedDocuments {
  [date: string]: Document[];
}

interface MovementsPanelProps {
  documents: Document[] | null | undefined;
  isLoading: boolean;
  showAllMovements: boolean;
  movementTypeFilter: "all" | "sale" | "purchase";
  visibleGroupedDocuments: GroupedDocuments;
  documentsByDate: [string, Document[]][];
  filteredDocumentsCount: number;
  hasNextPage: boolean | undefined;
  isFetchingNextPage: boolean;
  loadMoreRef: React.RefObject<HTMLDivElement | null>;
  onToggleExpand: () => void;
  onFilterChange: (filter: "all" | "sale" | "purchase") => void;
  onDownloadCSV: () => void;
  formatDate: (date: string) => string;
  formatCurrency: (amount: number) => string;
}

export function MovementsPanel({
  documents,
  isLoading,
  showAllMovements,
  movementTypeFilter,
  visibleGroupedDocuments,
  documentsByDate,
  filteredDocumentsCount,
  hasNextPage,
  isFetchingNextPage,
  loadMoreRef,
  onToggleExpand,
  onFilterChange,
  onDownloadCSV,
  formatDate,
  formatCurrency,
}: MovementsPanelProps) {
  return (
    <div
      className={`flex flex-col overflow-hidden rounded-xl border border-slate-200 bg-white p-6 dark:border-slate-700 dark:bg-slate-900 ${
        showAllMovements ? "h-full" : ""
      }`}
    >
      <div className="mb-4 flex flex-shrink-0 flex-col gap-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Receipt className="h-5 w-5 text-slate-600 dark:text-slate-400" />
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white">
              {showAllMovements ? "Todos los Movimientos" : "Movimientos"}
            </h3>
            {documents && (
              <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-medium text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400">
                {showAllMovements && movementTypeFilter !== "all"
                  ? `${filteredDocumentsCount} / ${documents.length}`
                  : documents.length}
              </span>
            )}
          </div>
          <div className="flex items-center gap-2">
            {/* Download CSV button - only show when expanded */}
            {showAllMovements && documents && documents.length > 0 && (
              <button
                onClick={onDownloadCSV}
                className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium text-slate-600 transition-colors hover:bg-emerald-100 hover:text-emerald-700 dark:text-slate-400 dark:hover:bg-emerald-900/30 dark:hover:text-emerald-400"
                title="Descargar CSV"
              >
                <Download className="h-4 w-4" />
                <span className="hidden sm:inline">CSV</span>
              </button>
            )}
            <button
              onClick={onToggleExpand}
              className="flex items-center gap-1 rounded-lg px-3 py-1.5 text-sm font-medium text-slate-600 transition-colors hover:bg-slate-100 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-white"
            >
              {showAllMovements ? (
                <>
                  <X className="h-4 w-4" />
                  <span>Cerrar</span>
                </>
              ) : (
                <>
                  <Maximize2 className="h-4 w-4" />
                  <span>Expandir</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Filters - Only show in expanded desktop view */}
        {showAllMovements && (
          <div className="hidden items-center gap-2 lg:flex">
            <span className="text-sm text-slate-600 dark:text-slate-400">
              Tipo:
            </span>
            <div className="flex gap-1 rounded-lg bg-slate-100 p-1 dark:bg-slate-800">
              <button
                onClick={() => onFilterChange("all")}
                className={`rounded-md px-3 py-1 text-xs font-medium transition-colors ${
                  movementTypeFilter === "all"
                    ? "bg-white text-slate-900 shadow-sm dark:bg-slate-700 dark:text-white"
                    : "text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white"
                }`}
              >
                Todos
              </button>
              <button
                onClick={() => onFilterChange("sale")}
                className={`flex items-center gap-1.5 rounded-md px-3 py-1 text-xs font-medium transition-colors ${
                  movementTypeFilter === "sale"
                    ? "bg-white text-emerald-700 shadow-sm dark:bg-slate-700 dark:text-emerald-400"
                    : "text-slate-600 hover:text-emerald-700 dark:text-slate-400 dark:hover:text-emerald-400"
                }`}
              >
                <ArrowUpRight className="h-3 w-3" />
                Ventas
              </button>
              <button
                onClick={() => onFilterChange("purchase")}
                className={`flex items-center gap-1.5 rounded-md px-3 py-1 text-xs font-medium transition-colors ${
                  movementTypeFilter === "purchase"
                    ? "bg-white text-blue-700 shadow-sm dark:bg-slate-700 dark:text-blue-400"
                    : "text-slate-600 hover:text-blue-700 dark:text-slate-400 dark:hover:text-blue-400"
                }`}
              >
                <ArrowDownLeft className="h-3 w-3" />
                Compras
              </button>
            </div>
          </div>
        )}
      </div>

      <div className="flex-1 overflow-y-auto pr-2">
        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <div className="h-6 w-6 animate-spin rounded-full border-2 border-emerald-500 border-t-transparent" />
          </div>
        ) : !documents || documents.length === 0 ? (
          <div className="py-8 text-center">
            <Receipt className="mx-auto h-12 w-12 text-slate-300 dark:text-slate-600" />
            <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
              No hay movimientos registrados
            </p>
          </div>
        ) : showAllMovements ? (
          <div className="overflow-x-auto">
            <table className="w-full">
              <tbody className="bg-white dark:bg-slate-900">
                {Object.entries(visibleGroupedDocuments)
                  .sort(
                    ([dateA], [dateB]) =>
                      new Date(dateB).getTime() - new Date(dateA).getTime()
                  )
                  .map(([date, docs]) => (
                    <React.Fragment key={date}>
                      {/* Date Group Header Row */}
                      <tr className="sticky top-0 z-10 bg-slate-100 dark:bg-slate-800/80">
                        <td colSpan={5} className="px-4 py-2">
                          <div className="flex items-center gap-2">
                            <Calendar className="h-4 w-4 text-slate-500" />
                            <span className="text-sm font-semibold text-slate-900 dark:text-white">
                              {formatDate(date)}
                            </span>
                            <div className="h-px flex-1 bg-slate-300 dark:bg-slate-600" />
                            <span className="text-xs text-slate-500">
                              {docs.length} docs
                            </span>
                          </div>
                        </td>
                      </tr>
                      {/* Document Rows */}
                      {docs.map((doc) => (
                        <ChateableWrapper
                          key={doc.id}
                          as="fragment"
                          message={`Muéstrame los detalles del documento ${doc.document_type}${doc.folio ? ` N° ${doc.folio}` : ""} de ${doc.counterparty_name || "proveedor"}`}
                          contextData={{
                            documentId: doc.id,
                            documentType: doc.document_type,
                            folio: doc.folio,
                            counterpartyName: doc.counterparty_name,
                            totalAmount: doc.total_amount,
                            taxAmount: doc.tax_amount,
                            type: doc.type,
                            issueDate: doc.issue_date,
                          }}
                          uiComponent="document_detail"
                          entityId={doc.id}
                          entityType={
                            doc.type === "sale"
                              ? "sales_document"
                              : "purchase_document"
                          }
                        >
                          <tr className="border-b border-slate-200 transition-colors hover:bg-slate-50 dark:border-slate-700 dark:hover:bg-slate-800/50">
                            <td className="px-4 py-3">
                              <div className="flex items-center gap-2">
                                <div
                                  className={`flex h-7 w-7 items-center justify-center rounded-lg ${
                                    doc.type === "sale"
                                      ? "bg-emerald-100 dark:bg-emerald-900/30"
                                      : "bg-blue-100 dark:bg-blue-900/30"
                                  }`}
                                >
                                  {doc.type === "sale" ? (
                                    <ArrowUpRight className="h-3.5 w-3.5 text-emerald-600 dark:text-emerald-400" />
                                  ) : (
                                    <ArrowDownLeft className="h-3.5 w-3.5 text-blue-600 dark:text-blue-400" />
                                  )}
                                </div>
                                <span
                                  className={`text-xs font-medium ${
                                    doc.type === "sale"
                                      ? "text-emerald-700 dark:text-emerald-400"
                                      : "text-blue-700 dark:text-blue-400"
                                  }`}
                                >
                                  {doc.type === "sale" ? "Venta" : "Compra"}
                                </span>
                              </div>
                            </td>
                            <td className="px-4 py-3">
                              <div className="text-sm text-slate-900 dark:text-white">
                                {doc.document_type}
                              </div>
                              {doc.folio && (
                                <div className="text-xs text-slate-500 dark:text-slate-400">
                                  N° {doc.folio}
                                </div>
                              )}
                            </td>
                            <td className="px-4 py-3 text-sm text-slate-900 dark:text-white">
                              <div className="max-w-xs truncate">
                                {doc.counterparty_name || "Sin nombre"}
                              </div>
                            </td>
                            <td className="whitespace-nowrap px-4 py-3 text-right text-sm font-medium text-slate-900 dark:text-white">
                              {formatCurrency(doc.total_amount - doc.tax_amount)}
                            </td>
                            <td
                              className={`whitespace-nowrap px-4 py-3 text-right text-sm font-bold ${
                                doc.type === "sale"
                                  ? "text-emerald-600 dark:text-emerald-400"
                                  : "text-blue-600 dark:text-blue-400"
                              }`}
                            >
                              {doc.type === "sale" ? "+" : "-"}
                              {formatCurrency(doc.total_amount)}
                            </td>
                          </tr>
                        </ChateableWrapper>
                      ))}
                    </React.Fragment>
                  ))}
              </tbody>
            </table>
            {/* Infinite scroll trigger */}
            {hasNextPage && (
              <div
                ref={loadMoreRef}
                className="flex items-center justify-center py-4"
              >
                {isFetchingNextPage ? (
                  <div className="h-8 w-8 animate-spin rounded-full border-4 border-emerald-500 border-t-transparent" />
                ) : (
                  <div className="text-sm text-slate-500 dark:text-slate-400">
                    Desplázate para cargar más
                  </div>
                )}
              </div>
            )}
          </div>
        ) : (
          <div className="space-y-4">
            {documentsByDate.map(([date, docs]) => (
              <div key={date}>
                <p className="mb-2 text-xs font-medium text-slate-500 dark:text-slate-400">
                  {formatDate(date)}
                </p>
                <div className="space-y-2">
                  {docs.map((doc) => (
                    <ChateableWrapper
                      key={doc.id}
                      message={`Muéstrame los detalles del documento ${doc.document_type}${doc.folio ? ` N° ${doc.folio}` : ""} de ${doc.counterparty_name || "proveedor"}`}
                      contextData={{
                        documentId: doc.id,
                        documentType: doc.document_type,
                        folio: doc.folio,
                        counterpartyName: doc.counterparty_name,
                        totalAmount: doc.total_amount,
                        taxAmount: doc.tax_amount,
                        type: doc.type,
                        issueDate: doc.issue_date,
                      }}
                      uiComponent="document_detail"
                      entityId={doc.id}
                      entityType={
                        doc.type === "sale"
                          ? "sales_document"
                          : "purchase_document"
                      }
                    >
                      <div className="flex items-center justify-between rounded-lg bg-slate-50 p-3 dark:bg-slate-800">
                        <div className="flex items-center gap-3">
                          <div
                            className={`flex h-8 w-8 items-center justify-center rounded-lg ${
                              doc.type === "sale"
                                ? "bg-emerald-100 dark:bg-emerald-900/30"
                                : "bg-blue-100 dark:bg-blue-900/30"
                            }`}
                          >
                            {doc.type === "sale" ? (
                              <ArrowUpRight className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
                            ) : (
                              <ArrowDownLeft className="h-4 w-4 text-blue-600 dark:text-blue-400" />
                            )}
                          </div>
                          <div className="flex flex-col">
                            <span className="text-sm text-slate-900 dark:text-white">
                              {doc.counterparty_name ||
                                `${doc.document_type} ${doc.folio || ""}`}
                            </span>
                            <span className="text-xs text-slate-500 dark:text-slate-400">
                              {doc.document_type}{" "}
                              {doc.folio ? `N° ${doc.folio}` : ""}
                            </span>
                          </div>
                        </div>
                        <span
                          className={`text-sm font-semibold ${
                            doc.type === "sale"
                              ? "text-emerald-600 dark:text-emerald-400"
                              : "text-blue-600 dark:text-blue-400"
                          }`}
                        >
                          {doc.type === "sale" ? "+" : "-"}
                          {formatCurrency(doc.total_amount)}
                        </span>
                      </div>
                    </ChateableWrapper>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
