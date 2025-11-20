/**
 * SII Backend Client
 *
 * HTTP client for communicating with backend-v2 SII endpoints
 */

import { BackendClient } from '@/lib/backend-client';
import { SIILoginResponse } from '@/types/sii.types';

export class SIIBackendClient {
  /**
   * Authenticate with SII through backend-v2
   *
   * @param rutBody - RUT without DV (e.g., "77794858")
   * @param dv - DV character (e.g., "K" or "k")
   * @param password - SII password
   * @returns SII login response with contributor info and cookies
   * @throws Error if backend call fails or authentication fails
   */
  static async login(
    rutBody: string,
    dv: string,
    password: string
  ): Promise<SIILoginResponse> {
    console.log('[SII Backend Client] Authenticating with SII');

    try {
      const data = await BackendClient.post<SIILoginResponse>(
        '/api/sii/login',
        {
          rut: rutBody,
          dv: dv,
          password: password,
        }
      );

      console.log(
        '[SII Backend Client] Response:',
        JSON.stringify(data, null, 2)
      );

      if (!data.success) {
        console.log('[SII Backend Client] Login failed:', data.message);
        throw new Error(data.message || 'Error al autenticar con SII');
      }

      console.log('[SII Backend Client] Login successful');
      return data;
    } catch (error) {
      if (error instanceof Error) {
        throw error;
      }
      throw new Error('Unknown error communicating with backend');
    }
  }
}

