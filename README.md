# Fizko v2 - Plataforma de Gestión Tributaria con IA

Fizko es una plataforma moderna para pequeñas empresas chilenas que combina inteligencia artificial conversacional con gestión tributaria y contable. Construida sobre la arquitectura multi-agente de OpenAI ChatKit.

## 🚀 Características Principales

- 🤖 **Asistente IA Multi-Agente**
  - Agente SII General: Experto en normativa tributaria chilena
  - Agente de Remuneraciones: Especialista en cálculos de nómina y aportes

- 📊 **Dashboard Financiero**
  - Resúmenes tributarios (IVA, Impuesto a la Renta)
  - Gestión de nómina y remuneraciones
  - Tracking de documentos tributarios (DTEs)
  - Información de empresa (RUT, régimen tributario)

- 🔐 **Autenticación Segura**
  - Login con Google OAuth via Supabase
  - JWT tokens para API segura
  - Persistencia de sesiones

- 💾 **Base de Datos**
  - PostgreSQL via Supabase
  - Modelos: Company, TaxSummary, PayrollRecord, TaxDocument
  - Persistencia de conversaciones

## 📁 Estructura del Proyecto

```
fizko-v2/
├── backend/          # FastAPI + OpenAI Agents SDK + Supabase
│   ├── app/
│   │   ├── agents/        # Sistema multi-agente (SII + Remuneraciones)
│   │   ├── db/            # Modelos SQLAlchemy
│   │   ├── routers/       # API endpoints
│   │   ├── stores/        # Persistencia de conversaciones
│   │   └── main.py        # Aplicación FastAPI
│   └── pyproject.toml     # Dependencias Python (uv)
│
├── frontend/         # React + TypeScript + TailwindCSS + Vite
│   ├── src/
│   │   ├── components/    # Componentes React
│   │   │   ├── ChatKitPanel.tsx        # Chat conversacional
│   │   │   ├── FinancialDashboard.tsx  # Dashboard principal
│   │   │   ├── TaxSummaryCard.tsx      # Resumen tributario
│   │   │   ├── PayrollSummaryCard.tsx  # Resumen de nómina
│   │   │   └── ...
│   │   ├── hooks/         # Custom hooks
│   │   └── contexts/      # React contexts (Auth)
│   └── package.json       # Dependencias Node
│
├── impor-ai/         # Proyecto original (Import management)
└── package.json      # Scripts raíz para todo el monorepo
```

## 🛠️ Stack Tecnológico

### Backend
- **Framework**: FastAPI 0.115+
- **IA**: OpenAI GPT-4o + ChatKit Python SDK
- **Base de Datos**: PostgreSQL (Supabase)
- **ORM**: SQLAlchemy 2.0 (async)
- **Auth**: JWT + Supabase Auth
- **Gestor de Paquetes**: uv (moderno, rápido)

### Frontend
- **Framework**: React 19.2 + TypeScript 5.4
- **Build Tool**: Vite 7.1
- **UI**: TailwindCSS 3.4 + lucide-react icons
- **Chat**: @openai/chatkit-react
- **Auth**: @supabase/supabase-js

## 🚦 Inicio Rápido

### Prerrequisitos

1. **Node.js 20+** y **npm 10+**
2. **Python 3.11+**
3. **uv** (instalador: https://docs.astral.sh/uv/getting-started/installation/)
4. **OpenAI API Key** (https://platform.openai.com/api-keys)
5. **Proyecto Supabase** configurado con tablas

### Instalación

**1. Clonar el repositorio**
```bash
git clone https://github.com/akashi-labs/fizko-v2.git
cd fizko-v2
```

**2. Configurar Backend**
```bash
cd backend
cp .env.example .env
# Editar .env con tus credenciales:
# - OPENAI_API_KEY
# - SUPABASE_URL
# - SUPABASE_ANON_KEY
# - SUPABASE_JWT_SECRET
# - DATABASE_URL
```

**3. Configurar Frontend**
```bash
cd ../frontend
cp .env.example .env
# Editar .env con:
# - VITE_CHATKIT_API_DOMAIN_KEY (usar placeholder para dev local)
# - VITE_SUPABASE_URL
# - VITE_SUPABASE_ANON_KEY
```

**4. Crear tablas en Supabase**

Ejecuta los siguientes SQL scripts en el SQL Editor de Supabase:

```sql
-- Ver backend/migrations/ para scripts completos
-- Tablas necesarias:
-- - profiles
-- - companies
-- - conversations
-- - messages
-- - chatkit_attachments
-- - tax_summaries
-- - payroll_records
-- - tax_documents
```

**5. Iniciar la aplicación**

Desde la raíz del proyecto:
```bash
npm install  # Instala concurrently
npm start    # Inicia backend (puerto 8089) y frontend (puerto 5171)
```

O manualmente:

**Backend** (Terminal 1):
```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload --port 8089
```

**Frontend** (Terminal 2):
```bash
cd frontend
npm install
npm run dev  # Puerto 5171
```

**6. Abrir en el navegador**
```
http://localhost:5171
```

## 📖 Uso

### 1. Iniciar Sesión
- Haz clic en "Iniciar Sesión"
- Autentica con Google
- Tu empresa se carga automáticamente

### 2. Chat con el Asistente IA

Ejemplos de preguntas:

**Consultas SII:**
- "¿Cuáles son las fechas de declaración de IVA para este mes?"
- "¿Qué régimen tributario me conviene si facturo 50 millones al año?"
- "Explícame qué es el régimen 14 ter"

**Consultas de Remuneraciones:**
- "Calcula el sueldo líquido para un sueldo bruto de $1.200.000"
- "¿Cuánto debo aportar como empleador por cada trabajador?"
- "¿Qué porcentaje de AFP se descuenta?"

### 3. Dashboard Financiero

El panel derecho muestra:
- **Información de Empresa**: RUT, razón social, régimen tributario
- **Resumen Tributario**: Ingresos, gastos, IVA, impuesto a la renta
- **Resumen de Nómina**: Total empleados, sueldos, descuentos, aportes
- **Documentos Recientes**: DTEs, facturas, boletas emitidas

## 🎨 Arquitectura Multi-Agente

Fizko utiliza una arquitectura de agentes especializados:

```
Usuario → POST /chatkit → FizkoServer → Triage Agent
                                            ↓
                            ┌───────────────┴───────────────┐
                            ↓                               ↓
                    SII General Agent            Remuneraciones Agent
                    - Consultas SII              - Cálculos de sueldo
                    - Régimenes tributarios      - AFP, ISAPRE
                    - Fechas y deadlines         - Aportes patronales
                    - Cálculo de IVA             - Seguro desempleo
```

### Agentes Disponibles

1. **Triage Agent** (Router)
   - Analiza la intención del usuario
   - Redirige al agente especializado apropiado

2. **SII General Agent**
   - Experto en normativa del SII chileno
   - Regímenes tributarios (14 A, 14 B, ProPyme, 14 ter)
   - Cálculos de IVA, impuesto a la renta
   - Fechas de declaración

3. **Remuneraciones Agent**
   - Especialista en nómina y sueldos
   - Cálculos de AFP (10%), Salud (7%)
   - Aportes patronales (empresa)
   - Seguro de cesantía

## 🔧 Desarrollo

### Estructura de Carpetas

**Backend:**
```
backend/app/
├── agents/
│   ├── specialized/
│   │   ├── sii_general_agent.py
│   │   └── remuneraciones_agent.py
│   ├── triage_agent.py
│   ├── multi_agent_system.py
│   └── lazy_handoffs.py
├── db/models.py          # SQLAlchemy models
├── routers/              # API endpoints
└── main.py               # FastAPI app
```

**Frontend:**
```
frontend/src/
├── components/
│   ├── ChatKitPanel.tsx           # Chat interface
│   ├── FinancialDashboard.tsx     # Dashboard principal
│   ├── TaxSummaryCard.tsx         # Card de impuestos
│   └── PayrollSummaryCard.tsx     # Card de nómina
├── hooks/
│   ├── useCompany.ts              # Fetch company data
│   ├── useTaxSummary.ts           # Fetch tax summaries
│   └── usePayroll.ts              # Fetch payroll data
└── contexts/AuthContext.tsx       # Auth state
```

### Agregar un Nuevo Agente

1. Crear archivo en `backend/app/agents/specialized/`:
```python
# mi_nuevo_agente.py
from agents import Agent, function_tool

def create_mi_nuevo_agente(db, openai_client, company_id=None):
    @function_tool(strict_mode=False)
    async def mi_herramienta(ctx, param: str):
        """Descripción de la herramienta"""
        # Lógica aquí
        return {"resultado": "éxito"}

    return Agent(
        name="mi_nuevo_agente",
        model="gpt-4o",
        instructions="Instrucciones del agente...",
        tools=[mi_herramienta]
    )
```

2. Actualizar `multi_agent_system.py`:
```python
from .specialized import create_mi_nuevo_agente

self.agents["mi_nuevo_agente"] = create_mi_nuevo_agente(...)
```

3. Actualizar `triage_agent.py` para agregar handoff:
```python
def handoff_to_mi_nuevo() -> handoff:
    return handoff(agent_name="mi_nuevo_agente", ...)
```

### Linting y Calidad de Código

**Backend:**
```bash
cd backend
uv run ruff check .              # Revisar issues
uv run ruff check --fix .        # Auto-fix
uv run mypy app/                 # Type checking
```

**Frontend:**
```bash
cd frontend
npm run lint                     # ESLint
npm run type-check               # TypeScript
```

## 🧪 Testing

### Backend
```bash
cd backend
# TODO: Agregar pytest cuando estén los tests
uv run pytest
```

### Frontend
```bash
cd frontend
npm run test  # Vitest (configurar)
```

## 🚀 Deployment

**Esta aplicación está configurada como monorepo** con deployment separado:

- **Backend → Railway** (FastAPI + Selenium + Chrome)
- **Frontend → Vercel** (React + Vite)
- **Database → Supabase** (PostgreSQL + Auth)

### Guía Completa de Deployment

Ver **[DEPLOY.md](./DEPLOY.md)** para instrucciones detalladas paso a paso.

### Resumen Rápido

**Backend en Railway:**
1. Conectar repositorio Git
2. Railway detecta `railway.json` y `backend/Dockerfile`
3. Configurar variables de entorno (ver `backend/.env.example`)
4. Deploy automático

**Frontend en Vercel:**
1. Conectar repositorio Git
2. Vercel detecta `vercel.json`
3. Root directory: `frontend/`
4. Configurar variables de entorno (ver `frontend/.env.example`)
5. Deploy automático

**Costos estimados:** ~$10-15 USD/mes (Railway) + $0 (Vercel) + Supabase (según plan)

## 📚 Documentación Adicional

- [Backend README](backend/README.md) - Detalles técnicos del backend
- [Frontend README](frontend/README.md) - Guía del frontend
- [Frontend QUICKSTART](frontend/QUICKSTART.md) - Inicio rápido frontend
- [Impor-AI CLAUDE.md](impor-ai/CLAUDE.md) - Arquitectura original (referencia)

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📝 Licencia

Este proyecto está bajo la licencia MIT. Ver archivo `LICENSE` para más detalles.

## 🙋‍♂️ Soporte

- 📧 Email: support@akashi-labs.com
- 💬 GitHub Issues: https://github.com/akashi-labs/fizko-v2/issues
- 📖 Docs: https://docs.fizko.cl (próximamente)

## 🌟 Roadmap

- [ ] Integración con API del SII (facturación electrónica)
- [ ] Generación automática de declaraciones de impuestos
- [ ] Dashboard analytics avanzado
- [ ] Exportación a Excel/PDF
- [ ] Notificaciones por email (deadlines, vencimientos)
- [ ] App móvil (React Native)
- [ ] Más agentes especializados (inventario, caja, etc.)

---

**Construido con ❤️ por Akashi Labs**

Inspirado en OpenAI ChatKit y adaptado para el ecosistema tributario chileno.
