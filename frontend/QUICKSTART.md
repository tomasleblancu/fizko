# 🚀 Quick Start - ChatKit + Agents SDK

## Iniciar el proyecto

### 1. Instalar dependencias (ya hecho)
```bash
npm install
```

### 2. Configurar `.env.local` (ya hecho)
El archivo `.env.local` ya tiene todas las variables necesarias, incluyendo:
- ✅ `OPENAI_API_KEY` (copiado desde backend)
- ✅ `NEXT_PUBLIC_BACKEND_URL`
- ✅ Supabase credentials

### 3. Iniciar el servidor
```bash
npm run dev
```

### 4. Probar el chat
Abrir en el navegador:
```
http://localhost:3000/chat
```

## ✅ Qué incluye esta implementación

### Agentes
- ✅ **Supervisor Agent**: Router principal
- ✅ **General Knowledge Agent**: Preguntas conceptuales sobre impuestos
- ✅ **Tax Documents Agent**: Consulta documentos reales via backend API

### Tools
- ✅ `get_documentos_tributarios`: Obtiene DTEs (compras, ventas, honorarios)
- ✅ `get_tax_summary`: Resumen tributario con IVA
- ✅ `get_f29_info`: Información del F29

### API Endpoints
- ✅ `POST /api/chatkit`: Endpoint principal de ChatKit
- ✅ `POST /api/agents/session`: Crear sesiones

### UI
- ✅ ChatKitPanel component
- ✅ Página de prueba en `/chat`

## 🧪 Ejemplos de Preguntas

### Conceptuales (→ General Knowledge Agent)
- "¿Qué es el IVA?"
- "¿Cómo funciona el F29?"
- "¿Qué diferencia hay entre factura y boleta?"

### Datos Reales (→ Tax Documents Agent)
- "Muéstrame mis facturas de compra"
- "¿Cuánto gasté este mes?"
- "¿Cuánto debo de IVA?"

## 📁 Archivos Clave

```
src/
├── lib/agents/
│   ├── specialized/
│   │   ├── supervisor.ts           # ← Punto de entrada
│   │   ├── general-knowledge.ts
│   │   └── tax-documents.ts
│   └── tools/tax/
│       └── documents.ts             # ← Tools que llaman al backend
│
├── app/api/
│   └── chatkit/route.ts             # ← Endpoint principal
│
└── components/chat/
    └── chatkit-panel.tsx            # ← UI de ChatKit
```

## 🔍 Debugging

### Ver logs del servidor
Los logs aparecen en la terminal donde corriste `npm run dev`:
```
[HandoffsManager] Creating new supervisor for thread: abc123
[ChatKitServer] Processing message: { op: 'create_message', ... }
```

### Ver traces en OpenAI Dashboard
1. Ir a: https://platform.openai.com/traces
2. Buscar por fecha/hora
3. Ver qué agente respondió y qué tools llamó

## ⚠️ Requisitos

### Backend debe estar corriendo
El frontend hace llamadas al backend para obtener datos:
```bash
cd backend
./dev.sh
```

Verifica que el backend esté en: `http://localhost:8089`

### OpenAI API Key válida
Verifica que `OPENAI_API_KEY` en `.env.local` sea válida.

## 📚 Documentación Completa

Ver [CHATKIT_AGENTS_SDK.md](./CHATKIT_AGENTS_SDK.md) para:
- Arquitectura detallada
- Cómo crear nuevos agentes
- Cómo crear nuevas herramientas
- Troubleshooting
- Comparación con backend Python

## 🎯 Próximos Pasos

1. **Probar handoffs**: Hacer preguntas que requieran diferentes agentes
2. **Agregar más agentes**: Monthly Taxes, Payroll, Settings
3. **Implementar streaming**: Token por token en lugar de todo de una vez
4. **Agregar autenticación**: Integrar con Supabase Auth
5. **Agregar widgets UI**: Charts, tables, cards interactivos

## ❓ ¿Problemas?

### Error: "ChatKit script not loaded"
**Solución**: El script de ChatKit se carga en `layout.tsx`. Asegúrate de que esté presente.

### Error: "OPENAI_API_KEY is required"
**Solución**: Verificar que `.env.local` tenga `OPENAI_API_KEY`.

### Error: "Failed to fetch"
**Solución**: Verificar que el backend esté corriendo en `http://localhost:8089`.

### El agente no responde
**Solución**: Verificar logs en la terminal del servidor Next.js.
