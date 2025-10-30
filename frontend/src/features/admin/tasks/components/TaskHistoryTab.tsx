import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useAuth } from "@/app/providers/AuthContext";
import { API_BASE_URL } from "@/shared/lib/config";
import { apiFetch } from "@/shared/lib/api-client";
import {
  CheckCircle2,
  XCircle,
  Clock,
  RefreshCw,
  Loader2,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '../../../../shared/components/ui/dialog';
import { Button } from "@/shared/components/ui/button";
import { Card, CardContent } from "@/shared/components/ui/card";

interface TaskExecution {
  id: number;
  task_id: string;
  task_name: string;
  status: string;
  worker: string | null;
  result: any;
  traceback: string | null;
  date_created: string;
  date_done: string | null;
}

export default function TaskHistoryTab() {
  const { session } = useAuth();
  const [selectedExecution, setSelectedExecution] = useState<TaskExecution | null>(null);
  const [expandedId, setExpandedId] = useState<number | null>(null);

  // Note: This would ideally query a general history endpoint
  // For now, we'll show a placeholder
  const { data: executions = [], isLoading, refetch } = useQuery({
    queryKey: ['task-history'],
    queryFn: async () => {
      if (!session?.access_token) throw new Error('No session');

      // TODO: Implement GET /api/tasks/history endpoint
      // For now, return empty array as placeholder
      return [] as TaskExecution[];
    },
    enabled: !!session?.access_token,
    refetchInterval: 15000, // Refresh every 15 seconds
  });

  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'success':
        return <CheckCircle2 className="h-5 w-5 text-green-600" />;
      case 'failure':
        return <XCircle className="h-5 w-5 text-red-600" />;
      case 'pending':
      case 'started':
        return <Clock className="h-5 w-5 text-blue-600" />;
      default:
        return <Clock className="h-5 w-5 text-slate-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'success':
        return 'bg-green-100 text-green-700 border-green-200';
      case 'failure':
        return 'bg-red-100 text-red-700 border-red-200';
      case 'pending':
        return 'bg-yellow-100 text-yellow-700 border-yellow-200';
      case 'started':
        return 'bg-blue-100 text-blue-700 border-blue-200';
      default:
        return 'bg-slate-100 text-slate-700 border-slate-200';
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('es-CL', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  };

  const calculateDuration = (start: string, end: string | null) => {
    if (!end) return 'En progreso...';
    const duration = new Date(end).getTime() - new Date(start).getTime();
    if (duration < 1000) return `${duration}ms`;
    if (duration < 60000) return `${(duration / 1000).toFixed(1)}s`;
    return `${Math.floor(duration / 60000)}m ${Math.floor((duration % 60000) / 1000)}s`;
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
          <h2 className="text-lg font-semibold text-slate-900">Historial de Ejecuciones</h2>
          <p className="text-sm text-slate-600">
            Últimas {executions.length} ejecuciones de tareas
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

      {/* Flower Integration Card */}
      <Card className="border-blue-200 bg-blue-50/30">
        <CardContent className="pt-6">
          <div className="space-y-4">
            <div className="flex gap-3">
              <Clock className="h-5 w-5 text-blue-600 shrink-0 mt-0.5" />
              <div className="text-sm text-slate-700">
                <p className="font-medium mb-1">Historial Completo de Ejecuciones</p>
                <p className="text-slate-600">
                  Para ver el historial completo de todas las tareas ejecutadas, incluyendo
                  resultados, errores y métricas, usa <strong>Flower</strong>.
                </p>
              </div>
            </div>

            <div className="flex gap-2">
              <Button
                onClick={() => window.open('http://localhost:5555/tasks', '_blank')}
                className="gap-2"
                variant="default"
              >
                <Clock className="h-4 w-4" />
                Ver Historial en Flower
              </Button>
              <Button
                onClick={() => window.open('http://localhost:5555', '_blank')}
                variant="outline"
                className="gap-2"
              >
                Abrir Dashboard Completo
              </Button>
            </div>

            <div className="text-xs text-slate-500 space-y-1">
              <p>
                <strong>Nota técnica:</strong> La integración nativa está pendiente de
                implementación.
              </p>
              <p>
                Requiere endpoints:{' '}
                <code className="px-1 py-0.5 bg-slate-200 rounded">GET /api/tasks/history</code>
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Executions List */}
      {executions.length === 0 ? (
        <Card className="border-2 border-dashed">
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Clock className="h-12 w-12 text-slate-300 mb-4" />
            <p className="text-slate-600 font-medium mb-2">
              Integración Pendiente
            </p>
            <p className="text-slate-500 text-sm text-center max-w-md">
              Usa el botón de arriba para acceder a Flower y ver el historial completo de
              ejecuciones de tareas
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-2">
          {executions.map((execution) => (
            <Card
              key={execution.id}
              className="hover:shadow-md transition-shadow cursor-pointer"
              onClick={() => setExpandedId(expandedId === execution.id ? null : execution.id)}
            >
              <CardContent className="p-4">
                <div className="flex items-start gap-4">
                  {/* Status Icon */}
                  <div className="shrink-0">{getStatusIcon(execution.status)}</div>

                  {/* Main Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <p className="font-medium text-sm truncate">{execution.task_name}</p>
                      <Badge
                        variant="outline"
                        className={`text-xs ${getStatusColor(execution.status)}`}
                      >
                        {execution.status}
                      </Badge>
                    </div>

                    <div className="mt-2 space-y-1 text-xs text-slate-600">
                      <div className="flex items-center gap-4 flex-wrap">
                        <span>
                          <span className="font-medium">Inicio:</span>{' '}
                          {formatDate(execution.date_created)}
                        </span>
                        {execution.date_done && (
                          <>
                            <span>
                              <span className="font-medium">Fin:</span>{' '}
                              {formatDate(execution.date_done)}
                            </span>
                            <span>
                              <span className="font-medium">Duración:</span>{' '}
                              {calculateDuration(
                                execution.date_created,
                                execution.date_done
                              )}
                            </span>
                          </>
                        )}
                      </div>
                      {execution.worker && (
                        <p className="text-slate-500">Worker: {execution.worker}</p>
                      )}
                    </div>

                    {/* Expanded Details */}
                    {expandedId === execution.id && (
                      <div className="mt-4 pt-4 border-t space-y-3">
                        {/* Task ID */}
                        <div>
                          <p className="text-xs font-medium text-slate-700 mb-1">Task ID:</p>
                          <code className="text-xs bg-slate-100 px-2 py-1 rounded block break-all">
                            {execution.task_id}
                          </code>
                        </div>

                        {/* Result */}
                        {execution.result && (
                          <div>
                            <p className="text-xs font-medium text-slate-700 mb-1">
                              Resultado:
                            </p>
                            <pre className="text-xs bg-slate-100 p-2 rounded overflow-x-auto">
                              {JSON.stringify(execution.result, null, 2)}
                            </pre>
                          </div>
                        )}

                        {/* Traceback (errors) */}
                        {execution.traceback && (
                          <div>
                            <p className="text-xs font-medium text-red-700 mb-1">Error:</p>
                            <pre className="text-xs bg-red-50 text-red-900 p-2 rounded overflow-x-auto max-h-40 overflow-y-auto">
                              {execution.traceback}
                            </pre>
                          </div>
                        )}

                        {/* Actions */}
                        <div className="flex gap-2 pt-2">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={(e) => {
                              e.stopPropagation();
                              setSelectedExecution(execution);
                            }}
                          >
                            Ver Detalles Completos
                          </Button>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Expand Icon */}
                  <div className="shrink-0">
                    {expandedId === execution.id ? (
                      <ChevronUp className="h-5 w-5 text-slate-400" />
                    ) : (
                      <ChevronDown className="h-5 w-5 text-slate-400" />
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Details Dialog */}
      {selectedExecution && (
        <Dialog
          open={!!selectedExecution}
          onOpenChange={() => setSelectedExecution(null)}
        >
          <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Detalles de Ejecución</DialogTitle>
              <DialogDescription>{selectedExecution.task_name}</DialogDescription>
            </DialogHeader>

            <div className="space-y-4 py-4">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="font-medium text-slate-700">Estado</p>
                  <Badge
                    variant="outline"
                    className={`mt-1 ${getStatusColor(selectedExecution.status)}`}
                  >
                    {selectedExecution.status}
                  </Badge>
                </div>
                <div>
                  <p className="font-medium text-slate-700">Task ID</p>
                  <code className="text-xs bg-slate-100 px-2 py-1 rounded block mt-1 break-all">
                    {selectedExecution.task_id}
                  </code>
                </div>
                <div>
                  <p className="font-medium text-slate-700">Inicio</p>
                  <p className="text-slate-600 mt-1">
                    {formatDate(selectedExecution.date_created)}
                  </p>
                </div>
                {selectedExecution.date_done && (
                  <div>
                    <p className="font-medium text-slate-700">Fin</p>
                    <p className="text-slate-600 mt-1">
                      {formatDate(selectedExecution.date_done)}
                    </p>
                  </div>
                )}
                {selectedExecution.worker && (
                  <div className="col-span-2">
                    <p className="font-medium text-slate-700">Worker</p>
                    <p className="text-slate-600 mt-1">{selectedExecution.worker}</p>
                  </div>
                )}
              </div>

              {selectedExecution.result && (
                <div>
                  <p className="font-medium text-slate-700 mb-2">Resultado Completo</p>
                  <pre className="text-xs bg-slate-100 p-3 rounded overflow-x-auto">
                    {JSON.stringify(selectedExecution.result, null, 2)}
                  </pre>
                </div>
              )}

              {selectedExecution.traceback && (
                <div>
                  <p className="font-medium text-red-700 mb-2">Stack Trace Completo</p>
                  <pre className="text-xs bg-red-50 text-red-900 p-3 rounded overflow-x-auto max-h-60 overflow-y-auto">
                    {selectedExecution.traceback}
                  </pre>
                </div>
              )}
            </div>
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
}
