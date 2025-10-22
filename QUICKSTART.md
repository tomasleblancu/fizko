# Fizko v2 - Inicio Rápido ⚡

Guía de 5 minutos para ejecutar Fizko localmente.

## ✅ Prerrequisitos

- [ ] Node.js 20+ instalado
- [ ] Python 3.11+ instalado
- [ ] uv instalado ([instalar](https://docs.astral.sh/uv/getting-started/installation/))
- [ ] OpenAI API Key
- [ ] Proyecto Supabase creado

## 🚀 Instalación

### 1. Configurar Backend

```bash
cd backend
cp .env.example .env
```

**Edita `backend/.env`:**
```bash
OPENAI_API_KEY=sk-proj-TU_API_KEY_AQUI

SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_ANON_KEY=tu-anon-key
SUPABASE_JWT_SECRET=tu-jwt-secret
DATABASE_URL=postgresql://postgres:password@db.tu-proyecto.supabase.co:5432/postgres
```

### 2. Configurar Frontend

```bash
cd ../frontend
cp .env.example .env
```

**Edita `frontend/.env`:**
```bash
VITE_CHATKIT_API_DOMAIN_KEY=domain_pk_localhost_dev

VITE_SUPABASE_URL=https://tu-proyecto.supabase.co
VITE_SUPABASE_ANON_KEY=tu-anon-key
```

### 3. Crear Tablas en Supabase

Copia y ejecuta en el **SQL Editor** de Supabase:

```sql
-- Tabla de perfiles (extiende auth.users)
CREATE TABLE IF NOT EXISTS profiles (
  id UUID REFERENCES auth.users(id) PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  full_name TEXT,
  company_name TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabla de empresas
CREATE TABLE IF NOT EXISTS companies (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) NOT NULL,
  rut VARCHAR(12) UNIQUE NOT NULL,
  business_name TEXT NOT NULL,
  tax_regime VARCHAR(50),
  activity_code VARCHAR(10),
  address TEXT,
  commune TEXT,
  region TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabla de conversaciones
CREATE TABLE IF NOT EXISTS conversations (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) NOT NULL,
  chatkit_session_id TEXT UNIQUE,
  company_id UUID REFERENCES companies(id),
  title TEXT,
  status VARCHAR(20) DEFAULT 'active',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabla de mensajes
CREATE TABLE IF NOT EXISTS messages (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE NOT NULL,
  role VARCHAR(20) NOT NULL,
  content TEXT NOT NULL,
  metadata JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabla de resúmenes tributarios
CREATE TABLE IF NOT EXISTS tax_summaries (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  company_id UUID REFERENCES companies(id) NOT NULL,
  period_start DATE NOT NULL,
  period_end DATE NOT NULL,
  total_revenue NUMERIC(15, 2) DEFAULT 0,
  total_expenses NUMERIC(15, 2) DEFAULT 0,
  iva_collected NUMERIC(15, 2) DEFAULT 0,
  iva_paid NUMERIC(15, 2) DEFAULT 0,
  net_iva NUMERIC(15, 2) DEFAULT 0,
  income_tax NUMERIC(15, 2) DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabla de registros de nómina
CREATE TABLE IF NOT EXISTS payroll_records (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  company_id UUID REFERENCES companies(id) NOT NULL,
  employee_name TEXT NOT NULL,
  rut_employee VARCHAR(12),
  gross_salary NUMERIC(15, 2) NOT NULL,
  afp_deduction NUMERIC(15, 2) DEFAULT 0,
  isapre_deduction NUMERIC(15, 2) DEFAULT 0,
  unemployment_deduction NUMERIC(15, 2) DEFAULT 0,
  other_deductions NUMERIC(15, 2) DEFAULT 0,
  net_salary NUMERIC(15, 2) NOT NULL,
  employer_contributions NUMERIC(15, 2) DEFAULT 0,
  period DATE NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabla de documentos tributarios
CREATE TABLE IF NOT EXISTS tax_documents (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  company_id UUID REFERENCES companies(id) NOT NULL,
  document_type VARCHAR(50) NOT NULL,
  document_number VARCHAR(50) NOT NULL,
  issue_date DATE NOT NULL,
  due_date DATE,
  amount NUMERIC(15, 2) NOT NULL,
  status VARCHAR(20) DEFAULT 'emitida',
  recipient_name TEXT,
  recipient_rut VARCHAR(12),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabla de attachments (ChatKit)
CREATE TABLE IF NOT EXISTS chatkit_attachments (
  id TEXT PRIMARY KEY,
  conversation_id UUID REFERENCES conversations(id),
  name TEXT NOT NULL,
  mime_type TEXT NOT NULL,
  storage_path TEXT,
  public_url TEXT,
  preview_url TEXT,
  metadata JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices para mejor performance
CREATE INDEX IF NOT EXISTS idx_companies_user_id ON companies(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_company_id ON conversations(company_id);
CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_tax_summaries_company_id ON tax_summaries(company_id);
CREATE INDEX IF NOT EXISTS idx_payroll_records_company_id ON payroll_records(company_id);
CREATE INDEX IF NOT EXISTS idx_tax_documents_company_id ON tax_documents(company_id);

-- RLS (Row Level Security) - Opcional pero recomendado
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE companies ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE tax_summaries ENABLE ROW LEVEL SECURITY;
ALTER TABLE payroll_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE tax_documents ENABLE ROW LEVEL SECURITY;

-- Políticas RLS básicas (los usuarios solo ven sus propios datos)
CREATE POLICY "Users can view own profile" ON profiles FOR SELECT USING (auth.uid() = id);
CREATE POLICY "Users can update own profile" ON profiles FOR UPDATE USING (auth.uid() = id);

CREATE POLICY "Users can view own companies" ON companies FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own companies" ON companies FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own companies" ON companies FOR UPDATE USING (auth.uid() = user_id);
```

### 4. Insertar Datos de Prueba (Opcional)

Después de hacer login por primera vez, ejecuta:

```sql
-- Insertar una empresa de prueba (reemplaza USER_ID con tu UUID de auth.users)
INSERT INTO companies (user_id, rut, business_name, tax_regime, activity_code, address, commune, region)
VALUES (
  'tu-user-id-aqui',
  '76.123.456-7',
  'Empresa de Prueba SpA',
  '14 A',
  '620200',
  'Av. Providencia 123',
  'Providencia',
  'Metropolitana'
);

-- Insertar resumen tributario de prueba
INSERT INTO tax_summaries (company_id, period_start, period_end, total_revenue, total_expenses, iva_collected, iva_paid, net_iva, income_tax)
VALUES (
  (SELECT id FROM companies WHERE rut = '76.123.456-7'),
  '2025-01-01',
  '2025-01-31',
  5000000,
  2000000,
  950000,
  380000,
  570000,
  270000
);

-- Insertar registros de nómina de prueba
INSERT INTO payroll_records (company_id, employee_name, rut_employee, gross_salary, afp_deduction, isapre_deduction, unemployment_deduction, net_salary, employer_contributions, period)
VALUES
  (
    (SELECT id FROM companies WHERE rut = '76.123.456-7'),
    'Juan Pérez',
    '12.345.678-9',
    1200000,
    120000,
    84000,
    12000,
    984000,
    120000,
    '2025-01-01'
  ),
  (
    (SELECT id FROM companies WHERE rut = '76.123.456-7'),
    'María González',
    '98.765.432-1',
    1500000,
    150000,
    105000,
    15000,
    1230000,
    150000,
    '2025-01-01'
  );

-- Insertar documentos tributarios de prueba
INSERT INTO tax_documents (company_id, document_type, document_number, issue_date, amount, status, recipient_name, recipient_rut)
VALUES
  (
    (SELECT id FROM companies WHERE rut = '76.123.456-7'),
    'Factura Electrónica',
    '1234',
    '2025-01-15',
    500000,
    'pagada',
    'Cliente ABC Ltda.',
    '77.777.777-7'
  ),
  (
    (SELECT id FROM companies WHERE rut = '76.123.456-7'),
    'Boleta Electrónica',
    '5678',
    '2025-01-20',
    150000,
    'emitida',
    'Cliente XYZ',
    '88.888.888-8'
  );
```

### 5. Iniciar la Aplicación

**Desde la raíz del proyecto:**

```bash
# Instalar concurrently (solo primera vez)
npm install

# Iniciar backend + frontend juntos
npm start
```

**O manualmente en terminales separadas:**

**Terminal 1 - Backend:**
```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload --port 8089
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm install
npm run dev
```

### 6. Abrir en el Navegador

```
http://localhost:5171
```

## 🎯 Primeros Pasos

1. **Haz clic en "Iniciar Sesión"** en la esquina superior derecha
2. **Autentica con Google** (usa la cuenta configurada en Supabase)
3. **Prueba el chat** con estas preguntas:
   - "¿Cuáles son los regímenes tributarios en Chile?"
   - "Calcula el sueldo líquido para un bruto de $1.200.000"
   - "¿Cuándo debo declarar el IVA?"

4. **Explora el Dashboard** en el panel derecho:
   - Información de tu empresa
   - Resúmenes tributarios
   - Nómina
   - Documentos recientes

## 🔧 Troubleshooting

### Backend no inicia

**Error: "OpenAI API key not found"**
```bash
# Verificar que .env existe y tiene OPENAI_API_KEY
cat backend/.env | grep OPENAI_API_KEY
```

**Error: "Connection refused to database"**
```bash
# Verificar DATABASE_URL en backend/.env
# Debe apuntar a tu proyecto Supabase
```

### Frontend no inicia

**Error: "Failed to load environment variables"**
```bash
# Verificar que .env existe en frontend/
cat frontend/.env
```

**Error: CORS en /chatkit**
```bash
# El backend debe estar corriendo en puerto 8089
# Vite está configurado para proxy automático
```

### No aparecen datos en el Dashboard

1. **Verificar que tienes una empresa creada** en Supabase:
```sql
SELECT * FROM companies WHERE user_id = 'tu-user-id';
```

2. **Verificar que hay datos de prueba**:
```sql
SELECT * FROM tax_summaries;
SELECT * FROM payroll_records;
SELECT * FROM tax_documents;
```

3. **Revisar consola del navegador** (F12) para errores de API

## 📚 Próximos Pasos

- Lee el [README.md](README.md) completo para entender la arquitectura
- Explora [backend/README.md](backend/README.md) para detalles del backend
- Revisa [frontend/README.md](frontend/README.md) para detalles del frontend
- Personaliza los agentes en `backend/app/agents/specialized/`
- Agrega más componentes al dashboard en `frontend/src/components/`

## 🆘 Soporte

- GitHub Issues: https://github.com/akashi-labs/fizko-v2/issues
- Email: support@akashi-labs.com

---

**¡Listo! 🎉 Ya tienes Fizko corriendo localmente.**
