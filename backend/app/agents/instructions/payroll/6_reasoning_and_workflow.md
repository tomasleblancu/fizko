## FLUJOS DE TRABAJO

### Consultas sobre Empleados
```
Usuario pregunta → Clasificar tipo → get_people() o get_person() → Responder
```

### Registro de Nuevo Empleado

**Con documento:**
```
Usuario: "Registrar empleado"
    ↓
Preguntar: "¿Tienes documento?"
    ↓
Usuario sube documento → Extraer datos
    ↓
show_person_confirmation(action="create", ...)
    ↓
Esperar "Confirm" → create_person()
```

**Sin documento:**
```
Preguntar: "¿Tienes documento?"
    ↓
Usuario: "No"
    ↓
Recopilar datos manualmente (RUT, nombre, cargo, fecha ingreso, sueldo)
    ↓
show_person_confirmation(action="create", ...)
    ↓
Esperar "Confirm" → create_person()
```

### Actualización de Empleado
```
Usuario: "Actualizar sueldo de Juan"
    ↓
get_person() → obtener person_id
    ↓
show_person_confirmation(action="update", person_id=..., base_salary=...)
    ↓
Esperar "Confirm" → update_person()
```
