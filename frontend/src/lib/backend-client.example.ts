/**
 * Backend Client Usage Examples
 *
 * This file demonstrates how to use the centralized BackendClient
 * for different types of API calls to backend-v2.
 */

import { BackendClient } from './backend-client';

// ===================================================================
// Example 1: Simple GET request
// ===================================================================

interface CompanyData {
  id: string;
  rut: string;
  business_name: string;
}

async function getCompanyExample(companyId: string) {
  try {
    const company = await BackendClient.get<CompanyData>(
      `/api/companies/${companyId}`
    );
    console.log('Company:', company);
    return company;
  } catch (error) {
    console.error('Error fetching company:', error);
    throw error;
  }
}

// ===================================================================
// Example 2: POST request with body
// ===================================================================

interface TaxDocumentRequest {
  company_id: string;
  period: string;
  document_type: 'compras' | 'ventas';
}

interface TaxDocumentResponse {
  success: boolean;
  documents: any[];
  total: number;
}

async function fetchTaxDocumentsExample(request: TaxDocumentRequest) {
  try {
    const response = await BackendClient.post<TaxDocumentResponse>(
      '/api/tax/documents/sync',
      request
    );
    console.log('Tax documents:', response.documents);
    return response;
  } catch (error) {
    console.error('Error fetching tax documents:', error);
    throw error;
  }
}

// ===================================================================
// Example 3: PUT request for update
// ===================================================================

interface UpdateCompanyRequest {
  business_name?: string;
  trade_name?: string;
  address?: string;
}

async function updateCompanyExample(
  companyId: string,
  updates: UpdateCompanyRequest
) {
  try {
    const company = await BackendClient.put<CompanyData>(
      `/api/companies/${companyId}`,
      updates
    );
    console.log('Updated company:', company);
    return company;
  } catch (error) {
    console.error('Error updating company:', error);
    throw error;
  }
}

// ===================================================================
// Example 4: DELETE request
// ===================================================================

interface DeleteResponse {
  success: boolean;
  message: string;
}

async function deleteContactExample(contactId: string) {
  try {
    const response = await BackendClient.delete<DeleteResponse>(
      `/api/contacts/${contactId}`
    );
    console.log('Delete response:', response);
    return response;
  } catch (error) {
    console.error('Error deleting contact:', error);
    throw error;
  }
}

// ===================================================================
// Example 5: PATCH request for partial update
// ===================================================================

interface PatchCompanyRequest {
  phone?: string;
  email?: string;
}

async function patchCompanyExample(
  companyId: string,
  patches: PatchCompanyRequest
) {
  try {
    const company = await BackendClient.patch<CompanyData>(
      `/api/companies/${companyId}`,
      patches
    );
    console.log('Patched company:', company);
    return company;
  } catch (error) {
    console.error('Error patching company:', error);
    throw error;
  }
}

// ===================================================================
// Example 6: GET with query parameters (manual construction)
// ===================================================================

interface DocumentSearchParams {
  period: string;
  document_type?: string;
  limit?: number;
}

async function searchDocumentsExample(params: DocumentSearchParams) {
  try {
    // Construct query string manually
    const queryParams = new URLSearchParams();
    queryParams.append('period', params.period);
    if (params.document_type) {
      queryParams.append('document_type', params.document_type);
    }
    if (params.limit) {
      queryParams.append('limit', params.limit.toString());
    }

    const response = await BackendClient.get<TaxDocumentResponse>(
      `/api/tax/documents?${queryParams.toString()}`
    );
    console.log('Search results:', response);
    return response;
  } catch (error) {
    console.error('Error searching documents:', error);
    throw error;
  }
}

// ===================================================================
// Example 7: Custom headers
// ===================================================================

async function requestWithCustomHeadersExample() {
  try {
    const response = await BackendClient.post<any>(
      '/api/some-endpoint',
      { data: 'example' },
      {
        headers: {
          'X-Custom-Header': 'custom-value',
          'X-Request-ID': crypto.randomUUID(),
        },
      }
    );
    return response;
  } catch (error) {
    console.error('Error with custom headers:', error);
    throw error;
  }
}

// ===================================================================
// Example 8: Using in a service class
// ===================================================================

export class TaxDocumentService {
  /**
   * Sync tax documents for a company and period
   */
  static async syncDocuments(
    companyId: string,
    period: string
  ): Promise<TaxDocumentResponse> {
    console.log('[Tax Document Service] Syncing documents');

    const response = await BackendClient.post<TaxDocumentResponse>(
      '/api/tax/documents/sync',
      {
        company_id: companyId,
        period,
        document_type: 'compras',
      }
    );

    console.log(`[Tax Document Service] Synced ${response.total} documents`);
    return response;
  }

  /**
   * Get documents for a period
   */
  static async getDocuments(
    companyId: string,
    period: string
  ): Promise<any[]> {
    console.log('[Tax Document Service] Fetching documents');

    const queryParams = new URLSearchParams({
      company_id: companyId,
      period: period,
    });

    const response = await BackendClient.get<TaxDocumentResponse>(
      `/api/tax/documents?${queryParams.toString()}`
    );

    return response.documents;
  }
}

// ===================================================================
// Example 9: Error handling pattern
// ===================================================================

async function robustApiCallExample() {
  try {
    const data = await BackendClient.get<any>('/api/some-endpoint');
    return { success: true, data };
  } catch (error) {
    if (error instanceof Error) {
      // Backend error with message
      console.error('Backend error:', error.message);
      return { success: false, error: error.message };
    }
    // Unknown error
    console.error('Unknown error:', error);
    return { success: false, error: 'Unknown error occurred' };
  }
}

// ===================================================================
// Example 10: Getting the base URL (useful for debugging)
// ===================================================================

function logBackendUrlExample() {
  const baseUrl = BackendClient.getBaseUrl();
  console.log('Backend URL:', baseUrl);

  const fullUrl = BackendClient.getUrl('/api/sii/login');
  console.log('Full URL:', fullUrl);
}

// Export examples for reference
export const BackendClientExamples = {
  getCompanyExample,
  fetchTaxDocumentsExample,
  updateCompanyExample,
  deleteContactExample,
  patchCompanyExample,
  searchDocumentsExample,
  requestWithCustomHeadersExample,
  robustApiCallExample,
  logBackendUrlExample,
};
