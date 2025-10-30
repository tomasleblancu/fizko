import React, { createContext, useContext, useState, useCallback, useRef } from 'react';

interface CacheEntry<T> {
  data: T;
  timestamp: number;
  isStale?: boolean;
}

interface DashboardCacheContextType {
  get: <T>(key: string) => CacheEntry<T> | null;
  set: <T>(key: string, data: T) => void;
  invalidate: (key: string) => void;
  invalidateAll: () => void;
  markStale: (key: string) => void;
}

const DashboardCacheContext = createContext<DashboardCacheContextType | undefined>(undefined);

// Default TTL: 5 minutes
const DEFAULT_TTL_MS = 5 * 60 * 1000;

export function DashboardCacheProvider({ children }: { children: React.ReactNode }) {
  const cacheRef = useRef<Map<string, CacheEntry<any>>>(new Map());

  const get = useCallback(<T,>(key: string): CacheEntry<T> | null => {
    const entry = cacheRef.current.get(key);

    if (!entry) {
      return null;
    }

    // Check if entry is expired (beyond TTL)
    const now = Date.now();
    const age = now - entry.timestamp;

    if (age > DEFAULT_TTL_MS) {
      // Entry is expired, remove it
      cacheRef.current.delete(key);
      return null;
    }

    return entry as CacheEntry<T>;
  }, []);

  const set = useCallback(<T,>(key: string, data: T) => {
    cacheRef.current.set(key, {
      data,
      timestamp: Date.now(),
      isStale: false,
    });
  }, []);

  const invalidate = useCallback((key: string) => {
    cacheRef.current.delete(key);
  }, []);

  const invalidateAll = useCallback(() => {
    cacheRef.current.clear();
  }, []);

  const markStale = useCallback((key: string) => {
    const entry = cacheRef.current.get(key);
    if (entry) {
      cacheRef.current.set(key, {
        ...entry,
        isStale: true,
      });
    }
  }, []);

  const value: DashboardCacheContextType = {
    get,
    set,
    invalidate,
    invalidateAll,
    markStale,
  };

  return (
    <DashboardCacheContext.Provider value={value}>
      {children}
    </DashboardCacheContext.Provider>
  );
}

export function useDashboardCache() {
  const context = useContext(DashboardCacheContext);
  if (context === undefined) {
    throw new Error('useDashboardCache must be used within a DashboardCacheProvider');
  }
  return context;
}
