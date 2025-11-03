# Refactorización NotificationTemplatesPage

## Resumen

Se modularizó completamente el componente `NotificationTemplatesPage.tsx` que tenía **1129 líneas** en un solo archivo, con mucha duplicación de código entre los modales de creación y edición.

## Estructura Antes

```
frontend/src/features/admin/notifications/
└── pages/
    └── NotificationTemplatesPage.tsx (1129 líneas)
        - Interfaces de tipos
        - Funciones helper para labels y colores
        - Lógica de fetch y mutación
        - Componente principal
        - Modal de creación (duplicado)
        - Modal de edición (duplicado)
        - Modal de eliminación
```

## Estructura Después

```
frontend/src/features/admin/notifications/
├── types/
│   └── index.ts                    # Tipos compartidos e iniciales
├── utils/
│   ├── index.ts                    # Barrel export
│   └── templateHelpers.ts          # Funciones helper para labels, colores, timing
├── hooks/
│   ├── index.ts                    # Barrel export
│   ├── useTemplateVariables.ts     # Hook existente
│   └── useNotificationTemplates.ts # Hook para CRUD de templates
├── components/
│   └── templates/
│       ├── index.ts                # Barrel export
│       ├── TemplateCard.tsx        # Componente de tarjeta de template
│       └── TemplateForm.tsx        # Formulario reutilizable
└── pages/
    └── NotificationTemplatesPage.tsx (362 líneas)
```

## Cambios Principales

### 1. **Tipos Centralizados** (`types/index.ts`)
- `NotificationTemplate`: Interfaz del template
- `CreateNotificationTemplateForm`: Interfaz del formulario
- `INITIAL_FORM_DATA`: Estado inicial del formulario

### 2. **Utilidades** (`utils/templateHelpers.ts`)
- `getCategoryLabel()`: Etiquetas de categorías
- `getCategoryColor()`: Colores de categorías
- `getPriorityLabel()`: Etiquetas de prioridades
- `getPriorityColor()`: Colores de prioridades
- `getTimingDescription()`: Descripción legible del timing
- `buildTimingConfig()`: Constructor de configuración de timing

### 3. **Hook Personalizado** (`hooks/useNotificationTemplates.ts`)
Maneja toda la lógica de estado y API:
- `templates`: Lista de templates
- `loading`, `error`, `submitting`, `successMessage`: Estados
- `fetchTemplates()`: Fetch inicial
- `createTemplate()`: Crear template
- `updateTemplate()`: Actualizar template
- `deleteTemplate()`: Eliminar template
- `clearMessages()`: Limpiar mensajes

### 4. **Componentes Reutilizables**

#### `TemplateCard.tsx`
Muestra un template con:
- Header con nombre, código, categoría, prioridad, estado
- Descripción
- Mensaje del template
- Detalles (timing, entity_type, auto-assign)
- Botones de acción (editar, eliminar)

#### `TemplateForm.tsx`
Formulario completo reutilizado para crear y editar:
- Campos de código y nombre
- Descripción
- Categoría y tipo de entidad
- Mensaje con panel de variables
- Configuración de timing
- Prioridad
- Checkboxes (activo, auto-assign)
- Botones de acción

### 5. **Página Principal Simplificada** (`NotificationTemplatesPage.tsx`)
Reducida de **1129 a 362 líneas** (68% de reducción):
- Solo maneja estado de modales
- Usa hooks personalizados para lógica
- Usa componentes modulares para UI
- No hay duplicación entre modales

## Beneficios

### ✅ Mantenibilidad
- Código organizado por responsabilidad
- Fácil de encontrar y modificar funcionalidad específica
- Sin duplicación de código

### ✅ Reutilización
- `TemplateForm` se usa para crear y editar
- Helpers reutilizables en otros componentes
- Hook puede usarse en otras páginas

### ✅ Testabilidad
- Funciones puras en `templateHelpers.ts`
- Hook aislado para testing
- Componentes desacoplados

### ✅ Legibilidad
- Componente principal más corto y claro
- Lógica de negocio separada de UI
- Nombres descriptivos y documentación

### ✅ Escalabilidad
- Fácil agregar nuevos tipos de templates
- Simple extender funcionalidad
- Estructura clara para nuevos desarrolladores

## Comparación de Código

### Antes (1129 líneas)
```tsx
// Todo en un archivo gigante
export default function AdminNotificationTemplates() {
  // 70 líneas de estado y lógica
  const [templates, setTemplates] = useState<NotificationTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  // ... 10+ estados más

  // 25 líneas de fetch
  const fetchTemplates = async () => { ... }

  // 65 líneas de create
  const handleCreateTemplate = async (e: React.FormEvent) => { ... }

  // 70 líneas de update
  const handleUpdateTemplate = async (e: React.FormEvent) => { ... }

  // 30 líneas de delete
  const handleDeleteTemplate = async (templateId: string) => { ... }

  // 50 líneas de helpers
  const getCategoryLabel = (category: string) => { ... }
  const getCategoryColor = (category: string) => { ... }
  // ... más helpers

  return (
    // 600+ líneas de JSX con modales duplicados
  )
}
```

### Después (362 líneas)
```tsx
export default function AdminNotificationTemplates() {
  // 5 líneas de estado (solo modales)
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [formData, setFormData] = useState<CreateNotificationTemplateForm>(INITIAL_FORM_DATA);
  // ...

  // Hooks personalizados (2 líneas)
  const { templates, loading, createTemplate, updateTemplate, deleteTemplate } =
    useNotificationTemplates(session?.access_token);

  // Handlers simples (30 líneas total)
  const handleCreateTemplate = async (e: React.FormEvent) => {
    e.preventDefault();
    const success = await createTemplate(formData);
    if (success) {
      setShowCreateModal(false);
      setFormData(INITIAL_FORM_DATA);
    }
  };

  return (
    // JSX limpio con componentes modulares
    <TemplateCard template={template} onEdit={handleEditClick} onDelete={setDeleteConfirm} />
    <TemplateForm formData={formData} onChange={setFormData} onSubmit={handleCreateTemplate} />
  )
}
```

## Archivos Creados

1. `/frontend/src/features/admin/notifications/types/index.ts`
2. `/frontend/src/features/admin/notifications/utils/index.ts`
3. `/frontend/src/features/admin/notifications/utils/templateHelpers.ts`
4. `/frontend/src/features/admin/notifications/hooks/useNotificationTemplates.ts`
5. `/frontend/src/features/admin/notifications/components/templates/index.ts`
6. `/frontend/src/features/admin/notifications/components/templates/TemplateCard.tsx`
7. `/frontend/src/features/admin/notifications/components/templates/TemplateForm.tsx`

## Archivos Modificados

1. `/frontend/src/features/admin/notifications/pages/NotificationTemplatesPage.tsx` (refactorizado)
2. `/frontend/src/features/admin/notifications/hooks/index.ts` (agregado export)

## Testing

✅ No hay errores de TypeScript
✅ Estructura modular completa
✅ Todos los imports funcionando correctamente

## Próximos Pasos Recomendados

1. Aplicar el mismo patrón a otros componentes grandes
2. Crear tests unitarios para hooks y helpers
3. Documentar convenciones de estructura
4. Considerar usar React Query para manejo de estado del servidor
