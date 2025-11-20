#!/bin/bash

# Script de verificación de infraestructura de agentes
# Backend V2 - SII Integration Service

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 Verificación de Infraestructura de Agentes"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo

# Contador de errores
ERRORS=0

# 1. Verificar estructura de directorios
echo "📁 Verificando estructura de directorios..."
REQUIRED_DIRS=(
    "app/agents"
    "app/agents/config"
    "app/agents/core"
    "app/agents/guardrails"
    "app/agents/guardrails/implementations"
    "app/agents/instructions"
    "app/agents/orchestration"
    "app/agents/specialized"
    "app/agents/tools"
    "app/agents/tools/feedback"
    "app/agents/tools/memory"
    "app/agents/tools/orchestration"
    "app/agents/tools/payroll"
    "app/agents/tools/settings"
    "app/agents/tools/tax"
    "app/agents/tools/widgets"
    "app/agents/tools/widgets/builders"
    "app/agents/ui_tools"
    "app/agents/ui_tools/core"
    "app/agents/ui_tools/tools"
)

for dir in "${REQUIRED_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        echo "  ✅ $dir"
    else
        echo "  ❌ $dir - NO EXISTE"
        ERRORS=$((ERRORS + 1))
    fi
done

echo

# 2. Contar archivos Python
echo "📊 Contando archivos Python..."
TOTAL_PY_FILES=$(find app/agents -name "*.py" -type f | wc -l | tr -d ' ')
echo "  Total de archivos .py: $TOTAL_PY_FILES"

if [ "$TOTAL_PY_FILES" -eq 90 ]; then
    echo "  ✅ Número correcto de archivos (90)"
else
    echo "  ⚠️  Se esperaban 90 archivos, se encontraron $TOTAL_PY_FILES"
    ERRORS=$((ERRORS + 1))
fi

echo

# 3. Verificar archivos clave
echo "🔑 Verificando archivos clave..."
KEY_FILES=(
    "app/agents/__init__.py"
    "app/agents/runner.py"
    "app/agents/core/context.py"
    "app/agents/core/context_loader.py"
    "app/agents/orchestration/handoffs_manager.py"
    "app/agents/orchestration/multi_agent_orchestrator.py"
    "app/agents/specialized/general_knowledge_agent.py"
    "app/agents/specialized/tax_documents_agent.py"
    "app/agents/tools/tax/f29_tools.py"
    "app/agents/tools/tax/documentos_tributarios_tools.py"
)

for file in "${KEY_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✅ $file"
    else
        echo "  ❌ $file - NO EXISTE"
        ERRORS=$((ERRORS + 1))
    fi
done

echo

# 4. Compilar todos los archivos Python
echo "🔨 Compilando archivos Python..."
COMPILE_OUTPUT=$(find app/agents -name "*.py" -type f -exec python3 -m py_compile {} + 2>&1)
COMPILE_EXIT=$?

if [ $COMPILE_EXIT -eq 0 ]; then
    echo "  ✅ Todos los archivos compilan correctamente"
else
    echo "  ❌ Errores de compilación encontrados:"
    echo "$COMPILE_OUTPUT" | head -20
    ERRORS=$((ERRORS + 1))
fi

echo

# 5. Verificar agentes especializados
echo "🤖 Verificando agentes especializados..."
SPECIALIZED_AGENTS=(
    "app/agents/specialized/general_knowledge_agent.py"
    "app/agents/specialized/tax_documents_agent.py"
    "app/agents/specialized/monthly_taxes_agent.py"
    "app/agents/specialized/payroll_agent.py"
    "app/agents/specialized/expense_agent.py"
    "app/agents/specialized/feedback_agent.py"
    "app/agents/specialized/settings_agent.py"
)

for agent in "${SPECIALIZED_AGENTS[@]}"; do
    if [ -f "$agent" ]; then
        agent_name=$(basename "$agent" .py)
        echo "  ✅ $agent_name"
    else
        echo "  ❌ $agent - NO EXISTE"
        ERRORS=$((ERRORS + 1))
    fi
done

echo

# 6. Verificar herramientas de agentes
echo "🔧 Verificando herramientas de agentes..."
TOOL_CATEGORIES=(
    "app/agents/tools/tax"
    "app/agents/tools/payroll"
    "app/agents/tools/widgets"
    "app/agents/tools/feedback"
    "app/agents/tools/memory"
    "app/agents/tools/settings"
    "app/agents/tools/orchestration"
)

for category in "${TOOL_CATEGORIES[@]}"; do
    if [ -d "$category" ]; then
        tool_count=$(find "$category" -maxdepth 1 -name "*.py" -not -name "__init__.py" | wc -l | tr -d ' ')
        category_name=$(basename "$category")
        echo "  ✅ $category_name ($tool_count herramientas)"
    else
        echo "  ❌ $category - NO EXISTE"
        ERRORS=$((ERRORS + 1))
    fi
done

echo

# 7. Verificar UI tools
echo "🎨 Verificando UI tools..."
UI_TOOL_COUNT=$(find app/agents/ui_tools/tools -maxdepth 1 -name "*.py" -not -name "__init__.py" | wc -l | tr -d ' ')
echo "  UI tools implementadas: $UI_TOOL_COUNT"
if [ "$UI_TOOL_COUNT" -gt 0 ]; then
    echo "  ✅ UI tools presentes"
else
    echo "  ⚠️  No se encontraron UI tools"
fi

echo

# Resumen final
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ $ERRORS -eq 0 ]; then
    echo "✅ VERIFICACIÓN EXITOSA"
    echo "   Infraestructura de agentes completamente instalada"
    echo "   Total de archivos: $TOTAL_PY_FILES"
    echo "   Errores de compilación: 0"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    exit 0
else
    echo "❌ VERIFICACIÓN FALLIDA"
    echo "   Se encontraron $ERRORS errores"
    echo "   Revise los mensajes anteriores para más detalles"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    exit 1
fi
