# ChatKit + Agents SDK Integration

Esta implementación combina la UI de **ChatKit** con el **OpenAI Agents SDK** para crear un sistema de agentes multi-agente self-hosted en el frontend de Next.js.

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────────────────────────┐
│                     FRONTEND (Next.js)                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ChatKit Widget (UI) → /api/chatkit                             │
│                              ↓                                   │
│              ChatKitServerAdapter                                │
│                              ↓                                   │
│              HandoffsManager                                     │
│                              ↓                                   │
│              Supervisor Agent                                    │
│                    ↙         ↓         ↘                         │
│      General Knowledge   Tax Documents   Monthly Taxes          │
│           Agent              Agent          Agent                │
│             │                  │               │                 │
│             └──────────────────┴───────────────┘                 │
│                              │                                   │
│                        Tools (fetch)                             │
│                              │                                   │
└──────────────────────────────┼───────────────────────────────────┘
                               │
┌──────────────────────────────▼───────────────────────────────────┐
│                     BACKEND API (FastAPI)                        │
├──────────────────────────────────────────────────────────────────┤
│  GET /tax/documents/compras                                      │
│  GET /tax/summary                                                │
│  GET /tax/form29                                                 │
└──────────────────────────────────────────────────────────────────┘
```

## 📂 Estructura de Archivos

```
frontend-nextjs/
├── src/
│   ├── lib/
│   │   ├── agents/
│   │   │   ├── core/
│   │   │   │   └── context.ts             # FizkoContext
│   │   │   ├── orchestration/
│   │   │   │   └── handoffs-manager.ts    # Cache de orquestadores
│   │   │   ├── specialized/
│   │   │   │   ├── supervisor.ts          # Supervisor agent
│   │   │   │   ├── general-knowledge.ts   # Agente conceptual
│   │   │   │   └── tax-documents.ts       # Agente de datos reales
│   │   │   └── tools/
│   │   │       └── tax/
│   │   │           └── documents.ts       # Tools para consultar backend
│   │   ├── chatkit/
│   │   │   └── server.ts                  # ChatKit server adapter
│   │   └── api/
│   │       └── client.ts                  # Cliente para backend API
│   │
│   ├── app/
│   │   ├── api/
│   │   │   ├── chatkit/
│   │   │   │   └── route.ts               # Endpoint principal de ChatKit
│   │   │   └── agents/
│   │   │       └── session/route.ts       # Crear sesiones
│   │   ├── chat/
│   │   │   └── page.tsx                   # Página de prueba
│   │   └── layout.tsx                     # Layout con script de ChatKit
│   │
│   └── components/
│       └── chat/
│           └── chatkit-panel.tsx          # Componente de ChatKit
```

## 🚀 Instalación

### 1. Instalar dependencias

Ya instaladas durante la implementación:
```bash
npm install @openai/agents @openai/chatkit-react zod@3
```

### 2. Configurar variables de entorno

Crear `.env.local` basado en `.env.example`:

```bash
# OpenAI API Key
OPENAI_API_KEY=sk-your-api-key-here

# Backend API URL
NEXT_PUBLIC_BACKEND_URL=http://localhost:8089

# Supabase (opcional, para auth)
NEXT_PUBLIC_SUPABASE_URL=your-supabase-url
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=your-anon-key
```

### 3. Iniciar el servidor de desarrollo

```bash
npm run dev
```

## 📝 Uso

### Acceder a la página de prueba

Navegar a: `http://localhost:3000/chat`

### Integrar en tu aplicación

```tsx
import { ChatKitPanel } from '@/components/chat/chatkit-panel';

export default function MyPage() {
  return (
    <div className="h-screen">
      <ChatKitPanel companyId="your-company-id" />
    </div>
  );
}
```

## 🤖 Sistema de Agentes

### Agentes Disponibles

#### 1. **Supervisor Agent** (`supervisor_agent`)
- **Modelo**: gpt-4o-mini
- **Rol**: Router principal que delega a especialistas
- **Comportamiento**: NO responde directamente, solo hace handoffs

#### 2. **General Knowledge Agent** (`general_knowledge_agent`)
- **Modelo**: gpt-4o-mini
- **Rol**: Responde preguntas conceptuales sobre impuestos y contabilidad
- **Ejemplos**:
  - "¿Qué es el IVA?"
  - "¿Cómo se calcula el PPM?"
  - "¿Qué diferencia hay entre factura y boleta?"

#### 3. **Tax Documents Agent** (`tax_documents_agent`)
- **Modelo**: gpt-4o-mini
- **Rol**: Consulta documentos tributarios reales via backend API
- **Tools**:
  - `get_documentos_tributarios`: Obtiene DTEs (compras, ventas, honorarios)
  - `get_tax_summary`: Obtiene resumen tributario
  - `get_f29_info`: Obtiene información del F29
- **Ejemplos**:
  - "Muéstrame mis facturas de compra"
  - "¿Cuánto gasté este mes?"
  - "¿Cuánto debo de IVA?"

## 🛠️ Crear Nuevos Agentes

### Paso 1: Crear el agente

```typescript
// src/lib/agents/specialized/my-agent.ts
import { Agent } from '@openai/agents';
import { myTools } from '../tools/my-tools';

export function createMyAgent(): Agent {
  return new Agent({
    name: 'my_agent',
    model: 'gpt-4o-mini',
    instructions: `Tu eres...`,
    tools: myTools,
  });
}
```

### Paso 2: Agregar al supervisor

```typescript
// src/lib/agents/specialized/supervisor.ts
import { createMyAgent } from './my-agent';

export function createSupervisorAgent(): Agent {
  const myAgent = createMyAgent();

  return new Agent({
    name: 'supervisor_agent',
    handoffs: [
      generalKnowledgeAgent,
      taxDocumentsAgent,
      myAgent, // ← Nuevo agente
    ],
  });
}
```

## 🔧 Crear Nuevas Herramientas (Tools)

```typescript
// src/lib/agents/tools/my-tools.ts
import { tool } from '@openai/agents';
import { z } from 'zod';
import { FizkoContext } from '../core/context';
import { createApiClient } from '@/lib/api/client';

export const myTool = tool({
  name: 'my_tool',
  description: 'Descripción de qué hace la herramienta',
  parameters: z.object({
    param1: z.string().describe('Descripción del parámetro'),
  }),
  execute: async (params, context: FizkoContext) => {
    const apiClient = createApiClient({
      companyId: context.company_id,
    });

    const response = await apiClient.get('/my-endpoint', {
      params: { param1: params.param1 },
    });

    return {
      success: true,
      data: response,
    };
  },
});
```

## 🔍 Debugging

### Ver logs de agentes

Los logs se imprimen en la consola del servidor:

```bash
npm run dev
```

Busca logs como:
- `[HandoffsManager] Creating new supervisor for thread: ...`
- `[ChatKitServer] Processing message: ...`

### Ver traces en OpenAI Dashboard

Navega a: https://platform.openai.com/traces

Aquí puedes ver:
- Qué agente respondió
- Qué tools se llamaron
- Cuánto tiempo tomó cada paso

### Inspeccionar cache

```typescript
import { handoffsManager } from '@/lib/agents/orchestration/handoffs-manager';

// En el código
const stats = handoffsManager.getCacheStats();
console.log('Cache stats:', stats);
```

## ⚡ Performance

### Cache de Agentes

Los agentes se cachean por `thread_id` durante 30 minutos:

```typescript
// Configuración en handoffs-manager.ts
private readonly CACHE_TTL = 30 * 60 * 1000; // 30 minutes
```

### Limpiar Cache

```typescript
// Limpiar thread específico
handoffsManager.clearThread('thread-123');

// Limpiar todo el cache
handoffsManager.clearAll();
```

## 🚨 Errores Comunes

### 1. `OPENAI_API_KEY is required`

**Solución**: Agregar `OPENAI_API_KEY` a `.env.local`

### 2. `Failed to create session`

**Solución**: Verificar que `/api/agents/session` esté funcionando:
```bash
curl -X POST http://localhost:3000/api/agents/session \
  -H "Content-Type: application/json" \
  -d '{"company_id":"demo"}'
```

### 3. `ChatKit script not loaded`

**Solución**: Verificar que el script esté en `layout.tsx`:
```tsx
<Script
  src="https://cdn.platform.openai.com/deployments/chatkit/chatkit.js"
  strategy="beforeInteractive"
/>
```

### 4. Tools fallan con `company_id is required`

**Solución**: Pasar `companyId` al ChatKitPanel:
```tsx
<ChatKitPanel companyId="your-company-id" />
```

## 📊 Comparación con Backend Python

| Aspecto | Backend (Python) | Frontend (TypeScript) |
|---------|------------------|----------------------|
| Ubicación | FastAPI | Next.js API Routes |
| Lenguaje | Python | TypeScript |
| Agentes | Python Agents SDK | TypeScript Agents SDK |
| Tools | Python functions | TypeScript functions |
| DB Access | Direct (SQLAlchemy) | Via API (fetch) |
| Deployment | Railway | Vercel |

## 🎯 Próximos Pasos

1. **Autenticación**: Integrar con Supabase Auth
2. **Más agentes**: Agregar Monthly Taxes Agent, Payroll Agent
3. **Guardrails**: Implementar input/output validation
4. **Widgets UI**: Agregar componentes interactivos (charts, tables)
5. **Streaming real**: Implementar streaming token por token
6. **Tests**: Agregar tests unitarios y de integración

## 📚 Referencias

- [OpenAI Agents SDK (TypeScript)](https://openai.github.io/openai-agents-js/)
- [ChatKit Documentation](https://openai.github.io/chatkit-js/)
- [Next.js API Routes](https://nextjs.org/docs/app/building-your-application/routing/route-handlers)
