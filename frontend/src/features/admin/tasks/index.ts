/**
 * Admin Tasks Feature
 *
 * Public API for the Task Manager feature.
 * Manages Celery scheduled tasks, monitoring, and history.
 */

// Pages
export { default as TaskManagerPage } from './pages/TaskManagerPage';

// Components (if needed by other features)
export { default as ScheduledTasksTab } from './components/ScheduledTasksTab';
export { default as TaskQueueTab } from './components/TaskQueueTab';
export { default as TaskHistoryTab } from './components/TaskHistoryTab';
export { default as CreateTaskDialog } from './components/CreateTaskDialog';

// Re-export types when we create them
// export type * from '../shared/types/task.types';
