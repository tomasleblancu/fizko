# Quick Start - Chat en Expo

Implementación rápida del chat para tu app Expo en 5 minutos.

## 🚀 Setup Rápido

### 1. Instala dependencias (opcional)

```bash
npm install zustand  # Para state management (opcional)
```

### 2. Copia estos archivos a tu proyecto

```
tu-proyecto/
├── hooks/
│   └── useChat.ts          # Hook principal
├── services/
│   └── chatService.ts      # Servicio de streaming
└── screens/
    └── ChatScreen.tsx      # Pantalla de chat
```

---

## 📁 Archivo 1: Hook de Chat

**`hooks/useChat.ts`**

```typescript
import { useState, useCallback } from 'react';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: number;
}

const API_URL = 'http://localhost:8000/api/chat/stream';

/**
 * Hook para chat con streaming
 *
 * @param companyId - UUID de la empresa (opcional)
 *                    Formato: "550e8400-e29b-41d4-a716-446655440000"
 *                    Si no se provee, el chat funcionará sin contexto de empresa
 */
export function useChat(companyId?: string) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [threadId, setThreadId] = useState<string>();

  const sendMessage = useCallback(async (text: string) => {
    // Agregar mensaje del usuario
    setMessages(prev => [...prev, {
      id: `user_${Date.now()}`,
      role: 'user',
      content: text,
      timestamp: Date.now(),
    }]);

    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: text,
          thread_id: threadId,
          company_id: companyId,
        }),
      });

      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      let content = '';
      const assistantId = `assistant_${Date.now()}`;

      // Agregar mensaje vacío del asistente
      setMessages(prev => [...prev, {
        id: assistantId,
        role: 'assistant',
        content: '',
        timestamp: Date.now(),
      }]);

      // Leer stream
      while (reader) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));

              if (data.type === 'start' && data.thread_id) {
                setThreadId(data.thread_id);
              } else if (data.type === 'content') {
                content += data.content;
                setMessages(prev => prev.map(msg =>
                  msg.id === assistantId ? { ...msg, content } : msg
                ));
              } else if (data.type === 'error') {
                throw new Error(data.content || data.error);
              }
            } catch (e) {
              console.warn('Parse error:', e);
            }
          }
        }
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Error';
      setError(msg);
      setMessages(prev => [...prev, {
        id: `error_${Date.now()}`,
        role: 'assistant',
        content: `❌ ${msg}`,
        timestamp: Date.now(),
      }]);
    } finally {
      setIsLoading(false);
    }
  }, [threadId, companyId]);

  const clearChat = useCallback(() => {
    setMessages([]);
    setThreadId(undefined);
    setError(null);
  }, []);

  return { messages, isLoading, error, threadId, sendMessage, clearChat };
}
```

---

## 📁 Archivo 2: Pantalla de Chat

**`screens/ChatScreen.tsx`**

```typescript
import React, { useState, useRef, useEffect } from 'react';
import {
  View,
  Text,
  TextInput,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { useChat } from '../hooks/useChat';

export default function ChatScreen() {
  const [input, setInput] = useState('');
  const listRef = useRef<FlatList>(null);
  const { messages, isLoading, sendMessage } = useChat();

  useEffect(() => {
    listRef.current?.scrollToEnd();
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;
    await sendMessage(input.trim());
    setInput('');
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      keyboardVerticalOffset={90}
    >
      {/* Mensajes */}
      <FlatList
        ref={listRef}
        data={messages}
        keyExtractor={item => item.id}
        renderItem={({ item }) => (
          <View style={[
            styles.bubble,
            item.role === 'user' ? styles.userBubble : styles.assistantBubble
          ]}>
            <Text style={[
              styles.text,
              item.role === 'user' ? styles.userText : styles.assistantText
            ]}>
              {item.content}
            </Text>
          </View>
        )}
        contentContainerStyle={styles.list}
      />

      {/* Loading */}
      {isLoading && (
        <View style={styles.loading}>
          <ActivityIndicator />
          <Text style={styles.loadingText}>Escribiendo...</Text>
        </View>
      )}

      {/* Input */}
      <View style={styles.inputContainer}>
        <TextInput
          style={styles.input}
          value={input}
          onChangeText={setInput}
          placeholder="Escribe un mensaje..."
          multiline
          editable={!isLoading}
        />
        <TouchableOpacity
          style={[styles.button, (!input.trim() || isLoading) && styles.buttonDisabled]}
          onPress={handleSend}
          disabled={!input.trim() || isLoading}
        >
          <Text style={styles.buttonText}>➤</Text>
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F5F5',
  },
  list: {
    padding: 16,
  },
  bubble: {
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
    backgroundColor: '#FFF',
  },
  text: {
    fontSize: 16,
  },
  userText: {
    color: '#FFF',
  },
  assistantText: {
    color: '#000',
  },
  loading: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    gap: 8,
  },
  loadingText: {
    color: '#666',
  },
  inputContainer: {
    flexDirection: 'row',
    padding: 16,
    backgroundColor: '#FFF',
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
  button: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#007AFF',
    justifyContent: 'center',
    alignItems: 'center',
  },
  buttonDisabled: {
    opacity: 0.5,
  },
  buttonText: {
    color: '#FFF',
    fontSize: 20,
  },
});
```

---

## 📱 Uso en tu App

### Opción 1: En Stack Navigator

```typescript
import ChatScreen from './screens/ChatScreen';

const Stack = createNativeStackNavigator();

function App() {
  return (
    <Stack.Navigator>
      <Stack.Screen name="Chat" component={ChatScreen} />
    </Stack.Navigator>
  );
}
```

### Opción 2: Directo en Component

```typescript
import { useChat } from './hooks/useChat';

export function MiComponente() {
  const { messages, sendMessage, isLoading } = useChat('company_123');

  return (
    <View>
      {messages.map(msg => (
        <Text key={msg.id}>{msg.content}</Text>
      ))}
      <Button
        title="Enviar"
        onPress={() => sendMessage('Hola')}
        disabled={isLoading}
      />
    </View>
  );
}
```

---

## 🔧 Configuración

### Cambiar URL del API

```typescript
// hooks/useChat.ts
const API_URL = 'https://tu-api.com/api/chat/stream';
```

### Agregar Company ID

El `company_id` debe ser un **UUID válido** de la empresa del usuario.

```typescript
// ❌ INCORRECTO - estos NO funcionarán
const { sendMessage } = useChat('company_abc123');  // No es UUID
const { sendMessage } = useChat('unknown');         // Se ignora

// ✅ CORRECTO - UUID válido
const { sendMessage } = useChat('550e8400-e29b-41d4-a716-446655440000');

// ✅ Dinámico desde auth
const [companyId, setCompanyId] = useState<string>();

// Obtener company_id desde Supabase auth
useEffect(() => {
  const loadCompany = async () => {
    const { data } = await supabase.auth.getUser();
    const userCompanyId = data.user?.user_metadata?.company_id;
    if (userCompanyId) {
      setCompanyId(userCompanyId);
    }
  };
  loadCompany();
}, []);

const { sendMessage } = useChat(companyId);

// ✅ Desde query params (si usas deep linking)
const route = useRoute();
const companyId = route.params?.companyId;
const { sendMessage } = useChat(companyId);
```

**Cómo obtener el company_id:**

```typescript
// Opción 1: Desde user metadata (Supabase)
import { supabase } from '../lib/supabase';

const { data } = await supabase.auth.getUser();
const companyId = data.user?.user_metadata?.company_id;

// Opción 2: Desde una tabla de companies
const { data: companies } = await supabase
  .from('companies')
  .select('id')
  .eq('user_id', userId)
  .single();

const companyId = companies?.id;

// Opción 3: Context Provider
const { companyId } = useCompanyContext();
```

### Persistir Thread ID

```typescript
import AsyncStorage from '@react-native-async-storage/async-storage';

// Guardar cuando cambia
useEffect(() => {
  if (threadId) {
    AsyncStorage.setItem('chat_thread', threadId);
  }
}, [threadId]);

// Cargar al inicio
const [initialThread, setInitialThread] = useState<string>();

useEffect(() => {
  AsyncStorage.getItem('chat_thread').then(setInitialThread);
}, []);

const { ... } = useChat(companyId, initialThread);
```

---

## 🎨 Personalización

### Colores

```typescript
const colors = {
  userBubble: '#007AFF',
  assistantBubble: '#FFFFFF',
  userText: '#FFFFFF',
  assistantText: '#000000',
  background: '#F5F5F5',
  inputBackground: '#F5F5F5',
};
```

### Formateo de Mensajes

```typescript
// Agregar markdown, links, etc.
import Markdown from 'react-native-markdown-display';

<Markdown>{item.content}</Markdown>
```

### Typing Indicator

```typescript
{isLoading && (
  <View style={styles.typingIndicator}>
    <Text>●</Text>
    <Text>●</Text>
    <Text>●</Text>
  </View>
)}
```

---

## ⚡ Mejoras Opcionales

### 1. Auto-scroll al nuevo mensaje

```typescript
useEffect(() => {
  setTimeout(() => {
    listRef.current?.scrollToEnd({ animated: true });
  }, 100);
}, [messages.length]);
```

### 2. Limpiar chat

```typescript
const { clearChat } = useChat();

<Button title="Limpiar" onPress={clearChat} />
```

### 3. Retry en errores

```typescript
const [retryCount, setRetryCount] = useState(0);

const handleSendWithRetry = async (text: string) => {
  try {
    await sendMessage(text);
    setRetryCount(0);
  } catch (err) {
    if (retryCount < 3) {
      setRetryCount(prev => prev + 1);
      setTimeout(() => handleSendWithRetry(text), 1000);
    }
  }
};
```

### 4. Sugerencias rápidas

```typescript
const suggestions = [
  '¿Cuáles son mis documentos?',
  '¿Cuánto debo en impuestos?',
  'Resumen del mes',
];

{messages.length === 0 && (
  <View style={styles.suggestions}>
    {suggestions.map(text => (
      <TouchableOpacity
        key={text}
        onPress={() => sendMessage(text)}
      >
        <Text>{text}</Text>
      </TouchableOpacity>
    ))}
  </View>
)}
```

---

## 🐛 Troubleshooting

### Error de conexión
```typescript
// Verifica la URL
console.log('API URL:', API_URL);

// Prueba con curl
curl -X POST http://localhost:8000/api/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message":"test"}'
```

### Stream no funciona
```typescript
// Verifica que el reader existe
if (!response.body) {
  throw new Error('No body in response');
}
```

### Mensajes duplicados
```typescript
// Usa IDs únicos
id: `${role}_${Date.now()}_${Math.random()}`
```

---

## ✅ Checklist

- [ ] Hook `useChat.ts` copiado
- [ ] Screen `ChatScreen.tsx` copiado
- [ ] URL del API configurada
- [ ] Dependencias instaladas
- [ ] Navegación configurada
- [ ] Probado en iOS/Android

---

## 📚 Recursos

- [Guía completa](./CHAT_FRONTEND_GUIDE.md)
- [API Docs](http://localhost:8000/docs)
- [React Native Docs](https://reactnative.dev)

¡Listo! 🎉 Ahora tienes un chat funcional en tu app Expo.
