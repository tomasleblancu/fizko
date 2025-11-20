import { Clock, ExternalLink, History } from 'lucide-react';
import { Button } from "@/shared/components/ui/button";
import { Card, CardContent } from "@/shared/components/ui/card";

/**
 * TaskHistoryTab - Integración con Flower para historial de tareas
 *
 * Este componente redirige a Flower (http://localhost:5555/tasks) para ver
 * el historial completo de ejecuciones de tareas con resultados y errores.
 */
export default function TaskHistoryTab() {
  return (
    <div className="space-y-4">
      {/* Header */}
      <div>
        <h2 className="text-lg font-semibold text-slate-900">Historial de Ejecuciones</h2>
        <p className="text-sm text-slate-600">
          Registro completo de tareas ejecutadas
        </p>
      </div>

      {/* Flower Integration Card */}
      <Card className="border-blue-200 bg-gradient-to-br from-blue-50 to-white">
        <CardContent className="pt-6">
          <div className="space-y-4">
            <div className="flex gap-3">
              <History className="h-6 w-6 text-blue-600 shrink-0" />
              <div>
                <h3 className="font-semibold text-slate-900 mb-2">
                  Historial Completo en Flower
                </h3>
                <p className="text-sm text-slate-600 mb-4">
                  Flower te permite explorar el historial completo de ejecuciones con:
                </p>
                <ul className="text-sm text-slate-600 space-y-1 list-disc list-inside mb-4">
                  <li>Estado de cada tarea (success, failure, pending, etc.)</li>
                  <li>Resultados y valores de retorno</li>
                  <li>Stack traces completos de errores</li>
                  <li>Tiempos de ejecución y timestamps</li>
                  <li>Búsqueda y filtrado por nombre, estado, fecha</li>
                </ul>
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
                <ExternalLink className="h-4 w-4" />
                Abrir Dashboard Completo
              </Button>
            </div>

            <div className="text-xs text-slate-500 bg-slate-50 p-3 rounded-lg">
              <p className="font-medium mb-1">ℹ️ Nota:</p>
              <p>
                Flower debe estar corriendo en <code className="px-1 bg-slate-200 rounded">http://localhost:5555</code>.
                El historial incluye todas las tareas ejecutadas desde que se inició Flower.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
