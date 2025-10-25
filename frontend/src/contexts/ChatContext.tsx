import React, { createContext, useContext, useState, useCallback } from 'react';

interface ChatContextType {
  sendUserMessage: ((text: string, metadata?: Record<string, any>) => Promise<void>) | null;
  isReady: boolean;
  setSendUserMessage: (fn: (text: string, metadata?: Record<string, any>) => Promise<void>) => void;
  onChateableClick: (() => void) | null;
  setOnChateableClick: (fn: () => void) => void;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export function ChatProvider({ children }: { children: React.ReactNode }) {
  const [sendUserMessage, setSendUserMessageState] = useState<
    ((text: string, metadata?: Record<string, any>) => Promise<void>) | null
  >(null);
  const [onChateableClick, setOnChateableClickState] = useState<(() => void) | null>(null);

  const setSendUserMessage = useCallback((fn: (text: string, metadata?: Record<string, any>) => Promise<void>) => {
    setSendUserMessageState(() => fn);
  }, []);

  const setOnChateableClick = useCallback((fn: () => void) => {
    setOnChateableClickState(() => fn);
  }, []);

  const value: ChatContextType = {
    sendUserMessage,
    isReady: sendUserMessage !== null,
    setSendUserMessage,
    onChateableClick,
    setOnChateableClick,
  };

  return <ChatContext.Provider value={value}>{children}</ChatContext.Provider>;
}

export function useChat() {
  const context = useContext(ChatContext);
  if (context === undefined) {
    throw new Error('useChat must be used within a ChatProvider');
  }
  return context;
}
