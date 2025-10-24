import { FileText, CheckCircle, Clock } from 'lucide-react';
import type { TaxDocument } from '../types/fizko';

// Mock documents for the landing page preview
const currentDate = new Date();
const currentYear = currentDate.getFullYear();
const currentMonth = currentDate.getMonth();

const mockDocuments: TaxDocument[] = [
  // Today's documents
  {
    id: '1',
    company_id: 'preview-company',
    document_type: 'venta_factura_electronica',
    document_number: '12345',
    issue_date: new Date(currentYear, currentMonth, currentDate.getDate()).toISOString(),
    amount: 850000,
    tax_amount: 161500,
    status: 'Emitida',
    description: 'Servicios de consultoría',
    created_at: new Date().toISOString(),
  },
  {
    id: '2',
    company_id: 'preview-company',
    document_type: 'venta_boleta_electronica',
    document_number: '67890',
    issue_date: new Date(currentYear, currentMonth, currentDate.getDate()).toISOString(),
    amount: 125000,
    tax_amount: 23750,
    status: 'Emitida',
    description: 'Venta productos',
    created_at: new Date().toISOString(),
  },
  // Yesterday's documents
  {
    id: '3',
    company_id: 'preview-company',
    document_type: 'compra_factura_electronica',
    document_number: '11223',
    issue_date: new Date(currentYear, currentMonth, currentDate.getDate() - 1).toISOString(),
    amount: 450000,
    tax_amount: 85500,
    status: 'Recibida',
    description: 'Compra insumos',
    created_at: new Date().toISOString(),
  },
  {
    id: '4',
    company_id: 'preview-company',
    document_type: 'venta_factura_exenta',
    document_number: '44556',
    issue_date: new Date(currentYear, currentMonth, currentDate.getDate() - 1).toISOString(),
    amount: 320000,
    status: 'Emitida',
    description: 'Servicios profesionales',
    created_at: new Date().toISOString(),
  },
  // Older documents
  {
    id: '5',
    company_id: 'preview-company',
    document_type: 'compra_factura_electronica',
    document_number: '78901',
    issue_date: new Date(currentYear, currentMonth, currentDate.getDate() - 3).toISOString(),
    amount: 680000,
    tax_amount: 129200,
    status: 'Recibida',
    description: 'Arriendo oficina',
    created_at: new Date().toISOString(),
  },
  {
    id: '6',
    company_id: 'preview-company',
    document_type: 'venta_nota_credito',
    document_number: '23456',
    issue_date: new Date(currentYear, currentMonth, currentDate.getDate() - 5).toISOString(),
    amount: -125000,
    tax_amount: -23750,
    status: 'Emitida',
    description: 'Devolución productos',
    created_at: new Date().toISOString(),
  },
  {
    id: '7',
    company_id: 'preview-company',
    document_type: 'venta_factura_electronica',
    document_number: '34567',
    issue_date: new Date(currentYear, currentMonth, currentDate.getDate() - 7).toISOString(),
    amount: 1450000,
    tax_amount: 275500,
    status: 'Emitida',
    description: 'Proyecto desarrollo web',
    created_at: new Date().toISOString(),
  },
  {
    id: '8',
    company_id: 'preview-company',
    document_type: 'compra_factura_electronica',
    document_number: '45678',
    issue_date: new Date(currentYear, currentMonth, currentDate.getDate() - 8).toISOString(),
    amount: 350000,
    tax_amount: 66500,
    status: 'Recibida',
    description: 'Servicios contables',
    created_at: new Date().toISOString(),
  },
  {
    id: '9',
    company_id: 'preview-company',
    document_type: 'venta_boleta_electronica',
    document_number: '56789',
    issue_date: new Date(currentYear, currentMonth, currentDate.getDate() - 10).toISOString(),
    amount: 89000,
    tax_amount: 16910,
    status: 'Emitida',
    created_at: new Date().toISOString(),
  },
  {
    id: '10',
    company_id: 'preview-company',
    document_type: 'compra_factura_electronica',
    document_number: '67891',
    issue_date: new Date(currentYear, currentMonth, currentDate.getDate() - 12).toISOString(),
    amount: 520000,
    tax_amount: 98800,
    status: 'Pendiente',
    description: 'Servicios marketing',
    created_at: new Date().toISOString(),
  },
  {
    id: '11',
    company_id: 'preview-company',
    document_type: 'venta_factura_electronica',
    document_number: '78902',
    issue_date: new Date(currentYear, currentMonth, currentDate.getDate() - 14).toISOString(),
    amount: 2100000,
    tax_amount: 399000,
    status: 'Emitida',
    description: 'Mantenimiento sistema',
    created_at: new Date().toISOString(),
  },
  {
    id: '12',
    company_id: 'preview-company',
    document_type: 'venta_boleta_electronica',
    document_number: '89013',
    issue_date: new Date(currentYear, currentMonth, currentDate.getDate() - 15).toISOString(),
    amount: 145000,
    tax_amount: 27550,
    status: 'Emitida',
    created_at: new Date().toISOString(),
  },
];

interface DocumentsPreviewProps {
  scheme?: 'light' | 'dark';
}

/**
 * DocumentsPreview component for the landing page.
 * Shows the documents list with mock data to give users a preview.
 */
export function DocumentsPreview({ scheme = 'light' }: DocumentsPreviewProps) {
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
        day: 'numeric',
        month: 'long',
      });
    }
  };

  const formatDocumentTypeName = (docType: string) => {
    return docType
      .split('_')
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
      .join(' ');
  };

  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'emitida':
      case 'recibida':
      case 'pagada':
        return <CheckCircle className="h-4 w-4 text-emerald-500" />;
      case 'pendiente':
        return <Clock className="h-4 w-4 text-amber-500" />;
      default:
        return <FileText className="h-4 w-4 text-slate-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'emitida':
      case 'recibida':
      case 'pagada':
        return 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/30 dark:text-emerald-400';
      case 'pendiente':
        return 'bg-amber-50 text-amber-700 dark:bg-amber-950/30 dark:text-amber-400';
      default:
        return 'bg-slate-50 text-slate-700 dark:bg-slate-800 dark:text-slate-400';
    }
  };

  // Group documents by date
  const groupDocumentsByDate = (docs: TaxDocument[]) => {
    const groups = new Map<string, TaxDocument[]>();

    docs.forEach((doc) => {
      const dateKey = doc.issue_date;
      if (!groups.has(dateKey)) {
        groups.set(dateKey, []);
      }
      groups.get(dateKey)!.push(doc);
    });

    return Array.from(groups.entries())
      .sort(([dateA], [dateB]) => new Date(dateB).getTime() - new Date(dateA).getTime())
      .map(([date, docs]) => ({ date, docs }));
  };

  const groupedDocuments = groupDocumentsByDate(mockDocuments);

  // Calculate statistics - matching real component
  const totalVentas = mockDocuments
    .filter((doc) => doc.document_type.startsWith('venta_') && doc.amount > 0)
    .length;
  const totalF29 = 12; // Fixed number for demo
  const totalBoletas = mockDocuments.filter((doc) =>
    doc.document_type.includes('boleta')
  ).length * 67; // Multiply to get a realistic count

  return (
    <div className="w-full max-w-4xl mx-auto">
      <div className="overflow-hidden rounded-3xl border border-gray-200 bg-white shadow-2xl dark:border-gray-700 dark:bg-gray-800">
        {/* Fake browser chrome */}
        <div className="flex items-center justify-between border-b border-gray-200 bg-gray-50 px-4 py-3 dark:border-gray-700 dark:bg-gray-900">
          <div className="flex items-center space-x-2">
            <div className="h-3 w-3 rounded-full bg-red-500" />
            <div className="h-3 w-3 rounded-full bg-yellow-500" />
            <div className="h-3 w-3 rounded-full bg-green-500" />
          </div>
          <div className="text-xs font-medium text-gray-500 dark:text-gray-400">
            Documentos Tributarios
          </div>
          <div className="w-16" />
        </div>

        {/* Content */}
        <div className="relative max-h-[600px] overflow-hidden">
          <div className="pointer-events-none p-6 opacity-95">
            {/* Stats Header */}
            <div className="mb-6 grid grid-cols-3 gap-4">
              <div className="rounded-lg bg-blue-50 p-3 dark:bg-blue-900/20">
                <p className="text-xs text-slate-600 dark:text-slate-400">Facturas emitidas</p>
                <p className="text-2xl font-bold text-blue-700 dark:text-blue-400">{totalVentas}</p>
              </div>
              <div className="rounded-lg bg-green-50 p-3 dark:bg-green-900/20">
                <p className="text-xs text-slate-600 dark:text-slate-400">F29 presentados</p>
                <p className="text-2xl font-bold text-green-700 dark:text-green-400">12</p>
              </div>
              <div className="rounded-lg bg-purple-50 p-3 dark:bg-purple-900/20">
                <p className="text-xs text-slate-600 dark:text-slate-400">Boletas registradas</p>
                <p className="text-2xl font-bold text-purple-700 dark:text-purple-400">
                  {totalBoletas * 67}
                </p>
              </div>
            </div>

            {/* Documents List */}
            <div className="space-y-6">
              {groupedDocuments.map(({ date, docs }) => (
                <div key={date}>
                  <h4 className="mb-3 text-sm font-semibold text-slate-900 dark:text-slate-100">
                    {formatFullDate(date)}
                  </h4>
                  <div className="space-y-2">
                    {docs.map((doc) => (
                      <div
                        key={doc.id}
                        className="flex items-center justify-between rounded-lg border border-slate-200 bg-white p-4 transition-all hover:border-slate-300 hover:shadow-sm dark:border-slate-700 dark:bg-slate-900 dark:hover:border-slate-600"
                      >
                        <div className="flex flex-1 items-center gap-3">
                          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-slate-100 dark:bg-slate-800">
                            <FileText className="h-5 w-5 text-slate-600 dark:text-slate-400" />
                          </div>
                          <div className="flex-1">
                            <div className="flex items-center gap-2">
                              <p className="text-sm font-medium text-slate-900 dark:text-slate-100">
                                {formatDocumentTypeName(doc.document_type)}
                              </p>
                              <span
                                className={`rounded-full px-2 py-0.5 text-xs font-medium ${getStatusColor(
                                  doc.status
                                )}`}
                              >
                                {getStatusIcon(doc.status)}
                              </span>
                            </div>
                            <div className="mt-1 flex items-center gap-2 text-xs text-slate-600 dark:text-slate-400">
                              <span>N° {doc.document_number}</span>
                              {doc.description && (
                                <>
                                  <span>•</span>
                                  <span>{doc.description}</span>
                                </>
                              )}
                            </div>
                          </div>
                        </div>
                        <div className="text-right">
                          <p
                            className={`text-base font-bold ${
                              doc.amount >= 0
                                ? 'text-slate-900 dark:text-slate-100'
                                : 'text-red-600 dark:text-red-400'
                            }`}
                          >
                            {formatCurrency(doc.amount)}
                          </p>
                          {doc.tax_amount && (
                            <p className="text-xs text-slate-500 dark:text-slate-400">
                              IVA: {formatCurrency(doc.tax_amount)}
                            </p>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Gradient overlay at bottom */}
          <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-white to-transparent dark:from-gray-800" />
        </div>
      </div>
    </div>
  );
}
