#!/bin/bash
# Script para iniciar el servicio de integración SII

echo "🚀 Iniciando SII Integration Service..."
echo ""

# Verificar si existe el entorno virtual
if [ ! -d ".venv" ]; then
    echo "⚠️  No se encontró el entorno virtual. Ejecutando 'uv sync'..."
    uv sync
    echo ""
fi

# Iniciar el servidor
echo "🌐 Iniciando servidor en http://localhost:8090"
echo "📚 Documentación disponible en http://localhost:8090/docs"
echo ""

uv run uvicorn app.main:app --reload --port 8090
