/**
 * TemplateCard Component
 *
 * Displays a notification template card with all its information
 * and action buttons (edit, delete)
 */

import { Edit2, Trash2 } from 'lucide-react';
import { NotificationTemplate } from '../../types';
import {
  getCategoryLabel,
  getCategoryColor,
  getPriorityLabel,
  getPriorityColor,
  getTimingDescription,
} from '../../utils/templateHelpers';

interface TemplateCardProps {
  template: NotificationTemplate;
  onEdit: (template: NotificationTemplate) => void;
  onDelete: (templateId: string) => void;
}

export function TemplateCard({ template, onEdit, onDelete }: TemplateCardProps) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-800">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          {/* Header */}
          <div className="flex items-center gap-3">
            <h3 className="text-xl font-semibold text-gray-900 dark:text-white">
              {template.name}
            </h3>
            <span className="text-xs font-mono text-gray-500 dark:text-gray-400">
              {template.code}
            </span>
            <span
              className={`rounded-full px-3 py-1 text-sm font-medium ${getCategoryColor(
                template.category
              )}`}
            >
              {getCategoryLabel(template.category)}
            </span>
            <span
              className={`rounded-full px-3 py-1 text-sm font-medium ${getPriorityColor(
                template.priority
              )}`}
            >
              {getPriorityLabel(template.priority)}
            </span>
            {!template.is_active && (
              <span className="rounded-full bg-gray-100 px-3 py-1 text-sm font-medium text-gray-700 dark:bg-gray-900/30 dark:text-gray-400">
                Inactivo
              </span>
            )}
          </div>

          {/* Description */}
          <p className="mt-2 text-gray-600 dark:text-gray-400">{template.description}</p>

          {/* Message Template */}
          <div className="mt-3 rounded-lg bg-gray-50 p-3 dark:bg-gray-900/50">
            <p className="text-xs font-medium text-gray-500 dark:text-gray-400">Mensaje:</p>
            <p className="mt-1 text-sm text-gray-700 dark:text-gray-300">
              {template.message_template}
            </p>
          </div>

          {/* Details Grid */}
          <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <div>
              <p className="text-xs font-medium text-gray-500 dark:text-gray-400">Timing</p>
              <p className="mt-1 text-sm font-semibold text-gray-900 dark:text-white">
                {getTimingDescription(template.timing_config)}
              </p>
            </div>

            {template.entity_type && (
              <div>
                <p className="text-xs font-medium text-gray-500 dark:text-gray-400">
                  Tipo de Entidad
                </p>
                <p className="mt-1 text-sm font-semibold text-gray-900 dark:text-white">
                  {template.entity_type}
                </p>
              </div>
            )}

            {template.auto_assign_to_new_companies && (
              <div>
                <p className="text-xs font-medium text-gray-500 dark:text-gray-400">
                  Auto-asignación
                </p>
                <p className="mt-1 text-sm font-semibold text-green-600 dark:text-green-400">
                  Habilitada
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Action Buttons */}
        <div className="ml-4 flex gap-2">
          <button
            onClick={() => onEdit(template)}
            className="rounded-lg p-2 text-blue-600 hover:bg-blue-50 dark:text-blue-400 dark:hover:bg-blue-900/20"
            title="Editar template"
          >
            <Edit2 className="h-5 w-5" />
          </button>
          <button
            onClick={() => onDelete(template.id)}
            className="rounded-lg p-2 text-red-600 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-900/20"
            title="Eliminar template"
          >
            <Trash2 className="h-5 w-5" />
          </button>
        </div>
      </div>
    </div>
  );
}
