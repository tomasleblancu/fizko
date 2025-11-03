import { Activity, ExternalLink } from 'lucide-react';
import { Button } from "@/shared/components/ui/button";
import { Card, CardContent } from "@/shared/components/ui/card";

/**
 * TaskQueueTab - Integración con Flower para monitoreo de cola de tareas
 *
 * Este componente redirige a Flower (http://localhost:5555) para el monitoreo completo
 * de la cola de tareas, workers activos y tareas en ejecución.
 */
export default function TaskQueueTab() {
  return (
    <div className="space-y-4">
      {/* Header */}
      <div>
        <h2 className="text-lg font-semibold text-slate-900">Cola de Tareas</h2>
        <p className="text-sm text-slate-600">
          Monitoreo en tiempo real de tareas en ejecución
        </p>
      </div>

      {/* Flower Integration Card */}
      <Card className="border-blue-200 bg-gradient-to-br from-blue-50 to-white">
        <CardContent className="pt-6">
          <div className="space-y-4">
            <div className="flex gap-3">
              <Activity className="h-6 w-6 text-blue-600 shrink-0" />
              <div>
                <h3 className="font-semibold text-slate-900 mb-2">
                  Monitoreo en Tiempo Real con Flower
                </h3>
                <p className="text-sm text-slate-600 mb-4">
                  Flower es la herramienta estándar para monitorear Celery. Te permite ver:
                </p>
                <ul className="text-sm text-slate-600 space-y-1 list-disc list-inside mb-4">
                  <li>Tareas activas y en cola en tiempo real</li>
                  <li>Estado y salud de workers</li>
                  <li>Métricas de rendimiento y throughput</li>
                  <li>Gestión de colas (high, default, low)</li>
                </ul>
              </div>
            </div>

            <div className="flex gap-2">
              <Button
                onClick={() => window.open('http://localhost:5555', '_blank')}
                className="gap-2"
                variant="default"
              >
                <Activity className="h-4 w-4" />
                Abrir Flower (Dashboard Completo)
              </Button>
              <Button
                onClick={() => window.open('http://localhost:5555/tasks', '_blank')}
                variant="outline"
                className="gap-2"
              >
                <ExternalLink className="h-4 w-4" />
                Ver Cola de Tareas
              </Button>
            </div>

            <div className="text-xs text-slate-500 bg-slate-50 p-3 rounded-lg">
              <p className="font-medium mb-1">ℹ️ Nota:</p>
              <p>
                Flower debe estar corriendo en <code className="px-1 bg-slate-200 rounded">http://localhost:5555</code>.
                Si usas Docker, asegúrate de que el servicio <code className="px-1 bg-slate-200 rounded">flower</code> esté activo.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
