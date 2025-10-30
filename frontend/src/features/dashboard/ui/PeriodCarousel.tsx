import { useState, useEffect, useRef, useCallback } from 'react';
import clsx from 'clsx';

interface Period {
  year: number;
  month: number;
  label: string;
  key: string;
}

interface PeriodCarouselProps {
  onPeriodChange?: (year: number, month: number) => void;
  onPrefetchPeriod?: (year: number, month: number) => void;
  className?: string;
}

// Generate periods: last 24 months + current month (no future months)
function generatePeriods(): Period[] {
  const periods: Period[] = [];
  const now = new Date();
  const currentYear = now.getFullYear();
  const currentMonth = now.getMonth() + 1; // 1-12

  const monthNames = [
    'Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun',
    'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'
  ];

  // Generate periods from 24 months ago to current month (inclusive)
  for (let i = -24; i <= 0; i++) {
    const date = new Date(currentYear, currentMonth - 1 + i, 1);
    const year = date.getFullYear();
    const month = date.getMonth() + 1;

    periods.push({
      year,
      month,
      label: `${monthNames[month - 1]} ${year}`,
      key: `${year}-${month.toString().padStart(2, '0')}`,
    });
  }

  return periods;
}

export function PeriodCarousel({ onPeriodChange, onPrefetchPeriod, className }: PeriodCarouselProps) {
  const now = new Date();
  const currentYear = now.getFullYear();
  const currentMonth = now.getMonth() + 1;

  const [selectedPeriod, setSelectedPeriod] = useState<Period>({
    year: currentYear,
    month: currentMonth,
    label: '',
    key: `${currentYear}-${currentMonth.toString().padStart(2, '0')}`,
  });

  const [periods] = useState<Period[]>(generatePeriods());
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = scrollContainerRef.current;
    if (!container) return;

    // Scroll to current period on mount
    const currentIndex = periods.findIndex(p => p.key === selectedPeriod.key);
    if (currentIndex !== -1) {
      const button = container.children[currentIndex] as HTMLElement;
      if (button) {
        button.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
      }
    }
  }, [periods, selectedPeriod.key]);

  // Notify parent when period changes
  useEffect(() => {
    if (onPeriodChange && selectedPeriod.year && selectedPeriod.month) {
      onPeriodChange(selectedPeriod.year, selectedPeriod.month);
    }
  }, [selectedPeriod, onPeriodChange]);

  // Prefetch adjacent periods when selection changes
  useEffect(() => {
    if (!onPrefetchPeriod) return;

    const currentIndex = periods.findIndex(p => p.key === selectedPeriod.key);

    // Prefetch previous period
    if (currentIndex > 0) {
      const prevPeriod = periods[currentIndex - 1];
      onPrefetchPeriod(prevPeriod.year, prevPeriod.month);
    }

    // Prefetch next period
    if (currentIndex < periods.length - 1) {
      const nextPeriod = periods[currentIndex + 1];
      onPrefetchPeriod(nextPeriod.year, nextPeriod.month);
    }
  }, [selectedPeriod, periods, onPrefetchPeriod]);

  const handlePeriodClick = (period: Period) => {
    setSelectedPeriod(period);

    // Scroll the clicked period to center
    const container = scrollContainerRef.current;
    if (container) {
      const index = periods.findIndex(p => p.key === period.key);
      const button = container.children[index] as HTMLElement;
      if (button) {
        button.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
      }
    }
  };

  // Keyboard navigation
  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    if (e.key === 'ArrowLeft') {
      e.preventDefault();
      const currentIndex = periods.findIndex(p => p.key === selectedPeriod.key);
      if (currentIndex > 0) {
        handlePeriodClick(periods[currentIndex - 1]);
      }
    } else if (e.key === 'ArrowRight') {
      e.preventDefault();
      const currentIndex = periods.findIndex(p => p.key === selectedPeriod.key);
      if (currentIndex < periods.length - 1) {
        handlePeriodClick(periods[currentIndex + 1]);
      }
    }
  }, [periods, selectedPeriod.key]);

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  return (
    <div className={clsx('overflow-hidden', className)}>
      {/* Scrollable period container - NO gap, use margin on items instead */}
      <div
        ref={scrollContainerRef}
        className="overflow-x-auto py-2 scrollbar-hide"
        style={{
          scrollbarWidth: 'none',
          msOverflowStyle: 'none',
          WebkitOverflowScrolling: 'touch',
          display: 'flex',
          whiteSpace: 'nowrap',
        }}
      >
        {periods.map((period) => {
          const isActive = period.key === selectedPeriod.key;
          const isCurrentMonth = period.year === currentYear && period.month === currentMonth;

          return (
            <button
              key={period.key}
              onClick={() => handlePeriodClick(period)}
              className={clsx(
                'inline-block flex-shrink-0 rounded-full px-4 py-2 mr-2 text-sm font-medium transition-all duration-200 whitespace-nowrap',
                isActive
                  ? 'bg-gradient-to-r from-blue-500 to-blue-600 text-white ring-2 ring-inset ring-blue-300 dark:ring-blue-400'
                  : isCurrentMonth
                  ? 'bg-blue-50 text-blue-700 hover:bg-blue-100 dark:bg-blue-950/30 dark:text-blue-400 dark:hover:bg-blue-900/40'
                  : 'bg-slate-100 text-slate-700 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700'
              )}
            >
              {period.label}
            </button>
          );
        })}
      </div>

      {/* CSS to hide scrollbar */}
      <style>{`
        .scrollbar-hide::-webkit-scrollbar {
          display: none;
        }
      `}</style>
    </div>
  );
}
