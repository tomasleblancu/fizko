import { useState, useEffect, useCallback, useRef } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { API_BASE_URL } from '../lib/config';

export interface SIISession {
  id: string;
  user_id: string;
  company_id: string;
  company?: {
    id: string;
    rut: string;
    business_name: string;
    trade_name?: string;
  };
  is_active: boolean;
  has_cookies: boolean;
  has_resources: boolean;
  last_accessed_at?: string;
  created_at: string;
  updated_at: string;
}

export interface OnboardingStatus {
  needsOnboarding: boolean;
  hasSession: boolean;
  session: SIISession | null;
}

export function useSession() {
  const { user, session: authSession } = useAuth();
  const [session, setSession] = useState<SIISession | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  // Start with false to prevent showing onboarding immediately
  // Will be set to true only after confirming it's needed
  const [needsOnboarding, setNeedsOnboarding] = useState(false);
  const [isInitialized, setIsInitialized] = useState(false);
  const lastFetchKeyRef = useRef<string>('');

  const fetchSession = useCallback(async (force: boolean = false) => {
    if (!user || !authSession) {
      setNeedsOnboarding(true);
      setIsInitialized(true);
      setLoading(false);
      return;
    }

    // Create a unique key for this user+session combo
    const fetchKey = `${user.id}-${authSession.access_token.slice(0, 10)}`;

    // Prevent duplicate calls unless forced
    if (lastFetchKeyRef.current === fetchKey && !force) {
      console.log('[useSession] Skipping duplicate fetch for', fetchKey);
      return;
    }

    lastFetchKeyRef.current = fetchKey;

    try {
      // Keep isInitialized as false while fetching
      setIsInitialized(false);
      setLoading(true);
      setError(null);

      console.log('[useSession] Fetching sessions for', fetchKey);

      const response = await fetch(`${API_BASE_URL}/sessions`, {
        headers: {
          'Authorization': `Bearer ${authSession.access_token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch session');
      }

      const result = await response.json();

      // Check if user has any active sessions
      if (result.data && result.data.length > 0) {
        const activeSession = result.data.find((s: SIISession) => s.is_active);
        if (activeSession) {
          setSession(activeSession);
          setNeedsOnboarding(false);
          setIsInitialized(true);
          setLoading(false);
        } else {
          // Has sessions but none are active - needs onboarding
          setSession(result.data[0]);
          setNeedsOnboarding(true);
          setIsInitialized(true);
          setLoading(false);
        }
      } else {
        // No sessions at all - needs onboarding
        setSession(null);
        setNeedsOnboarding(true);
        setIsInitialized(true);
        setLoading(false);
      }
    } catch (err) {
      console.error('Error fetching session:', err);
      setError(err instanceof Error ? err.message : 'Unknown error');
      setNeedsOnboarding(true);
      setIsInitialized(true);
      setLoading(false);
    }
  }, [user, authSession]);

  const saveSIICredentials = useCallback(async (credentials: { rut: string; password: string }) => {
    if (!authSession) {
      throw new Error('No estás autenticado');
    }

    // Call the new SII auth login endpoint
    const response = await fetch(`${API_BASE_URL}/sii/auth/login`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${authSession.access_token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(credentials),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Error al autenticar con el SII');
    }

    const result = await response.json();

    // Update local session state with the new session
    if (result.session) {
      setSession({
        id: result.session.id,
        user_id: result.session.user_id,
        company_id: result.session.company_id,
        company: result.company ? {
          id: result.company.id,
          rut: result.company.rut,
          business_name: result.company.business_name,
          trade_name: result.company.trade_name,
        } : undefined,
        is_active: result.session.is_active,
        has_cookies: result.session.has_cookies,
        has_resources: false,
        last_accessed_at: result.session.last_accessed_at,
        created_at: result.session.last_accessed_at || new Date().toISOString(),
        updated_at: result.session.last_accessed_at || new Date().toISOString(),
      });
      setNeedsOnboarding(false);
    }

    return result;
  }, [authSession]);

  useEffect(() => {
    fetchSession();
  }, [fetchSession]);

  return {
    session,
    loading,
    error,
    needsOnboarding,
    isInitialized,
    saveSIICredentials,
    refresh: fetchSession,
  };
}
