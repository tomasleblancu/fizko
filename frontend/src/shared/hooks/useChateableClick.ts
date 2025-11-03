import { useCallback } from 'react';
import { useChat } from "@/app/providers/ChatContext";
import type { ChateableClickOptions, ChateableClickReturn } from "@/shared/types/chateable";

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
  const { message, contextData, onClick: additionalOnClick, disabled = false, uiComponent, entityId, entityType } = options;
  const { sendUserMessage, isReady } = useChat();

  const generateMessage = useCallback((): string => {
    if (typeof message === 'function') {
      return message(contextData || {});
    }
    return message;
  }, [message, contextData]);

  const { onChateableClick } = useChat();

  const handleClick = useCallback(
    (e: React.MouseEvent) => {
      // Prevent event propagation to avoid triggering parent chateables
      e.stopPropagation();

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

      // Generate and send the message with ui_component, entity_id, and entity_type metadata
      const messageText = generateMessage();
      const metadata: Record<string, string> = {};
      if (uiComponent) metadata.ui_component = uiComponent;
      if (entityId) metadata.entity_id = entityId;
      if (entityType) metadata.entity_type = entityType;
      sendUserMessage(messageText, Object.keys(metadata).length > 0 ? metadata : undefined);
    },
    [disabled, isReady, sendUserMessage, additionalOnClick, generateMessage, uiComponent, entityId, entityType, onChateableClick]
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

        // Call chateable click callback (e.g., to close drawers)
        if (onChateableClick) {
          onChateableClick();
        }

        if (additionalOnClick) {
          additionalOnClick();
        }

        const messageText = generateMessage();
        const metadata: Record<string, string> = {};
        if (uiComponent) metadata.ui_component = uiComponent;
        if (entityId) metadata.entity_id = entityId;
        if (entityType) metadata.entity_type = entityType;
        sendUserMessage(messageText, Object.keys(metadata).length > 0 ? metadata : undefined);
      }
    },
    [disabled, isReady, sendUserMessage, additionalOnClick, generateMessage, uiComponent, entityId, entityType, onChateableClick]
  );

  return {
    onClick: handleClick,
    className: 'chateable-element',
    role: 'button',
    tabIndex: disabled ? -1 : 0,
    onKeyDown: handleKeyDown,
  };
}
