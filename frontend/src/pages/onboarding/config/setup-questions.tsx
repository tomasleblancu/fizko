/**
 * Centralized configuration for company setup onboarding questions
 *
 * This file contains all questions shown during the initial company setup flow.
 * Edit this file to modify questions, their order, or add new ones.
 */

import { CompanySettingsUpdate } from "@/shared/hooks/useCompanySettings";

export type SettingValue = boolean | null | string;

export interface SetupQuestion {
  key: keyof CompanySettingsUpdate;
  title: string;
  description: string;
  icon: React.ReactNode;
  type?: 'boolean' | 'text';
  placeholder?: string;
  maxLength?: number;
}

/**
 * Questions displayed during company setup onboarding
 *
 * Order matters - questions will be shown in the order they appear here.
 *
 * Question types:
 * - 'boolean' (default): Shows Sí/No/No estoy seguro buttons, auto-advances
 * - 'text': Shows textarea input, requires manual "Continuar" button
 */
export const setupQuestions: SetupQuestion[] = [
  {
    key: 'has_formal_employees',
    title: '¿Tienes empleados contratados?',
    description: 'Empleados con contrato indefinido, a plazo fijo o por obra.',
    icon: (
      <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
      </svg>
    ),
  },
  {
    key: 'has_lease_contracts',
    title: '¿Tiene contratos de arriendo?',
    description: 'Arrienda oficinas, locales, bodegas u otros inmuebles.',
    icon: (
      <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
      </svg>
    ),
  },
  {
    key: 'has_imports',
    title: '¿Realiza importaciones?',
    description: 'Compra de productos o servicios desde el extranjero.',
    icon: (
      <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
      </svg>
    ),
  },
  {
    key: 'has_exports',
    title: '¿Realiza exportaciones?',
    description: 'Venta de productos o servicios hacia el extranjero.',
    icon: (
      <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 21v-4m0 0V5a2 2 0 012-2h6.5l1 1H21l-3 6 3 6h-8.5l-1-1H5a2 2 0 00-2 2zm9-13.5V9" />
      </svg>
    ),
  },
  {
    key: 'has_bank_loans',
    title: '¿Tienes algún crédito activo con algún banco, a nombre de tu empresa?',
    description: 'Créditos comerciales, líneas de crédito o préstamos bancarios.',
    icon: (
      <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
      </svg>
    ),
  },
  {
    key: 'business_description',
    title: '¿Si tuvieras que describir tu negocio en no más de 200 palabras, cómo lo describirías?',
    description: 'Una breve descripción de tu negocio nos ayudará a personalizar tu experiencia.',
    type: 'text',
    placeholder: 'Describe tu negocio aquí...',
    maxLength: 200,
    icon: (
      <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
    ),
  },
];

/**
 * Initial state for all setup questions
 *
 * Boolean questions default to null (unanswered)
 * Text questions default to empty string
 */
export const getInitialAnswers = (): Record<string, SettingValue> => {
  return setupQuestions.reduce((acc, question) => {
    acc[question.key] = question.type === 'text' ? '' : null;
    return acc;
  }, {} as Record<string, SettingValue>);
};
