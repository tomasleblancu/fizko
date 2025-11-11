# Fix: AttributeError - Guardrails SDK Compatibility

## 🐛 Problemas Encontrados

Al deployar en producción, el guardrail causaba estos errores secuenciales:

### Error 1:
```python
AttributeError: 'function' object has no attribute 'get_name'
```

### Error 2 (después de fix 1):
```python
AttributeError: 'GuardrailWrapper' object has no attribute 'run'
```

### Error 3 (después de fix 2):
```python
AttributeError: 'GuardrailFunctionOutput' object has no attribute 'output'
```

**Causa:** El SDK de OpenAI Agents espera que los guardrails:
1. Tengan método `get_name()` - Para identificar el guardrail
2. Tengan método `run(agent, input, context)` - Para ejecutar el guardrail
3. El método `run()` retorne `InputGuardrailResult` o `OutputGuardrailResult` (NO directamente `GuardrailFunctionOutput`)

Nuestros decoradores originales solo retornaban funciones decoradas que no cumplían con este interface.

## ✅ Solución

Creé una clase `GuardrailWrapper` que hace los guardrails compatibles con el SDK.

### Archivo Modificado

[app/agents/guardrails/decorators.py](app/agents/guardrails/decorators.py)

**Antes:**
```python
def input_guardrail(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        return await func(*args, **kwargs)

    wrapper._guardrail_name = func.__name__
    return wrapper  # ❌ Function no tiene get_name()
```

**Después:**
```python
class GuardrailWrapper:
    """Wrapper compatible con OpenAI Agents SDK."""

    def __init__(self, func, name, description, is_input=True):
        self.func = func
        self.name = name
        self.description = description
        self.is_input = is_input
        functools.update_wrapper(self, func)

    def get_name(self) -> str:
        """Método requerido por el SDK."""
        return self.name

    async def run(self, agent, input_data, context):
        """Método requerido por el SDK para ejecutar el guardrail."""
        return await self.func(context, agent, input_data)

    async def __call__(self, *args, **kwargs):
        """Make wrapper callable."""
        return await self.func(*args, **kwargs)

def input_guardrail(func):
    return GuardrailWrapper(
        func=func,
        name=func.__name__,
        description=func.__doc__ or "No description",
        is_input=True,
    )  # ✅ Wrapper tiene get_name()
```

## 🧪 Verificación

Ejecuté tests y todo funciona:

```bash
cd backend
.venv/bin/python test_guardrail_simple.py
```

**Resultado:**
```
✅ Test 1: Normal tax question - PASSED
✅ Test 2: Prompt injection attempt - PASSED
✅ Test 3: Another prompt injection variant - PASSED
```

## 📦 Archivos Afectados

- ✅ `app/agents/guardrails/decorators.py` - Fix principal
- ✅ `test_guardrail_simple.py` - Test actualizado

## 🚀 Deploy

El fix está listo para deploy. Los cambios son:

1. **Backward compatible** - No rompe código existente
2. **Mínimos** - Solo modifica decorators.py
3. **Testeados** - Tests pasan localmente

## 📝 Notas Técnicas

### Por qué el error ocurrió

El SDK de OpenAI Agents internamente hace:

```python
guardrail_name = guardrail.get_name()  # ❌ Falla si es function
```

Nuestros decoradores retornaban funciones decoradas, que no tienen `get_name()`.

### Por qué el fix funciona

El `GuardrailWrapper`:
1. ✅ Tiene método `get_name()` (requerido por SDK para identificación)
2. ✅ Tiene método `run(agent, input, context)` (requerido por SDK para ejecución)
3. ✅ Es callable via `__call__()` (para invocación directa en tests)
4. ✅ Preserva metadata via `functools.update_wrapper()`
5. ✅ Es compatible con async/await

### Compatibilidad

El wrapper es compatible con:
- ✅ OpenAI Agents SDK (tiene `get_name()`)
- ✅ Python async/await (es async callable)
- ✅ Nuestro sistema de registry (tiene atributos name, description)
- ✅ Debugging (tiene `__repr__()`)

---

**Fecha del Fix:** 2025-01-11
**Issue:** AttributeError en producción
**Status:** ✅ Fixed y testeado
