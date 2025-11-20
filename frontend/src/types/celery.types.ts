/**
 * Celery Task Types
 *
 * Type definitions for Celery task management and execution
 */

/**
 * Available Celery task types
 */
export type CeleryTaskType =
  | 'sii.sync_documents'
  | 'sii.sync_f29'
  | 'calendar.sync_company_calendar'
  | 'calendar.process_events'
  | 'notifications.send_batch';

/**
 * Parameters for SII document sync task
 */
export interface SIISyncDocumentsParams {
  company_id: string;
  months: number;
  month_offset?: number;
}

/**
 * Parameters for SII Form29 sync task
 */
export interface SIISyncForm29Params {
  company_id: string;
  year: string;
}

/**
 * Parameters for calendar sync task
 */
export interface CalendarSyncParams {
  company_id: string;
}

/**
 * Generic task parameters (can be extended)
 */
export type CeleryTaskParams =
  | SIISyncDocumentsParams
  | SIISyncForm29Params
  | CalendarSyncParams
  | Record<string, any>;

/**
 * Request to launch a Celery task
 */
export interface LaunchTaskRequest {
  task_type: CeleryTaskType;
  params: CeleryTaskParams;
}

/**
 * Response from launching a Celery task
 */
export interface LaunchTaskResponse {
  success: boolean;
  task_id: string;
  task_type: string;
  status: 'pending' | 'started' | 'success' | 'failure';
  message?: string;
}

/**
 * Task status information
 */
export interface TaskStatus {
  task_id: string;
  status: 'pending' | 'started' | 'success' | 'failure' | 'retry';
  result?: any;
  error?: string;
  progress?: number;
  created_at?: string;
  started_at?: string;
  completed_at?: string;
}
