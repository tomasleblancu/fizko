/**
 * Template Helpers - Utility functions for notification templates
 *
 * Provides helper functions for:
 * - Category labels and colors
 * - Priority labels and colors
 * - Timing descriptions
 * - Timing config builders
 */

// ============================================================================
// TYPES
// ============================================================================

export interface TimingConfig {
  type: 'immediate' | 'absolute' | 'relative';
  offset_days?: number;
  time?: string;
}

// ============================================================================
// CATEGORY HELPERS
// ============================================================================

const CATEGORY_LABELS: Record<string, string> = {
  calendar: 'Calendario',
  tax_document: 'Documento Tributario',
  payroll: 'Remuneraciones',
  system: 'Sistema',
  custom: 'Personalizado',
};

const CATEGORY_COLORS: Record<string, string> = {
  calendar: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
  tax_document: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400',
  payroll: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  system: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',
  custom: 'bg-pink-100 text-pink-700 dark:bg-pink-900/30 dark:text-pink-400',
};

export function getCategoryLabel(category: string): string {
  return CATEGORY_LABELS[category] || category;
}

export function getCategoryColor(category: string): string {
  return CATEGORY_COLORS[category] || CATEGORY_COLORS.custom;
}

// ============================================================================
// PRIORITY HELPERS
// ============================================================================

const PRIORITY_LABELS: Record<string, string> = {
  low: 'Baja',
  normal: 'Normal',
  high: 'Alta',
  urgent: 'Urgente',
};

const PRIORITY_COLORS: Record<string, string> = {
  low: 'bg-gray-100 text-gray-700 dark:bg-gray-900/30 dark:text-gray-400',
  normal: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
  high: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',
  urgent: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
};

export function getPriorityLabel(priority: string): string {
  return PRIORITY_LABELS[priority] || priority;
}

export function getPriorityColor(priority: string): string {
  return PRIORITY_COLORS[priority] || PRIORITY_COLORS.normal;
}

// ============================================================================
// TIMING HELPERS
// ============================================================================

export function getTimingDescription(timing: TimingConfig): string {
  if (timing.type === 'immediate') {
    return 'Inmediato';
  }

  if (timing.type === 'absolute') {
    return `Hora fija: ${timing.time || 'No definido'}`;
  }

  if (timing.type === 'relative') {
    const days = timing.offset_days || 0;
    const time = timing.time || '09:00';

    if (days === 0) {
      return `El mismo día a las ${time}`;
    }

    if (days < 0) {
      return `${Math.abs(days)} día(s) antes a las ${time}`;
    }

    return `${days} día(s) después a las ${time}`;
  }

  return 'No definido';
}

export function buildTimingConfig(
  timingType: string,
  offsetDays: string,
  timingTime: string
): TimingConfig {
  if (timingType === 'immediate') {
    return { type: 'immediate' };
  }

  if (timingType === 'absolute') {
    return {
      type: 'absolute',
      time: timingTime,
    };
  }

  // relative
  return {
    type: 'relative',
    offset_days: parseInt(offsetDays) || 0,
    time: timingTime,
  };
}
