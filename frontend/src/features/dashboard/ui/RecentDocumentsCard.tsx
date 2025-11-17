import { useState } from 'react';
import clsx from 'clsx';
import {
  FileText, Calendar, DollarSign, CheckCircle, Clock, AlertCircle,
  Maximize2, Minimize2, Search, ArrowUpCircle, ArrowDownCircle,
  Receipt, ScrollText, FileCheck, FileMinus, CreditCard
} from 'lucide-react';
import type { TaxDocument } from "@/shared/types/fizko";
import type { ColorScheme } from "@/shared/hooks/useColorScheme";
import { RecentDocumentsCardSkeleton } from './RecentDocumentsCardSkeleton';
import { ChateableWrapper } from '@/shared/ui/ChateableWrapper';

interface RecentDocumentsCardProps {
  documents: TaxDocument[];
  loading: boolean;
  scheme: ColorScheme;
  isExpanded?: boolean;
  onToggleExpand?: () => void;
  isInDrawer?: boolean;
}

// Helper function to get icon based on document type
const getDocumentIcon = (docType: string, isVenta: boolean) => {
  const cleanType = docType.toLowerCase().replace(/_(venta|compra)$/i, '');
  const iconClass = "h-5 w-5 flex-shrink-0";

  // Facturas (invoices)
  if (cleanType.includes('factura') && !cleanType.includes('liquidacion')) {
    return <FileText className={clsx(iconClass, isVenta ? "text-emerald-500" : "text-rose-500")} />;
  }

  // Boletas (receipts)
  if (cleanType.includes('boleta')) {
    return <Receipt className={clsx(iconClass, "text-emerald-500")} />;
  }

  // Notas de crédito (credit notes)
  if (cleanType.includes('nota') && cleanType.includes('credito')) {
    return <FileMinus className={clsx(iconClass, isVenta ? "text-amber-500" : "text-orange-500")} />;
  }

  // Notas de débito (debit notes)
  if (cleanType.includes('nota') && cleanType.includes('debito')) {
    return <FileCheck className={clsx(iconClass, isVenta ? "text-blue-500" : "text-indigo-500")} />;
  }

  // Liquidaciones (settlements)
  if (cleanType.includes('liquidacion')) {
    return <ScrollText className={clsx(iconClass, isVenta ? "text-purple-500" : "text-violet-500")} />;
  }

  // Comprobantes de pago (payment vouchers)
  if (cleanType.includes('comprobante')) {
    return <CreditCard className={clsx(iconClass, "text-teal-500")} />;
  }

  // Default fallback
  return isVenta ? (
    <ArrowUpCircle className={clsx(iconClass, "text-emerald-500")} />
  ) : (
    <ArrowDownCircle className={clsx(iconClass, "text-rose-500")} />
  );
};

export function RecentDocumentsCard({ documents, loading, scheme, isExpanded = false, onToggleExpand, isInDrawer = false }: RecentDocumentsCardProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [filter, setFilter] = useState<'all' | 'venta' | 'compra'>('all');

  if (loading) {
    return <RecentDocumentsCardSkeleton count={isExpanded ? 10 : 5} />;
  }

  // Inject keyframes for animations if not already present
  if (typeof document !== 'undefined' && !document.getElementById('recent-docs-animations')) {
    const style = document.createElement('style');
    style.id = 'recent-docs-animations';
    style.textContent = `
      @keyframes fadeIn {
        from {
          opacity: 0;
        }
        to {
          opacity: 1;
        }
      }
      @keyframes zoomIn {
        from {
          opacity: 0;
          transform: scale(0.95);
        }
        to {
          opacity: 1;
          transform: scale(1);
        }
      }
      @keyframes slideInFromTop {
        from {
          opacity: 0;
          transform: translateY(-8px);
        }
        to {
          opacity: 1;
          transform: translateY(0);
        }
      }
    `;
    document.head.appendChild(style);
  }

  // Filter documents based on search and filter
  const filteredDocuments = documents.filter((doc) => {
    // Apply type filter based on source field
    if (filter === 'venta' && doc.source !== 'sale') {
      return false;
    }
    if (filter === 'compra' && doc.source !== 'purchase') {
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

  // When collapsed: show only 10 documents
  // When expanded: show ALL filtered documents with scroll
  const COLLAPSED_LIMIT = 10;
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
      "flex h-full w-full flex-col transition-all duration-300",
      isInDrawer ? "" : "rounded-2xl border border-slate-200/70 bg-white/90 p-6 dark:border-slate-800/70 dark:bg-slate-900/70"
    )} style={{ boxSizing: 'border-box' }}>
      <div className="mb-4 flex flex-shrink-0 flex-col gap-4">
        {/* Header - Clickeable para expandir/contraer */}
        <div
          className={clsx(
            "flex items-center justify-between",
            onToggleExpand && documents.length > 0 && "cursor-pointer group"
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
          <div
            className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between"
            style={{
              animation: 'slideInFromTop 0.3s ease-out',
            }}
          >
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
        <>
          {/* Collapsed: Grouped by date (Desktop) */}
          {!isExpanded && !isInDrawer && (
            <div
              className="min-h-0 flex-1 space-y-4 overflow-y-auto overflow-x-hidden"
              style={{
                scrollbarGutter: 'stable',
                animation: 'fadeIn 0.3s ease-out',
              }}
            >
              {groupDocumentsByDate(displayedDocuments).map(({ date, docs }) => (
                <div key={date}>
                  {/* Date header */}
                  <div className="sticky top-0 z-10 bg-gradient-to-r from-emerald-50 to-teal-50 dark:from-emerald-950/40 dark:to-teal-950/40 backdrop-blur-sm -mx-2 px-4 py-2 mb-3 rounded-lg border border-emerald-200/50 dark:border-emerald-800/50">
                    <h4 className="text-sm font-bold text-emerald-900 dark:text-emerald-100">
                      {formatFullDate(date)}
                    </h4>
                  </div>

                  {/* Documents for this date */}
                  <div className="space-y-1.5">
                    {docs.map((doc) => {
                      // Determine if it's a purchase or sale based on source field (from backend)
                      const isCompra = doc.source === 'purchase';
                      const isVenta = doc.source === 'sale';

                      // Clean document type: remove "_venta" or "_compra" suffix
                      const cleanDocType = doc.document_type.replace(/_(venta|compra)$/i, '');

                      // Check if it's a credit note (nota de crédito)
                      const isNotaCredito = cleanDocType.toLowerCase().includes('nota') && cleanDocType.toLowerCase().includes('credito');

                      // Clean description: remove "Purchase: " or "Sale: " prefix
                      const cleanDescription = doc.description
                        ? doc.description.replace(/^(Purchase|Sale):\s*/i, '')
                        : '';

                      // Format amount with sign
                      // Ventas: positivas en verde (+)
                      // Compras: negativas en rojo (-)
                      // Notas de crédito invierten el signo
                      let amountSign = '';
                      let amountColor = 'text-slate-900 dark:text-slate-100';

                      if (isVenta) {
                        amountSign = isNotaCredito ? '-' : '+';
                        amountColor = 'text-emerald-600 dark:text-emerald-400'; // Verde para ventas
                      } else if (isCompra) {
                        amountSign = isNotaCredito ? '+' : '-';
                        amountColor = 'text-rose-600 dark:text-rose-400'; // Rojo para compras
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
                              <p className="text-sm font-medium text-slate-900 dark:text-slate-100 truncate">
                                {cleanDescription || 'Sin descripción'}
                              </p>
                            </div>
                            <div className="flex-shrink-0 text-right">
                              <span className={clsx("text-base font-semibold whitespace-nowrap", amountColor)}>
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

          {/* Drawer (Mobile): Grouped by date with simplified view */}
          {!isExpanded && isInDrawer && (
            <div
              className="min-h-0 flex-1 space-y-4 overflow-y-auto overflow-x-hidden"
              style={{
                scrollbarGutter: 'stable',
                animation: 'fadeIn 0.3s ease-out',
              }}
            >
              {groupDocumentsByDate(displayedDocuments).map(({ date, docs }) => (
                <div key={date}>
                  {/* Date header */}
                  <div className="sticky top-0 z-10 bg-gradient-to-r from-emerald-50 to-teal-50 dark:from-emerald-950/40 dark:to-teal-950/40 backdrop-blur-sm -mx-2 px-4 py-2 mb-3 rounded-lg border border-emerald-200/50 dark:border-emerald-800/50">
                    <h4 className="text-sm font-bold text-emerald-900 dark:text-emerald-100">
                      {formatFullDate(date)}
                    </h4>
                  </div>

                  {/* Documents for this date */}
                  <div className="space-y-1.5">
                    {docs.map((doc) => {
                      // Determine if it's a purchase or sale based on source field (from backend)
                      const isCompra = doc.source === 'purchase';
                      const isVenta = doc.source === 'sale';

                      // Clean document type: remove "_venta" or "_compra" suffix
                      const cleanDocType = doc.document_type.replace(/_(venta|compra)$/i, '');

                      // Check if it's a credit note (nota de crédito)
                      const isNotaCredito = cleanDocType.toLowerCase().includes('nota') && cleanDocType.toLowerCase().includes('credito');

                      // Clean description: remove "Purchase: " or "Sale: " prefix
                      const cleanDescription = doc.description
                        ? doc.description.replace(/^(Purchase|Sale):\s*/i, '')
                        : '';

                      // Format amount with sign
                      // Ventas: positivas en verde (+)
                      // Compras: negativas en rojo (-)
                      // Notas de crédito invierten el signo
                      let amountSign = '';
                      let amountColor = 'text-slate-900 dark:text-slate-100';

                      if (isVenta) {
                        amountSign = isNotaCredito ? '-' : '+';
                        amountColor = 'text-emerald-600 dark:text-emerald-400'; // Verde para ventas
                      } else if (isCompra) {
                        amountSign = isNotaCredito ? '+' : '-';
                        amountColor = 'text-rose-600 dark:text-rose-400'; // Rojo para compras
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
                              <p className="text-sm font-medium text-slate-900 dark:text-slate-100 truncate">
                                {cleanDescription || 'Sin descripción'}
                              </p>
                            </div>
                            <div className="flex-shrink-0">
                              <span className={clsx("text-sm font-semibold whitespace-nowrap", amountColor)}>
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

          {/* Expanded: Detailed view WITH scroll for all documents */}
          {isExpanded && (
            <div
              className="min-h-0 flex-1 space-y-4 overflow-y-auto overflow-x-hidden"
              style={{
                scrollbarGutter: 'stable',
                animation: 'zoomIn 0.3s ease-out',
              }}
            >
              {groupDocumentsByDate(displayedDocuments).map(({ date, docs }) => (
                <div key={date}>
                  {/* Date header */}
                  <div className="sticky top-0 z-10 bg-gradient-to-r from-emerald-50 to-teal-50 dark:from-emerald-950/40 dark:to-teal-950/40 backdrop-blur-sm -mx-2 px-4 py-2 mb-3 rounded-lg border border-emerald-200/50 dark:border-emerald-800/50">
                    <h4 className="text-sm font-bold text-emerald-900 dark:text-emerald-100">
                      {formatFullDate(date)}
                    </h4>
                  </div>

                  {/* Documents for this date */}
                  <div className="space-y-1.5">
                    {docs.map((doc) => {
                      // Determine if it's a purchase or sale based on source field (from backend)
                      const isCompra = doc.source === 'purchase';
                      const isVenta = doc.source === 'sale';

                      // Clean document type: remove "_venta" or "_compra" suffix
                      const cleanDocType = doc.document_type.replace(/_(venta|compra)$/i, '');

                      // Check if it's a credit note (nota de crédito)
                      const isNotaCredito = cleanDocType.toLowerCase().includes('nota') && cleanDocType.toLowerCase().includes('credito');

                      // Clean description: remove "Purchase: " or "Sale: " prefix
                      const cleanDescription = doc.description
                        ? doc.description.replace(/^(Purchase|Sale):\s*/i, '')
                        : '';

                      // Format amount with sign
                      // Ventas: positivas en verde (+)
                      // Compras: negativas en rojo (-)
                      // Notas de crédito invierten el signo
                      let amountSign = '';
                      let amountColor = 'text-slate-900 dark:text-slate-100';

                      if (isVenta) {
                        amountSign = isNotaCredito ? '-' : '+';
                        amountColor = 'text-emerald-600 dark:text-emerald-400'; // Verde para ventas
                      } else if (isCompra) {
                        amountSign = isNotaCredito ? '+' : '-';
                        amountColor = 'text-rose-600 dark:text-rose-400'; // Rojo para compras
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
                                {!isInDrawer && (
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
                              <span className={clsx("text-sm font-semibold whitespace-nowrap", amountColor)}>
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

        </>
      )}
    </div>
  );
}
