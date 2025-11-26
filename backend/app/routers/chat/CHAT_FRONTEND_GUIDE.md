# Chat API - Guía de Implementación Frontend

Documentación completa para implementar el chat en aplicaciones React Native/Expo.

## 📋 Tabla de Contenidos

- [Descripción General](#descripción-general)
- [Endpoints Disponibles](#endpoints-disponibles)
- [Implementación en Expo/React Native](#implementación-en-exporeact-native)
- [Manejo de Streaming (SSE)](#manejo-de-streaming-sse)
- [Gestión de Estado](#gestión-de-estado)
- [Ejemplos Completos](#ejemplos-completos)
- [Best Practices](#best-practices)

---

## Descripción General

El Chat API proporciona dos endpoints para comunicación con el sistema de agentes AI:

- **Streaming (SSE)**: Para respuestas en tiempo real con mejor UX
- **Blocking**: Para respuestas completas más simples

**Características:**

✅ Sistema multi-agente (Supervisor → Agentes especializados)
✅ Memoria conversacional por thread
✅ Soporte para contexto de empresa
✅ Sin autenticación requerida (por ahora)
✅ Streaming con Server-Sent Events

---

## Endpoints Disponibles

### 1. POST /api/chat/stream (Recomendado)

Streaming con Server-Sent Events para respuestas en tiempo real.

**URL:** `http://localhost:8000/api/chat/stream`

**Request Body:**
```json
{
  "message": "¿Cuáles son mis documentos pendientes?",
  "thread_id": "thread_abc123",  // Opcional - se autogenera
  "company_id": "company_xyz",    // Opcional
  "metadata": {}                  // Opcional
}
```

**Response (SSE Stream):**
```javascript
// Evento 1: Inicio
data: {"type": "start", "thread_id": "thread_abc123", "timestamp": 1234567890}

// Evento 2-N: Contenido (chunks de texto)
data: {"type": "content", "content": "Tus documentos "}
data: {"type": "content", "content": "pendientes son..."}

// Evento opcional: Llamada a herramienta
data: {"type": "tool_call", "tool_name": "get_tax_documents"}

// Evento final: Completado
data: {"type": "done", "thread_id": "thread_abc123", "elapsed_ms": 2500}

// Evento de error (si ocurre)
data: {"type": "error", "content": "Mensaje de error", "error": "detalle técnico"}
```

### 2. POST /api/chat (Alternativa Blocking)

Respuesta completa sin streaming.

**URL:** `http://localhost:8000/api/chat`

**Request Body:**
```json
{
  "message": "¿Cuál es mi RUT?",
  "thread_id": "thread_abc123",
  "company_id": "company_xyz",
  "metadata": {}
}
```

**Response (JSON):**
```json
{
  "response": "Tu RUT es 12.345.678-9 según la información registrada.",
  "thread_id": "thread_abc123",
  "metadata": {
    "elapsed_ms": 1500,
    "char_count": 57
  }
}
```

---

## Implementación en Expo/React Native

### Instalación de Dependencias

```bash
# Para streaming SSE
npm install eventsource-parser

# Para gestión de estado (opcional pero recomendado)
npm install zustand
```

### Hook Personalizado para Chat Streaming

```typescript
// hooks/useChat.ts
import { useState, useCallback } from 'react';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: number;
}

interface UseChatOptions {
  apiUrl?: string;
  threadId?: string;
  companyId?: string;
}

export const useChat = (options: UseChatOptions = {}) => {
  const {
    apiUrl = 'http://localhost:8000/api/chat/stream',
    threadId: initialThreadId,
    companyId,
  } = options;

  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [threadId, setThreadId] = useState<string | undefined>(initialThreadId);

  const sendMessage = useCallback(async (userMessage: string) => {
    // Agregar mensaje del usuario
    const userMsg: Message = {
      id: `user_${Date.now()}`,
      role: 'user',
      content: userMessage,
      timestamp: Date.now(),
    };

    setMessages(prev => [...prev, userMsg]);
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: userMessage,
          thread_id: threadId,
          company_id: companyId,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      // Procesar stream
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      let assistantContent = '';
      const assistantMsg: Message = {
        id: `assistant_${Date.now()}`,
        role: 'assistant',
        content: '',
        timestamp: Date.now(),
      };

      // Agregar mensaje vacío del asistente
      setMessages(prev => [...prev, assistantMsg]);

      while (reader) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));

              switch (data.type) {
                case 'start':
                  // Guardar thread_id
                  if (data.thread_id && !threadId) {
                    setThreadId(data.thread_id);
                  }
                  break;

                case 'content':
                  // Acumular contenido
                  assistantContent += data.content;
                  setMessages(prev =>
                    prev.map(msg =>
                      msg.id === assistantMsg.id
                        ? { ...msg, content: assistantContent }
                        : msg
                    )
                  );
                  break;

                case 'tool_call':
                  console.log('🔧 Tool called:', data.tool_name);
                  break;

                case 'done':
                  console.log('✅ Completed in', data.elapsed_ms, 'ms');
                  setIsLoading(false);
                  break;

                case 'error':
                  throw new Error(data.content || data.error);
              }
            } catch (parseError) {
              console.warn('Failed to parse SSE data:', parseError);
            }
          }
        }
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error desconocido';
      setError(errorMessage);
      setIsLoading(false);

      // Agregar mensaje de error
      setMessages(prev => [
        ...prev,
        {
          id: `error_${Date.now()}`,
          role: 'assistant',
          content: `❌ Error: ${errorMessage}`,
          timestamp: Date.now(),
        },
      ]);
    }
  }, [apiUrl, threadId, companyId]);

  const clearMessages = useCallback(() => {
    setMessages([]);
    setThreadId(undefined);
    setError(null);
  }, []);

  return {
    messages,
    isLoading,
    error,
    threadId,
    sendMessage,
    clearMessages,
  };
};
```

---

## Manejo de Streaming (SSE)

### Implementación Nativa (sin librerías)

```typescript
// services/chatService.ts
export interface ChatStreamEvent {
  type: 'start' | 'content' | 'tool_call' | 'done' | 'error';
  content?: string;
  thread_id?: string;
  tool_name?: string;
  elapsed_ms?: number;
  error?: string;
  timestamp?: number;
}

export async function streamChat(
  message: string,
  options: {
    threadId?: string;
    companyId?: string;
    onEvent: (event: ChatStreamEvent) => void;
    onError?: (error: Error) => void;
    onComplete?: () => void;
  }
): Promise<void> {
  const { threadId, companyId, onEvent, onError, onComplete } = options;

  try {
    const response = await fetch('http://localhost:8000/api/chat/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message,
        thread_id: threadId,
        company_id: companyId,
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error('No reader available');
    }

    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();

      if (done) {
        onComplete?.();
        break;
      }

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');

      // Guardar la última línea incompleta
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const event = JSON.parse(line.slice(6)) as ChatStreamEvent;
            onEvent(event);
          } catch (parseError) {
            console.warn('Failed to parse SSE line:', line, parseError);
          }
        }
      }
    }
  } catch (error) {
    onError?.(error instanceof Error ? error : new Error(String(error)));
  }
}
```

### Uso del Servicio de Streaming

```typescript
// En tu componente
import { streamChat } from './services/chatService';

const [responseText, setResponseText] = useState('');
const [isStreaming, setIsStreaming] = useState(false);

const handleSendMessage = async (message: string) => {
  setIsStreaming(true);
  setResponseText('');

  await streamChat(message, {
    threadId: currentThreadId,
    companyId: selectedCompanyId,

    onEvent: (event) => {
      switch (event.type) {
        case 'start':
          console.log('Stream started:', event.thread_id);
          break;

        case 'content':
          setResponseText(prev => prev + event.content);
          break;

        case 'tool_call':
          console.log('Tool called:', event.tool_name);
          break;

        case 'done':
          console.log('Completed in', event.elapsed_ms, 'ms');
          break;

        case 'error':
          console.error('Stream error:', event.error);
          break;
      }
    },

    onError: (error) => {
      console.error('Connection error:', error);
      setIsStreaming(false);
    },

    onComplete: () => {
      setIsStreaming(false);
    },
  });
};
```

---

## Gestión de Estado

### Store con Zustand (Recomendado)

```typescript
// store/chatStore.ts
import { create } from 'zustand';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: number;
}

interface ChatState {
  // Estado
  messages: Message[];
  threadId: string | null;
  isLoading: boolean;
  error: string | null;

  // Acciones
  addMessage: (message: Omit<Message, 'id' | 'timestamp'>) => void;
  updateLastMessage: (content: string) => void;
  setThreadId: (threadId: string) => void;
  setLoading: (isLoading: boolean) => void;
  setError: (error: string | null) => void;
  clearChat: () => void;
}

export const useChatStore = create<ChatState>((set) => ({
  // Estado inicial
  messages: [],
  threadId: null,
  isLoading: false,
  error: null,

  // Acciones
  addMessage: (message) =>
    set((state) => ({
      messages: [
        ...state.messages,
        {
          ...message,
          id: `${message.role}_${Date.now()}`,
          timestamp: Date.now(),
        },
      ],
    })),

  updateLastMessage: (content) =>
    set((state) => ({
      messages: state.messages.map((msg, idx) =>
        idx === state.messages.length - 1 ? { ...msg, content } : msg
      ),
    })),

  setThreadId: (threadId) => set({ threadId }),

  setLoading: (isLoading) => set({ isLoading }),

  setError: (error) => set({ error }),

  clearChat: () =>
    set({
      messages: [],
      threadId: null,
      isLoading: false,
      error: null,
    }),
}));
```

### Uso del Store

```typescript
// screens/ChatScreen.tsx
import { useChatStore } from '../store/chatStore';
import { streamChat } from '../services/chatService';

export function ChatScreen() {
  const {
    messages,
    threadId,
    isLoading,
    addMessage,
    updateLastMessage,
    setThreadId,
    setLoading,
    setError,
  } = useChatStore();

  const handleSend = async (text: string) => {
    // Agregar mensaje del usuario
    addMessage({ role: 'user', content: text });

    // Agregar mensaje vacío del asistente
    addMessage({ role: 'assistant', content: '' });

    setLoading(true);
    setError(null);

    await streamChat(text, {
      threadId: threadId || undefined,

      onEvent: (event) => {
        if (event.type === 'start' && event.thread_id) {
          setThreadId(event.thread_id);
        } else if (event.type === 'content') {
          updateLastMessage(prev => prev + event.content!);
        } else if (event.type === 'done') {
          setLoading(false);
        } else if (event.type === 'error') {
          setError(event.content || event.error || 'Error desconocido');
          setLoading(false);
        }
      },

      onError: (error) => {
        setError(error.message);
        setLoading(false);
      },
    });
  };

  return (
    <View>
      {/* Renderizar mensajes, input, etc. */}
    </View>
  );
}
```

---

## Ejemplos Completos

### Componente Chat Completo

```typescript
// components/ChatInterface.tsx
import React, { useState, useRef, useEffect } from 'react';
import {
  View,
  TextInput,
  FlatList,
  TouchableOpacity,
  Text,
  StyleSheet,
  ActivityIndicator,
} from 'react-native';
import { useChat } from '../hooks/useChat';

export function ChatInterface({ companyId }: { companyId?: string }) {
  const [inputText, setInputText] = useState('');
  const flatListRef = useRef<FlatList>(null);

  const { messages, isLoading, sendMessage } = useChat({
    companyId,
  });

  // Auto-scroll al final cuando lleguen nuevos mensajes
  useEffect(() => {
    flatListRef.current?.scrollToEnd({ animated: true });
  }, [messages]);

  const handleSend = async () => {
    if (inputText.trim() && !isLoading) {
      await sendMessage(inputText.trim());
      setInputText('');
    }
  };

  return (
    <View style={styles.container}>
      {/* Lista de mensajes */}
      <FlatList
        ref={flatListRef}
        data={messages}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => (
          <View
            style={[
              styles.messageBubble,
              item.role === 'user' ? styles.userBubble : styles.assistantBubble,
            ]}
          >
            <Text
              style={[
                styles.messageText,
                item.role === 'user' ? styles.userText : styles.assistantText,
              ]}
            >
              {item.content}
            </Text>
          </View>
        )}
        contentContainerStyle={styles.messageList}
      />

      {/* Loading indicator */}
      {isLoading && (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="small" color="#007AFF" />
          <Text style={styles.loadingText}>Escribiendo...</Text>
        </View>
      )}

      {/* Input de texto */}
      <View style={styles.inputContainer}>
        <TextInput
          style={styles.input}
          value={inputText}
          onChangeText={setInputText}
          placeholder="Escribe un mensaje..."
          multiline
          editable={!isLoading}
        />
        <TouchableOpacity
          style={[styles.sendButton, isLoading && styles.sendButtonDisabled]}
          onPress={handleSend}
          disabled={isLoading || !inputText.trim()}
        >
          <Text style={styles.sendButtonText}>Enviar</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F5F5',
  },
  messageList: {
    padding: 16,
  },
  messageBubble: {
    maxWidth: '80%',
    padding: 12,
    borderRadius: 16,
    marginBottom: 8,
  },
  userBubble: {
    alignSelf: 'flex-end',
    backgroundColor: '#007AFF',
  },
  assistantBubble: {
    alignSelf: 'flex-start',
    backgroundColor: '#FFFFFF',
  },
  messageText: {
    fontSize: 16,
  },
  userText: {
    color: '#FFFFFF',
  },
  assistantText: {
    color: '#000000',
  },
  loadingContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    gap: 8,
  },
  loadingText: {
    color: '#666',
    fontSize: 14,
  },
  inputContainer: {
    flexDirection: 'row',
    padding: 16,
    backgroundColor: '#FFFFFF',
    borderTopWidth: 1,
    borderTopColor: '#E0E0E0',
  },
  input: {
    flex: 1,
    backgroundColor: '#F5F5F5',
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 8,
    maxHeight: 100,
    marginRight: 8,
  },
  sendButton: {
    backgroundColor: '#007AFF',
    borderRadius: 20,
    paddingHorizontal: 20,
    paddingVertical: 10,
    justifyContent: 'center',
  },
  sendButtonDisabled: {
    opacity: 0.5,
  },
  sendButtonText: {
    color: '#FFFFFF',
    fontWeight: '600',
  },
});
```

---

## Best Practices

### 1. **Manejo de Errores**

```typescript
try {
  await sendMessage(text);
} catch (error) {
  if (error.message.includes('network')) {
    Alert.alert('Error de conexión', 'Verifica tu conexión a internet');
  } else if (error.message.includes('timeout')) {
    Alert.alert('Tiempo agotado', 'La solicitud tardó demasiado');
  } else {
    Alert.alert('Error', 'Ocurrió un problema. Intenta de nuevo.');
  }
}
```

### 2. **Persistencia de Thread ID**

```typescript
import AsyncStorage from '@react-native-async-storage/async-storage';

// Guardar
await AsyncStorage.setItem('chat_thread_id', threadId);

// Cargar
const savedThreadId = await AsyncStorage.getItem('chat_thread_id');
```

### 3. **Cancelación de Requests**

```typescript
const abortController = new AbortController();

fetch(url, {
  signal: abortController.signal,
  // ...
});

// Para cancelar
abortController.abort();
```

### 4. **Retry Logic**

```typescript
async function sendWithRetry(message: string, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await sendMessage(message);
    } catch (error) {
      if (i === maxRetries - 1) throw error;
      await new Promise(resolve => setTimeout(resolve, 1000 * Math.pow(2, i)));
    }
  }
}
```

### 5. **Typing Indicators**

```typescript
const [isTyping, setIsTyping] = useState(false);

// Cuando empieza el stream
onEvent: (event) => {
  if (event.type === 'start') {
    setIsTyping(true);
  } else if (event.type === 'done') {
    setIsTyping(false);
  }
}
```

---

## Variables de Entorno

```bash
# .env
EXPO_PUBLIC_API_URL=http://localhost:8000
EXPO_PUBLIC_CHAT_STREAM_URL=http://localhost:8000/api/chat/stream
EXPO_PUBLIC_CHAT_URL=http://localhost:8000/api/chat
```

```typescript
// Uso
const API_URL = process.env.EXPO_PUBLIC_CHAT_STREAM_URL;
```

---

## Debugging

### Logs Útiles

```typescript
// En el hook useChat
console.log('📤 Sending:', { message, threadId, companyId });
console.log('📥 Received event:', event.type, event);
console.log('✅ Stream complete');
console.log('❌ Error:', error);
```

### Network Inspector

```typescript
// React Native Debugger
// Cmd+D (iOS) / Cmd+M (Android) → Debug

// O usa Reactotron
import Reactotron from 'reactotron-react-native';

Reactotron.log('Chat event:', event);
```

---

## FAQ

**Q: ¿Cómo manejo mensajes largos?**
A: El streaming SSE maneja automáticamente mensajes de cualquier longitud. Solo actualiza el estado con cada chunk.

**Q: ¿Puedo usar WebSockets?**
A: Por ahora solo SSE está disponible. WebSockets pueden agregarse en el futuro.

**Q: ¿Se guarda el historial?**
A: El thread_id mantiene el contexto conversacional. Persiste el thread_id para retomar conversaciones.

**Q: ¿Hay límite de mensajes?**
A: No hay límite técnico, pero considera la memoria del dispositivo para historiales muy largos.

**Q: ¿Funciona offline?**
A: No. Requiere conexión a internet. Implementa retry logic para manejar desconexiones.

---

## Próximos Pasos

- [ ] Autenticación JWT
- [ ] Soporte para adjuntos/imágenes
- [ ] Notificaciones push
- [ ] Modo offline con queue
- [ ] WebSocket support

---

## Soporte

Si tienes problemas:

1. Revisa los logs del backend
2. Verifica la URL del API
3. Comprueba la conexión de red
4. Revisa la documentación del backend en `/api/docs`

**Contacto:** [Tu equipo de desarrollo]
