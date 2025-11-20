"use client";

import { useState, useEffect, useRef, useMemo } from "react";
import { useInfiniteCompanyDocuments } from "@/hooks/useInfiniteCompanyDocuments";
import { useTaxSummary } from "@/hooks/useTaxSummary";
import { useUpcomingEvents } from "@/hooks/useUpcomingEvents";
import { useF29Forms } from "@/hooks/useF29Forms";
import type { DocumentWithType } from "@/types/database";
import { PeriodCard } from "./components/PeriodCard";
import { QuickActions } from "./components/QuickActions";
import { CalendarWidget } from "./components/CalendarWidget";
import { MovementsPanel } from "./components/MovementsPanel";
import { CSVDownloadModal } from "./components/CSVDownloadModal";
import "@/styles/chateable.css";

interface DashboardViewProps {
  companyId?: string;
}

export function DashboardView({ companyId }: DashboardViewProps) {
  const [showAllMovements, setShowAllMovements] = useState(false);
  const [movementTypeFilter, setMovementTypeFilter] = useState<'all' | 'sale' | 'purchase'>('all');
  const [showDownloadModal, setShowDownloadModal] = useState(false);
  const loadMoreRef = useRef<HTMLDivElement>(null);

  // CSV download filters
  const [csvDocTypes, setCsvDocTypes] = useState<string[]>([]);
  const [csvYear, setCsvYear] = useState<string>('');
  const [csvMonths, setCsvMonths] = useState<number[]>([]);

  // Calculate periods
  const now = new Date();
  const currentYear = now.getFullYear();
  const currentMonth = now.getMonth() + 1; // JS months are 0-indexed
  const previousMonth = currentMonth === 1 ? 12 : currentMonth - 1;
  const previousYear = currentMonth === 1 ? currentYear - 1 : currentYear;

  const currentPeriod = `${currentYear}-${String(currentMonth).padStart(2, '0')}`;
  const previousPeriod = `${previousYear}-${String(previousMonth).padStart(2, '0')}`;

  // Fetch tax summaries
  const { data: previousMonthSummary, isLoading: previousLoading } = useTaxSummary({
    companyId: companyId || '',
    period: previousPeriod,
  });

  const { data: currentMonthSummary, isLoading: currentLoading } = useTaxSummary({
    companyId: companyId || '',
    period: currentPeriod,
  });

  // Fetch company documents with infinite scroll
  const {
    data: infiniteData,
    isLoading: documentsLoading,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } = useInfiniteCompanyDocuments({
    companyId: companyId || '',
    pageSize: 50,
  });

  // Flatten all pages into a single array
  const documents = useMemo(() => {
    if (!infiniteData?.pages) return [];
    return infiniteData.pages.flatMap(page => page.documents);
  }, [infiniteData]);

  // Fetch upcoming calendar events
  const { data: upcomingEvents, isLoading: calendarLoading } = useUpcomingEvents({
    companyId: companyId || '',
    daysAhead: 30,
  });

  // Fetch F29 forms for previous month to check submission status
  const { data: previousMonthF29 } = useF29Forms({
    companyId: companyId || '',
    year: previousYear,
    month: previousMonth,
  });

  // Check if previous month F29 has been submitted
  const previousF29Form = previousMonthF29?.data?.[0];

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat("es-CL", {
      style: "currency",
      currency: "CLP",
      minimumFractionDigits: 0,
    }).format(amount);
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat("es-CL", {
      weekday: "long",
      day: "numeric",
      month: "long",
    }).format(date);
  };

  const formatMonthYear = (year: number, month: number) => {
    const date = new Date(year, month - 1, 1);
    return new Intl.DateTimeFormat("es-CL", {
      month: "long",
      year: "numeric",
    }).format(date);
  };

  const formatDueDate = (dateString: string) => {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat("es-CL", {
      day: "numeric",
      month: "short",
      year: "numeric",
    }).format(date);
  };

  const formatDaysLeft = (days: number) => {
    if (days === 0) return "Hoy";
    if (days === 1) return "Mañana";
    return `${days} días`;
  };

  // Period string for chateable context
  const previousPeriodString = `${formatMonthYear(previousYear, previousMonth)}`;

  // Group documents by date
  const groupedDocuments = (documents || []).reduce((acc, doc) => {
    const dateKey = doc.issue_date;
    if (!acc[dateKey]) {
      acc[dateKey] = [];
    }
    acc[dateKey].push(doc);
    return acc;
  }, {} as Record<string, DocumentWithType[]>);

  // Convert to array and sort by date (most recent first)
  const documentsByDate = Object.entries(groupedDocuments)
    .sort(([dateA], [dateB]) => new Date(dateB).getTime() - new Date(dateA).getTime())
    .slice(0, 10); // Show last 10 days with activity

  // For expanded view: apply filters and group documents
  const visibleGroupedDocuments = useMemo(() => {
    if (!showAllMovements) return groupedDocuments;

    let filteredDocs = documents || [];

    // Apply movement type filter
    if (movementTypeFilter !== 'all') {
      filteredDocs = filteredDocs.filter(doc => doc.type === movementTypeFilter);
    }

    return filteredDocs.reduce((acc, doc) => {
      const dateKey = doc.issue_date;
      if (!acc[dateKey]) {
        acc[dateKey] = [];
      }
      acc[dateKey].push(doc);
      return acc;
    }, {} as Record<string, DocumentWithType[]>);
  }, [documents, showAllMovements, groupedDocuments, movementTypeFilter]);

  // Intersection Observer for infinite scroll - fetches more pages from backend
  useEffect(() => {
    if (!showAllMovements || !loadMoreRef.current || !hasNextPage || isFetchingNextPage) return;

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) {
          fetchNextPage();
        }
      },
      { threshold: 0.1 }
    );

    observer.observe(loadMoreRef.current);

    return () => observer.disconnect();
  }, [showAllMovements, hasNextPage, isFetchingNextPage, fetchNextPage]);

  // Reset filter when closing expanded view
  useEffect(() => {
    if (!showAllMovements) {
      setMovementTypeFilter('all');
    }
  }, [showAllMovements]);

  // Calculate filtered document count
  const filteredDocumentsCount = useMemo(() => {
    if (!documents) return 0;
    if (movementTypeFilter === 'all') return documents.length;
    return documents.filter(doc => doc.type === movementTypeFilter).length;
  }, [documents, movementTypeFilter]);

  // Get unique document types from current documents
  const availableDocTypes = useMemo(() => {
    if (!documents) return [];
    const types = new Set(documents.map(doc => doc.document_type));
    return Array.from(types).sort();
  }, [documents]);

  // Get available years from documents
  const availableYears = useMemo(() => {
    if (!documents) return [];
    const years = new Set(documents.map(doc => new Date(doc.issue_date).getFullYear()));
    return Array.from(years).sort((a, b) => b - a).map(String); // Most recent first, as strings
  }, [documents]);

  // Open download modal with default values
  const handleDownloadCSV = () => {
    if (!documents || documents.length === 0) return;

    // Set defaults
    setCsvDocTypes([]); // All types selected by default
    setCsvYear(currentYear.toString());
    setCsvMonths([]); // All months by default
    setShowDownloadModal(true);
  };

  // Perform the actual download with filters
  const handleConfirmDownload = async () => {
    if (!companyId || !csvYear) return;

    try {
      // Build query params
      const params = new URLSearchParams({
        companyId,
        year: csvYear,
      });

      // Add doc types if not all selected
      if (csvDocTypes.length > 0) {
        params.append('docTypes', csvDocTypes.join(','));
      }

      // Add months if not all selected
      if (csvMonths.length > 0) {
        params.append('months', csvMonths.join(','));
      }

      // Add movement type filter if active
      if (movementTypeFilter !== 'all') {
        params.append('type', movementTypeFilter);
      }

      // Call API to generate CSV
      const response = await fetch(`/api/documents/export-csv?${params.toString()}`);

      if (!response.ok) {
        throw new Error('Error al generar CSV');
      }

      // Download the CSV
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;

      // Generate filename
      const monthsSuffix = csvMonths.length > 0 ? `_${csvMonths.length}meses` : '_todos';
      const typeSuffix = movementTypeFilter === 'all' ? '' : `_${movementTypeFilter === 'sale' ? 'ventas' : 'compras'}`;
      link.download = `movimientos_${csvYear}${monthsSuffix}${typeSuffix}.csv`;

      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);

      // Close modal
      setShowDownloadModal(false);
    } catch (error) {
      console.error('Error downloading CSV:', error);
      alert('Error al descargar el CSV. Por favor intenta nuevamente.');
    }
  };

  // Toggle document type selection
  const toggleDocType = (docType: string) => {
    setCsvDocTypes(prev =>
      prev.includes(docType)
        ? prev.filter(t => t !== docType)
        : [...prev, docType]
    );
  };

  // Toggle month selection
  const toggleMonth = (month: number) => {
    setCsvMonths(prev =>
      prev.includes(month)
        ? prev.filter(m => m !== month)
        : [...prev, month].sort((a, b) => a - b)
    );
  };

  return (
    <div className="flex h-full flex-col gap-4">
      {/* Period Cards - Hidden when movements expanded */}
      {!showAllMovements && (
        <div className="grid flex-shrink-0 gap-4 lg:grid-cols-2">
          {/* Previous Month Card */}
          <PeriodCard
            period={previousPeriodString}
            year={previousYear}
            month={previousMonth}
            monthlyTax={previousMonthSummary?.monthly_tax || 0}
            totalRevenue={previousMonthSummary?.total_revenue || 0}
            totalExpenses={previousMonthSummary?.total_expenses || 0}
            isLoading={previousLoading}
            isPrevious={true}
            f29Form={previousF29Form}
            formatCurrency={formatCurrency}
            formatMonthYear={formatMonthYear}
          />

          {/* Right Column - Split into Current Month Summary and Quick Actions */}
          <div className="flex flex-1 flex-col gap-4">
            {/* Current Month Card */}
            <PeriodCard
              period={formatMonthYear(currentYear, currentMonth)}
              year={currentYear}
              month={currentMonth}
              monthlyTax={currentMonthSummary?.monthly_tax || 0}
              totalRevenue={currentMonthSummary?.total_revenue || 0}
              totalExpenses={currentMonthSummary?.total_expenses || 0}
              isLoading={currentLoading}
              isPrevious={false}
              formatCurrency={formatCurrency}
              formatMonthYear={formatMonthYear}
            />

            {/* Quick Actions */}
            <QuickActions />
          </div>
        </div>
      )}

      {/* Calendar and Movements */}
      <div className={`grid flex-1 gap-4 overflow-hidden ${showAllMovements ? '' : 'lg:grid-cols-[38%_1fr]'}`}>
        {/* Calendar - Hidden when movements expanded */}
        {!showAllMovements && (
          <CalendarWidget
            upcomingEvents={upcomingEvents}
            isLoading={calendarLoading}
            formatDueDate={formatDueDate}
            formatDaysLeft={formatDaysLeft}
          />
        )}

        {/* Recent Movements */}
        <MovementsPanel
          documents={documents}
          isLoading={documentsLoading}
          showAllMovements={showAllMovements}
          movementTypeFilter={movementTypeFilter}
          visibleGroupedDocuments={visibleGroupedDocuments}
          documentsByDate={documentsByDate}
          filteredDocumentsCount={filteredDocumentsCount}
          hasNextPage={hasNextPage}
          isFetchingNextPage={isFetchingNextPage}
          loadMoreRef={loadMoreRef}
          onToggleExpand={() => setShowAllMovements(!showAllMovements)}
          onFilterChange={setMovementTypeFilter}
          onDownloadCSV={handleDownloadCSV}
          formatDate={formatDate}
          formatCurrency={formatCurrency}
        />
      </div>

      {/* Download CSV Modal */}
      <CSVDownloadModal
        isOpen={showDownloadModal}
        csvYear={csvYear}
        csvMonths={csvMonths}
        csvDocTypes={csvDocTypes}
        availableYears={availableYears}
        availableDocTypes={availableDocTypes}
        onClose={() => setShowDownloadModal(false)}
        onYearChange={setCsvYear}
        onToggleMonth={toggleMonth}
        onToggleDocType={toggleDocType}
        onClearMonths={() => setCsvMonths([])}
        onClearDocTypes={() => setCsvDocTypes([])}
        onConfirm={handleConfirmDownload}
      />
    </div>
  );
}
