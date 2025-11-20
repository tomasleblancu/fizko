import { useState, useEffect, useRef } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import clsx from 'clsx';

interface MonthItem {
  label: string;
  shortLabel: string;
  value: string; // YYYY-MM format
  monthNumber: number;
  year: number;
}

interface MonthCarouselProps {
  onMonthSelect: (month: string | undefined) => void;
  selectedMonth?: string;
  monthsToShow?: number;
  orientation?: 'horizontal' | 'vertical';
}

export function MonthCarousel({
  onMonthSelect,
  selectedMonth,
  monthsToShow = 6
}: MonthCarouselProps) {
  const [months, setMonths] = useState<MonthItem[]>([]);
  const [scrollPosition, setScrollPosition] = useState(0);
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  // Generate last N months
  useEffect(() => {
    const generateMonths = () => {
      const result: MonthItem[] = [];
      const now = new Date();

      for (let i = monthsToShow - 1; i >= 0; i--) {
        const date = new Date(now.getFullYear(), now.getMonth() - i, 1);
        const year = date.getFullYear();
        const month = date.getMonth();

        const monthNames = [
          'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
          'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
        ];

        const shortMonthNames = [
          'Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun',
          'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'
        ];

        result.push({
          label: `${monthNames[month]} ${year}`,
          shortLabel: `${shortMonthNames[month]} ${year}`,
          value: `${year}-${String(month + 1).padStart(2, '0')}`,
          monthNumber: month + 1,
          year
        });
      }

      return result;
    };

    setMonths(generateMonths());
  }, [monthsToShow]);

  // Auto-select current month on mount if no selection
  useEffect(() => {
    if (!selectedMonth && months.length > 0) {
      // Select the last month (current month)
      onMonthSelect(months[months.length - 1].value);
    }
  }, [months, selectedMonth, onMonthSelect]);

  const handleScroll = (direction: 'left' | 'right') => {
    if (!scrollContainerRef.current) return;

    const container = scrollContainerRef.current;
    const scrollAmount = 200;
    const newPosition = direction === 'left'
      ? Math.max(0, scrollPosition - scrollAmount)
      : Math.min(
          container.scrollWidth - container.clientWidth,
          scrollPosition + scrollAmount
        );

    container.scrollTo({ left: newPosition, behavior: 'smooth' });
    setScrollPosition(newPosition);
  };

  const handleMonthClick = (month: MonthItem) => {
    onMonthSelect(month.value);
  };

  const canScrollLeft = scrollPosition > 0;
  const canScrollRight = scrollContainerRef.current
    ? scrollPosition < scrollContainerRef.current.scrollWidth - scrollContainerRef.current.clientWidth
    : false;

  return (
    <div className="relative w-full">
      {/* Scroll Left Button */}
      {canScrollLeft && (
        <button
          onClick={() => handleScroll('left')}
          className="absolute left-0 top-1/2 z-10 -translate-y-1/2 rounded-full bg-white p-1.5 shadow-lg transition-all hover:bg-slate-50 dark:bg-slate-800 dark:hover:bg-slate-700"
          aria-label="Desplazar a la izquierda"
        >
          <ChevronLeft className="h-4 w-4 text-slate-700 dark:text-slate-300" />
        </button>
      )}

      {/* Months Container - Horizontal */}
      <div
        ref={scrollContainerRef}
        className="flex gap-2 overflow-x-auto scrollbar-hide px-8 py-1"
        onScroll={(e) => setScrollPosition(e.currentTarget.scrollLeft)}
      >
        {months.map((month) => {
          const isSelected = selectedMonth === month.value;
          const isCurrentMonth = month.value === months[months.length - 1]?.value;

          return (
            <button
              key={month.value}
              onClick={() => handleMonthClick(month)}
              className={clsx(
                "flex flex-col items-center justify-center rounded-lg px-3 py-2 transition-all duration-200 flex-shrink-0 min-w-[75px]",
                "border-2",
                isSelected
                  ? "border-emerald-500 bg-emerald-50 dark:border-emerald-400 dark:bg-emerald-950/30"
                  : "border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:hover:border-slate-600 dark:hover:bg-slate-800"
              )}
            >
              <div className={clsx(
                "text-base font-bold uppercase tracking-tight",
                isSelected
                  ? "text-emerald-700 dark:text-emerald-400"
                  : "text-slate-900 dark:text-slate-100"
              )}>
                {month.shortLabel.split(' ')[0]}
              </div>
              <div className={clsx(
                "text-[10px] font-medium",
                isSelected
                  ? "text-emerald-600 dark:text-emerald-500"
                  : "text-slate-500 dark:text-slate-400"
              )}>
                {month.year}
              </div>
              {isCurrentMonth && (
                <div className="mt-1 h-0.5 w-6 rounded-full bg-emerald-500 dark:bg-emerald-400" />
              )}
            </button>
          );
        })}
      </div>

      {/* Scroll Right Button */}
      {canScrollRight && (
        <button
          onClick={() => handleScroll('right')}
          className="absolute right-0 top-1/2 z-10 -translate-y-1/2 rounded-full bg-white p-1.5 shadow-lg transition-all hover:bg-slate-50 dark:bg-slate-800 dark:hover:bg-slate-700"
          aria-label="Desplazar a la derecha"
        >
          <ChevronRight className="h-4 w-4 text-slate-700 dark:text-slate-300" />
        </button>
      )}

      {/* Custom styles for hiding scrollbar */}
      <style>{`
        .scrollbar-hide::-webkit-scrollbar {
          display: none;
        }
        .scrollbar-hide {
          -ms-overflow-style: none;
          scrollbar-width: none;
        }
      `}</style>
    </div>
  );
}
