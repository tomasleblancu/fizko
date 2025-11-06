/**
 * Types for the chateable components system
 */

export type MessageGenerator<T = any> = string | ((data: T) => string);

export interface ChateableContextData {
  [key: string]: any;
}

export interface ChateableWrapperProps {
  /** The message to send when clicked, or a function to generate it */
  message: MessageGenerator;
  /** Contextual data to pass to the message generator */
  contextData?: ChateableContextData;
  /** Additional onClick handler (called before sending message) */
  onClick?: () => void;
  /** Additional CSS classes */
  className?: string;
  /** Disable the chateable functionality */
  disabled?: boolean;
  /** Child components */
  children: React.ReactNode;
  /** UI component name to pass as metadata to backend */
  uiComponent?: string;
  /** Entity ID (for specific documents, contacts, etc.) */
  entityId?: string;
  /** Entity type (e.g., 'sales_document', 'purchase_document', 'contact') */
  entityType?: string;
  /** HTML element type or 'fragment' for table rows (default: 'div') */
  as?: 'div' | 'span' | 'fragment';
}

export interface ChateableClickOptions {
  /** The message to send when clicked, or a function to generate it */
  message: MessageGenerator;
  /** Contextual data to pass to the message generator */
  contextData?: ChateableContextData;
  /** Additional onClick handler (called before sending message) */
  onClick?: () => void;
  /** Disable the chateable functionality */
  disabled?: boolean;
  /** UI component name to pass as metadata to backend */
  uiComponent?: string;
  /** Entity ID (for specific documents, contacts, etc.) */
  entityId?: string;
  /** Entity type (e.g., 'sales_document', 'purchase_document', 'contact') */
  entityType?: string;
}

export interface ChateableClickReturn {
  /** Click handler */
  onClick: (e: React.MouseEvent) => void;
  /** CSS classes for chateable styling */
  className: string;
  /** ARIA role for accessibility */
  role: string;
  /** Tab index for keyboard navigation */
  tabIndex: number;
  /** Keyboard handler for Enter/Space */
  onKeyDown: (e: React.KeyboardEvent) => void;
}
