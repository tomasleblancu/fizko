import { useState, useEffect } from 'react';
import { Calendar } from 'lucide-react';

interface PeriodSelectorProps {
  onPeriodChange?: (year: number, month: number) => void;
}

export function PeriodSelector({ onPeriodChange }: PeriodSelectorProps) {
  const currentDate = new Date();
  const currentYear = currentDate.getFullYear();
  const currentMonth = currentDate.getMonth() + 1;

  const [selectedYear, setSelectedYear] = useState(currentYear);
  const [selectedMonth, setSelectedMonth] = useState(currentMonth);

  // Month names in Spanish
  const months = [
    { value: 1, label: 'Enero' },
    { value: 2, label: 'Febrero' },
    { value: 3, label: 'Marzo' },
    { value: 4, label: 'Abril' },
    { value: 5, label: 'Mayo' },
    { value: 6, label: 'Junio' },
    { value: 7, label: 'Julio' },
    { value: 8, label: 'Agosto' },
    { value: 9, label: 'Septiembre' },
    { value: 10, label: 'Octubre' },
    { value: 11, label: 'Noviembre' },
    { value: 12, label: 'Diciembre' },
  ];

  // Generate years (last 2 years + current year + next year)
  const years = [];
  for (let year = currentYear - 2; year <= currentYear + 1; year++) {
    years.push(year);
  }

  // Notify parent when period changes
  useEffect(() => {
    if (onPeriodChange) {
      onPeriodChange(selectedYear, selectedMonth);
    }
  }, [selectedYear, selectedMonth, onPeriodChange]);

  const handleYearChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedYear(parseInt(e.target.value));
  };

  const handleMonthChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedMonth(parseInt(e.target.value));
  };

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2 text-sm font-medium text-slate-700 dark:text-slate-300">
        <Calendar className="h-4 w-4 text-slate-400" />
        <span>Periodo</span>
      </div>

      <div className="rounded-2xl border border-slate-200/70 bg-gradient-to-br from-white to-slate-50 p-4 dark:border-slate-800/70 dark:from-slate-900/70 dark:to-slate-800/70">
        <div className="flex gap-3">
          {/* Month Selector */}
          <div className="flex-1">
            <label htmlFor="month-select" className="mb-1.5 block text-xs font-medium text-slate-600 dark:text-slate-400">
              Mes
            </label>
            <select
              id="month-select"
              value={selectedMonth}
              onChange={handleMonthChange}
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm font-medium text-slate-900 transition-colors hover:border-blue-400 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100 dark:hover:border-blue-500"
            >
              {months.map((month) => (
                <option key={month.value} value={month.value}>
                  {month.label}
                </option>
              ))}
            </select>
          </div>

          {/* Year Selector */}
          <div className="w-32">
            <label htmlFor="year-select" className="mb-1.5 block text-xs font-medium text-slate-600 dark:text-slate-400">
              Año
            </label>
            <select
              id="year-select"
              value={selectedYear}
              onChange={handleYearChange}
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm font-medium text-slate-900 transition-colors hover:border-blue-400 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100 dark:hover:border-blue-500"
            >
              {years.map((year) => (
                <option key={year} value={year}>
                  {year}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>
    </div>
  );
}
