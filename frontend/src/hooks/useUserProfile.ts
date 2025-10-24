import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { API_BASE_URL } from '../lib/config';
import { apiFetch } from '../lib/api-client';

export interface UserProfile {
  id: string;
  email: string;
  name: string | null;
  lastname: string | null;
  phone: string | null;
  phone_verified: boolean;
  phone_verified_at: string | null;
  full_name: string | null;
  company_name: string | null;
  avatar_url: string | null;
  rol: string | null;
  created_at: string;
  updated_at: string;
}

export interface ProfileUpdateData {
  name?: string;
  lastname?: string;
  phone?: string;
  full_name?: string;
  company_name?: string;
  avatar_url?: string;
}

export function useUserProfile() {
  const { session } = useAuth();
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchProfile = useCallback(async () => {
    if (!session?.access_token) {
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const response = await apiFetch(`${API_BASE_URL}/profile`, {
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        if (response.status === 404) {
          setProfile(null);
          setError('Perfil no encontrado');
          return;
        }
        throw new Error(`Failed to fetch profile: ${response.statusText}`);
      }

      const data = await response.json();
      setProfile(data.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch profile');
      setProfile(null);
    } finally {
      setLoading(false);
    }
  }, [session?.access_token]);

  const updateProfile = useCallback(async (updateData: ProfileUpdateData): Promise<boolean> => {
    if (!session?.access_token) {
      setError('No authenticated session');
      return false;
    }

    try {
      setError(null);

      const response = await apiFetch(`${API_BASE_URL}/profile`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(updateData),
      });

      if (!response.ok) {
        throw new Error(`Failed to update profile: ${response.statusText}`);
      }

      const data = await response.json();
      setProfile(data.data);
      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update profile');
      return false;
    }
  }, [session?.access_token]);

  const requestPhoneVerification = useCallback(async (): Promise<boolean> => {
    if (!session?.access_token) {
      setError('No authenticated session');
      return false;
    }

    try {
      setError(null);

      const response = await apiFetch(`${API_BASE_URL}/profile/verify-phone/request`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to request verification');
      }

      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to request verification');
      return false;
    }
  }, [session?.access_token]);

  const confirmPhoneVerification = useCallback(async (code: string): Promise<boolean> => {
    if (!session?.access_token) {
      setError('No authenticated session');
      return false;
    }

    try {
      setError(null);

      const response = await apiFetch(`${API_BASE_URL}/profile/verify-phone/confirm?code=${encodeURIComponent(code)}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to verify code');
      }

      // Refresh profile to get updated verification status
      await fetchProfile();
      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to verify code');
      return false;
    }
  }, [session?.access_token, fetchProfile]);

  useEffect(() => {
    fetchProfile();
  }, [fetchProfile]);

  return {
    profile,
    loading,
    error,
    refresh: fetchProfile,
    updateProfile,
    requestPhoneVerification,
    confirmPhoneVerification,
  };
}
