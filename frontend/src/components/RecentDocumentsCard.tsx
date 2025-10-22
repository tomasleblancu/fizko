import clsx from 'clsx';
import { FileText, Calendar, DollarSign, CheckCircle, Clock, AlertCircle, Maximize2, Minimize2 } from 'lucide-react';
import type { TaxDocument } from '../types/fizko';
import type { ColorScheme } from '../hooks/useColorScheme';
import { RecentDocumentsCardSkeleton } from './RecentDocumentsCardSkeleton';

interface RecentDocumentsCardProps {
  documents: TaxDocument[];
  loading: boolean;
  scheme: ColorScheme;
  isExpanded?: boolean;
  onToggleExpand?: () => void;
}

export function RecentDocumentsCard({ documents, loading, scheme, isExpanded = false, onToggleExpand }: RecentDocumentsCardProps) {
  if (loading) {
    return <RecentDocumentsCardSkeleton count={isExpanded ? 10 : 5} />;
  }

  // When collapsed: show only 3 documents
  // When expanded: show ALL documents with scroll
  const COLLAPSED_LIMIT = 3;
  const displayedDocuments = isExpanded ? documents : documents.slice(0, COLLAPSED_LIMIT);
  const hasMore = documents.length > COLLAPSED_LIMIT;

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
      "rounded-2xl border border-slate-200/70 bg-white/90 p-6 transition-all duration-300 dark:border-slate-800/70 dark:bg-slate-900/70",
      isExpanded ? "flex h-[500px] flex-col" : ""
    )}>
      <div className="mb-4 flex flex-shrink-0 items-center justify-between">
        <div className="flex items-center gap-3">
          <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
            Documentos Tributarios Recientes
          </h3>
          {documents.length > 0 && (
            <span className="rounded-full bg-purple-100 px-2.5 py-0.5 text-xs font-medium text-purple-700 dark:bg-purple-900/30 dark:text-purple-400">
              {documents.length}
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
              title={isExpanded ? "Ver menos" : `Ver todos (${documents.length})`}
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

      {documents.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-8 text-center">
          <FileText className="mb-3 h-12 w-12 text-slate-300 dark:text-slate-600" />
          <p className="text-sm text-slate-600 dark:text-slate-400">
            No hay documentos recientes
          </p>
        </div>
      ) : (
        <>
          {/* Collapsed: Simple one-line list, NO scroll */}
          {!isExpanded && (
            <div className="space-y-1.5">
              {displayedDocuments.map((doc) => (
                <div
                  key={doc.id}
                  className="flex items-center justify-between rounded-lg border border-slate-200/50 bg-slate-50/50 px-3 py-2 transition-colors hover:bg-slate-100 dark:border-slate-800/50 dark:bg-slate-800/30 dark:hover:bg-slate-800/50"
                >
                  {/* Date */}
                  <span className="w-20 flex-shrink-0 text-xs text-slate-600 dark:text-slate-400">
                    {formatDate(doc.issue_date)}
                  </span>

                  {/* Provider/Description */}
                  <span className="flex-1 truncate px-3 text-sm text-slate-700 dark:text-slate-300">
                    {doc.description || doc.document_type}
                  </span>

                  {/* Amount */}
                  <span className="flex-shrink-0 text-sm font-semibold text-slate-900 dark:text-slate-100">
                    {formatCurrency(doc.amount)}
                  </span>
                </div>
              ))}
            </div>
          )}

          {/* Expanded: Detailed view WITH scroll for all documents */}
          {isExpanded && (
            <div className="min-h-0 flex-1 space-y-2 overflow-y-auto pr-2">
              {displayedDocuments.map((doc) => (
                <div
                  key={doc.id}
                  className="flex items-center justify-between rounded-xl border border-slate-200/50 bg-slate-50/50 p-3 transition-all hover:border-slate-300 hover:bg-slate-50 dark:border-slate-800/50 dark:bg-slate-800/30 dark:hover:border-slate-700 dark:hover:bg-slate-800/50"
                >
                  <div className="flex items-center gap-3 flex-1 min-w-0">
                    {getStatusIcon(doc.status)}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <p className="text-sm font-medium text-slate-900 dark:text-slate-100 truncate">
                          {doc.document_type} {doc.document_number}
                        </p>
                        <span className={clsx(
                          'inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium',
                          getStatusColor(doc.status)
                        )}>
                          {doc.status}
                        </span>
                      </div>
                      <div className="flex items-center gap-3 mt-1 text-xs text-slate-500 dark:text-slate-400">
                        <span className="flex items-center gap-1">
                          <Calendar className="h-3 w-3" />
                          {formatDate(doc.issue_date)}
                        </span>
                        {doc.description && (
                          <span className="truncate">{doc.description}</span>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="ml-3 flex flex-col items-end">
                    <span className="text-sm font-bold text-slate-900 dark:text-slate-100">
                      {formatCurrency(doc.amount)}
                    </span>
                    {doc.tax_amount && (
                      <span className="text-xs text-slate-500 dark:text-slate-400">
                        IVA: {formatCurrency(doc.tax_amount)}
                      </span>
                    )}
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
