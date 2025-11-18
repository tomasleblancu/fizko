import React, { createContext, useContext, useState, useCallback, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useAuth } from './AuthContext';
import { API_BASE_URL } from '@/shared/lib/config';
import type { SIISession } from '@/shared/hooks/useSession';

interface CompanyInfo {
  id: string;
  rut: string;
  business_name: string;
  trade_name?: string;
}

interface CompanyContextType {
  availableCompanies: CompanyInfo[];
  selectedCompanyId: string | null;
  selectedCompany: CompanyInfo | null;
  setSelectedCompany: (companyId: string) => void;
  isLoading: boolean;
}

const CompanyContext = createContext<CompanyContextType | undefined>(undefined);

const STORAGE_KEY = 'fizko_selected_company_id';

export function CompanyProvider({ children }: { children: React.ReactNode }) {
  const { session: authSession } = useAuth();
  const [selectedCompanyId, setSelectedCompanyIdState] = useState<string | null>(() => {
    // Initialize from localStorage
    return localStorage.getItem(STORAGE_KEY);
  });

  // Use React Query to fetch sessions - this handles caching and deduplication automatically
  const { data: sessionsData, isLoading } = useQuery({
    queryKey: ['sessions'],
    queryFn: async () => {
      if (!authSession?.access_token) {
        throw new Error('No auth token');
      }

      // API_BASE_URL already includes /api, so just append /sessions
      const response = await fetch(`${API_BASE_URL}/sessions`, {
        headers: {
          'Authorization': `Bearer ${authSession.access_token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch sessions');
      }

      const result = await response.json();
      return result.data as SIISession[];
    },
    enabled: !!authSession?.access_token,
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchOnWindowFocus: false,
    refetchOnMount: false, // Prevent refetch on component mount
  });

  // Extract companies from sessions
  const availableCompanies = useMemo(() => {
    if (!sessionsData) return [];

    const companies = sessionsData
      .filter(s => s.company)
      .map(s => s.company!)
      .filter((company, index, self) =>
        index === self.findIndex(c => c.id === company.id)
      );

    return companies;
  }, [sessionsData]);

  // Auto-select company if needed
  useMemo(() => {
    if (isLoading || availableCompanies.length === 0) return;

    // If already selected and valid, keep it
    if (selectedCompanyId && availableCompanies.some(c => c.id === selectedCompanyId)) {
      return;
    }

    // Auto-select based on priority
    const storedCompanyId = localStorage.getItem(STORAGE_KEY);
    const activeSession = sessionsData?.find(s => s.is_active);

    let companyToSelect: string | null = null;

    if (storedCompanyId && availableCompanies.some(c => c.id === storedCompanyId)) {
      companyToSelect = storedCompanyId;
    } else if (activeSession?.company) {
      companyToSelect = activeSession.company.id;
    } else if (availableCompanies.length > 0) {
      companyToSelect = availableCompanies[0].id;
    }

    if (companyToSelect) {
      setSelectedCompanyIdState(companyToSelect);
      localStorage.setItem(STORAGE_KEY, companyToSelect);
    }
  }, [availableCompanies, selectedCompanyId, sessionsData, isLoading]);

  const setSelectedCompany = useCallback((companyId: string) => {
    setSelectedCompanyIdState(companyId);
    localStorage.setItem(STORAGE_KEY, companyId);

    // Reload the page to refresh all data with new company context
    window.location.reload();
  }, []);

  const selectedCompany = useMemo(() => {
    return selectedCompanyId
      ? availableCompanies.find(c => c.id === selectedCompanyId) || null
      : null;
  }, [selectedCompanyId, availableCompanies]);

  const value = useMemo(() => ({
    availableCompanies,
    selectedCompanyId,
    selectedCompany,
    setSelectedCompany,
    isLoading,
  }), [availableCompanies, selectedCompanyId, selectedCompany, setSelectedCompany, isLoading]);

  return (
    <CompanyContext.Provider value={value}>
      {children}
    </CompanyContext.Provider>
  );
}

export function useCompanyContext() {
  const context = useContext(CompanyContext);
  if (context === undefined) {
    throw new Error('useCompanyContext must be used within a CompanyProvider');
  }
  return context;
}
