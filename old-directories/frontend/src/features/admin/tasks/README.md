# Admin Tasks Feature

Celery task management interface for administrators.

## Overview

This feature provides a complete interface for managing Celery Beat scheduled tasks, monitoring active tasks, and viewing execution history.

## Structure

```
tasks/
├── components/           # Feature-specific components
│   ├── ScheduledTasksTab.tsx      # Main tasks CRUD interface
│   ├── CreateTaskDialog.tsx       # Modal for creating tasks
│   ├── TaskQueueTab.tsx           # Real-time monitoring
│   └── TaskHistoryTab.tsx         # Execution history
├── pages/               # Page components
│   └── TaskManagerPage.tsx        # Main page with tabs
├── hooks/               # Custom hooks (to be added)
├── api/                 # API calls (to be added)
├── types/               # TypeScript types (to be added)
├── index.ts             # Public API exports
└── README.md            # This file
```

## Usage

### In Routes (main.tsx)

```typescript
import { TaskManagerPage } from './features/admin/tasks';

<Route path="/admin/task-manager" element={<TaskManagerPage />} />
```

### Using Components Separately

```typescript
import { ScheduledTasksTab, TaskQueueTab } from '@/features/admin/tasks';

// Use in custom layouts
<ScheduledTasksTab />
```

## Components

### TaskManagerPage

Main page with 3 tabs:
- Scheduled Tasks
- Task Queue (monitoring)
- History

### ScheduledTasksTab

Complete CRUD interface for scheduled tasks:
- Create: Interval or Crontab schedules
- Read: List all tasks with filters
- Update: Enable/disable tasks
- Delete: Remove tasks
- Execute: Trigger tasks manually

### TaskQueueTab

Integration with Flower for real-time monitoring:
- Redirects to Flower dashboard (http://localhost:5555)
- Provides quick access to active tasks, workers, and queues
- Note: Native integration pending - uses Flower as the monitoring tool

### TaskHistoryTab

Integration with Flower for execution history:
- Redirects to Flower tasks page (http://localhost:5555/tasks)
- Provides quick access to past executions with results and errors
- Note: Native integration pending - uses Flower as the history viewer

### CreateTaskDialog

Modal form for creating new tasks:
- Basic info (name, task, description)
- Schedule (interval or crontab)
- Queue selection (high, default, low)
- Task arguments (JSON kwargs)

## API Integration

### Endpoints Used

**Scheduled Tasks (Backend):**
- `GET /api/scheduled-tasks` - List tasks
- `POST /api/scheduled-tasks` - Create task
- `PUT /api/scheduled-tasks/{id}` - Update task
- `DELETE /api/scheduled-tasks/{id}` - Delete task
- `POST /api/scheduled-tasks/{id}/enable` - Enable task
- `POST /api/scheduled-tasks/{id}/disable` - Disable task
- `POST /api/scheduled-tasks/{id}/run-now` - Execute immediately
- `GET /api/scheduled-tasks/{id}/executions` - Get history

**Task Queue & History (Flower):**
- Queue monitoring: http://localhost:5555
- Task history: http://localhost:5555/tasks
- Note: No custom endpoints needed - Flower provides the UI

## Dependencies

### Internal
- `@/components/ui/*` - shadcn/ui components (tabs, dialog, button, etc.)
- `@/contexts/AuthContext` - Authentication
- `@/lib/config` - API base URL
- `@/lib/api-client` - API fetch wrapper

### External
- `@tanstack/react-query` - Data fetching
- `lucide-react` - Icons
- `sonner` - Toast notifications
- `react-router-dom` - Routing

## Future Enhancements

- [ ] Add custom hooks (`useScheduledTasks`, `useTaskQueue`)
- [ ] Add TypeScript types in `types/`
- [ ] Add API client in `api/tasksApi.ts`
- [ ] Add unit tests
- [ ] Add storybook stories
- [ ] Implement task editing (currently only create/delete)
- [ ] Add search and filters
- [ ] Add bulk operations

## Related Documentation

- [Task Manager User Guide](../../../../TASK_MANAGER.md)
- [Backend Documentation](../../../../../backend/CELERY_BEAT.md)
