import { useState, useRef, useCallback, useEffect } from 'react';
import clsx from 'clsx';
import {
  FileText, Maximize2, Minimize2, Search, ArrowUpCircle, ArrowDownCircle,
  Receipt, ScrollText, FileCheck, FileMinus, CreditCard, Loader2
} from 'lucide-react';
import type { TaxDocument } from "@/shared/types/fizko";
import type { ColorScheme } from "@/shared/hooks/useColorScheme";
import { useTaxDocumentsInfiniteQuery } from "@/shared/hooks/useTaxDocumentsInfiniteQuery";
import { RecentDocumentsCardSkeleton } from './RecentDocumentsCardSkeleton';
import { ChateableWrapper } from '@/shared/ui/ChateableWrapper';

interface RecentDocumentsCardInfiniteProps {
  companyId?: string | null;
  scheme: ColorScheme;
  isExpanded?: boolean;
  onToggleExpand?: () => void;
  isInDrawer?: boolean;
}

// Helper function to get icon based on document type
const getDocumentIcon = (docType: string, isVenta: boolean) => {
  const cleanType = docType.toLowerCase().replace(/_(venta|compra)$/i, '');
  const iconClass = "h-5 w-5 flex-shrink-0";

  if (cleanType.includes('factura') && !cleanType.includes('liquidacion')) {
    return <FileText className={clsx(iconClass, isVenta ? "text-emerald-500" : "text-rose-500")} />;
  }

  if (cleanType.includes('boleta')) {
    return <Receipt className={clsx(iconClass, "text-emerald-500")} />;
  }

  if (cleanType.includes('nota') && cleanType.includes('credito')) {
    return <FileMinus className={clsx(iconClass, isVenta ? "text-amber-500" : "text-orange-500")} />;
  }

  if (cleanType.includes('nota') && cleanType.includes('debito')) {
    return <FileCheck className={clsx(iconClass, isVenta ? "text-blue-500" : "text-indigo-500")} />;
  }

  if (cleanType.includes('liquidacion')) {
    return <ScrollText className={clsx(iconClass, isVenta ? "text-purple-500" : "text-violet-500")} />;
  }

  if (cleanType.includes('comprobante')) {
    return <CreditCard className={clsx(iconClass, "text-teal-500")} />;
  }

  return isVenta ? (
    <ArrowUpCircle className={clsx(iconClass, "text-emerald-500")} />
  ) : (
    <ArrowDownCircle className={clsx(iconClass, "text-rose-500")} />
  );
};

export function RecentDocumentsCardInfinite({
  companyId,
  scheme,
  isExpanded = false,
  onToggleExpand,
  isInDrawer = false
}: RecentDocumentsCardInfiniteProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [filter, setFilter] = useState<'all' | 'venta' | 'compra'>('all');

  // Intersection observer ref for infinite scroll
  const observerTarget = useRef<HTMLDivElement>(null);

  // Use infinite query
  const {
    data,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    isLoading,
    isError
  } = useTaxDocumentsInfiniteQuery(50, undefined, undefined, !!companyId);

  // Flatten all pages into a single array
  const documents = data?.pages.flat() ?? [];

  // Setup intersection observer for infinite scroll
  useEffect(() => {
    if (!isExpanded) return; // Only enable infinite scroll when expanded

    const observer = new IntersectionObserver(
      (entries) => {
        const target = entries[0];
        if (target.isIntersecting && hasNextPage && !isFetchingNextPage) {
          fetchNextPage();
        }
      },
      { threshold: 0.1 }
    );

    const currentTarget = observerTarget.current;
    if (currentTarget) {
      observer.observe(currentTarget);
    }

    return () => {
      if (currentTarget) {
        observer.unobserve(currentTarget);
      }
    };
  }, [isExpanded, hasNextPage, isFetchingNextPage, fetchNextPage]);

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('es-CL', {
      style: 'currency',
      currency: 'CLP',
      minimumFractionDigits: 0,
    }).format(amount);
  };

  const formatFullDate = (dateStr: string) => {
    const date = new Date(dateStr);
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);

    const resetTime = (d: Date) => new Date(d.getFullYear(), d.getMonth(), d.getDate());
    const dateOnly = resetTime(date);
    const todayOnly = resetTime(today);
    const yesterdayOnly = resetTime(yesterday);

    if (dateOnly.getTime() === todayOnly.getTime()) {
      return 'Hoy';
    } else if (dateOnly.getTime() === yesterdayOnly.getTime()) {
      return 'Ayer';
    } else {
      return date.toLocaleDateString('es-CL', {
        weekday: 'long',
        day: 'numeric',
        month: 'long'
      });
    }
  };

  const formatDocumentTypeName = (docType: string) => {
    return docType
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
      .join(' ');
  };

  // Filter documents based on search and filter
  const filteredDocuments = documents.filter((doc) => {
    if (filter === 'venta' && doc.source !== 'sale') {
      return false;
    }
    if (filter === 'compra' && doc.source !== 'purchase') {
      return false;
    }

    if (searchTerm) {
      const searchLower = searchTerm.toLowerCase();
      const matchesNumber = doc.document_number?.toString().includes(searchLower);
      const matchesDescription = doc.description?.toLowerCase().includes(searchLower);
      const matchesType = doc.document_type.toLowerCase().includes(searchLower);
      const matchesAmount = doc.amount.toString().includes(searchLower);

      return matchesNumber || matchesDescription || matchesType || matchesAmount;
    }

    return true;
  });

  // When collapsed: show only 10 documents
  const COLLAPSED_LIMIT = 10;
  const displayedDocuments = isExpanded ? filteredDocuments : filteredDocuments.slice(0, COLLAPSED_LIMIT);
  const hasMore = filteredDocuments.length > COLLAPSED_LIMIT;

  // Group documents by month and then by date
  const groupDocumentsByMonthAndDate = (docs: TaxDocument[]) => {
    // First group by month
    const monthGroups = new Map<string, TaxDocument[]>();

    docs.forEach(doc => {
      const date = new Date(doc.issue_date);
      const monthKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`; // YYYY-MM

      if (!monthGroups.has(monthKey)) {
        monthGroups.set(monthKey, []);
      }
      monthGroups.get(monthKey)!.push(doc);
    });

    // Sort months descending and create month groups with day groups inside
    return Array.from(monthGroups.entries())
      .sort(([monthA], [monthB]) => monthB.localeCompare(monthA))
      .map(([monthKey, monthDocs]) => {
        // Calculate month totals
        let totalEntradas = 0;
        let totalSalidas = 0;

        monthDocs.forEach(doc => {
          const isVenta = doc.source === 'sale';
          const isCompra = doc.source === 'purchase';
          const cleanDocType = doc.document_type.replace(/_(venta|compra)$/i, '');
          const isNotaCredito = cleanDocType.toLowerCase().includes('nota') && cleanDocType.toLowerCase().includes('credito');

          if (isVenta) {
            // Ventas son entradas, pero notas de crédito son salidas
            if (isNotaCredito) {
              totalSalidas += doc.amount;
            } else {
              totalEntradas += doc.amount;
            }
          } else if (isCompra) {
            // Compras son salidas, pero notas de crédito son entradas
            if (isNotaCredito) {
              totalEntradas += doc.amount;
            } else {
              totalSalidas += doc.amount;
            }
          }
        });

        // Group by date within month
        const dateGroups = new Map<string, TaxDocument[]>();
        monthDocs.forEach(doc => {
          const dateKey = doc.issue_date;
          if (!dateGroups.has(dateKey)) {
            dateGroups.set(dateKey, []);
          }
          dateGroups.get(dateKey)!.push(doc);
        });

        const dayGroups = Array.from(dateGroups.entries())
          .sort(([dateA], [dateB]) => new Date(dateB).getTime() - new Date(dateA).getTime())
          .map(([date, docs]) => ({ date, docs }));

        // Format month label
        const [year, month] = monthKey.split('-');
        const monthDate = new Date(parseInt(year), parseInt(month) - 1, 1);
        const monthLabel = monthDate.toLocaleDateString('es-CL', {
          month: 'long',
          year: 'numeric'
        });

        return {
          monthKey,
          monthLabel,
          totalEntradas,
          totalSalidas,
          dayGroups
        };
      });
  };

  if (isLoading) {
    return <RecentDocumentsCardSkeleton count={isExpanded ? 10 : 5} />;
  }

  if (isError) {
    return (
      <div className="flex flex-col items-center justify-center py-8 text-center">
        <FileText className="mb-3 h-12 w-12 text-rose-300 dark:text-rose-600" />
        <p className="text-sm text-rose-600 dark:text-rose-400">
          Error al cargar los documentos
        </p>
      </div>
    );
  }

  const renderDocument = (doc: TaxDocument) => {
    const isCompra = doc.source === 'purchase';
    const isVenta = doc.source === 'sale';
    const cleanDocType = doc.document_type.replace(/_(venta|compra)$/i, '');
    const isNotaCredito = cleanDocType.toLowerCase().includes('nota') && cleanDocType.toLowerCase().includes('credito');
    const cleanDescription = doc.description
      ? doc.description.replace(/^(Purchase|Sale):\s*/i, '')
      : '';

    let amountSign = '';
    let amountColor = 'text-slate-900 dark:text-slate-100';

    if (isVenta) {
      amountSign = isNotaCredito ? '-' : '+';
      amountColor = 'text-emerald-600 dark:text-emerald-400';
    } else if (isCompra) {
      amountSign = isNotaCredito ? '+' : '-';
      amountColor = 'text-rose-600 dark:text-rose-400';
    }

    return (
      <ChateableWrapper
        key={doc.id}
        message={`Muéstrame detalles del documento ${formatDocumentTypeName(cleanDocType)} #${doc.document_number} de ${formatCurrency(doc.amount)}`}
        contextData={{
          documentId: doc.id,
          documentType: doc.document_type,
          documentNumber: doc.document_number,
          amount: doc.amount,
          issueDate: doc.issue_date,
          description: doc.description,
        }}
        uiComponent="document_detail"
        entityId={doc.id}
        entityType={isVenta ? "sales_document" : isCompra ? "purchase_document" : "document"}
      >
        <div className="flex items-center justify-between gap-2 py-2 px-1 rounded-lg">
          <div className="flex items-center gap-2 flex-1 min-w-0">
            {getDocumentIcon(cleanDocType, isVenta)}
            <div className="flex items-center gap-2 min-w-0 flex-1">
              <p className="text-sm font-medium text-slate-900 dark:text-slate-100 truncate">
                {cleanDescription || 'Sin descripción'}
              </p>
              {!isInDrawer && isExpanded && (
                <>
                  <span className="hidden md:inline text-slate-400 dark:text-slate-600">|</span>
                  <span className="hidden md:inline text-xs text-slate-500 dark:text-slate-400 whitespace-nowrap">
                    {formatDocumentTypeName(cleanDocType)}
                  </span>
                </>
              )}
            </div>
          </div>
          <div className="flex-shrink-0">
            <span className={clsx(isExpanded && !isInDrawer ? "text-sm" : "text-base", "font-semibold whitespace-nowrap", amountColor)}>
              {amountSign}{formatCurrency(doc.amount)}
            </span>
          </div>
        </div>
      </ChateableWrapper>
    );
  };

  return (
    <div className={clsx(
      "flex h-full w-full flex-col transition-all duration-300",
      isInDrawer ? "" : "rounded-2xl border border-slate-200/70 bg-white/90 p-6 dark:border-slate-800/70 dark:bg-slate-900/70"
    )} style={{ boxSizing: 'border-box' }}>
      <div className="mb-4 flex flex-shrink-0 flex-col gap-4">
        {/* Header - Clickeable para expandir/contraer */}
        <div
          className={clsx(
            "flex items-center justify-between transition-all duration-200",
            onToggleExpand && documents.length > 0 && "cursor-pointer group hover:scale-[1.02] active:scale-[0.98]"
          )}
          onClick={onToggleExpand && documents.length > 0 ? onToggleExpand : undefined}
          role={onToggleExpand && documents.length > 0 ? "button" : undefined}
          aria-label={onToggleExpand && documents.length > 0 ? (isExpanded ? "Contraer lista" : "Expandir lista") : undefined}
          title={onToggleExpand && documents.length > 0 ? (isExpanded ? "Ver menos" : hasMore ? `Ver todos (${filteredDocuments.length})` : "Expandir vista") : undefined}
        >
          <div className="flex items-center gap-2">
            <FileText className="h-5 w-5 text-emerald-500" />
            <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
              Movimientos
            </h3>
            {documents.length > 0 && (
              <span className="rounded-full bg-emerald-100 px-2.5 py-0.5 text-xs font-medium text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400">
                {filteredDocuments.length}
              </span>
            )}
          </div>
          <div className="flex items-center gap-2">
            {onToggleExpand && documents.length > 0 && (
              <div className="transition-all duration-300">
                {isExpanded ? (
                  <Minimize2 className="h-5 w-5 text-slate-600 dark:text-slate-400 transition-all duration-300 group-hover:text-emerald-600 group-hover:rotate-90 dark:group-hover:text-emerald-400" />
                ) : (
                  <Maximize2 className="h-5 w-5 text-slate-600 dark:text-slate-400 transition-all duration-300 group-hover:text-emerald-600 group-hover:rotate-180 dark:group-hover:text-emerald-400" />
                )}
              </div>
            )}
          </div>
        </div>

        {/* Search and Filters - Only show when expanded */}
        {isExpanded && (
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            {/* Search */}
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Buscar por número, descripción, tipo o monto..."
                className="w-full rounded-lg border border-slate-200 bg-white pl-10 pr-4 py-2 text-sm text-slate-900 placeholder-slate-400 focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100 dark:placeholder-slate-500"
              />
            </div>

            {/* Quick Filters */}
            <div className="flex gap-2">
              <button
                onClick={() => setFilter('all')}
                className={clsx(
                  "rounded-lg px-4 py-2 text-sm font-medium transition-colors",
                  filter === 'all'
                    ? "bg-emerald-600 text-white shadow-sm dark:bg-emerald-500"
                    : "bg-slate-100 text-slate-700 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700"
                )}
              >
                Todos
              </button>
              <button
                onClick={() => setFilter('venta')}
                className={clsx(
                  "rounded-lg px-4 py-2 text-sm font-medium transition-colors",
                  filter === 'venta'
                    ? "bg-emerald-600 text-white shadow-sm dark:bg-emerald-500"
                    : "bg-slate-100 text-slate-700 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700"
                )}
              >
                Venta
              </button>
              <button
                onClick={() => setFilter('compra')}
                className={clsx(
                  "rounded-lg px-4 py-2 text-sm font-medium transition-colors",
                  filter === 'compra'
                    ? "bg-rose-600 text-white shadow-sm dark:bg-rose-500"
                    : "bg-slate-100 text-slate-700 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700"
                )}
              >
                Compra
              </button>
            </div>
          </div>
        )}
      </div>

      {documents.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-8 text-center">
          <FileText className="mb-3 h-12 w-12 text-slate-300 dark:text-slate-600" />
          <p className="text-sm text-slate-600 dark:text-slate-400">
            No hay documentos recientes
          </p>
        </div>
      ) : (
        <div
          className="min-h-0 flex-1 space-y-6 overflow-y-auto overflow-x-hidden"
          style={{ scrollbarGutter: 'stable' }}
        >
          {groupDocumentsByMonthAndDate(displayedDocuments).map(({ monthKey, monthLabel, totalEntradas, totalSalidas, dayGroups }) => (
            <div key={monthKey} className="space-y-4">
              {/* Month header with totals */}
              <div className="sticky top-0 z-20 bg-gradient-to-r from-slate-100 to-slate-50 dark:from-slate-800 dark:to-slate-900 backdrop-blur-sm -mx-2 px-4 py-3 rounded-xl border border-slate-300 dark:border-slate-700 shadow-sm">
                <div className="flex items-center justify-between">
                  <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 capitalize">
                    {monthLabel}
                  </h3>
                  <div className="flex items-center gap-4">
                    <div className="flex items-center gap-1.5">
                      <span className="text-xs font-medium text-slate-500 dark:text-slate-400">Entradas:</span>
                      <span className="text-sm font-bold text-emerald-600 dark:text-emerald-400">
                        {formatCurrency(totalEntradas)}
                      </span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <span className="text-xs font-medium text-slate-500 dark:text-slate-400">Salidas:</span>
                      <span className="text-sm font-bold text-rose-600 dark:text-rose-400">
                        {formatCurrency(totalSalidas)}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Days within this month */}
              {dayGroups.map(({ date, docs }) => (
                <div key={date} className="ml-2">
                  {/* Date header */}
                  <div className="sticky top-14 z-10 bg-gradient-to-r from-emerald-50 to-teal-50 dark:from-emerald-950/40 dark:to-teal-950/40 backdrop-blur-sm -mx-2 px-4 py-2 mb-3 rounded-lg border border-emerald-200/50 dark:border-emerald-800/50">
                    <h4 className="text-sm font-bold text-emerald-900 dark:text-emerald-100">
                      {formatFullDate(date)}
                    </h4>
                  </div>

                  {/* Documents for this date */}
                  <div className="space-y-1.5">
                    {docs.map(renderDocument)}
                  </div>
                </div>
              ))}
            </div>
          ))}

          {/* Infinite scroll trigger */}
          {isExpanded && hasNextPage && (
            <div ref={observerTarget} className="flex items-center justify-center py-4">
              {isFetchingNextPage && (
                <div className="flex items-center gap-2 text-sm text-emerald-600 dark:text-emerald-400">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span>Cargando más documentos...</span>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
