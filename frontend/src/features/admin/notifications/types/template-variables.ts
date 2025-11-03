/**
 * Type definitions for template variables
 */

export interface TemplateVariable {
  name: string;
  type: string;
  description: string;
  example: string;
}

export interface TemplateVariablesData {
  name: string;
  description: string;
  method: string;
  service: string;
  variables: TemplateVariable[];
}

export interface TemplateVariablesResponse {
  success: boolean;
  data?: TemplateVariablesData;
  error?: string;
}
