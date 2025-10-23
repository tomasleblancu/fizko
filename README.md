# Fizko v2 - Plataforma de Gestión Tributaria con IA

Plataforma para pequeñas empresas chilenas con asistente de IA para consultas tributarias y gestión contable.

## 🚀 Desarrollo Local

### Requisitos
- Node.js 20+
- Python 3.11+
- [uv](https://docs.astral.sh/uv/getting-started/installation/) (gestor de paquetes Python)

### Quick Start

**Terminal 1 - Backend:**
```bash
cd backend
cp .env.example .env  # Edita con tus credenciales
./dev.sh
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm install
npm run dev
```

**URLs:**
- 🌐 Frontend: http://localhost:5171
- 🔧 Backend API: http://localhost:8089
- 📚 API Docs: http://localhost:8089/docs

## 📦 Deploy en Producción

### Backend → Railway

1. Conectar repositorio a Railway
2. Railway detecta automáticamente `railway.json`
3. Configurar variables de entorno (ver `backend/.env.example`)
4. Deploy automático ✅

### Frontend → Vercel

1. Conectar repositorio a Vercel
2. Vercel detecta automáticamente `vercel.json`
3. Configurar variables de entorno (ver `frontend/.env.example`)
4. Deploy automático ✅

### Archivos de Configuración

- **`railway.json`** - Configuración Railway (backend)
- **`vercel.json`** - Configuración Vercel (frontend)
- **`backend/Dockerfile`** - Container para Railway
- **`backend/dev.sh`** - Script de desarrollo local

## 🛠️ Stack Tecnológico

### Backend
- FastAPI + Uvicorn + Gunicorn
- OpenAI GPT-4o + ChatKit SDK
- PostgreSQL (Supabase)
- SQLAlchemy 2.0 async
- Selenium + Chromium (scraping SII)

### Frontend
- React 19 + TypeScript
- Vite 7
- TailwindCSS 3
- @openai/chatkit-react
- Supabase Auth

## 📁 Estructura

```
fizko-v2/
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── agents/       # Sistema multi-agente
│   │   ├── routers/      # API endpoints
│   │   └── main.py
│   ├── Dockerfile        # Railway deploy
│   └── dev.sh            # Dev local
│
├── frontend/             # React frontend
│   ├── src/
│   │   ├── components/
│   │   └── pages/
│   └── package.json
│
├── railway.json          # Config Railway
└── vercel.json           # Config Vercel
```

## 🤖 Agentes Especializados

- **Triage Agent**: Router de consultas
- **SII General**: Experto en normativa tributaria chilena
- **Remuneraciones**: Especialista en cálculos de nómina
- **F29**: Gestión de declaraciones F29
- **Documentos Tributarios**: DTEs y facturación
- **Operación Renta**: Declaración anual de impuestos

## 📚 Documentación

- [Backend README](backend/README.md) - Detalles técnicos del backend
- [Frontend README](frontend/README.md) - Guía del frontend

## 📄 Licencia

MIT

---

**Construido por Akashi Labs**
