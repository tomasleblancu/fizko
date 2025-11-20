/**
 * ChatKit Panel Component
 *
 * Renders the ChatKit UI with Fizko agent system integration.
 */

'use client';

import { useCallback, useMemo, useEffect, useRef } from 'react';
import { ChatKit, useChatKit } from '@openai/chatkit-react';
import { useTheme } from 'next-themes';
import { createClient } from '@/lib/supabase/client';

export interface ChatKitPanelProps {
  companyId?: string;
  className?: string;
}

/**
 * ChatKit Panel Component
 */
export function ChatKitPanel({ companyId, className }: ChatKitPanelProps) {
  const { theme: systemTheme } = useTheme();
  const supabase = createClient();

  // Store pending metadata for next message
  const pendingMetadataRef = useRef<Record<string, string> | null>(null);

  // Determine effective theme (light or dark)
  const theme = systemTheme === 'dark' ? 'dark' : 'light';

  // Memoize theme configuration
  const themeConfig = useMemo(
    () => ({
      colorScheme: theme,
      color: {
        grayscale: {
          hue: 220,
          tint: 6,
          shade: theme === 'dark' ? -1 : -4,
        },
        accent: {
          primary: theme === 'dark' ? '#f1f5f9' : '#0f172a',
          level: 1,
        },
      },
      radius: 'round' as const,
      typography: {
        baseSize: 16,
        fontFamily: 'Questrial, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
        fontFamilyMono: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace',
        fontSources: [
          {
            family: 'Questrial',
            src: 'https://fonts.gstatic.com/s/questrial/v19/QdVUSTchPBm7nuUeVf7EuQ.ttf',
            weight: '400',
            style: 'normal',
            display: 'swap',
          },
        ],
      },
    }),
    [theme]
  );

  // Memoize start screen configuration
  const startScreenConfig = useMemo(
    () => ({
      greeting: 'Fizko',
      prompts: [
        {
          label: 'Quiero agregar un gasto',
          prompt: 'Quiero registrar un gasto manual',
          icon: 'notebook-pencil',
        },
        {
          label: 'Dame un resumen de ventas',
          prompt: 'Muéstrame un resumen de las ventas del mes',
          icon: 'notebook',
        },
        {
          label: 'Agrega un nuevo colaborador',
          prompt: 'Quiero agregar un nuevo colaborador a la nómina',
          icon: 'user',
        },
        {
          label: 'Quiero darte feedback',
          prompt: 'Quiero reportar un problema o darte feedback sobre la plataforma',
          icon: 'circle-question',
        },
      ],
    }),
    []
  );

  // Memoize composer configuration
  const composerConfig = useMemo(
    () => ({
      placeholder: 'Pregúntame sobre impuestos, facturas, F29...',
      attachments: {
        enabled: true,
        maxCount: 5,
        maxSize: 10485760, // 10MB
        accept: {
          'image/png': ['.png'],
          'image/jpeg': ['.jpg', '.jpeg'],
          'image/gif': ['.gif'],
          'image/webp': ['.webp'],
          'application/pdf': ['.pdf'],
        },
      },
    }),
    []
  );

  // Memoize thread item actions config
  const threadItemActionsConfig = useMemo(
    () => ({
      feedback: false,
    }),
    []
  );

  // Custom fetch function with auth headers and metadata injection
  const customFetch = useCallback(
    async (input: RequestInfo | URL, init?: RequestInit) => {
      const headers = new Headers(init?.headers);

      // Get current session
      const { data: { session } } = await supabase.auth.getSession();

      if (session?.access_token) {
        headers.set('Authorization', `Bearer ${session.access_token}`);
      }

      // Inject metadata into URL query params for create_message operations
      let finalInput = input;
      if (init?.method === 'POST' && pendingMetadataRef.current) {
        // Parse URL (preserving existing query params)
        const inputStr = typeof input === 'string' ? input : input.toString();
        const url = inputStr.startsWith('http')
          ? new URL(inputStr)
          : new URL(inputStr, window.location.origin);

        // Add metadata as query params (preserves existing params)
        Object.entries(pendingMetadataRef.current).forEach(([key, value]) => {
          url.searchParams.set(key, value);
        });

        finalInput = url.toString();

        console.log('[ChatKitPanel] Injected metadata into URL:', url.toString());

        // Clear pending metadata after use
        pendingMetadataRef.current = null;
      }

      return fetch(finalInput, {
        ...init,
        headers: Object.fromEntries(headers.entries()),
      });
    },
    [supabase]
  );

  // Build API URL with company_id
  const apiUrl = useMemo(() => {
    const params = new URLSearchParams();
    if (companyId) {
      params.set('company_id', companyId);
    }
    return `/api/chatkit?${params.toString()}`;
  }, [companyId]);

  // Event handlers
  const handleResponseEnd = useCallback(() => {
    console.log('[ChatKitPanel] Response ended');
  }, []);

  const handleResponseStart = useCallback(() => {
    console.log('[ChatKitPanel] Response started');
  }, []);

  const handleError = useCallback(({ error }: { error: unknown }) => {
    console.error('[ChatKitPanel] Error:', error);
  }, []);

  const handleThreadChange = useCallback(() => {
    console.log('[ChatKitPanel] Thread changed');
  }, []);

  // ChatKit configuration - Advanced integration mode
  // We use 'url' + 'domainKey' to proxy all ChatKit operations through our backend
  // This allows us to use our own Agents SDK instead of OpenAI Agent Builder
  const chatkit = useChatKit({
    api: {
      url: apiUrl,
      domainKey: 'domain_pk_localhost_dev', // For local dev
      fetch: customFetch,
      uploadStrategy: { type: 'two_phase' },
    },
    locale: 'es-ES',
    theme: themeConfig,
    startScreen: startScreenConfig,
    composer: composerConfig,
    threadItemActions: threadItemActionsConfig,
    onResponseEnd: handleResponseEnd,
    onResponseStart: handleResponseStart,
    onError: handleError,
    onThreadChange: handleThreadChange,
  });

  // Listen for chateable click events from dashboard
  useEffect(() => {
    const handleChateableMessage = (event: CustomEvent) => {
      const { message, metadata } = event.detail;

      if (chatkit && message) {
        console.log('[ChatKitPanel] Received chateable message:', message, metadata);

        // Store metadata in ref so customFetch can inject it into the next POST request
        if (metadata && Object.keys(metadata).length > 0) {
          pendingMetadataRef.current = metadata;
          console.log('[ChatKitPanel] Stored metadata for next request:', metadata);
        }

        // Use sendUserMessage method directly on chatkit object
        if (typeof chatkit.sendUserMessage === 'function') {
          console.log('[ChatKitPanel] Sending message via sendUserMessage');
          chatkit.sendUserMessage({
            text: message,
          });
        } else {
          console.error('[ChatKitPanel] sendUserMessage method not found');
          console.error('[ChatKitPanel] ChatKit object keys:', Object.keys(chatkit));
        }
      }
    };

    // Add event listener
    window.addEventListener('chatkit:sendMessage' as any, handleChateableMessage as EventListener);

    // Cleanup
    return () => {
      window.removeEventListener('chatkit:sendMessage' as any, handleChateableMessage as EventListener);
    };
  }, [chatkit]);

  // Render ChatKit
  return (
    <div className={`h-full ${className}`}>
      <ChatKit control={chatkit.control} />
    </div>
  );
}
