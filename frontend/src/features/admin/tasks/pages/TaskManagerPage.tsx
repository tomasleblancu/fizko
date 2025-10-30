import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/shared/components/ui/tabs";
import { Clock, ListChecks, Activity, Calendar, ArrowLeft } from 'lucide-react';
import ScheduledTasksTab from '../components/ScheduledTasksTab';
import TaskQueueTab from '../components/TaskQueueTab';
import TaskHistoryTab from '../components/TaskHistoryTab';

/**
 * AdminTaskManager - Centralized Celery task management interface
 *
 * Features:
 * - Scheduled Tasks: Create, view, edit CRON/interval tasks
 * - Task Queue: Monitor active tasks, workers, queues
 * - History: View task execution history and results
 */
export default function AdminTaskManager() {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<string>('scheduled');

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <div className="border-b border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800">
        <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => navigate('/admin')}
                className="rounded-lg p-2 hover:bg-gray-100 dark:hover:bg-gray-700"
              >
                <ArrowLeft className="h-5 w-5 text-gray-600 dark:text-gray-400" />
              </button>
              <div className="flex items-center gap-3">
                <Clock className="h-8 w-8 text-blue-600" />
                <div>
                  <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                    Gestor de Tareas
                  </h1>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Administra tareas programadas y monitorea ejecuciones en tiempo real
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-3 lg:w-auto lg:inline-grid">
            <TabsTrigger value="scheduled">
              <Calendar className="h-4 w-4 mr-2" />
              Tareas Programadas
            </TabsTrigger>
            <TabsTrigger value="queue">
              <Activity className="h-4 w-4 mr-2" />
              Cola de Tareas
            </TabsTrigger>
            <TabsTrigger value="history">
              <ListChecks className="h-4 w-4 mr-2" />
              Historial
            </TabsTrigger>
          </TabsList>

          <TabsContent value="scheduled" className="space-y-4">
            <ScheduledTasksTab />
          </TabsContent>

          <TabsContent value="queue" className="space-y-4">
            <TaskQueueTab />
          </TabsContent>

          <TabsContent value="history" className="space-y-4">
            <TaskHistoryTab />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
