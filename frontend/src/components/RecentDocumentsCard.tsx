import { useState } from 'react';
import clsx from 'clsx';
import { FileText, Calendar, DollarSign, CheckCircle, Clock, AlertCircle, Maximize2, Minimize2, Search } from 'lucide-react';
import type { TaxDocument } from '../types/fizko';
import type { ColorScheme } from '../hooks/useColorScheme';
import { RecentDocumentsCardSkeleton } from './RecentDocumentsCardSkeleton';
import { ChateableWrapper } from './ChateableWrapper';

interface RecentDocumentsCardProps {
  documents: TaxDocument[];
  loading: boolean;
  scheme: ColorScheme;
  isExpanded?: boolean;
  onToggleExpand?: () => void;
}

export function RecentDocumentsCard({ documents, loading, scheme, isExpanded = false, onToggleExpand }: RecentDocumentsCardProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [filter, setFilter] = useState<'all' | 'venta' | 'compra'>('all');

  if (loading) {
    return <RecentDocumentsCardSkeleton count={isExpanded ? 10 : 5} />;
  }

  // Filter documents based on search and filter
  const filteredDocuments = documents.filter((doc) => {
    // Apply type filter
    if (filter === 'venta' && !doc.document_type.toLowerCase().startsWith('venta_')) {
      return false;
    }
    if (filter === 'compra' && !doc.document_type.toLowerCase().startsWith('compra_')) {
      return false;
    }

    // Apply search filter
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

  // When collapsed: show only 3 documents
  // When expanded: show ALL filtered documents with scroll
  const COLLAPSED_LIMIT = 3;
  const displayedDocuments = isExpanded ? filteredDocuments : filteredDocuments.slice(0, COLLAPSED_LIMIT);
  const hasMore = filteredDocuments.length > COLLAPSED_LIMIT;

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('es-CL', {
      style: 'currency',
      currency: 'CLP',
      minimumFractionDigits: 0,
    }).format(amount);
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('es-CL', { day: 'numeric', month: 'short' });
  };

  const formatFullDate = (dateStr: string) => {
    const date = new Date(dateStr);
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);

    // Reset hours for date comparison
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
    // Convert snake_case to Title Case: "liquidacion_factura" → "Liquidación Factura"
    return docType
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
      .join(' ');
  };

  // Group documents by date
  const groupDocumentsByDate = (docs: TaxDocument[]) => {
    const groups = new Map<string, TaxDocument[]>();

    docs.forEach(doc => {
      const dateKey = doc.issue_date;
      if (!groups.has(dateKey)) {
        groups.set(dateKey, []);
      }
      groups.get(dateKey)!.push(doc);
    });

    // Sort groups by date descending
    return Array.from(groups.entries())
      .sort(([dateA], [dateB]) => new Date(dateB).getTime() - new Date(dateA).getTime())
      .map(([date, docs]) => ({ date, docs }));
  };

  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'emitida':
      case 'pagada':
        return <CheckCircle className="h-4 w-4 text-emerald-500" />;
      case 'pendiente':
        return <Clock className="h-4 w-4 text-amber-500" />;
      case 'vencida':
        return <AlertCircle className="h-4 w-4 text-rose-500" />;
      default:
        return <FileText className="h-4 w-4 text-slate-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'emitida':
      case 'pagada':
        return 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/30 dark:text-emerald-400';
      case 'pendiente':
        return 'bg-amber-50 text-amber-700 dark:bg-amber-950/30 dark:text-amber-400';
      case 'vencida':
        return 'bg-rose-50 text-rose-700 dark:bg-rose-950/30 dark:text-rose-400';
      default:
        return 'bg-slate-50 text-slate-700 dark:bg-slate-800 dark:text-slate-400';
    }
  };

  return (
    <div className={clsx(
      "rounded-2xl border border-slate-200/70 bg-white/90 transition-all duration-300 dark:border-slate-800/70 dark:bg-slate-900/70",
      isExpanded ? "flex h-full flex-col p-6" : "p-6"
    )}>
      <div className="mb-4 flex flex-shrink-0 flex-col gap-4">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
              Documentos Tributarios Recientes
            </h3>
            {documents.length > 0 && (
              <span className="rounded-full bg-purple-100 px-2.5 py-0.5 text-xs font-medium text-purple-700 dark:bg-purple-900/30 dark:text-purple-400">
                {filteredDocuments.length}
              </span>
            )}
          </div>
          <div className="flex items-center gap-2">
            <FileText className="h-6 w-6 text-purple-500" />
            {onToggleExpand && hasMore && (
              <button
                onClick={onToggleExpand}
                className="rounded-lg p-1.5 transition-colors hover:bg-slate-100 dark:hover:bg-slate-800"
                aria-label={isExpanded ? "Contraer lista" : "Expandir lista"}
                title={isExpanded ? "Ver menos" : `Ver todos (${filteredDocuments.length})`}
              >
                {isExpanded ? (
                  <Minimize2 className="h-5 w-5 text-slate-600 dark:text-slate-400" />
                ) : (
                  <Maximize2 className="h-5 w-5 text-slate-600 dark:text-slate-400" />
                )}
              </button>
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
                className="w-full rounded-lg border border-slate-200 bg-white pl-10 pr-4 py-2 text-sm text-slate-900 placeholder-slate-400 focus:border-purple-500 focus:outline-none focus:ring-2 focus:ring-purple-500/20 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100 dark:placeholder-slate-500"
              />
            </div>

            {/* Quick Filters */}
            <div className="flex gap-2">
              <button
                onClick={() => setFilter('all')}
                className={clsx(
                  "rounded-lg px-4 py-2 text-sm font-medium transition-colors",
                  filter === 'all'
                    ? "bg-purple-600 text-white shadow-sm dark:bg-purple-500"
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
        <>
          {/* Collapsed: Detailed list, NO scroll */}
          {!isExpanded && (
            <div className="space-y-1.5">
              {displayedDocuments.map((doc) => {
                // Determine if it's a purchase or sale based on document_type prefix
                const isVenta = doc.document_type.toLowerCase().startsWith('venta_');
                const isCompra = doc.document_type.toLowerCase().startsWith('compra_');

                // Clean document type: remove "venta_" or "compra_" prefix
                const cleanDocType = doc.document_type.replace(/^(venta_|compra_)/i, '');

                // Check if it's a credit note (nota de crédito)
                const isNotaCredito = cleanDocType.toLowerCase().includes('nota') && cleanDocType.toLowerCase().includes('credito');

                // Clean description: remove document type prefix if present
                const cleanDescription = doc.description
                  ? doc.description.replace(new RegExp(`^(${doc.document_type}|${cleanDocType})\\s*-?\\s*`, 'i'), '')
                  : '';

                // Format amount with sign
                // Credit notes have opposite sign: venta NC = negative, compra NC = positive
                let amountSign = '';
                let amountColor = 'text-slate-900 dark:text-slate-100';

                if (isVenta) {
                  amountSign = isNotaCredito ? '-' : '+';
                  amountColor = isNotaCredito
                    ? 'text-rose-600 dark:text-rose-400'
                    : 'text-emerald-600 dark:text-emerald-400';
                } else if (isCompra) {
                  amountSign = isNotaCredito ? '+' : '-';
                  amountColor = isNotaCredito
                    ? 'text-emerald-600 dark:text-emerald-400'
                    : 'text-rose-600 dark:text-rose-400';
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
                    <div className="flex items-center justify-between py-2 px-1 rounded-lg">
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-slate-900 dark:text-slate-100 truncate">
                          {cleanDescription || 'Sin descripción'}
                        </p>
                        <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                          {formatDocumentTypeName(cleanDocType)} #{doc.document_number}
                        </p>
                      </div>
                      <div className="ml-4 flex-shrink-0">
                        <span className={clsx("text-sm font-semibold", amountColor)}>
                          {amountSign}{formatCurrency(doc.amount)}
                        </span>
                      </div>
                    </div>
                  </ChateableWrapper>
                );
              })}
            </div>
          )}

          {/* Expanded: Detailed view WITH scroll for all documents */}
          {isExpanded && (
            <div className="min-h-0 flex-1 space-y-4 overflow-y-auto pr-2">
              {groupDocumentsByDate(displayedDocuments).map(({ date, docs }) => (
                <div key={date}>
                  {/* Date header */}
                  <div className="sticky top-0 z-10 bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-950/40 dark:to-purple-950/40 backdrop-blur-sm -mx-2 px-2 py-2 mb-3 rounded-lg border border-blue-200/50 dark:border-blue-800/50">
                    <h4 className="text-sm font-bold text-blue-900 dark:text-blue-100">
                      {formatFullDate(date)}
                    </h4>
                  </div>

                  {/* Documents for this date */}
                  <div className="space-y-1.5">
                    {docs.map((doc) => {
                      // Determine if it's a purchase or sale based on document_type prefix
                      const isVenta = doc.document_type.toLowerCase().startsWith('venta_');
                      const isCompra = doc.document_type.toLowerCase().startsWith('compra_');

                      // Clean document type: remove "venta_" or "compra_" prefix
                      const cleanDocType = doc.document_type.replace(/^(venta_|compra_)/i, '');

                      // Check if it's a credit note (nota de crédito)
                      const isNotaCredito = cleanDocType.toLowerCase().includes('nota') && cleanDocType.toLowerCase().includes('credito');

                      // Clean description: remove document type prefix if present
                      const cleanDescription = doc.description
                        ? doc.description.replace(new RegExp(`^(${doc.document_type}|${cleanDocType})\\s*-?\\s*`, 'i'), '')
                        : '';

                      // Format amount with sign
                      // Credit notes have opposite sign: venta NC = negative, compra NC = positive
                      let amountSign = '';
                      let amountColor = 'text-slate-900 dark:text-slate-100';

                      if (isVenta) {
                        amountSign = isNotaCredito ? '-' : '+';
                        amountColor = isNotaCredito
                          ? 'text-rose-600 dark:text-rose-400'
                          : 'text-emerald-600 dark:text-emerald-400';
                      } else if (isCompra) {
                        amountSign = isNotaCredito ? '+' : '-';
                        amountColor = isNotaCredito
                          ? 'text-emerald-600 dark:text-emerald-400'
                          : 'text-rose-600 dark:text-rose-400';
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
                          <div className="flex items-center justify-between py-2 px-1 rounded-lg">
                            <div className="flex-1 min-w-0">
                              <p className="text-sm font-medium text-slate-900 dark:text-slate-100 truncate">
                                {cleanDescription || 'Sin descripción'}
                              </p>
                              <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                                {formatDocumentTypeName(cleanDocType)} #{doc.document_number}
                              </p>
                            </div>
                            <div className="ml-4 flex-shrink-0">
                              <span className={clsx("text-sm font-semibold", amountColor)}>
                                {amountSign}{formatCurrency(doc.amount)}
                              </span>
                            </div>
                          </div>
                        </ChateableWrapper>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Show "view more" button when collapsed */}
          {!isExpanded && hasMore && (
            <div className="mt-3 flex items-center justify-center">
              <button
                onClick={onToggleExpand}
                className="group flex items-center gap-2 rounded-lg px-3 py-2 text-xs font-medium text-slate-600 transition-colors hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800"
              >
                <span>Ver todos ({documents.length})</span>
                <Maximize2 className="h-3.5 w-3.5 transition-transform group-hover:scale-110" />
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
