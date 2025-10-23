import { useCallback } from 'react';
import { useChat } from '../contexts/ChatContext';
import type { ChateableWrapperProps } from '../types/chateable';
import '../styles/chateable.css';

/**
 * Wrapper component that makes its children chateable (clickable to send a message to chat).
 * Useful for wrapping entire cards or components.
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
}: ChateableWrapperProps) {
  const { sendUserMessage, isReady } = useChat();

  const generateMessage = useCallback((): string => {
    if (typeof message === 'function') {
      return message(contextData || {});
    }
    return message;
  }, [message, contextData]);

  const handleClick = useCallback(() => {
    if (disabled || !isReady || !sendUserMessage) {
      return;
    }

    // Call additional onClick handler if provided
    if (additionalOnClick) {
      additionalOnClick();
    }

    // Generate and send the message with ui_component metadata
    const messageText = generateMessage();
    const metadata = uiComponent ? { ui_component: uiComponent } : undefined;
    sendUserMessage(messageText, metadata);
  }, [disabled, isReady, sendUserMessage, additionalOnClick, generateMessage, uiComponent]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      // Support Enter and Space for accessibility
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();

        if (disabled || !isReady || !sendUserMessage) {
          return;
        }

        if (additionalOnClick) {
          additionalOnClick();
        }

        const messageText = generateMessage();
        const metadata = uiComponent ? { ui_component: uiComponent } : undefined;
        sendUserMessage(messageText, metadata);
      }
    },
    [disabled, isReady, sendUserMessage, additionalOnClick, generateMessage, uiComponent]
  );

  const combinedClassName = `chateable-wrapper ${className}`.trim();

  return (
    <div
      className={combinedClassName}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      role="button"
      tabIndex={disabled ? -1 : 0}
      aria-disabled={disabled}
    >
      {children}
    </div>
  );
}
