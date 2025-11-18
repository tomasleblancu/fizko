import { useCallback, cloneElement, isValidElement, Fragment } from 'react';
import { useChat } from "@/app/providers/ChatContext";
import { useHasActiveSubscription } from "@/shared/hooks/useSubscription";
import type { ChateableWrapperProps } from "@/shared/types/chateable";
import '@/app/styles/chateable.css';

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
  const { sendUserMessage, isReady } = useChat();
  const { hasActiveSubscription, subscription } = useHasActiveSubscription();

  const generateMessage = useCallback((): string => {
    if (typeof message === 'function') {
      return message(contextData || {});
    }
    return message;
  }, [message, contextData]);

  const { onChateableClick } = useChat();

  const handleClick = useCallback(() => {
    if (disabled || !isReady || !sendUserMessage) {
      return;
    }

    // Call chateable click callback (e.g., to close drawers)
    if (onChateableClick) {
      onChateableClick();
    }

    // Call additional onClick handler if provided
    if (additionalOnClick) {
      additionalOnClick();
    }

    // Check if user has active subscription
    if (!hasActiveSubscription) {
      // Send a message to the chat indicating user tried to use the feature
      sendUserMessage("Acabo de clickear algo pensando que me iba a dar más información!");
      return;
    }

    // Generate and send the message with metadata
    const messageText = generateMessage();
    const metadata: Record<string, any> = {};

    if (uiComponent) {
      metadata.ui_component = uiComponent;
    }
    if (entityId) {
      metadata.entity_id = entityId;
    }
    if (entityType) {
      metadata.entity_type = entityType;
    }

    sendUserMessage(messageText, Object.keys(metadata).length > 0 ? metadata : undefined);
  }, [disabled, isReady, sendUserMessage, additionalOnClick, generateMessage, uiComponent, entityId, entityType, onChateableClick, hasActiveSubscription]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      // Support Enter and Space for accessibility
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();

        if (disabled || !isReady || !sendUserMessage) {
          return;
        }

        // Call chateable click callback (e.g., to close drawers)
        if (onChateableClick) {
          onChateableClick();
        }

        if (additionalOnClick) {
          additionalOnClick();
        }

        // Check if user has active subscription
        if (!hasActiveSubscription) {
          // Send a message to the chat indicating user tried to use the feature
          sendUserMessage("Acabo de clickear algo pensando que me iba a dar más información!");
          return;
        }

        const messageText = generateMessage();
        const metadata: Record<string, any> = {};

        if (uiComponent) {
          metadata.ui_component = uiComponent;
        }
        if (entityId) {
          metadata.entity_id = entityId;
        }
        if (entityType) {
          metadata.entity_type = entityType;
        }

        sendUserMessage(messageText, Object.keys(metadata).length > 0 ? metadata : undefined);
      }
    },
    [disabled, isReady, sendUserMessage, additionalOnClick, generateMessage, uiComponent, entityId, entityType, onChateableClick, hasActiveSubscription]
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
