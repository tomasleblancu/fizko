import { useQuery } from '@tanstack/react-query';
import { useAuth } from "@/app/providers/AuthContext";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/components/ui/card";
import { Badge } from "@/shared/components/ui/badge";
import { Activity, Clock, Zap, Loader2, RefreshCw } from 'lucide-react';
import { Button } from "@/shared/components/ui/button";

interface TaskStatus {
  task_id: string;
  task_name: string;
  status: string;
  worker: string | null;
  date_created: string;
}

export default function TaskQueueTab() {
  const { session } = useAuth();

  // Fetch active/recent tasks
  const { data: tasks = [], isLoading, refetch } = useQuery({
    queryKey: ['task-queue'],
    queryFn: async () => {
      if (!session?.access_token) throw new Error('No session');

      // This endpoint would need to be created on the backend
      // For now, we'll return empty array as placeholder
      // TODO: Implement GET /api/tasks/active endpoint
      return [] as TaskStatus[];
    },
    enabled: !!session?.access_token,
    refetchInterval: 5000, // Refresh every 5 seconds
  });

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'pending':
        return 'bg-yellow-100 text-yellow-700 border-yellow-200';
      case 'started':
      case 'running':
        return 'bg-blue-100 text-blue-700 border-blue-200';
      case 'success':
        return 'bg-green-100 text-green-700 border-green-200';
      case 'failure':
        return 'bg-red-100 text-red-700 border-red-200';
      case 'retry':
        return 'bg-orange-100 text-orange-700 border-orange-200';
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
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-slate-900">Cola de Tareas</h2>
          <p className="text-sm text-slate-600">
            Monitoreo en tiempo real de tareas en ejecución
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => refetch()}
          className="gap-2"
        >
          <RefreshCw className="h-4 w-4" />
          Actualizar
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card className="border-blue-200 bg-gradient-to-br from-blue-50 to-white">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Tareas Activas</CardTitle>
            <Activity className="h-4 w-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">0</div>
            <p className="text-xs text-slate-600 mt-1">En ejecución ahora</p>
          </CardContent>
        </Card>

        <Card className="border-yellow-200 bg-gradient-to-br from-yellow-50 to-white">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">En Cola</CardTitle>
            <Clock className="h-4 w-4 text-yellow-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-600">0</div>
            <p className="text-xs text-slate-600 mt-1">Esperando ejecución</p>
          </CardContent>
        </Card>

        <Card className="border-green-200 bg-gradient-to-br from-green-50 to-white">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Workers Activos</CardTitle>
            <Zap className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">-</div>
            <p className="text-xs text-slate-600 mt-1">Disponibles</p>
          </CardContent>
        </Card>
      </div>

      {/* Active Tasks List */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Tareas en Tiempo Real</CardTitle>
        </CardHeader>
        <CardContent>
          {tasks.length === 0 ? (
            <div className="text-center py-8 text-slate-500">
              <Activity className="h-12 w-12 mx-auto mb-3 text-slate-300" />
              <p className="font-medium">No hay tareas en ejecución</p>
              <p className="text-sm mt-1">
                Las tareas activas aparecerán aquí automáticamente
              </p>
            </div>
          ) : (
            <div className="space-y-2">
              {tasks.map((task) => (
                <div
                  key={task.task_id}
                  className="flex items-center justify-between p-3 border rounded-lg hover:bg-slate-50"
                >
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-sm truncate">{task.task_name}</p>
                    <p className="text-xs text-slate-500 truncate">{task.task_id}</p>
                    {task.worker && (
                      <p className="text-xs text-slate-400 mt-1">Worker: {task.worker}</p>
                    )}
                  </div>
                  <Badge
                    variant="outline"
                    className={`ml-3 ${getStatusColor(task.status)}`}
                  >
                    {task.status}
                  </Badge>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Info Card - Flower Integration */}
      <Card className="border-blue-200 bg-blue-50/30">
        <CardContent className="pt-6">
          <div className="space-y-4">
            <div className="flex gap-3">
              <Activity className="h-5 w-5 text-blue-600 shrink-0 mt-0.5" />
              <div className="text-sm text-slate-700">
                <p className="font-medium mb-1">Monitoreo en Tiempo Real</p>
                <p className="text-slate-600">
                  Para ver el estado completo de la cola de tareas, workers activos y métricas en
                  tiempo real, usa <strong>Flower</strong> - la interfaz de monitoreo de Celery.
                </p>
              </div>
            </div>

            <div className="flex gap-2">
              <Button
                onClick={() => window.open('http://localhost:5555', '_blank')}
                className="gap-2"
                variant="default"
              >
                <Activity className="h-4 w-4" />
                Abrir Flower (Monitoreo Completo)
              </Button>
              <Button
                onClick={() => window.open('http://localhost:5555/tasks', '_blank')}
                variant="outline"
                className="gap-2"
              >
                Ver Tareas en Flower
              </Button>
            </div>

            <div className="text-xs text-slate-500 space-y-1">
              <p>
                <strong>Nota técnica:</strong> La integración nativa está pendiente de
                implementación.
              </p>
              <p>
                Requiere endpoints:{' '}
                <code className="px-1 py-0.5 bg-slate-200 rounded">GET /api/tasks/active</code>
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
