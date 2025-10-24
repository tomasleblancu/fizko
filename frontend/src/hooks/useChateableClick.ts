import { useCallback } from 'react';
import { useChat } from '../contexts/ChatContext';
import type { ChateableClickOptions, ChateableClickReturn } from '../types/chateable';

/**
 * Hook to make any element chateable (clickable to send a message to the chat).
 * Returns props to spread on the target element.
 *
 * @example
 * const chateableProps = useChateableClick({
 *   message: "Explain this tax amount",
 *   contextData: { amount: 1000, period: "2024-01" }
 * });
 *
 * return <div {...chateableProps}>Click me</div>;
 */
export function useChateableClick(options: ChateableClickOptions): ChateableClickReturn {
  const { message, contextData, onClick: additionalOnClick, disabled = false, uiComponent } = options;
  const { sendUserMessage, isReady } = useChat();

  const generateMessage = useCallback((): string => {
    if (typeof message === 'function') {
      return message(contextData || {});
    }
    return message;
  }, [message, contextData]);

  const handleClick = useCallback(
    (e: React.MouseEvent) => {
      // Prevent event propagation to avoid triggering parent chateables
      e.stopPropagation();

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
    },
    [disabled, isReady, sendUserMessage, additionalOnClick, generateMessage, uiComponent]
  );

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      // Support Enter and Space for accessibility
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        e.stopPropagation();

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

  return {
    onClick: handleClick,
    className: 'chateable-element',
    role: 'button',
    tabIndex: disabled ? -1 : 0,
    onKeyDown: handleKeyDown,
  };
}
