/**
 * CSV Download Modal Component
 * Modal for selecting filters before downloading CSV export
 */

import { X, Download } from "lucide-react";

interface CSVDownloadModalProps {
  isOpen: boolean;
  csvYear: string;
  csvMonths: number[];
  csvDocTypes: string[];
  availableYears: string[];
  availableDocTypes: string[];
  onClose: () => void;
  onYearChange: (year: string) => void;
  onToggleMonth: (month: number) => void;
  onToggleDocType: (docType: string) => void;
  onClearMonths: () => void;
  onClearDocTypes: () => void;
  onConfirm: () => void;
}

export function CSVDownloadModal({
  isOpen,
  csvYear,
  csvMonths,
  csvDocTypes,
  availableYears,
  availableDocTypes,
  onClose,
  onYearChange,
  onToggleMonth,
  onToggleDocType,
  onClearMonths,
  onClearDocTypes,
  onConfirm,
}: CSVDownloadModalProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="w-full max-w-lg rounded-xl border border-slate-200 bg-white p-6 shadow-xl dark:border-slate-700 dark:bg-slate-900">
        {/* Modal Header */}
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-lg font-semibold text-slate-900 dark:text-white">
            Exportar Movimientos a CSV
          </h3>
          <button
            onClick={onClose}
            className="rounded-lg p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600 dark:hover:bg-slate-800 dark:hover:text-slate-300"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Modal Content */}
        <div className="space-y-4">
          {/* Year Selector */}
          <div>
            <label className="mb-2 block text-sm font-medium text-slate-700 dark:text-slate-300">
              Año <span className="text-red-500">*</span>
            </label>
            <select
              value={csvYear}
              onChange={(e) => onYearChange(e.target.value)}
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
            >
              <option value="">Seleccionar año</option>
              {availableYears.map((year) => (
                <option key={year} value={year}>
                  {year}
                </option>
              ))}
            </select>
            <p className="mt-1 text-xs text-slate-500">
              Solo se puede exportar un año a la vez
            </p>
          </div>

          {/* Month Selector */}
          <div>
            <label className="mb-2 block text-sm font-medium text-slate-700 dark:text-slate-300">
              Meses{" "}
              {csvMonths.length === 0 && (
                <span className="text-xs font-normal text-slate-500">
                  (todos)
                </span>
              )}
            </label>
            <div className="grid grid-cols-4 gap-2">
              {Array.from({ length: 12 }, (_, i) => i + 1).map((month) => (
                <button
                  key={month}
                  onClick={() => onToggleMonth(month)}
                  className={`rounded-lg border px-3 py-2 text-xs font-medium transition-colors ${
                    csvMonths.includes(month)
                      ? "border-emerald-500 bg-emerald-50 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400"
                      : "border-slate-300 bg-white text-slate-700 hover:border-emerald-300 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300"
                  }`}
                >
                  {new Date(2000, month - 1).toLocaleDateString("es-CL", {
                    month: "short",
                  })}
                </button>
              ))}
            </div>
            {csvMonths.length > 0 && (
              <button
                onClick={onClearMonths}
                className="mt-2 text-xs text-emerald-600 hover:text-emerald-700 dark:text-emerald-400"
              >
                Seleccionar todos
              </button>
            )}
          </div>

          {/* Document Type Selector */}
          <div>
            <label className="mb-2 block text-sm font-medium text-slate-700 dark:text-slate-300">
              Tipos de Documento{" "}
              {csvDocTypes.length === 0 && (
                <span className="text-xs font-normal text-slate-500">
                  (todos)
                </span>
              )}
            </label>
            <div className="max-h-48 space-y-2 overflow-y-auto rounded-lg border border-slate-200 p-3 dark:border-slate-700">
              {availableDocTypes.map((docType) => (
                <label
                  key={docType}
                  className="flex cursor-pointer items-center gap-2 text-sm text-slate-700 dark:text-slate-300"
                >
                  <input
                    type="checkbox"
                    checked={csvDocTypes.includes(docType)}
                    onChange={() => onToggleDocType(docType)}
                    className="h-4 w-4 rounded border-slate-300 text-emerald-600 focus:ring-2 focus:ring-emerald-500/20"
                  />
                  {docType}
                </label>
              ))}
            </div>
            {csvDocTypes.length > 0 && (
              <button
                onClick={onClearDocTypes}
                className="mt-2 text-xs text-emerald-600 hover:text-emerald-700 dark:text-emerald-400"
              >
                Seleccionar todos
              </button>
            )}
          </div>
        </div>

        {/* Modal Footer */}
        <div className="mt-6 flex items-center justify-end gap-3">
          <button
            onClick={onClose}
            className="rounded-lg px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
          >
            Cancelar
          </button>
          <button
            onClick={onConfirm}
            disabled={!csvYear}
            className="flex items-center gap-2 rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            <Download className="h-4 w-4" />
            Descargar CSV
          </button>
        </div>
      </div>
    </div>
  );
}
