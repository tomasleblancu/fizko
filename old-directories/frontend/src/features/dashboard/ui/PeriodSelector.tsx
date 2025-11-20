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
    <div className="flex items-center gap-3">
      {/* Month Selector */}
      <div className="flex-1">
        <select
          id="month-select"
          value={selectedMonth}
          onChange={handleMonthChange}
          className="w-full rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm transition-colors focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
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
        <select
          id="year-select"
          value={selectedYear}
          onChange={handleYearChange}
          className="w-full rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm transition-colors focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
        >
          {years.map((year) => (
            <option key={year} value={year}>
              {year}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
}
