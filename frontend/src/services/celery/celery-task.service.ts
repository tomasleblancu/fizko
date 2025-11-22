/**
 * Celery Task Service
 *
 * Handles launching and monitoring Celery background tasks
 */

import { BackendClient } from '@/lib/backend-client';
import type {
  LaunchTaskRequest,
  LaunchTaskResponse,
  TaskStatus,
  SIISyncDocumentsParams,
  SIISyncForm29Params,
  CalendarSyncParams,
  LoadCompanyMemoriesParams,
  Form29GenerateDraftParams,
} from '@/types/celery.types';

export class CeleryTaskService {
  /**
   * Launch a generic Celery task
   *
   * @param request - Task launch request with type and params
   * @returns Task launch response with task_id
   */
  static async launchTask(
    request: LaunchTaskRequest
  ): Promise<LaunchTaskResponse> {
    console.log('[Celery Task Service] Launching task:', request.task_type);

    const response = await BackendClient.post<LaunchTaskResponse>(
      '/api/celery/tasks/launch',
      request
    );

    console.log('[Celery Task Service] Task launched:', response.task_id);

    return response;
  }

  /**
   * Launch SII document sync task
   *
   * Syncs tax documents (compras/ventas) for a company
   *
   * @param companyId - Company UUID
   * @param months - Number of months to sync (default: 1)
   * @param monthOffset - Offset from current month (default: 0)
   * @returns Task launch response
   */
  static async syncSIIDocuments(
    companyId: string,
    months: number = 1,
    monthOffset: number = 0
  ): Promise<LaunchTaskResponse> {
    console.log(
      `[Celery Task Service] Syncing SII documents for company ${companyId}`
    );
    console.log(`[Celery Task Service] Months: ${months}, Offset: ${monthOffset}`);

    const params: SIISyncDocumentsParams = {
      company_id: companyId,
      months,
      month_offset: monthOffset,
    };

    return this.launchTask({
      task_type: 'sii.sync_documents',
      params,
    });
  }

  /**
   * Launch SII Form29 sync task
   *
   * Syncs Form29 declarations for a specific year
   *
   * @param companyId - Company UUID
   * @param year - Year in YYYY format (e.g., "2025"). Defaults to current year if not provided.
   * @returns Task launch response
   */
  static async syncSIIForm29(
    companyId: string,
    year?: string
  ): Promise<LaunchTaskResponse> {
    console.log(
      `[Celery Task Service] Syncing Form29 for company ${companyId}, year ${year || 'current'}`
    );

    const params: SIISyncForm29Params = {
      company_id: companyId,
      year: year || new Date().getFullYear().toString(),
    };

    return this.launchTask({
      task_type: 'sii.sync_f29',
      params,
    });
  }

  /**
   * Launch calendar sync task
   *
   * Syncs company calendar events based on company_events and event_templates.
   * This generates concrete calendar_events instances with due dates.
   *
   * @param companyId - Company UUID
   * @returns Task launch response
   */
  static async syncCompanyCalendar(
    companyId: string
  ): Promise<LaunchTaskResponse> {
    console.log(
      `[Celery Task Service] Syncing calendar for company ${companyId}`
    );

    const params: CalendarSyncParams = {
      company_id: companyId,
    };

    return this.launchTask({
      task_type: 'calendar.sync_company_calendar',
      params,
    });
  }

  /**
   * Launch company memories load task
   *
   * Loads company memories from existing data into Mem0.
   * This extracts data from company tables and stores as memories
   * in the memory system (Mem0 + Supabase brain tables).
   *
   * @param companyId - Company UUID
   * @returns Task launch response
   */
  static async syncCompanyMemories(
    companyId: string
  ): Promise<LaunchTaskResponse> {
    console.log(
      `[Celery Task Service] Syncing memories for company ${companyId}`
    );

    const params: LoadCompanyMemoriesParams = {
      company_id: companyId,
    };

    return this.launchTask({
      task_type: 'memory.load_company_memories',
      params,
    });
  }

  /**
   * Generate Form29 draft for a company
   *
   * Generates a Form29 draft with auto-calculated values from tax documents.
   * This creates a draft in the form29 table with all tax calculation components.
   *
   * @param companyId - Company UUID
   * @param periodYear - Year for the F29 period
   * @param periodMonth - Month for the F29 period (1-12)
   * @param autoCalculate - Whether to auto-calculate values from documents (default: true)
   * @returns Task launch response
   */
  static async generateForm29Draft(
    companyId: string,
    periodYear: number,
    periodMonth: number,
    autoCalculate: boolean = true
  ): Promise<LaunchTaskResponse> {
    console.log(
      `[Celery Task Service] Generating Form29 draft for company ${companyId}, period ${periodYear}-${periodMonth}`
    );

    const params: Form29GenerateDraftParams = {
      company_id: companyId,
      period_year: periodYear,
      period_month: periodMonth,
      auto_calculate: autoCalculate,
    };

    return this.launchTask({
      task_type: 'form29.generate_draft_for_company',
      params,
    });
  }

  /**
   * Get task status
   *
   * @param taskId - Celery task ID
   * @returns Task status information
   */
  static async getTaskStatus(taskId: string): Promise<TaskStatus> {
    console.log('[Celery Task Service] Getting task status:', taskId);

    const status = await BackendClient.get<TaskStatus>(
      `/api/celery/tasks/${taskId}/status`
    );

    console.log('[Celery Task Service] Task status:', status.status);

    return status;
  }

  /**
   * Wait for task completion
   *
   * Polls task status until completion or timeout
   *
   * @param taskId - Celery task ID
   * @param pollIntervalMs - Polling interval in milliseconds (default: 2000)
   * @param timeoutMs - Timeout in milliseconds (default: 300000 = 5 minutes)
   * @returns Final task status
   * @throws Error if task fails or times out
   */
  static async waitForTaskCompletion(
    taskId: string,
    pollIntervalMs: number = 2000,
    timeoutMs: number = 300000
  ): Promise<TaskStatus> {
    console.log('[Celery Task Service] Waiting for task completion:', taskId);

    const startTime = Date.now();

    while (Date.now() - startTime < timeoutMs) {
      const status = await this.getTaskStatus(taskId);

      if (status.status === 'success') {
        console.log('[Celery Task Service] Task completed successfully');
        return status;
      }

      if (status.status === 'failure') {
        console.error('[Celery Task Service] Task failed:', status.error);
        throw new Error(`Task failed: ${status.error || 'Unknown error'}`);
      }

      // Still pending or started, wait and poll again
      console.log(
        `[Celery Task Service] Task status: ${status.status}, polling again in ${pollIntervalMs}ms`
      );
      await new Promise((resolve) => setTimeout(resolve, pollIntervalMs));
    }

    throw new Error(`Task timeout after ${timeoutMs}ms`);
  }

  /**
   * Cancel a running task
   *
   * @param taskId - Celery task ID
   * @returns Cancellation response
   */
  static async cancelTask(taskId: string): Promise<{ success: boolean }> {
    console.log('[Celery Task Service] Cancelling task:', taskId);

    const response = await BackendClient.post<{ success: boolean }>(
      `/api/celery/tasks/${taskId}/cancel`
    );

    console.log('[Celery Task Service] Task cancelled:', response.success);

    return response;
  }
}
