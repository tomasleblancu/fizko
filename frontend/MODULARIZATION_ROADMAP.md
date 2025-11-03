# Roadmap de Modularización - NotificationTemplatesPage

## ✅ Completado (Fase 1)

### Módulos Creados:

1. **Types** ✅
   - `types/template-variables.ts` - Variables de template
   - `types/notification-template.ts` - Template y form data

2. **Hooks** ✅
   - `hooks/useTemplateVariables.ts` - Custom hook para variables
   - `hooks/index.ts` - Barrel export

3. **Components** ✅
   - `components/TemplateVariablesPanel.tsx` - Panel de variables
   - `components/index.ts` - Barrel export

4. **Utils** ✅
   - `utils/template-helpers.ts` - Funciones helper (labels, colors, timing)

### Mejoras Aplicadas:
- ✅ Eliminadas ~150 líneas de código inline
- ✅ Hook personalizado para fetching
- ✅ Componente reutilizable para variables
- ✅ Type safety completo
- ✅ Funciones helper extraídas

## 🔄 Pendiente (Fase 2) - Modularización de Modales

El archivo aún tiene ~1000 líneas porque contiene 3 modales grandes inline:

### 1. CreateTemplateModal (~150 líneas)

**Extraer a:** `components/CreateTemplateModal.tsx`

```tsx
interface CreateTemplateModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (template: NotificationTemplate) => void;
  accessToken?: string;
}

export function CreateTemplateModal({
  isOpen,
  onClose,
  onSuccess,
  accessToken
}: CreateTemplateModalProps) {
  // Lógica del form
  // Submit handler
  // UI del modal
}
```

**Beneficio:** -150 líneas

### 2. EditTemplateModal (~150 líneas)

**Extraer a:** `components/EditTemplateModal.tsx`

```tsx
interface EditTemplateModalProps {
  isOpen: boolean;
  template: NotificationTemplate | null;
  onClose: () => void;
  onSuccess: (template: NotificationTemplate) => void;
  accessToken?: string;
}

export function EditTemplateModal({
  isOpen,
  template,
  onClose,
  onSuccess,
  accessToken
}: EditTemplateModalProps) {
  // Similar a CreateTemplateModal pero con update
}
```

**Beneficio:** -150 líneas

### 3. DeleteConfirmModal (~40 líneas)

**Extraer a:** `components/DeleteConfirmModal.tsx`

```tsx
interface DeleteConfirmModalProps {
  isOpen: boolean;
  templateId: string | null;
  onClose: () => void;
  onConfirm: (id: string) => Promise<void>;
  isDeleting: boolean;
}

export function DeleteConfirmModal({
  isOpen,
  templateId,
  onClose,
  onConfirm,
  isDeleting
}: DeleteConfirmModalProps) {
  // UI del modal de confirmación
}
```

**Beneficio:** -40 líneas

### 4. TemplateCard (~80 líneas)

**Extraer a:** `components/TemplateCard.tsx`

```tsx
interface TemplateCardProps {
  template: NotificationTemplate;
  onEdit: (template: NotificationTemplate) => void;
  onDelete: (id: string) => void;
}

export function TemplateCard({
  template,
  onEdit,
  onDelete
}: TemplateCardProps) {
  // UI del card individual
}
```

**Beneficio:** -80 líneas

### 5. TemplateForm (Componente Compartido)

Tanto CreateTemplateModal como EditTemplateModal comparten el mismo formulario.

**Extraer a:** `components/TemplateForm.tsx`

```tsx
interface TemplateFormProps {
  formData: NotificationTemplateFormData;
  onChange: (data: NotificationTemplateFormData) => void;
  onSubmit: (e: React.FormEvent) => void;
  isSubmitting: boolean;
  submitLabel: string;
  variables?: TemplateVariable[];
  isLoadingVariables?: boolean;
}

export function TemplateForm({
  formData,
  onChange,
  onSubmit,
  isSubmitting,
  submitLabel,
  variables,
  isLoadingVariables
}: TemplateFormProps) {
  // Form fields compartidos
}
```

**Beneficio:** -100 líneas (eliminación de duplicación)

## 📁 Estructura Final Propuesta

```
frontend/src/features/admin/notifications/
├── types/
│   ├── template-variables.ts           ✅ Creado
│   ├── notification-template.ts        ✅ Creado
│   └── index.ts                        ⏳ Crear
├── hooks/
│   ├── useTemplateVariables.ts         ✅ Creado
│   └── index.ts                        ✅ Creado
├── components/
│   ├── TemplateVariablesPanel.tsx      ✅ Creado
│   ├── TemplateCard.tsx                ⏳ Crear
│   ├── TemplateForm.tsx                ⏳ Crear
│   ├── CreateTemplateModal.tsx         ⏳ Crear
│   ├── EditTemplateModal.tsx           ⏳ Crear
│   ├── DeleteConfirmModal.tsx          ⏳ Crear
│   └── index.ts                        ✅ Creado (actualizar)
├── utils/
│   ├── template-helpers.ts             ✅ Creado
│   └── index.ts                        ⏳ Crear
└── pages/
    └── NotificationTemplatesPage.tsx   ✅ Parcialmente refactorizado
```

## 🎯 Resultado Esperado Después de Fase 2

### NotificationTemplatesPage Final (~300 líneas)

```tsx
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Bell, Plus, ArrowLeft, Loader2 } from 'lucide-react';
import { useAuth } from "@/app/providers/AuthContext";
import {
  TemplateCard,
  CreateTemplateModal,
  EditTemplateModal,
  DeleteConfirmModal
} from '../components';

export default function NotificationTemplatesPage() {
  const navigate = useNavigate();
  const { session } = useAuth();

  // States (10 líneas)
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState(null);
  const [deleteConfirm, setDeleteConfirm] = useState(null);

  // Fetch templates (20 líneas)
  const fetchTemplates = async () => { /* ... */ };

  useEffect(() => {
    fetchTemplates();
  }, [session?.access_token]);

  // Handlers (30 líneas)
  const handleCreateSuccess = (template) => {
    setTemplates([...templates, template]);
    setShowCreateModal(false);
  };

  const handleEditSuccess = (updated) => {
    setTemplates(templates.map(t => t.id === updated.id ? updated : t));
  };

  const handleDeleteSuccess = (id) => {
    setTemplates(templates.filter(t => t.id !== id));
  };

  // Render (100 líneas)
  return (
    <div>
      {/* Header (30 líneas) */}
      {/* Stats (20 líneas) */}
      {/* Template Cards (30 líneas) */}
      {templates.map(template => (
        <TemplateCard
          key={template.id}
          template={template}
          onEdit={setEditingTemplate}
          onDelete={setDeleteConfirm}
        />
      ))}

      {/* Modals (20 líneas) */}
      <CreateTemplateModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onSuccess={handleCreateSuccess}
        accessToken={session?.access_token}
      />

      <EditTemplateModal
        isOpen={!!editingTemplate}
        template={editingTemplate}
        onClose={() => setEditingTemplate(null)}
        onSuccess={handleEditSuccess}
        accessToken={session?.access_token}
      />

      <DeleteConfirmModal
        isOpen={!!deleteConfirm}
        templateId={deleteConfirm}
        onClose={() => setDeleteConfirm(null)}
        onConfirm={handleDeleteSuccess}
      />
    </div>
  );
}
```

## 📊 Métricas de Mejora Proyectadas

| Métrica | Actual (Fase 1) | Después Fase 2 | Mejora Total |
|---------|-----------------|----------------|--------------|
| Líneas en Page | ~1000 | ~300 | -70% |
| Componentes reutilizables | 1 | 6 | +500% |
| Responsabilidades por archivo | 5+ | 1-2 | -60% |
| Testabilidad | Media | Alta | +200% |
| Duplicación de código | Media | Mínima | -80% |

## 🛠️ Pasos para Completar Fase 2

### Paso 1: Extraer TemplateCard

```bash
# 1. Crear archivo
touch src/features/admin/notifications/components/TemplateCard.tsx

# 2. Copiar el JSX del card individual
# 3. Agregar props interface
# 4. Importar helpers (getCategoryLabel, etc.)
# 5. Actualizar index.ts
```

### Paso 2: Extraer TemplateForm

```bash
# 1. Crear archivo compartido
touch src/features/admin/notifications/components/TemplateForm.tsx

# 2. Copiar fields compartidos entre Create y Edit
# 3. Agregar props para controlled component
# 4. Incluir TemplateVariablesPanel
```

### Paso 3: Extraer CreateTemplateModal

```bash
# 1. Crear archivo
touch src/features/admin/notifications/components/CreateTemplateModal.tsx

# 2. Mover lógica de submit
# 3. Usar TemplateForm component
# 4. Manejar success callback
```

### Paso 4: Extraer EditTemplateModal

```bash
# Similar a CreateTemplateModal
# Reutilizar TemplateForm
# Diferente endpoint (PUT vs POST)
```

### Paso 5: Extraer DeleteConfirmModal

```bash
# Modal simple de confirmación
# Reutilizable en otros lugares
```

### Paso 6: Refactorizar NotificationTemplatesPage

```bash
# Remover código inline
# Importar nuevos componentes
# Simplificar a orchestrator component
```

## 🧪 Testing Después de Fase 2

Cada componente se puede testear independientemente:

```typescript
// TemplateCard.test.tsx
test('renders template info correctly', () => {
  render(<TemplateCard template={mockTemplate} onEdit={jest.fn()} onDelete={jest.fn()} />);
  expect(screen.getByText('Template Name')).toBeInTheDocument();
});

// CreateTemplateModal.test.tsx
test('submits form with correct data', async () => {
  const onSuccess = jest.fn();
  render(<CreateTemplateModal isOpen={true} onSuccess={onSuccess} />);
  // Fill form...
  // Submit...
  await waitFor(() => expect(onSuccess).toHaveBeenCalled());
});
```

## 📚 Documentación Recomendada

Después de completar Fase 2, crear:

1. **README.md** en `/features/admin/notifications/`
   - Cómo usar cada componente
   - Props interfaces
   - Ejemplos de uso

2. **Storybook stories** para cada componente
   - Estados diferentes
   - Interacciones
   - Documentación visual

## ✨ Beneficios Finales

Después de completar ambas fases:

- ✅ Código ~70% más corto
- ✅ Componentes 100% reutilizables
- ✅ Tests unitarios simples
- ✅ Mantenimiento fácil
- ✅ Onboarding rápido de developers
- ✅ Reducción de bugs
- ✅ Mejor performance (code splitting)

---

**Fase 1:** ✅ Completado
**Fase 2:** ⏳ Pendiente (recomendado para próximo sprint)
**Tiempo estimado Fase 2:** 4-6 horas
