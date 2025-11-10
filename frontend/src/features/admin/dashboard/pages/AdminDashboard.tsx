import { useNavigate } from 'react-router-dom';
import {
  Building2,
  Bell,
  ListTodo,
  Calendar,
  Users,
  FileText,
  Activity,
  TrendingUp,
  ArrowRight,
  Clock,
} from 'lucide-react';

export default function AdminDashboard() {
  const navigate = useNavigate();

  // Mock data - reemplazar con datos reales del backend más adelante
  const stats = {
    totalCompanies: 12,
    activeUsers: 48,
    documentsThisMonth: 1234,
    pendingTasks: 7,
  };

  const recentActivity = [
    {
      id: '1',
      type: 'company',
      description: 'Nueva empresa registrada: Comercial Los Andes Ltda.',
      timestamp: '2025-11-09T10:30:00',
    },
    {
      id: '2',
      type: 'document',
      description: '156 documentos sincronizados para Inversiones del Sur',
      timestamp: '2025-11-09T09:15:00',
    },
    {
      id: '3',
      type: 'task',
      description: 'Tarea completada: Sincronización mensual F29',
      timestamp: '2025-11-09T08:00:00',
    },
    {
      id: '4',
      type: 'notification',
      description: '23 notificaciones enviadas (recordatorio F29)',
      timestamp: '2025-11-08T18:30:00',
    },
  ];

  const quickActions = [
    {
      title: 'Ver Empresas',
      description: 'Gestionar todas las empresas del sistema',
      icon: Building2,
      color: 'blue',
      path: '/admin/companies',
    },
    {
      title: 'Gestor de Tareas',
      description: 'Administrar tareas programadas y cola',
      icon: ListTodo,
      color: 'purple',
      path: '/admin/task-manager',
    },
    {
      title: 'Templates de Eventos',
      description: 'Configurar plantillas de eventos tributarios',
      icon: Calendar,
      color: 'green',
      path: '/admin/event-templates',
    },
    {
      title: 'Templates de Notificaciones',
      description: 'Gestionar plantillas de mensajes',
      icon: Bell,
      color: 'orange',
      path: '/admin/notification-templates',
    },
  ];

  const formatDateTime = (dateString: string) => {
    return new Date(dateString).toLocaleString('es-CL', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getActivityIcon = (type: string) => {
    switch (type) {
      case 'company':
        return Building2;
      case 'document':
        return FileText;
      case 'task':
        return ListTodo;
      case 'notification':
        return Bell;
      default:
        return Activity;
    }
  };

  const getActivityColor = (type: string) => {
    switch (type) {
      case 'company':
        return 'text-blue-600 bg-blue-100 dark:bg-blue-900/20';
      case 'document':
        return 'text-green-600 bg-green-100 dark:bg-green-900/20';
      case 'task':
        return 'text-purple-600 bg-purple-100 dark:bg-purple-900/20';
      case 'notification':
        return 'text-orange-600 bg-orange-100 dark:bg-orange-900/20';
      default:
        return 'text-gray-600 bg-gray-100 dark:bg-gray-700';
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <div className="border-b border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800">
        <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
              Panel de Administración
            </h1>
            <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
              Vista general del sistema Fizko
            </p>
          </div>
        </div>
      </div>

      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        {/* Stats Overview */}
        <div className="mb-8 grid gap-6 md:grid-cols-2 lg:grid-cols-4">
          <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-800">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  Empresas
                </p>
                <p className="mt-2 text-3xl font-bold text-gray-900 dark:text-white">
                  {stats.totalCompanies}
                </p>
              </div>
              <div className="rounded-full bg-blue-100 p-3 dark:bg-blue-900/20">
                <Building2 className="h-6 w-6 text-blue-600" />
              </div>
            </div>
          </div>

          <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-800">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  Usuarios Activos
                </p>
                <p className="mt-2 text-3xl font-bold text-gray-900 dark:text-white">
                  {stats.activeUsers}
                </p>
              </div>
              <div className="rounded-full bg-green-100 p-3 dark:bg-green-900/20">
                <Users className="h-6 w-6 text-green-600" />
              </div>
            </div>
          </div>

          <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-800">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  Documentos (mes)
                </p>
                <p className="mt-2 text-3xl font-bold text-gray-900 dark:text-white">
                  {stats.documentsThisMonth.toLocaleString()}
                </p>
              </div>
              <div className="rounded-full bg-purple-100 p-3 dark:bg-purple-900/20">
                <TrendingUp className="h-6 w-6 text-purple-600" />
              </div>
            </div>
          </div>

          <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-800">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  Tareas Pendientes
                </p>
                <p className="mt-2 text-3xl font-bold text-gray-900 dark:text-white">
                  {stats.pendingTasks}
                </p>
              </div>
              <div className="rounded-full bg-orange-100 p-3 dark:bg-orange-900/20">
                <ListTodo className="h-6 w-6 text-orange-600" />
              </div>
            </div>
          </div>
        </div>

        <div className="grid gap-6 lg:grid-cols-3">
          {/* Recent Activity */}
          <div className="lg:col-span-2">
            <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-800">
              <div className="mb-4 flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Activity className="h-5 w-5 text-gray-600 dark:text-gray-400" />
                  <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                    Actividad Reciente
                  </h2>
                </div>
                <button
                  onClick={() => navigate('/admin/companies')}
                  className="text-sm text-blue-600 hover:text-blue-700 dark:text-blue-400"
                >
                  Ver todo
                </button>
              </div>

              <div className="space-y-4">
                {recentActivity.map((activity) => {
                  const Icon = getActivityIcon(activity.type);
                  const colorClass = getActivityColor(activity.type);

                  return (
                    <div
                      key={activity.id}
                      className="flex items-start space-x-3 rounded-lg border border-gray-200 p-3 dark:border-gray-700"
                    >
                      <div className={`rounded-full p-2 ${colorClass}`}>
                        <Icon className="h-4 w-4" />
                      </div>
                      <div className="flex-1">
                        <p className="text-sm text-gray-900 dark:text-white">
                          {activity.description}
                        </p>
                        <div className="mt-1 flex items-center space-x-1 text-xs text-gray-600 dark:text-gray-400">
                          <Clock className="h-3 w-3" />
                          <span>{formatDateTime(activity.timestamp)}</span>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Quick Actions */}
          <div>
            <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-800">
              <div className="mb-4 flex items-center space-x-2">
                <Activity className="h-5 w-5 text-gray-600 dark:text-gray-400" />
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                  Acciones Rápidas
                </h2>
              </div>

              <div className="space-y-3">
                {quickActions.map((action) => {
                  const Icon = action.icon;
                  const colorClasses = {
                    blue: 'bg-blue-100 text-blue-600 dark:bg-blue-900/20',
                    purple: 'bg-purple-100 text-purple-600 dark:bg-purple-900/20',
                    green: 'bg-green-100 text-green-600 dark:bg-green-900/20',
                    orange: 'bg-orange-100 text-orange-600 dark:bg-orange-900/20',
                  }[action.color];

                  return (
                    <button
                      key={action.title}
                      onClick={() => navigate(action.path)}
                      className="group w-full rounded-lg border border-gray-200 bg-white p-4 text-left transition-all hover:border-gray-300 hover:shadow-md dark:border-gray-700 dark:bg-gray-800 dark:hover:border-gray-600"
                    >
                      <div className="flex items-start space-x-3">
                        <div className={`rounded-lg p-2 ${colorClasses}`}>
                          <Icon className="h-5 w-5" />
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center justify-between">
                            <p className="font-medium text-gray-900 dark:text-white">
                              {action.title}
                            </p>
                            <ArrowRight className="h-4 w-4 text-gray-400 transition-transform group-hover:translate-x-1" />
                          </div>
                          <p className="mt-1 text-xs text-gray-600 dark:text-gray-400">
                            {action.description}
                          </p>
                        </div>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
