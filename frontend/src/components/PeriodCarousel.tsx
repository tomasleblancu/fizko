import { useState, useEffect, useRef, useCallback } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
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
  const [showLeftArrow, setShowLeftArrow] = useState(false);
  const [showRightArrow, setShowRightArrow] = useState(false);
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  // Check scroll position to show/hide arrows
  const checkScrollPosition = useCallback(() => {
    const container = scrollContainerRef.current;
    if (!container) return;

    const { scrollLeft, scrollWidth, clientWidth } = container;
    setShowLeftArrow(scrollLeft > 10);
    setShowRightArrow(scrollLeft < scrollWidth - clientWidth - 10);
  }, []);

  useEffect(() => {
    const container = scrollContainerRef.current;
    if (!container) return;

    checkScrollPosition();

    // Scroll to current period on mount
    const currentIndex = periods.findIndex(p => p.key === selectedPeriod.key);
    if (currentIndex !== -1) {
      const button = container.children[currentIndex] as HTMLElement;
      if (button) {
        button.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
      }
    }

    container.addEventListener('scroll', checkScrollPosition);
    return () => container.removeEventListener('scroll', checkScrollPosition);
  }, [checkScrollPosition, periods, selectedPeriod.key]);

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

  const scrollLeft = () => {
    const container = scrollContainerRef.current;
    if (container) {
      container.scrollBy({ left: -200, behavior: 'smooth' });
    }
  };

  const scrollRight = () => {
    const container = scrollContainerRef.current;
    if (container) {
      container.scrollBy({ left: 200, behavior: 'smooth' });
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
    <div className={clsx('relative group', className)}>
      {/* Left fade gradient */}
      <div
        className={clsx(
          'pointer-events-none absolute left-0 top-0 z-10 h-full w-12 bg-gradient-to-r from-white to-transparent transition-opacity duration-300 dark:from-slate-900',
          showLeftArrow ? 'opacity-100' : 'opacity-0'
        )}
      />

      {/* Left arrow (desktop only) */}
      <button
        onClick={scrollLeft}
        className={clsx(
          'absolute left-1 top-1/2 z-20 hidden -translate-y-1/2 rounded-full bg-white p-1.5 shadow-lg transition-all hover:bg-slate-50 hover:shadow-xl lg:block dark:bg-slate-800 dark:hover:bg-slate-700',
          showLeftArrow ? 'opacity-100' : 'opacity-0 pointer-events-none'
        )}
        aria-label="Período anterior"
      >
        <ChevronLeft className="h-4 w-4 text-slate-600 dark:text-slate-300" />
      </button>

      {/* Scrollable period container */}
      <div
        ref={scrollContainerRef}
        className="flex gap-2 py-2 scrollbar-hide snap-x snap-mandatory"
        style={{
          scrollbarWidth: 'none',
          msOverflowStyle: 'none',
          overflowX: 'scroll',
          width: '100%',
          maxWidth: '100%',
          paddingRight: '16px',
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
                'snap-center flex-shrink-0 rounded-full px-4 py-2 text-sm font-medium transition-all duration-200 whitespace-nowrap',
                isActive
                  ? 'bg-gradient-to-r from-blue-500 to-blue-600 text-white shadow-lg shadow-blue-500/30 ring-2 ring-blue-400 ring-offset-2 dark:ring-offset-slate-900'
                  : isCurrentMonth
                  ? 'bg-blue-50 text-blue-700 hover:bg-blue-100 dark:bg-blue-950/30 dark:text-blue-400 dark:hover:bg-blue-900/40'
                  : 'bg-slate-100 text-slate-700 hover:bg-slate-200 hover:shadow-md dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700'
              )}
            >
              {period.label}
            </button>
          );
        })}
      </div>

      {/* Right fade gradient */}
      <div
        className={clsx(
          'pointer-events-none absolute right-0 top-0 z-10 h-full w-12 bg-gradient-to-l from-white to-transparent transition-opacity duration-300 dark:from-slate-900',
          showRightArrow ? 'opacity-100' : 'opacity-0'
        )}
      />

      {/* Right arrow (desktop only) */}
      <button
        onClick={scrollRight}
        className={clsx(
          'absolute right-1 top-1/2 z-20 hidden -translate-y-1/2 rounded-full bg-white p-1.5 shadow-lg transition-all hover:bg-slate-50 hover:shadow-xl lg:block dark:bg-slate-800 dark:hover:bg-slate-700',
          showRightArrow ? 'opacity-100' : 'opacity-0 pointer-events-none'
        )}
        aria-label="Período siguiente"
      >
        <ChevronRight className="h-4 w-4 text-slate-600 dark:text-slate-300" />
      </button>

      {/* CSS to hide scrollbar */}
      <style>{`
        .scrollbar-hide::-webkit-scrollbar {
          display: none;
        }
      `}</style>
    </div>
  );
}
