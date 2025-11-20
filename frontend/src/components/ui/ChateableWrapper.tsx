'use client';

import { useCallback, cloneElement, isValidElement } from 'react';
import type { ChateableWrapperProps } from '@/types/chateable';
import '@/styles/chateable.css';

/**
 * Wrapper component that makes its children chateable (clickable to send a message to chat).
 * Useful for wrapping entire cards or components.
 *
 * For table rows, use `as="fragment"` to avoid invalid HTML structure:
 * @example
 * <ChateableWrapper
 *   as="fragment"
 *   message="Analyze this contact"
 *   contextData={{ contactId: "123" }}
 * >
 *   <tr>...</tr>
 * </ChateableWrapper>
 *
 * @example
 * <ChateableWrapper
 *   message="Analyze my tax summary"
 *   contextData={{ period: "2024-01", companyId: "123" }}
 * >
 *   <TaxSummaryCard {...props} />
 * </ChateableWrapper>
 */
export function ChateableWrapper({
  message,
  contextData,
  onClick: additionalOnClick,
  className = '',
  disabled = false,
  children,
  uiComponent,
  entityId,
  entityType,
  as = 'div',
}: ChateableWrapperProps) {
  const generateMessage = useCallback((): string => {
    if (typeof message === 'function') {
      return message(contextData || {});
    }
    return message;
  }, [message, contextData]);

  const handleClick = useCallback(() => {
    if (disabled) {
      return;
    }

    // Call additional onClick handler if provided
    if (additionalOnClick) {
      additionalOnClick();
    }

    // Generate the message
    const messageText = generateMessage();

    // Build metadata if provided
    const metadata: Record<string, string> = {};
    if (uiComponent) metadata.ui_component = uiComponent;
    if (entityId) metadata.entity_id = entityId;
    if (entityType) metadata.entity_type = entityType;

    // Send message via custom event to ChatKit panel
    const event = new CustomEvent('chatkit:sendMessage', {
      detail: {
        message: messageText,
        metadata: Object.keys(metadata).length > 0 ? metadata : undefined,
      },
    });
    window.dispatchEvent(event);

    console.log('[ChateableWrapper] Sent message via event:', messageText, metadata);
  }, [disabled, additionalOnClick, generateMessage, uiComponent, entityId, entityType]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      // Support Enter and Space for accessibility
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();

        if (disabled) {
          return;
        }

        if (additionalOnClick) {
          additionalOnClick();
        }

        const messageText = generateMessage();
        const metadata: Record<string, string> = {};
        if (uiComponent) metadata.ui_component = uiComponent;
        if (entityId) metadata.entity_id = entityId;
        if (entityType) metadata.entity_type = entityType;

        // Send message via custom event to ChatKit panel
        const event = new CustomEvent('chatkit:sendMessage', {
          detail: {
            message: messageText,
            metadata: Object.keys(metadata).length > 0 ? metadata : undefined,
          },
        });
        window.dispatchEvent(event);

        console.log('[ChateableWrapper] Sent message via event (keyboard):', messageText, metadata);
      }
    },
    [disabled, additionalOnClick, generateMessage, uiComponent, entityId, entityType]
  );

  // When using fragment mode, attach event handlers directly to the child element
  if (as === 'fragment') {
    if (!isValidElement(children)) {
      console.warn('ChateableWrapper: "as=fragment" requires a single valid React element as children');
      return <>{children}</>;
    }

    // Get original props safely
    const originalProps = children.props as any;
    const originalOnClick = originalProps?.onClick;
    const originalOnKeyDown = originalProps?.onKeyDown;
    const originalRole = originalProps?.role;
    const originalTabIndex = originalProps?.tabIndex;
    const originalClassName = originalProps?.className || '';

    // Clone the child element and attach our handlers
    return cloneElement(children, {
      onClick: (e: React.MouseEvent) => {
        handleClick();
        // Call original onClick if it exists
        if (originalOnClick) {
          originalOnClick(e);
        }
      },
      onKeyDown: (e: React.KeyboardEvent) => {
        handleKeyDown(e);
        // Call original onKeyDown if it exists
        if (originalOnKeyDown) {
          originalOnKeyDown(e);
        }
      },
      role: originalRole || 'button',
      tabIndex: disabled ? -1 : (originalTabIndex ?? 0),
      'aria-disabled': disabled,
      className: `chateable-wrapper ${originalClassName}`.trim(),
    } as any);
  }

  // Default behavior: wrap in div
  const combinedClassName = `chateable-wrapper ${className}`.trim();
  const Component = as as any;

  return (
    <Component
      className={combinedClassName}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      role="button"
      tabIndex={disabled ? -1 : 0}
      aria-disabled={disabled}
    >
      {children}
    </Component>
  );
}
