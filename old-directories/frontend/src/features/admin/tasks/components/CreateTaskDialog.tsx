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
import { Clock, Calendar, Loader2 } from 'lucide-react';
// import { toast } from 'sonner'; // TODO: Install sonner package
const toast = {
  success: (msg: string) => console.log('✓', msg),
  error: (msg: string) => console.error('✗', msg),
};

interface CreateTaskDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess: () => void;
}

interface AvailableTask {
  name: string;
  description: string;
  default_kwargs: Record<string, any>;
  default_args?: any[];  // Some tasks use positional args instead of kwargs
  args_examples?: string[];
  args_help?: string;
}

export default function CreateTaskDialog({
  open,
  onOpenChange,
  onSuccess,
}: CreateTaskDialogProps) {
  const { session } = useAuth();

  // Form state
  const [scheduleType, setScheduleType] = useState<'interval' | 'crontab'>('interval');
  const [name, setName] = useState('');
  const [task, setTask] = useState('');
  const [description, setDescription] = useState('');
  const [queue, setQueue] = useState('default');
  const [runNow, setRunNow] = useState(false);

  // Interval fields
  const [intervalEvery, setIntervalEvery] = useState('30');
  const [intervalPeriod, setIntervalPeriod] = useState('minutes');

  // Crontab fields
  const [crontabMinute, setCrontabMinute] = useState('0');
  const [crontabHour, setCrontabHour] = useState('0');
  const [crontabDayOfWeek, setCrontabDayOfWeek] = useState('*');
  const [crontabDayOfMonth, setCrontabDayOfMonth] = useState('*');
  const [crontabMonthOfYear, setCrontabMonthOfYear] = useState('*');

  // Task arguments (JSON)
  const [kwargs, setKwargs] = useState('{"session_id": "", "months": 1}');
  const [args, setArgs] = useState('[]');
  const [selectedTaskInfo, setSelectedTaskInfo] = useState<AvailableTask | null>(null);

  // Fetch available tasks
  const { data: availableTasks = [], isLoading: isLoadingTasks } = useQuery<AvailableTask[]>({
    queryKey: ['available-tasks'],
    queryFn: async () => {
      if (!session?.access_token) return [];

      const response = await apiFetch(`${API_BASE_URL}/scheduled-tasks/available-tasks`, {
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch available tasks');
      }

      return response.json();
    },
    enabled: !!session?.access_token,
  });

  // Auto-populate args/kwargs based on selected task (from backend)
  useEffect(() => {
    if (!task) return;

    // Find the selected task in available tasks
    const selectedTask = availableTasks.find(t => t.name === task);
    setSelectedTaskInfo(selectedTask || null);

    if (selectedTask) {
      // Check if this task uses positional args (like template-driven notifications)
      if (selectedTask.default_args && selectedTask.default_args.length > 0) {
        // Task uses args
        setArgs(JSON.stringify(selectedTask.default_args, null, 2));
        setKwargs('{}');  // Clear kwargs when using args
      } else if (selectedTask.default_kwargs) {
        // Task uses kwargs
        setKwargs(JSON.stringify(selectedTask.default_kwargs, null, 2));
        setArgs('[]');  // Clear args when using kwargs
      } else {
        // No defaults
        setKwargs('{}');
        setArgs('[]');
      }
    } else {
      setKwargs('{}');
      setArgs('[]');
    }
  }, [task, availableTasks]);

  const createTaskMutation = useMutation({
    mutationFn: async (data: any) => {
      if (!session?.access_token) throw new Error('No session');

      const response = await apiFetch(`${API_BASE_URL}/scheduled-tasks`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to create task');
      }

      return response.json();
    },
    onSuccess: () => {
      toast.success('Tarea creada exitosamente');
      resetForm();
      onSuccess();
    },
    onError: (error: Error) => {
      toast.error(`Error: ${error.message}`);
    },
  });

  const resetForm = () => {
    setName('');
    setTask('');
    setDescription('');
    setQueue('default');
    setRunNow(false);
    setScheduleType('interval');
    setIntervalEvery('30');
    setIntervalPeriod('minutes');
    setCrontabMinute('0');
    setCrontabHour('0');
    setCrontabDayOfWeek('*');
    setCrontabDayOfMonth('*');
    setCrontabMonthOfYear('*');
    setKwargs('{"session_id": "", "months": 1}');
    setArgs('[]');
    setSelectedTaskInfo(null);
  };

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
      task,
      description: description.trim() || undefined,
      queue,
      args: parsedArgs,
      kwargs: parsedKwargs,
      schedule_type: scheduleType,
      enabled: true,
      run_now: runNow,
    };

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

    createTaskMutation.mutate(payload);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Crear Tarea Programada</DialogTitle>
          <DialogDescription>
            Configura una nueva tarea para ejecutar automáticamente
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* Basic Info */}
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
            <Label htmlFor="task">Tarea Celery *</Label>
            <Select value={task} onValueChange={setTask} disabled={isLoadingTasks}>
              <SelectTrigger>
                <SelectValue placeholder={isLoadingTasks ? "Cargando tareas..." : "Selecciona una tarea"} />
              </SelectTrigger>
              <SelectContent>
                {availableTasks.map((availableTask) => (
                  <SelectItem key={availableTask.name} value={availableTask.name}>
                    {availableTask.name}
                    {availableTask.description && ` - ${availableTask.description}`}
                  </SelectItem>
                ))}
                {availableTasks.length === 0 && !isLoadingTasks && (
                  <SelectItem value="no-tasks" disabled>
                    No hay tareas disponibles
                  </SelectItem>
                )}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="description">Descripción (opcional)</Label>
            <Textarea
              id="description"
              placeholder="Describe qué hace esta tarea..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={2}
            />
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

          {/* Run Now Checkbox */}
          <div className="flex items-start space-x-3 rounded-lg border border-slate-200 bg-slate-50 p-4">
            <input
              type="checkbox"
              id="run-now"
              checked={runNow}
              onChange={(e) => setRunNow(e.target.checked)}
              className="mt-0.5 h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <div className="flex-1">
              <Label htmlFor="run-now" className="cursor-pointer font-medium">
                Ejecutar inmediatamente
              </Label>
              <p className="text-xs text-slate-600 mt-1">
                {runNow
                  ? "La tarea se ejecutará de inmediato y luego según el intervalo programado"
                  : "La tarea se ejecutará por primera vez según el intervalo programado"}
              </p>
            </div>
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

          {/* Task Arguments - Show args or kwargs depending on task */}
          {selectedTaskInfo?.default_args && selectedTaskInfo.default_args.length > 0 ? (
            // Task uses positional arguments (args)
            <div className="space-y-2">
              <Label htmlFor="args">Argumentos Posicionales (Array JSON)</Label>
              <Textarea
                id="args"
                placeholder='["daily_business_summary"]'
                value={args}
                onChange={(e) => setArgs(e.target.value)}
                rows={3}
                className="font-mono text-sm"
              />
              {selectedTaskInfo.args_help && (
                <p className="text-xs text-blue-600 dark:text-blue-400">
                  💡 {selectedTaskInfo.args_help}
                </p>
              )}
              {selectedTaskInfo.args_examples && selectedTaskInfo.args_examples.length > 0 && (
                <details className="text-xs text-slate-500">
                  <summary className="cursor-pointer font-medium">Ver ejemplos</summary>
                  <ul className="mt-2 space-y-1 pl-4">
                    {selectedTaskInfo.args_examples.map((example, idx) => (
                      <li key={idx} className="font-mono">
                        ["{example}"]
                      </li>
                    ))}
                  </ul>
                </details>
              )}
              <p className="text-xs text-slate-500">
                Array de argumentos posicionales que se pasarán a la tarea
              </p>
            </div>
          ) : (
            // Task uses keyword arguments (kwargs)
            <div className="space-y-2">
              <Label htmlFor="kwargs">Argumentos (Object JSON)</Label>
              <Textarea
                id="kwargs"
                placeholder='{"session_id": "uuid", "months": 1}'
                value={kwargs}
                onChange={(e) => setKwargs(e.target.value)}
                rows={3}
                className="font-mono text-sm"
              />
              <p className="text-xs text-slate-500">
                Parámetros clave-valor que se pasarán a la tarea en formato JSON
              </p>
            </div>
          )}
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={createTaskMutation.isPending}
          >
            Cancelar
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={createTaskMutation.isPending}
            className="gap-2"
          >
            {createTaskMutation.isPending && (
              <Loader2 className="h-4 w-4 animate-spin" />
            )}
            Crear Tarea
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
