import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuth } from "@/app/providers/AuthContext";
import { API_BASE_URL } from "@/shared/lib/config";
import { apiFetch } from "@/shared/lib/api-client";
import { Button } from "@/shared/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/components/ui/card";
import { Badge } from "@/shared/components/ui/badge";
import {
  Plus,
  Play,
  Pause,
  Trash2,
  Clock,
  Calendar as CalendarIcon,
  TrendingUp,
  RefreshCw,
  Loader2,
  Pencil,
} from 'lucide-react';
import CreateTaskDialog from './CreateTaskDialog';
import EditTaskDialog from './EditTaskDialog';
// import { toast } from 'sonner'; // TODO: Install sonner package
const toast = {
  success: (msg: string) => console.log('✓', msg),
  error: (msg: string) => console.error('✗', msg),
};

interface ScheduledTask {
  id: number;
  name: string;
  task: string;
  schedule_type: string;
  schedule_display: string;
  enabled: boolean;
  last_run_at: string | null;
  total_run_count: number;
  queue: string | null;
  description: string | null;
}

export default function ScheduledTasksTab() {
  const { session } = useAuth();
  const queryClient = useQueryClient();
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [editingTaskId, setEditingTaskId] = useState<number | null>(null);

  // Fetch scheduled tasks
  const { data: tasks = [], isLoading, refetch } = useQuery({
    queryKey: ['scheduled-tasks'],
    queryFn: async () => {
      if (!session?.access_token) throw new Error('No session');

      const response = await apiFetch(`${API_BASE_URL}/scheduled-tasks`, {
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) throw new Error('Failed to fetch tasks');
      return response.json() as Promise<ScheduledTask[]>;
    },
    enabled: !!session?.access_token,
    refetchInterval: 10000, // Refresh every 10 seconds
  });

  // Toggle task enabled/disabled
  const toggleTaskMutation = useMutation({
    mutationFn: async ({ taskId, enabled }: { taskId: number; enabled: boolean }) => {
      if (!session?.access_token) throw new Error('No session');

      const endpoint = enabled ? 'enable' : 'disable';
      const response = await apiFetch(
        `${API_BASE_URL}/scheduled-tasks/${taskId}/${endpoint}`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${session.access_token}`,
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) throw new Error(`Failed to ${endpoint} task`);
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scheduled-tasks'] });
      toast.success('Tarea actualizada correctamente');
    },
    onError: (error: Error) => {
      toast.error(`Error: ${error.message}`);
    },
  });

  // Run task now
  const runTaskMutation = useMutation({
    mutationFn: async (taskId: number) => {
      if (!session?.access_token) throw new Error('No session');

      const response = await apiFetch(
        `${API_BASE_URL}/scheduled-tasks/${taskId}/run-now`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${session.access_token}`,
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) throw new Error('Failed to trigger task');
      return response.json();
    },
    onSuccess: (data) => {
      toast.success(`Tarea ejecutada: ${data.celery_task_id}`);
      queryClient.invalidateQueries({ queryKey: ['scheduled-tasks'] });
    },
    onError: (error: Error) => {
      toast.error(`Error: ${error.message}`);
    },
  });

  // Delete task
  const deleteTaskMutation = useMutation({
    mutationFn: async (taskId: number) => {
      if (!session?.access_token) throw new Error('No session');

      const response = await apiFetch(`${API_BASE_URL}/scheduled-tasks/${taskId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) throw new Error('Failed to delete task');
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scheduled-tasks'] });
      toast.success('Tarea eliminada correctamente');
    },
    onError: (error: Error) => {
      toast.error(`Error: ${error.message}`);
    },
  });

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'Nunca';
    return new Date(dateString).toLocaleString('es-CL', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getQueueBadgeColor = (queue: string | null) => {
    switch (queue) {
      case 'high':
        return 'bg-red-100 text-red-700 border-red-200';
      case 'low':
        return 'bg-blue-100 text-blue-700 border-blue-200';
      default:
        return 'bg-slate-100 text-slate-700 border-slate-200';
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header Actions */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-slate-900">Tareas Programadas</h2>
          <p className="text-sm text-slate-600">
            {tasks.length} tareas configuradas ({tasks.filter((t) => t.enabled).length}{' '}
            activas)
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => refetch()}
            className="gap-2"
          >
            <RefreshCw className="h-4 w-4" />
            Actualizar
          </Button>
          <Button
            onClick={() => setShowCreateDialog(true)}
            className="gap-2 bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700"
          >
            <Plus className="h-4 w-4" />
            Nueva Tarea
          </Button>
        </div>
      </div>

      {/* Tasks Grid */}
      {tasks.length === 0 ? (
        <Card className="border-2 border-dashed">
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Clock className="h-12 w-12 text-slate-300 mb-4" />
            <p className="text-slate-600 font-medium mb-2">No hay tareas programadas</p>
            <p className="text-slate-500 text-sm mb-4">
              Crea tu primera tarea para automatizar procesos
            </p>
            <Button onClick={() => setShowCreateDialog(true)} className="gap-2">
              <Plus className="h-4 w-4" />
              Crear Primera Tarea
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {tasks.map((task) => (
            <Card
              key={task.id}
              className={`hover:shadow-lg transition-all ${
                task.enabled
                  ? 'border-blue-200 bg-gradient-to-br from-white to-blue-50/30'
                  : 'border-slate-200 bg-slate-50/50'
              }`}
            >
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <CardTitle className="text-base truncate">{task.name}</CardTitle>
                    <CardDescription className="text-xs truncate">
                      {task.task}
                    </CardDescription>
                  </div>
                  <Badge
                    variant={task.enabled ? 'default' : 'secondary'}
                    className={`shrink-0 ${
                      task.enabled
                        ? 'bg-green-600 text-white border-green-700'
                        : 'bg-slate-100 text-slate-600 border-slate-200'
                    }`}
                  >
                    {task.enabled ? 'Activa' : 'Pausada'}
                  </Badge>
                </div>
              </CardHeader>

              <CardContent className="space-y-3">
                {/* Schedule */}
                <div className="flex items-center gap-2 text-sm">
                  {task.schedule_type === 'interval' ? (
                    <Clock className="h-4 w-4 text-blue-500" />
                  ) : (
                    <CalendarIcon className="h-4 w-4 text-purple-500" />
                  )}
                  <span className="text-slate-600 truncate">
                    {task.schedule_display}
                  </span>
                </div>

                {/* Queue */}
                {task.queue && (
                  <Badge
                    variant="outline"
                    className={`w-fit text-xs ${getQueueBadgeColor(task.queue)}`}
                  >
                    Cola: {task.queue}
                  </Badge>
                )}

                {/* Stats */}
                <div className="flex items-center gap-4 text-xs text-slate-600 pt-2 border-t">
                  <div className="flex items-center gap-1">
                    <TrendingUp className="h-3 w-3" />
                    <span>{task.total_run_count} ejecuciones</span>
                  </div>
                </div>

                <div className="text-xs text-slate-500">
                  Última ejecución: {formatDate(task.last_run_at)}
                </div>

                {/* Description */}
                {task.description && (
                  <p className="text-xs text-slate-600 line-clamp-2 pt-2 border-t">
                    {task.description}
                  </p>
                )}

                {/* Actions */}
                <div className="flex gap-2 pt-3 border-t">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() =>
                      toggleTaskMutation.mutate({
                        taskId: task.id,
                        enabled: !task.enabled,
                      })
                    }
                    disabled={toggleTaskMutation.isPending}
                    className="flex-1"
                  >
                    {task.enabled ? (
                      <>
                        <Pause className="h-3 w-3 mr-1" />
                        Pausar
                      </>
                    ) : (
                      <>
                        <Play className="h-3 w-3 mr-1" />
                        Activar
                      </>
                    )}
                  </Button>

                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => setEditingTaskId(task.id)}
                    title="Editar tarea"
                  >
                    <Pencil className="h-3 w-3" />
                  </Button>

                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => runTaskMutation.mutate(task.id)}
                    disabled={runTaskMutation.isPending || !task.enabled}
                    title={!task.enabled ? 'La tarea debe estar activa' : 'Ejecutar ahora'}
                  >
                    <Play className="h-3 w-3" />
                  </Button>

                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => {
                      if (
                        confirm(
                          `¿Eliminar la tarea "${task.name}"?\n\nEsta acción no se puede deshacer.`
                        )
                      ) {
                        deleteTaskMutation.mutate(task.id);
                      }
                    }}
                    disabled={deleteTaskMutation.isPending}
                    className="text-red-600 hover:text-red-700 hover:bg-red-50"
                  >
                    <Trash2 className="h-3 w-3" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Create Task Dialog */}
      <CreateTaskDialog
        open={showCreateDialog}
        onOpenChange={setShowCreateDialog}
        onSuccess={() => {
          setShowCreateDialog(false);
          queryClient.invalidateQueries({ queryKey: ['scheduled-tasks'] });
        }}
      />

      {/* Edit Task Dialog */}
      {editingTaskId && (
        <EditTaskDialog
          open={editingTaskId !== null}
          onOpenChange={(open) => {
            if (!open) setEditingTaskId(null);
          }}
          taskId={editingTaskId}
          onSuccess={() => {
            setEditingTaskId(null);
            queryClient.invalidateQueries({ queryKey: ['scheduled-tasks'] });
          }}
        />
      )}
    </div>
  );
}
