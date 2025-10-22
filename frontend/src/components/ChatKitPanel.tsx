import { useRef, useMemo, useEffect, useCallback, useState } from "react";
import { ChatKit, useChatKit } from "@openai/chatkit-react";
import {
  CHATKIT_API_URL,
  CHATKIT_API_DOMAIN_KEY,
  STARTER_PROMPTS,
  PLACEHOLDER_INPUT,
  GREETING,
} from "../lib/config";
import { ErrorOverlay } from "./ErrorOverlay";
import { useAuth } from "../contexts/AuthContext";
import type { ColorScheme } from "../hooks/useColorScheme";

type ChatKitPanelProps = {
  theme: ColorScheme;
  onResponseEnd: () => void;
  onThemeRequest: (scheme: ColorScheme) => void;
  onSendMessageReady?: (sendMessage: (text: string, metadata?: Record<string, any>) => Promise<void>) => void;
  currentCompanyId?: string | null;
  onCompanyIdChange?: (companyId: string | null) => void;
};

type ErrorState = {
  script: string | null;
  session: string | null;
  integration: string | null;
  retryable: boolean;
};

const isBrowser = typeof window !== "undefined";
const isDev = import.meta.env.DEV;
const MIN_LOADING_TIME = 800; // Minimum loading time in milliseconds

const createInitialErrors = (): ErrorState => ({
  script: null,
  session: null,
  integration: null,
  retryable: false,
});

export function ChatKitPanel({
  theme,
  onResponseEnd,
  onThemeRequest,
  onSendMessageReady,
  currentCompanyId,
  onCompanyIdChange,
}: ChatKitPanelProps) {
  const { session } = useAuth();
  const [errors, setErrors] = useState<ErrorState>(() => createInitialErrors());
  const [isInitializingSession, setIsInitializingSession] = useState(false);
  const loadingStartTimeRef = useRef<number>(Date.now());
  const isMountedRef = useRef(true);
  const [scriptStatus, setScriptStatus] = useState<"pending" | "ready" | "error">(() =>
    isBrowser && window.customElements?.get("openai-chatkit") ? "ready" : "pending"
  );
  const [widgetInstanceKey, setWidgetInstanceKey] = useState(0);

  const setErrorState = useCallback((updates: Partial<ErrorState>) => {
    setErrors((current) => ({ ...current, ...updates }));
  }, []);

  const finishLoading = useCallback(() => {
    const elapsed = Date.now() - loadingStartTimeRef.current;
    const remainingTime = Math.max(0, MIN_LOADING_TIME - elapsed);

    if (remainingTime > 0) {
      setTimeout(() => {
        if (isMountedRef.current) {
          setIsInitializingSession(false);
        }
      }, remainingTime);
    } else {
      setIsInitializingSession(false);
    }
  }, []);

  useEffect(() => {
    return () => {
      isMountedRef.current = false;
    };
  }, []);

  // Monitor chatkit.js script loading
  useEffect(() => {
    if (!isBrowser) {
      return;
    }

    let timeoutId: number | undefined;

    const handleLoaded = () => {
      if (!isMountedRef.current) return;
      console.log('[ChatKitPanel] Script loaded successfully');
      setScriptStatus("ready");
      setErrorState({ script: null });
    };

    const handleError = (event: Event) => {
      console.error("Failed to load chatkit.js", event);
      if (!isMountedRef.current) return;
      setScriptStatus("error");
      const detail = (event as CustomEvent<unknown>)?.detail ?? "unknown error";
      setErrorState({ script: `Error: ${detail}`, retryable: false });
      finishLoading();
    };

    window.addEventListener("chatkit-script-loaded", handleLoaded);
    window.addEventListener("chatkit-script-error", handleError as EventListener);

    if (window.customElements?.get("openai-chatkit")) {
      handleLoaded();
    } else if (scriptStatus === "pending") {
      timeoutId = window.setTimeout(() => {
        if (!window.customElements?.get("openai-chatkit")) {
          handleError(
            new CustomEvent("chatkit-script-error", {
              detail: "ChatKit web component is unavailable. Verify that the script URL is reachable.",
            })
          );
        }
      }, 5000);
    }

    return () => {
      window.removeEventListener("chatkit-script-loaded", handleLoaded);
      window.removeEventListener("chatkit-script-error", handleError as EventListener);
      if (timeoutId) {
        window.clearTimeout(timeoutId);
      }
    };
  }, [scriptStatus, setErrorState, finishLoading]);

  const handleResetChat = useCallback(() => {
    console.log('[ChatKitPanel] Resetting chat');
    if (isBrowser) {
      setScriptStatus(window.customElements?.get("openai-chatkit") ? "ready" : "pending");
    }
    loadingStartTimeRef.current = Date.now();
    setIsInitializingSession(true);
    setErrors(createInitialErrors());
    setWidgetInstanceKey((prev) => prev + 1);
  }, []);

  // Create custom fetch function with auth headers
  const customFetch = useCallback(
    async (input: RequestInfo | URL, init?: RequestInit) => {
      const headers = new Headers(init?.headers);

      if (session?.access_token) {
        headers.set("Authorization", `Bearer ${session.access_token}`);
      }

      return fetch(input, {
        ...init,
        headers,
      });
    },
    [session?.access_token]
  );

  // Build API URL with current company_id
  const apiUrl = useMemo(() => {
    if (currentCompanyId) {
      const params = new URLSearchParams({ company_id: currentCompanyId });
      const url = `${CHATKIT_API_URL}?${params.toString()}`;
      console.log("[ChatKitPanel] API URL updated:", url);
      return url;
    }
    console.log("[ChatKitPanel] API URL (no company):", CHATKIT_API_URL);
    return CHATKIT_API_URL;
  }, [currentCompanyId]);

  // Memoize callbacks
  const handleClientTool = useCallback(
    async (invocation: any) => {
      if (invocation.name === "switch_theme") {
        const requested = invocation.params.theme;
        if (requested === "light" || requested === "dark") {
          if (isDev) {
            console.debug("[ChatKitPanel] switch_theme", requested);
          }
          onThemeRequest(requested);
          return { success: true };
        }
        return { success: false };
      }

      return { success: false };
    },
    [onThemeRequest]
  );

  const handleResponseEnd = useCallback(() => {
    console.log("[ChatKitPanel] handleResponseEnd called");
    setErrorState({ integration: null, retryable: false });
    finishLoading();
    onResponseEnd();
  }, [onResponseEnd, setErrorState, finishLoading]);

  const handleResponseStart = useCallback(() => {
    setErrorState({ integration: null, retryable: false });
  }, [setErrorState]);

  const handleThreadChange = useCallback((event: any) => {
    console.log("[ChatKitPanel] Thread changed:", event);
  }, []);

  const handleError = useCallback(
    ({ error }: { error: any }) => {
      console.error("ChatKit error", error);
      const detail = error instanceof Error ? error.message : "An error occurred";
      setErrorState({ integration: detail, retryable: true });
      finishLoading();
    },
    [setErrorState, finishLoading]
  );

  // Memoize theme configuration
  const themeConfig = useMemo(
    () => ({
      colorScheme: theme,
      color: {
        grayscale: {
          hue: 220,
          tint: 6,
          shade: theme === "dark" ? -1 : -4,
        },
        accent: {
          primary: theme === "dark" ? "#f1f5f9" : "#0f172a",
          level: 1,
        },
      },
      radius: "round" as const,
    }),
    [theme]
  );

  // Memoize static configurations
  const startScreenConfig = useMemo(
    () => ({
      greeting: GREETING,
      prompts: STARTER_PROMPTS,
    }),
    []
  );

  const composerConfig = useMemo(
    () => ({
      placeholder: PLACEHOLDER_INPUT,
      attachments: {
        enabled: true,
        maxCount: 5,
        maxSize: 10485760, // 10MB
        accept: {
          "image/png": [".png"],
          "image/jpeg": [".jpg", ".jpeg"],
          "image/gif": [".gif"],
          "image/webp": [".webp"],
          "application/pdf": [".pdf"],
        },
      },
    }),
    []
  );

  const threadItemActionsConfig = useMemo(
    () => ({
      feedback: false,
    }),
    []
  );

  const chatkit = useChatKit({
    api: {
      url: apiUrl,
      domainKey: CHATKIT_API_DOMAIN_KEY,
      fetch: customFetch,
      uploadStrategy: { type: "two_phase" },
    },
    theme: themeConfig,
    startScreen: startScreenConfig,
    composer: composerConfig,
    threadItemActions: threadItemActionsConfig,
    onClientTool: handleClientTool,
    onResponseEnd: handleResponseEnd,
    onResponseStart: handleResponseStart,
    onThreadChange: handleThreadChange,
    onError: handleError,
  });

  // Expose sendUserMessage to parent component
  useEffect(() => {
    if (onSendMessageReady && chatkit.sendUserMessage) {
      const sendMessage = async (text: string, _metadata?: Record<string, any>) => {
        await chatkit.sendUserMessage({
          text,
        });
      };
      onSendMessageReady(sendMessage);
    }
  }, [onSendMessageReady, chatkit.sendUserMessage]);

  // Listen for thread metadata changes to update company_id
  useEffect(() => {
    const thread = chatkit.control?.thread;
    if (thread?.metadata?.company_id) {
      const newCompanyId = thread.metadata.company_id;
      if (newCompanyId !== currentCompanyId && onCompanyIdChange) {
        onCompanyIdChange(newCompanyId);
      }
    }
  }, [chatkit.control?.thread, currentCompanyId, onCompanyIdChange]);

  const activeError = errors.session ?? errors.integration;
  const blockingError = errors.script ?? activeError;

  return (
    <div className="relative flex h-full w-full flex-col overflow-hidden bg-white shadow-lg transition-colors dark:bg-slate-900">
      <ChatKit
        key={`${widgetInstanceKey}-${currentCompanyId || "no-company"}`}
        control={chatkit.control}
        className={
          blockingError || isInitializingSession
            ? "pointer-events-none opacity-0"
            : "block h-full w-full"
        }
      />
      <ErrorOverlay
        error={blockingError}
        fallbackMessage={
          blockingError || !isInitializingSession ? null : "Cargando asistente..."
        }
        onRetry={blockingError && errors.retryable ? handleResetChat : null}
        retryLabel="Reiniciar chat"
      />
    </div>
  );
}
