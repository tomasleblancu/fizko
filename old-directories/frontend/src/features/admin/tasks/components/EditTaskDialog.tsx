import { useState, useEffect } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { useAuth } from "@/app/providers/AuthContext";
import { API_BASE_URL } from "@/shared/lib/config";
import { apiFetch } from "@/shared/lib/api-client";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '../../../../shared/components/ui/dialog';
import { Button } from "@/shared/components/ui/button";
import { Input } from "@/shared/components/ui/input";
import { Label } from "@/shared/components/ui/label";
import { Textarea } from "@/shared/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../../../../shared/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/shared/components/ui/tabs";
import { Loader2, Clock, Calendar } from 'lucide-react';

const toast = {
  success: (msg: string) => console.log('✓', msg),
  error: (msg: string) => console.error('✗', msg),
};

interface EditTaskDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess: () => void;
  taskId: number;
}

interface IntervalSchedule {
  every: number;
  period: string;
}

interface CrontabSchedule {
  minute: string;
  hour: string;
  day_of_week: string;
  day_of_month: string;
  month_of_year: string;
  timezone: string;
}

interface ScheduledTask {
  id: number;
  name: string;
  task: string;
  schedule_type: string;
  schedule_display: string;
  interval?: IntervalSchedule | null;
  crontab?: CrontabSchedule | null;
  enabled: boolean;
  queue: string | null;
  priority: number | null;
  description: string | null;
  kwargs: Record<string, any>;
  args: any[];
  one_off: boolean;
  max_retries: number | null;
  soft_time_limit: number | null;
  hard_time_limit: number | null;
}

export default function EditTaskDialog({
  open,
  onOpenChange,
  onSuccess,
  taskId,
}: EditTaskDialogProps) {
  const { session } = useAuth();

  // Form state - Basic
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [queue, setQueue] = useState('default');
  const [priority, setPriority] = useState<string>('');
  const [args, setArgs] = useState('[]');
  const [kwargs, setKwargs] = useState('{}');
  const [maxRetries, setMaxRetries] = useState<string>('');
  const [softTimeLimit, setSoftTimeLimit] = useState<string>('');
  const [hardTimeLimit, setHardTimeLimit] = useState<string>('');

  // Form state - Schedule
  const [scheduleType, setScheduleType] = useState<'interval' | 'crontab'>('interval');
  const [intervalEvery, setIntervalEvery] = useState('30');
  const [intervalPeriod, setIntervalPeriod] = useState('minutes');
  const [crontabMinute, setCrontabMinute] = useState('0');
  const [crontabHour, setCrontabHour] = useState('0');
  const [crontabDayOfWeek, setCrontabDayOfWeek] = useState('*');
  const [crontabDayOfMonth, setCrontabDayOfMonth] = useState('*');
  const [crontabMonthOfYear, setCrontabMonthOfYear] = useState('*');

  // Fetch task details
  const { data: task, isLoading: isLoadingTask } = useQuery<ScheduledTask>({
    queryKey: ['scheduled-task', taskId],
    queryFn: async () => {
      if (!session?.access_token) throw new Error('No session');

      const response = await apiFetch(`${API_BASE_URL}/scheduled-tasks/${taskId}`, {
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch task details');
      }

      return response.json();
    },
    enabled: !!session?.access_token && open,
  });

  // Initialize form when task data is loaded
  useEffect(() => {
    if (task) {
      setName(task.name);
      setDescription(task.description || '');
      setQueue(task.queue || 'default');
      setPriority(task.priority?.toString() || '');

      // Set args and kwargs
      setArgs(JSON.stringify(task.args || [], null, 2));
      setKwargs(JSON.stringify(task.kwargs || {}, null, 2));

      setMaxRetries(task.max_retries?.toString() || '');
      setSoftTimeLimit(task.soft_time_limit?.toString() || '');
      setHardTimeLimit(task.hard_time_limit?.toString() || '');

      // Load schedule data from backend
      setScheduleType(task.schedule_type === 'interval' ? 'interval' : 'crontab');

      // Load interval schedule data
      if (task.schedule_type === 'interval' && task.interval) {
        setIntervalEvery(task.interval.every.toString());
        setIntervalPeriod(task.interval.period);
      }

      // Load crontab schedule data
      if (task.schedule_type === 'crontab' && task.crontab) {
        setCrontabMinute(task.crontab.minute);
        setCrontabHour(task.crontab.hour);
        setCrontabDayOfWeek(task.crontab.day_of_week);
        setCrontabDayOfMonth(task.crontab.day_of_month);
        setCrontabMonthOfYear(task.crontab.month_of_year);
      }
    }
  }, [task]);

  const updateTaskMutation = useMutation({
    mutationFn: async (data: any) => {
      if (!session?.access_token) throw new Error('No session');

      const response = await apiFetch(`${API_BASE_URL}/scheduled-tasks/${taskId}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to update task');
      }

      return response.json();
    },
    onSuccess: () => {
      toast.success('Tarea actualizada exitosamente');
      onSuccess();
    },
    onError: (error: Error) => {
      toast.error(`Error: ${error.message}`);
    },
  });

  const handleSubmit = () => {
    // Validate name
    if (!name.trim()) {
      toast.error('El nombre es obligatorio');
      return;
    }

    // Parse args
    let parsedArgs = [];
    try {
      parsedArgs = JSON.parse(args);
      if (!Array.isArray(parsedArgs)) {
        toast.error('Los args deben ser un array JSON');
        return;
      }
    } catch (error) {
      toast.error('Los args deben ser JSON válido');
      return;
    }

    // Parse kwargs
    let parsedKwargs = {};
    try {
      parsedKwargs = JSON.parse(kwargs);
    } catch (error) {
      toast.error('Los kwargs deben ser JSON válido');
      return;
    }

    // Build payload
    const payload: any = {
      name: name.trim(),
      description: description.trim() || null,
      queue,
      args: parsedArgs,
      kwargs: parsedKwargs,
    };

    // Add schedule fields
    if (scheduleType === 'interval') {
      payload.interval_every = parseInt(intervalEvery, 10);
      payload.interval_period = intervalPeriod;
    } else {
      payload.crontab_minute = crontabMinute;
      payload.crontab_hour = crontabHour;
      payload.crontab_day_of_week = crontabDayOfWeek;
      payload.crontab_day_of_month = crontabDayOfMonth;
      payload.crontab_month_of_year = crontabMonthOfYear;
      payload.crontab_timezone = 'America/Santiago';
    }

    // Add optional numeric fields if provided
    if (priority) {
      payload.priority = parseInt(priority, 10);
    }

    if (maxRetries) {
      payload.max_retries = parseInt(maxRetries, 10);
    }

    if (softTimeLimit) {
      payload.soft_time_limit = parseInt(softTimeLimit, 10);
    }

    if (hardTimeLimit) {
      payload.hard_time_limit = parseInt(hardTimeLimit, 10);
    }

    updateTaskMutation.mutate(payload);
  };

  if (!open) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Editar Tarea Programada</DialogTitle>
          <DialogDescription>
            Modifica la configuración de la tarea, incluyendo el schedule.
          </DialogDescription>
        </DialogHeader>

        {isLoadingTask ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
          </div>
        ) : task ? (
          <div className="space-y-4 py-4">
            {/* Task Type Info (Read-only) */}
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
              <p className="text-sm text-slate-700">
                <strong>Tarea Celery:</strong> {task.task}
              </p>
            </div>

            {/* Editable Fields */}
            <div className="space-y-2">
              <Label htmlFor="name">Nombre de la tarea *</Label>
              <Input
                id="name"
                placeholder="ej: sync-docs-hourly"
                value={name}
                onChange={(e) => setName(e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">Descripción</Label>
              <Textarea
                id="description"
                placeholder="Describe qué hace esta tarea..."
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={2}
              />
            </div>

            {/* Schedule Configuration */}
            <div className="space-y-2">
              <Label>Programación</Label>
              <Tabs value={scheduleType} onValueChange={(v) => setScheduleType(v as any)}>
                <TabsList className="grid w-full grid-cols-2">
                  <TabsTrigger value="interval">
                    <Clock className="h-4 w-4 mr-2" />
                    Intervalo
                  </TabsTrigger>
                  <TabsTrigger value="crontab">
                    <Calendar className="h-4 w-4 mr-2" />
                    Crontab
                  </TabsTrigger>
                </TabsList>

                <TabsContent value="interval" className="space-y-3 mt-4">
                  <div className="grid grid-cols-2 gap-3">
                    <div className="space-y-2">
                      <Label htmlFor="interval-every">Cada</Label>
                      <Input
                        id="interval-every"
                        type="number"
                        min="1"
                        value={intervalEvery}
                        onChange={(e) => setIntervalEvery(e.target.value)}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="interval-period">Unidad</Label>
                      <Select value={intervalPeriod} onValueChange={setIntervalPeriod}>
                        <SelectTrigger id="interval-period">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="minutes">Minutos</SelectItem>
                          <SelectItem value="hours">Horas</SelectItem>
                          <SelectItem value="days">Días</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                  <p className="text-sm text-slate-600">
                    Ejemplo: Cada {intervalEvery} {intervalPeriod}
                  </p>
                </TabsContent>

                <TabsContent value="crontab" className="space-y-3 mt-4">
                  <div className="grid grid-cols-2 gap-3">
                    <div className="space-y-2">
                      <Label htmlFor="cron-minute">Minuto (0-59)</Label>
                      <Input
                        id="cron-minute"
                        placeholder="0 o *"
                        value={crontabMinute}
                        onChange={(e) => setCrontabMinute(e.target.value)}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="cron-hour">Hora (0-23)</Label>
                      <Input
                        id="cron-hour"
                        placeholder="0 o *"
                        value={crontabHour}
                        onChange={(e) => setCrontabHour(e.target.value)}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="cron-day-month">Día del mes (1-31)</Label>
                      <Input
                        id="cron-day-month"
                        placeholder="* para todos"
                        value={crontabDayOfMonth}
                        onChange={(e) => setCrontabDayOfMonth(e.target.value)}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="cron-month">Mes (1-12)</Label>
                      <Input
                        id="cron-month"
                        placeholder="* para todos"
                        value={crontabMonthOfYear}
                        onChange={(e) => setCrontabMonthOfYear(e.target.value)}
                      />
                    </div>
                    <div className="space-y-2 col-span-2">
                      <Label htmlFor="cron-day-week">Día de la semana (0-6)</Label>
                      <Input
                        id="cron-day-week"
                        placeholder="* para todos, 0=domingo"
                        value={crontabDayOfWeek}
                        onChange={(e) => setCrontabDayOfWeek(e.target.value)}
                      />
                    </div>
                  </div>
                  <p className="text-sm text-slate-600">
                    Cron: {crontabMinute} {crontabHour} {crontabDayOfMonth}{' '}
                    {crontabMonthOfYear} {crontabDayOfWeek}
                  </p>
                </TabsContent>
              </Tabs>
            </div>

            <div className="space-y-2">
              <Label htmlFor="queue">Cola de ejecución</Label>
              <Select value={queue} onValueChange={setQueue}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="high">High (alta prioridad)</SelectItem>
                  <SelectItem value="default">Default (prioridad normal)</SelectItem>
                  <SelectItem value="low">Low (baja prioridad)</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="priority">Prioridad (0-10, opcional)</Label>
              <Input
                id="priority"
                type="number"
                min="0"
                max="10"
                placeholder="Dejar vacío para usar default"
                value={priority}
                onChange={(e) => setPriority(e.target.value)}
              />
            </div>

            {/* Task Arguments */}
            <div className="space-y-4">
              {/* Args (positional) */}
              <div className="space-y-2">
                <Label htmlFor="args">Args - Argumentos Posicionales (JSON Array)</Label>
                <Textarea
                  id="args"
                  placeholder='["daily_business_summary"]'
                  value={args}
                  onChange={(e) => setArgs(e.target.value)}
                  rows={3}
                  className="font-mono text-sm"
                />
                <p className="text-xs text-slate-500">
                  Array de argumentos posicionales. Ejemplo: ["arg1", "arg2"]
                </p>
              </div>

              {/* Kwargs (keyword arguments) */}
              <div className="space-y-2">
                <Label htmlFor="kwargs">Kwargs - Argumentos con Nombre (JSON Object)</Label>
                <Textarea
                  id="kwargs"
                  placeholder='{"session_id": "uuid", "months": 1}'
                  value={kwargs}
                  onChange={(e) => setKwargs(e.target.value)}
                  rows={3}
                  className="font-mono text-sm"
                />
                <p className="text-xs text-slate-500">
                  Objeto con argumentos con nombre. Ejemplo: {'{'}key: "value"{'}'}
                </p>
              </div>
            </div>

            {/* Advanced Settings */}
            <details className="border rounded-lg p-4">
              <summary className="cursor-pointer font-medium text-sm text-slate-700 mb-2">
                Configuración Avanzada
              </summary>
              <div className="space-y-3 mt-3">
                <div className="space-y-2">
                  <Label htmlFor="max-retries">Max Retries</Label>
                  <Input
                    id="max-retries"
                    type="number"
                    min="0"
                    placeholder="Número máximo de reintentos"
                    value={maxRetries}
                    onChange={(e) => setMaxRetries(e.target.value)}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="soft-time-limit">Soft Time Limit (segundos)</Label>
                  <Input
                    id="soft-time-limit"
                    type="number"
                    min="0"
                    placeholder="Tiempo límite suave"
                    value={softTimeLimit}
                    onChange={(e) => setSoftTimeLimit(e.target.value)}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="hard-time-limit">Hard Time Limit (segundos)</Label>
                  <Input
                    id="hard-time-limit"
                    type="number"
                    min="0"
                    placeholder="Tiempo límite estricto"
                    value={hardTimeLimit}
                    onChange={(e) => setHardTimeLimit(e.target.value)}
                  />
                </div>
              </div>
            </details>
          </div>
        ) : (
          <div className="text-center py-8 text-slate-500">
            No se pudo cargar la tarea
          </div>
        )}

        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={updateTaskMutation.isPending}
          >
            Cancelar
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={updateTaskMutation.isPending || isLoadingTask}
            className="gap-2"
          >
            {updateTaskMutation.isPending && (
              <Loader2 className="h-4 w-4 animate-spin" />
            )}
            Guardar Cambios
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
