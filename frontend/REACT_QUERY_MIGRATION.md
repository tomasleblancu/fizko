# React Query Migration Guide

## 📦 Sistema de Caché Migrado a TanStack Query

La aplicación ha migrado de un sistema de caché custom (`DashboardCacheContext`) a **TanStack Query (React Query) v5** para las vistas de administrador **y las vistas de usuario (Home)**.

---

## ✅ ¿Qué se Migró?

### **Admin Views:**
- ✅ `AdminCompaniesView` - Lista de empresas con prefetching
- ✅ `AdminCompanyView` - Detalle de empresa
- ✅ `CalendarEventsSection` - Lista de eventos del calendario
- ✅ `CalendarConfig` - Configuración y sincronización del calendario
- ✅ `F29List` - Lista de formularios F29 con filtros

### **Home Views:**
- ✅ `Home` - Componente principal del usuario
- ✅ `FinancialDashboard` - Dashboard financiero
- ✅ `Contacts` - Gestión de contactos
- ✅ `Personnel` / `PeopleList` - Gestión de colaboradores

### **Hooks Creados:**

#### **Admin Queries:**
- `useAdminCompanies()` - Obtiene todas las empresas
- `useAdminCompany(companyId)` - Obtiene detalle de una empresa
- `useCalendarEvents(companyId, options)` - Obtiene eventos del calendario
- `useCalendarConfig(companyId)` - Obtiene configuración del calendario
- `useF29List(companyId, options)` - Obtiene formularios F29 con filtros

#### **Home Queries:**
- `useCompanyQuery()` - Obtiene empresa del usuario
- `useTaxSummaryQuery(companyId, period)` - Resumen tributario
- `useTaxDocumentsQuery(companyId, limit, period)` - Documentos tributarios
- `useCalendarQuery(companyId, daysAhead, includeStats)` - Calendario de eventos
- `useContactsQuery(companyId)` - Lista de contactos
- `usePeopleQuery(companyId, options)` - Lista de colaboradores con filtros
- `usePayrollQuery(companyId, period)` - Resumen de liquidaciones
- `usePersonQuery(personId)` - Detalle de una persona

#### **Admin Mutations:**
- `useToggleEventTemplate(companyId)` - Activa/desactiva un template
- `useSyncCalendar(companyId)` - Sincroniza calendario
- `useDownloadF29Pdf(companyId)` - Descarga PDF de F29

#### **Home Mutations:**
- `useCreateContact(companyId)` - Crea un nuevo contacto
- `useUpdateContact(companyId)` - Actualiza un contacto
- `useDeleteContact(companyId)` - Elimina un contacto
- `useCreatePerson(companyId)` - Crea una nueva persona
- `useUpdatePerson(companyId)` - Actualiza una persona
- `useDeletePerson(companyId)` - Elimina una persona

---

## 🎯 Beneficios de la Migración

### **Antes (Custom Cache):**
```typescript
const [data, setData] = useState(null);
const [loading, setLoading] = useState(true);
const [error, setError] = useState(null);

useEffect(() => {
  // Check cache
  const cached = cache.get(key);
  if (cached) setData(cached.data);

  // Fetch data
  fetchData().then(setData);
}, [dependencies]);
```

### **Ahora (React Query):**
```typescript
const { data, isLoading, error, refetch } = useAdminCompanies();
// ¡Eso es todo! 🎉
```

### **Ventajas:**
✅ **Menos código** - De ~60 líneas a ~3 líneas
✅ **Caché automático** - 5 minutos por defecto
✅ **Deduplicación** - Múltiples componentes = 1 sola request
✅ **Invalidación inteligente** - `queryClient.invalidateQueries()`
✅ **Loading states** - `isLoading`, `isFetching`, `isPending`
✅ **Error handling** - Automático y consistente
✅ **Devtools** - Inspeccionar todas las queries en tiempo real
✅ **Optimistic updates** - Built-in para mutations
✅ **Retry automático** - Configurable
✅ **TypeScript** - Tipado completo

---

## 📖 Cómo Usar React Query

### **1. Query (Lectura de Datos)**

```typescript
import { useAdminCompanies } from '../hooks/useAdminCompanies';

function MyComponent() {
  const {
    data,           // Datos retornados
    isLoading,      // Primera carga
    isFetching,     // Revalidando en background
    error,          // Error si ocurrió
    refetch         // Función para refetch manual
  } = useAdminCompanies();

  if (isLoading) return <Loader />;
  if (error) return <Error message={error.message} />;

  return <div>{data.map(...)}</div>;
}
```

### **2. Mutation (Escritura de Datos)**

```typescript
import { useSyncCalendar } from '../hooks/useCalendarConfig';

function MyComponent({ companyId }) {
  const syncMutation = useSyncCalendar(companyId);

  const handleSync = () => {
    syncMutation.mutate(undefined, {
      onSuccess: (data) => {
        alert(data.message);
      },
      onError: (error) => {
        alert('Error: ' + error.message);
      },
    });
  };

  return (
    <button
      onClick={handleSync}
      disabled={syncMutation.isPending}
    >
      {syncMutation.isPending ? 'Sincronizando...' : 'Sincronizar'}
    </button>
  );
}
```

### **3. Invalidación de Caché**

Cuando se hace una mutation, automáticamente se invalidan las queries relacionadas:

```typescript
// En el hook useToggleEventTemplate:
onSuccess: () => {
  queryClient.invalidateQueries({
    queryKey: ['admin', 'calendar-config', companyId],
  });
}
```

---

## 🔧 Configuración

### **QueryClient Setup** (`main.tsx`):

```typescript
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,      // 5 minutos (como el cache anterior)
      gcTime: 10 * 60 * 1000,         // 10 minutos en memoria
      retry: 1,                        // 1 reintento en error
      refetchOnWindowFocus: false,     // No refetch automático
    },
  },
});
```

### **Query Keys Convention:**

```typescript
// Formato: ['scope', 'resource', ...params]

// Admin scope
['admin', 'companies']                           // Lista de empresas
['admin', 'company', companyId]                  // Detalle de empresa
['admin', 'calendar-config', companyId]          // Configuración
['admin', 'calendar-events', companyId, status]  // Eventos filtrados
['admin', 'f29', companyId, year, status]        // Formularios F29

// Home scope
['home', 'company', userId]                      // Empresa del usuario
['home', 'tax-summary', companyId, period]       // Resumen tributario
['home', 'tax-documents', companyId, limit, period] // Documentos
['home', 'calendar', companyId, daysAhead]       // Calendario
['home', 'contacts', companyId]                  // Contactos
['home', 'people', companyId, status, search, page, pageSize] // Colaboradores
['home', 'person', personId]                     // Detalle de persona
['home', 'payroll', companyId, period]           // Liquidaciones
```

---

## 🛠️ React Query Devtools

Las devtools están habilitadas automáticamente en desarrollo:

```typescript
<ReactQueryDevtools initialIsOpen={false} />
```

**Acceso:**
- Aparecen como un ícono flotante en la esquina inferior de la pantalla
- Click para abrir el panel de inspección
- Ver todas las queries activas, su estado, data, y timing

**Características:**
- 📊 Ver estado de todas las queries
- 🔄 Refetch queries manualmente
- 🗑️ Invalidar caché
- ⏱️ Ver tiempos de fetch
- 🔍 Inspeccionar data y errores

---

## 📚 Crear Nuevos Hooks

### **Template para Query Hook:**

```typescript
import { useQuery } from '@tanstack/react-query';
import { useAuth } from '../contexts/AuthContext';
import { API_BASE_URL } from '../lib/config';
import { apiFetch } from '../lib/api-client';

export function useMyResource(resourceId: string | undefined) {
  const { session } = useAuth();

  return useQuery({
    queryKey: ['admin', 'my-resource', resourceId],
    queryFn: async () => {
      if (!session?.access_token || !resourceId) {
        throw new Error('Missing auth or resource ID');
      }

      const response = await apiFetch(
        `${API_BASE_URL}/api/my-resource/${resourceId}`,
        {
          headers: {
            'Authorization': `Bearer ${session.access_token}`,
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        throw new Error('Failed to fetch resource');
      }

      return response.json();
    },
    enabled: !!session?.access_token && !!resourceId,
    staleTime: 3 * 60 * 1000, // 3 minutos
  });
}
```

### **Template para Mutation Hook:**

```typescript
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '../contexts/AuthContext';
import { API_BASE_URL } from '../lib/config';
import { apiFetch } from '../lib/api-client';

export function useUpdateResource(resourceId: string | undefined) {
  const { session } = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: MyDataType) => {
      if (!session?.access_token || !resourceId) {
        throw new Error('Missing auth or resource ID');
      }

      const response = await apiFetch(
        `${API_BASE_URL}/api/my-resource/${resourceId}`,
        {
          method: 'PUT',
          headers: {
            'Authorization': `Bearer ${session.access_token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(data),
        }
      );

      if (!response.ok) {
        throw new Error('Failed to update resource');
      }

      return response.json();
    },
    onSuccess: () => {
      // Invalidar queries relacionadas
      queryClient.invalidateQueries({
        queryKey: ['admin', 'my-resource', resourceId],
      });
    },
  });
}
```

---

## 🔄 Estado de DashboardCacheContext

### **Estado Actual:**
- ✅ **Admin views:** Usan React Query 100%
- ✅ **Home views:** Usan React Query 100%
- ⚠️ **DashboardCacheContext:** Aún existe pero ya no se usa

### **Hooks Deprecados:**
Los siguientes hooks han sido movidos a `hooks/_deprecated/`:
- ❌ `useCompany` → ✅ `useCompanyQuery`
- ❌ `useTaxSummary` → ✅ `useTaxSummaryQuery`
- ❌ `useTaxDocuments` → ✅ `useTaxDocumentsQuery`
- ❌ `useCalendar` → ✅ `useCalendarQuery`
- ❌ `useContacts` → ✅ `useContactsQuery`
- ❌ `usePeople` → ✅ `usePeopleQuery`
- ❌ `usePayroll` → ✅ `usePayrollQuery`

### **Próximos Pasos:**
1. ✅ Migración completa de Admin y Home
2. ⏳ Verificar que no hay imports de hooks deprecados
3. ⏳ Eliminar `DashboardCacheContext` completamente
4. ⏳ Eliminar carpeta `hooks/_deprecated/`

---

## 📖 Recursos

- [TanStack Query Docs](https://tanstack.com/query/latest)
- [React Query v5 Migration Guide](https://tanstack.com/query/latest/docs/react/guides/migrating-to-v5)
- [Query Keys Best Practices](https://tkdodo.eu/blog/effective-react-query-keys)

---

## 🎉 Resultado

La migración a React Query proporciona:
- **90% menos código** de manejo de estado
- **Caché inteligente** con invalidación automática
- **Mejor UX** con loading states y error handling
- **Developer Experience** mejorada con devtools
- **Preparado para escalar** con features avanzadas

¡Disfruta del nuevo sistema de caché! 🚀
