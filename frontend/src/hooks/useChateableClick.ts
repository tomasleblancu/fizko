import { useCallback } from 'react';
import type { ChateableClickOptions, ChateableClickReturn } from '@/types/chateable';

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

  // For now, chateable elements will just log until we integrate ChatKit provider properly
  // TODO: Wrap DashboardView in ChatKit provider context
  const chatKit = null;

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

      console.log('[Chateable] Sent message via event:', messageText, metadata);
    },
    [disabled, additionalOnClick, generateMessage, uiComponent, entityId, entityType]
  );

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      // Support Enter and Space for accessibility
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        e.stopPropagation();

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

        console.log('[Chateable] Sent message via event (keyboard):', messageText, metadata);
      }
    },
    [disabled, additionalOnClick, generateMessage, uiComponent, entityId, entityType]
  );

  return {
    onClick: handleClick,
    className: 'chateable-element',
    role: 'button',
    tabIndex: disabled ? -1 : 0,
    onKeyDown: handleKeyDown,
  };
}
