import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Download, FileText, Calendar, Loader2 } from "lucide-react";
import { CeleryTaskService } from "@/services/celery/celery-task.service";

interface CompanySyncActionsProps {
  companyId: string;
}

export function CompanySyncActions({ companyId }: CompanySyncActionsProps) {
  // Task execution states
  const [syncDocsLoading, setSyncDocsLoading] = useState(false);
  const [syncF29Loading, setSyncF29Loading] = useState(false);
  const [syncCalendarLoading, setSyncCalendarLoading] = useState(false);
  const [taskMessage, setTaskMessage] = useState<string | null>(null);

  // Task parameters
  const [docsMonths, setDocsMonths] = useState(1);
  const [docsOffset, setDocsOffset] = useState(1);
  const [f29Year, setF29Year] = useState(new Date().getFullYear().toString());

  const handleSyncDocuments = async () => {
    try {
      setSyncDocsLoading(true);
      setTaskMessage(null);

      const response = await CeleryTaskService.syncSIIDocuments(
        companyId,
        docsMonths,
        docsOffset
      );

      setTaskMessage(
        `✓ Sincronización de documentos iniciada. Task ID: ${response.task_id}`
      );
    } catch (error) {
      console.error("Error syncing documents:", error);
      setTaskMessage(
        `✗ Error: ${error instanceof Error ? error.message : "Unknown error"}`
      );
    } finally {
      setSyncDocsLoading(false);
    }
  };

  const handleSyncF29 = async () => {
    try {
      setSyncF29Loading(true);
      setTaskMessage(null);

      const response = await CeleryTaskService.syncSIIForm29(
        companyId,
        f29Year
      );

      setTaskMessage(
        `✓ Sincronización de F29 iniciada. Task ID: ${response.task_id}`
      );
    } catch (error) {
      console.error("Error syncing F29:", error);
      setTaskMessage(
        `✗ Error: ${error instanceof Error ? error.message : "Unknown error"}`
      );
    } finally {
      setSyncF29Loading(false);
    }
  };

  const handleSyncCalendar = async () => {
    try {
      setSyncCalendarLoading(true);
      setTaskMessage(null);

      const response = await CeleryTaskService.syncCompanyCalendar(companyId);

      setTaskMessage(
        `✓ Sincronización de calendario iniciada. Task ID: ${response.task_id}`
      );
    } catch (error) {
      console.error("Error syncing calendar:", error);
      setTaskMessage(
        `✗ Error: ${error instanceof Error ? error.message : "Unknown error"}`
      );
    } finally {
      setSyncCalendarLoading(false);
    }
  };

  return (
    <Card className="p-6">
      <h2 className="text-xl font-semibold text-gray-900 mb-4">
        Acciones de Sincronización
      </h2>

      <div className="space-y-6">
        {/* SII Documents Sync */}
        <div className="border-b border-gray-200 pb-6">
          <div className="flex items-start gap-3 mb-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Download className="h-5 w-5 text-blue-600" />
            </div>
            <div className="flex-1">
              <h3 className="font-semibold text-gray-900">
                Sincronizar Documentos SII
              </h3>
              <p className="text-sm text-gray-600">
                Sincroniza compras y ventas desde el SII
              </p>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4 mb-3">
            <div>
              <Label htmlFor="docsMonths">Meses</Label>
              <Input
                id="docsMonths"
                type="number"
                min="1"
                max="12"
                value={docsMonths}
                onChange={(e) => setDocsMonths(parseInt(e.target.value) || 1)}
                disabled={syncDocsLoading}
              />
            </div>
            <div>
              <Label htmlFor="docsOffset">Offset (meses atrás)</Label>
              <Input
                id="docsOffset"
                type="number"
                min="0"
                max="12"
                value={docsOffset}
                onChange={(e) => setDocsOffset(parseInt(e.target.value) || 0)}
                disabled={syncDocsLoading}
              />
            </div>
          </div>

          <Button
            onClick={handleSyncDocuments}
            disabled={syncDocsLoading}
            className="w-full"
          >
            {syncDocsLoading ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Sincronizando...
              </>
            ) : (
              <>
                <Download className="h-4 w-4 mr-2" />
                Sincronizar Documentos
              </>
            )}
          </Button>
        </div>

        {/* F29 Sync */}
        <div className="border-b border-gray-200 pb-6">
          <div className="flex items-start gap-3 mb-3">
            <div className="p-2 bg-green-100 rounded-lg">
              <FileText className="h-5 w-5 text-green-600" />
            </div>
            <div className="flex-1">
              <h3 className="font-semibold text-gray-900">Sincronizar F29</h3>
              <p className="text-sm text-gray-600">
                Sincroniza declaraciones F29 desde el SII
              </p>
            </div>
          </div>

          <div className="mb-3">
            <Label htmlFor="f29Year">Año</Label>
            <Input
              id="f29Year"
              type="text"
              placeholder="2025"
              value={f29Year}
              onChange={(e) => setF29Year(e.target.value)}
              disabled={syncF29Loading}
            />
          </div>

          <Button
            onClick={handleSyncF29}
            disabled={syncF29Loading}
            className="w-full"
          >
            {syncF29Loading ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Sincronizando...
              </>
            ) : (
              <>
                <FileText className="h-4 w-4 mr-2" />
                Sincronizar F29
              </>
            )}
          </Button>
        </div>

        {/* Calendar Sync */}
        <div>
          <div className="flex items-start gap-3 mb-3">
            <div className="p-2 bg-purple-100 rounded-lg">
              <Calendar className="h-5 w-5 text-purple-600" />
            </div>
            <div className="flex-1">
              <h3 className="font-semibold text-gray-900">
                Sincronizar Calendario
              </h3>
              <p className="text-sm text-gray-600">
                Genera eventos de calendario basados en configuración
              </p>
            </div>
          </div>

          <Button
            onClick={handleSyncCalendar}
            disabled={syncCalendarLoading}
            className="w-full"
          >
            {syncCalendarLoading ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Sincronizando...
              </>
            ) : (
              <>
                <Calendar className="h-4 w-4 mr-2" />
                Sincronizar Calendario
              </>
            )}
          </Button>
        </div>

        {/* Task Message */}
        {taskMessage && (
          <div
            className={`p-3 rounded-lg text-sm ${
              taskMessage.startsWith("✓")
                ? "bg-green-50 text-green-800"
                : "bg-red-50 text-red-800"
            }`}
          >
            {taskMessage}
          </div>
        )}
      </div>
    </Card>
  );
}
