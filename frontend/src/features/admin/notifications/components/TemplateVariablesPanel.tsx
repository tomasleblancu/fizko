/**
 * Template Variables Panel Component
 *
 * Displays available variables for a template with examples and descriptions.
 * Can be toggled to show/hide and provides a clean UI for variable reference.
 */

import { useState } from 'react';
import { Info, Loader2 } from 'lucide-react';
import type { TemplateVariable } from '../types/template-variables';

interface TemplateVariablesPanelProps {
  /** Template code to display variables for (for non-summary templates) */
  templateCode?: string;
  /** Service method name (for summary templates) */
  serviceMethod?: string;
  /** Array of available variables */
  variables: TemplateVariable[];
  /** Whether the variables are currently being loaded */
  isLoading?: boolean;
  /** Optional CSS class name */
  className?: string;
}

/**
 * Panel component that displays template variables with toggle functionality
 *
 * @example
 * ```tsx
 * <TemplateVariablesPanel
 *   templateCode="daily_business_summary"
 *   variables={variables}
 *   isLoading={isLoading}
 * />
 * ```
 */
export function TemplateVariablesPanel({
  templateCode,
  serviceMethod,
  variables,
  isLoading = false,
  className = '',
}: TemplateVariablesPanelProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const hasVariables = variables && variables.length > 0;
  const hasIdentifier = (templateCode && templateCode.trim() !== '') || (serviceMethod && serviceMethod.trim() !== '');

  return (
    <div className={className}>
      {/* Toggle Button - Always show */}
      <div className="flex items-center justify-between">
        <button
          type="button"
          onClick={() => setIsExpanded(!isExpanded)}
          className="flex items-center gap-1 text-xs text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
          disabled={isLoading}
        >
          <Info className="h-3 w-3" />
          {isExpanded ? 'Ocultar' : 'Ver'} variables disponibles
          {isLoading && <Loader2 className="ml-1 h-3 w-3 animate-spin" />}
        </button>
      </div>

      {/* Expandable Variables Panel */}
      {isExpanded && (
        <div className="mt-2 rounded-lg border border-blue-200 bg-blue-50 p-3 dark:border-blue-900 dark:bg-blue-900/20">
          <h4 className="mb-2 flex items-center gap-2 text-sm font-semibold text-blue-900 dark:text-blue-200">
            <Info className="h-4 w-4" />
            Variables Disponibles
            {templateCode && <span className="text-xs font-normal">para "{templateCode}"</span>}
            {serviceMethod && <span className="text-xs font-normal">para método "{serviceMethod}"</span>}
          </h4>

          {isLoading ? (
            // Loading state
            <div className="flex items-center justify-center py-4">
              <Loader2 className="h-5 w-5 animate-spin text-blue-600" />
              <span className="ml-2 text-sm text-blue-700 dark:text-blue-300">
                Cargando variables...
              </span>
            </div>
          ) : !hasIdentifier ? (
            // No template code entered yet
            <div className="rounded-md bg-yellow-50 p-3 dark:bg-yellow-900/20">
              <p className="text-sm text-yellow-800 dark:text-yellow-300">
                ⚠️ Ingresa un código de template para ver las variables disponibles
              </p>
            </div>
          ) : !hasVariables ? (
            // No variables found for this template
            <div className="rounded-md bg-gray-50 p-3 dark:bg-gray-800">
              <p className="text-sm text-gray-600 dark:text-gray-400">
                No hay variables específicas definidas para este template.
              </p>
              <p className="mt-2 text-xs text-gray-500 dark:text-gray-500">
                Puedes usar variables genéricas como:{' '}
                <code className="rounded bg-white px-1 py-0.5 dark:bg-gray-700">
                  {'{'}
                  {'{'}company_name{'}'} {'}'}
                </code>
                ,{' '}
                <code className="rounded bg-white px-1 py-0.5 dark:bg-gray-700">
                  {'{'}
                  {'{'}user_name{'}'} {'}'}
                </code>
              </p>
            </div>
          ) : (
            // Variables found - show them
            <>
              <div className="space-y-2">
                {variables.map((variable) => (
                  <VariableCard key={variable.name} variable={variable} />
                ))}
              </div>

              <p className="mt-2 text-xs text-blue-700 dark:text-blue-300">
                💡 Haz clic en las variables para copiarlas al portapapeles
              </p>
            </>
          )}
        </div>
      )}
    </div>
  );
}

/**
 * Individual variable card component
 */
function VariableCard({ variable }: { variable: TemplateVariable }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    const varText = `{{${variable.name}}}`;
    try {
      await navigator.clipboard.writeText(varText);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  return (
    <div
      className="cursor-pointer rounded-md bg-white p-2 transition-colors hover:bg-gray-50 dark:bg-gray-800 dark:hover:bg-gray-750"
      onClick={handleCopy}
      title="Clic para copiar"
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1">
          <code className="text-xs font-bold text-blue-700 dark:text-blue-400">
            {copied ? '✓ Copiado!' : `{{${variable.name}}}`}
          </code>
          <p className="mt-0.5 text-xs text-gray-600 dark:text-gray-400">
            {variable.description}
          </p>
          <p className="mt-0.5 text-xs text-gray-500 dark:text-gray-500">
            Tipo: <span className="font-mono">{variable.type}</span>
          </p>
        </div>
        <span className="rounded bg-gray-100 px-2 py-0.5 text-xs font-mono text-gray-700 dark:bg-gray-700 dark:text-gray-300">
          {variable.example}
        </span>
      </div>
    </div>
  );
}

/**
 * Compact version of the panel for inline use
 */
export function TemplateVariablesInline({
  variables,
  isLoading,
}: {
  variables: TemplateVariable[];
  isLoading?: boolean;
}) {
  if (!variables || variables.length === 0) {
    return null;
  }

  return (
    <div className="mt-1 rounded-md border border-gray-200 bg-gray-50 p-2 dark:border-gray-700 dark:bg-gray-800">
      <p className="mb-1 text-xs font-medium text-gray-700 dark:text-gray-300">
        Variables disponibles:
        {isLoading && <Loader2 className="ml-1 inline h-3 w-3 animate-spin" />}
      </p>
      <div className="flex flex-wrap gap-1">
        {variables.map((variable) => (
          <code
            key={variable.name}
            className="rounded bg-blue-100 px-1.5 py-0.5 text-xs text-blue-700 dark:bg-blue-900/30 dark:text-blue-400"
            title={variable.description}
          >
            {`{{${variable.name}}}`}
          </code>
        ))}
      </div>
    </div>
  );
}
