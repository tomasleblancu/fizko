# Sistema Chateable

El sistema chateable permite hacer que cualquier elemento de la UI sea clickeable para enviar mensajes al chat de forma contextual.

## Archivos del Sistema

```
frontend-nextjs/
├── src/
│   ├── types/
│   │   └── chateable.ts                    # Tipos TypeScript
│   ├── hooks/
│   │   └── useChateableClick.ts            # Hook para elementos individuales
│   ├── components/ui/
│   │   └── ChateableWrapper.tsx            # Componente wrapper
│   └── styles/
│       └── chateable.css                   # Estilos CSS
```

## Componentes y Hooks

### 1. `ChateableWrapper` - Para componentes completos

Envuelve componentes enteros (cards, filas de tabla, etc.) para hacerlos clickeables.

**Uso básico:**

```tsx
import { ChateableWrapper } from '@/components/ui/ChateableWrapper';

// Mensaje simple
<ChateableWrapper message="Explícame este resumen de impuestos">
  <TaxSummaryCard {...props} />
</ChateableWrapper>

// Mensaje con función generadora
<ChateableWrapper
  message={(data) => `Dame más detalles sobre ${data.documentType} folio ${data.folio}`}
  contextData={{ documentType: 'Factura', folio: '12345' }}
  uiComponent="DocumentCard"
  entityId={document.id}
  entityType="sales_document"
>
  <DocumentCard document={document} />
</ChateableWrapper>
```

**Para filas de tabla (use `as="fragment"`):**

```tsx
{documents.map((doc) => (
  <ChateableWrapper
    key={doc.id}
    as="fragment"
    message={`Analiza la factura ${doc.folio}`}
    uiComponent="DocumentRow"
    entityId={doc.id}
    entityType="sales_document"
  >
    <tr className="hover:bg-slate-50">
      <td>{doc.folio}</td>
      <td>{doc.amount}</td>
    </tr>
  </ChateableWrapper>
))}
```

### 2. `useChateableClick` - Para elementos individuales

Hook para hacer clickeable un elemento específico sin envolverlo.

**Uso:**

```tsx
import { useChateableClick } from '@/hooks/useChateableClick';

function TaxAmountBadge({ amount, period }) {
  const chateableProps = useChateableClick({
    message: `¿Por qué debo pagar $${amount} en impuestos este período?`,
    contextData: { amount, period },
    uiComponent: "TaxAmountBadge",
  });

  return (
    <div
      {...chateableProps}
      className="rounded-lg bg-red-100 px-3 py-1"
    >
      ${amount}
    </div>
  );
}
```

## Props y Opciones

### ChateableWrapper Props

| Prop | Tipo | Requerido | Descripción |
|------|------|-----------|-------------|
| `message` | `string \| ((data) => string)` | ✅ | Mensaje a enviar o función generadora |
| `contextData` | `object` | ❌ | Datos contextuales para la función generadora |
| `uiComponent` | `string` | ❌ | Nombre del componente (metadata para backend) |
| `entityId` | `string` | ❌ | ID de la entidad (documento, contacto, etc.) |
| `entityType` | `string` | ❌ | Tipo de entidad (`sales_document`, `contact`, etc.) |
| `onClick` | `() => void` | ❌ | Handler adicional (se llama antes de enviar) |
| `disabled` | `boolean` | ❌ | Deshabilitar funcionalidad chateable |
| `className` | `string` | ❌ | Clases CSS adicionales |
| `as` | `'div' \| 'span' \| 'fragment'` | ❌ | Tipo de elemento (default: `'div'`) |

### useChateableClick Options

Mismas opciones que ChateableWrapper excepto `children`, `className`, y `as`.

## Metadata para Backend

El sistema envía metadata al backend que puede usar para contexto:

```typescript
{
  ui_component: "DocumentCard",     // Nombre del componente
  entity_id: "doc_123",             // ID de la entidad
  entity_type: "sales_document"     // Tipo de entidad
}
```

### Entity Types Sugeridos

- `sales_document` - Documento de venta (factura, boleta)
- `purchase_document` - Documento de compra
- `contact` - Contacto (cliente/proveedor)
- `person` - Persona (empleado, colaborador)
- `tax_summary` - Resumen tributario
- `f29_form` - Formulario 29
- `calendar_event` - Evento de calendario

## Ejemplos Completos

### Ejemplo 1: Card de Contacto

```tsx
import { ChateableWrapper } from '@/components/ui/ChateableWrapper';

function ContactCard({ contact }) {
  return (
    <ChateableWrapper
      message={(data) =>
        `Dame más información sobre ${data.name} (RUT: ${data.rut})`
      }
      contextData={{
        name: contact.business_name,
        rut: contact.rut,
        type: contact.contact_type
      }}
      uiComponent="ContactCard"
      entityId={contact.id}
      entityType="contact"
    >
      <div className="rounded-lg border p-4">
        <h3>{contact.business_name}</h3>
        <p>{contact.rut}</p>
        <span>{contact.contact_type}</span>
      </div>
    </ChateableWrapper>
  );
}
```

### Ejemplo 2: Resumen de Impuestos

```tsx
function TaxSummaryCard({ summary, period }) {
  return (
    <ChateableWrapper
      message={`Explícame mi resumen de impuestos de ${period}`}
      contextData={{ period, ...summary }}
      uiComponent="TaxSummaryCard"
      entityType="tax_summary"
    >
      <div className="rounded-lg bg-gradient-to-br from-emerald-500 to-teal-600 p-6 text-white">
        <h3>Impuestos a Pagar</h3>
        <p className="text-3xl font-bold">${summary.total}</p>
      </div>
    </ChateableWrapper>
  );
}
```

### Ejemplo 3: Tabla de Documentos

```tsx
function DocumentsTable({ documents }) {
  return (
    <table>
      <thead>
        <tr>
          <th>Folio</th>
          <th>Monto</th>
          <th>Estado</th>
        </tr>
      </thead>
      <tbody>
        {documents.map((doc) => (
          <ChateableWrapper
            key={doc.id}
            as="fragment"
            message={`Analiza la ${doc.document_type} folio ${doc.folio}`}
            contextData={doc}
            uiComponent="DocumentRow"
            entityId={doc.id}
            entityType="sales_document"
          >
            <tr>
              <td>{doc.folio}</td>
              <td>${doc.total_amount}</td>
              <td>{doc.status}</td>
            </tr>
          </ChateableWrapper>
        ))}
      </tbody>
    </table>
  );
}
```

### Ejemplo 4: Elemento Individual con Hook

```tsx
import { useChateableClick } from '@/hooks/useChateableClick';

function QuickStatBadge({ label, value, explanation }) {
  const chateableProps = useChateableClick({
    message: explanation,
    uiComponent: "QuickStatBadge",
  });

  return (
    <div
      {...chateableProps}
      className="rounded-lg border border-slate-200 bg-white p-4"
    >
      <p className="text-sm text-slate-600">{label}</p>
      <p className="text-2xl font-bold">{value}</p>
    </div>
  );
}

// Uso:
<QuickStatBadge
  label="IVA a Pagar"
  value="$1,234,567"
  explanation="¿Cómo se calculó este monto de IVA?"
/>
```

## Estilos CSS

Los estilos se aplican automáticamente:

- `.chateable-wrapper` - Para componentes envueltos
- `.chateable-element` - Para elementos individuales
- Efectos hover con elevación y sombra
- Soporte para modo oscuro
- Estados focus y disabled
- Transiciones suaves

## Accesibilidad

El sistema incluye soporte completo de accesibilidad:

- ✅ `role="button"` para lectores de pantalla
- ✅ `tabIndex` para navegación por teclado
- ✅ `onKeyDown` para Enter y Espacio
- ✅ `aria-disabled` para estado deshabilitado
- ✅ Focus visible con outline

## Buenas Prácticas

### ✅ Hacer

- Usar mensajes descriptivos y contextuales
- Incluir metadata relevante (uiComponent, entityId, entityType)
- Usar `as="fragment"` para filas de tabla
- Proveer contextData cuando uses funciones generadoras

### ❌ Evitar

- Anidar ChateableWrappers (usa `e.stopPropagation()`)
- Mensajes genéricos sin contexto
- Olvidar el modo disabled cuando sea necesario
- Usar para elementos que ya tienen otra acción primaria

## Integración con Backend

El backend recibe:

```python
# En el router de chatkit
@router.post("/chatkit")
async def chatkit_endpoint(request: ChatkitRequest):
    # Los mensajes tienen metadata:
    message.metadata = {
        "ui_component": "DocumentCard",
        "entity_id": "doc_123",
        "entity_type": "sales_document"
    }

    # El agente puede usar esta información para:
    # 1. Cargar contexto específico de la entidad
    # 2. Personalizar la respuesta según el componente
    # 3. Trackear qué elementos son más consultados
```

## Testing

Ejemplo de test:

```tsx
import { render, fireEvent } from '@testing-library/react';
import { ChateableWrapper } from '@/components/ui/ChateableWrapper';

test('sends message on click', () => {
  const mockSendMessage = jest.fn();

  // Mock useChatKit
  jest.mock('@openai/chatkit-react', () => ({
    useChatKit: () => ({
      sendMessage: mockSendMessage
    })
  }));

  const { getByRole } = render(
    <ChateableWrapper message="Test message">
      <div>Click me</div>
    </ChateableWrapper>
  );

  fireEvent.click(getByRole('button'));

  expect(mockSendMessage).toHaveBeenCalledWith('Test message');
});
```

## Troubleshooting

**Problema:** El click no envía mensaje
- ✅ Verificar que ChatKit esté inicializado
- ✅ Revisar consola por errores
- ✅ Confirmar que `disabled` no esté en true

**Problema:** Estilos no se aplican
- ✅ Verificar que `@/styles/chateable.css` esté importado en layout
- ✅ Revisar que las clases CSS estén presentes en el DOM

**Problema:** Tabla se rompe con ChateableWrapper
- ✅ Usar `as="fragment"` para elementos `<tr>`
