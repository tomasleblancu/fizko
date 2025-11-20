#!/bin/bash
# Script para ejecutar tests E2E del SII Integration Service

set -e

echo "🧪 SII Integration Service - Test Runner"
echo "========================================"
echo ""

# Verificar que existe .env.test
if [ ! -f ".env.test" ]; then
    echo "❌ Error: .env.test no encontrado"
    echo ""
    echo "Por favor, crea el archivo .env.test con tus credenciales:"
    echo "  cp .env.test.example .env.test"
    echo "  nano .env.test"
    exit 1
fi

# Verificar que el servidor esté corriendo
echo "🔍 Verificando servidor..."
if ! curl -s http://localhost:8000/health > /dev/null; then
    echo "⚠️  Servidor no está corriendo en http://localhost:8000"
    echo ""
    echo "Por favor, inicia el servidor en otra terminal:"
    echo "  ./start.sh"
    echo ""
    exit 1
fi

echo "✅ Servidor está corriendo"
echo ""

# Instalar dependencias si es necesario
if [ ! -d ".venv" ]; then
    echo "📦 Instalando dependencias de test..."
    uv sync --extra dev
    echo ""
fi

# Ejecutar tests según argumento
case "${1:-all}" in
    all)
        echo "🧪 Ejecutando TODOS los tests..."
        echo ""
        uv run pytest tests/test_endpoints_e2e.py -v
        ;;

    quick)
        echo "⚡ Ejecutando tests rápidos (solo login y health)..."
        echo ""
        uv run pytest tests/test_endpoints_e2e.py::TestLoginEndpoint -v
        uv run pytest tests/test_endpoints_e2e.py::TestHealthEndpoint -v
        ;;

    flow)
        echo "🔄 Ejecutando test de flujo completo con cookies..."
        echo ""
        uv run pytest tests/test_endpoints_e2e.py::TestCookieReuseFlow::test_complete_flow_with_cookie_reuse -v -s
        ;;

    login)
        echo "🔐 Ejecutando tests de login..."
        echo ""
        uv run pytest tests/test_endpoints_e2e.py::TestLoginEndpoint -v -s
        ;;

    compras)
        echo "📥 Ejecutando tests de compras..."
        echo ""
        uv run pytest tests/test_endpoints_e2e.py::TestComprasEndpoint -v -s
        ;;

    ventas)
        echo "📤 Ejecutando tests de ventas..."
        echo ""
        uv run pytest tests/test_endpoints_e2e.py::TestVentasEndpoint -v -s
        ;;

    verify)
        echo "✅ Ejecutando tests de verificación de credenciales..."
        echo ""
        uv run pytest tests/test_endpoints_e2e.py::TestVerifyEndpoint -v -s
        ;;

    coverage)
        echo "📊 Ejecutando tests con coverage..."
        echo ""
        uv run pytest tests/test_endpoints_e2e.py --cov=app --cov-report=html --cov-report=term
        echo ""
        echo "✅ Coverage report generado en htmlcov/index.html"
        ;;

    *)
        echo "❌ Opción no reconocida: $1"
        echo ""
        echo "Uso: ./run_tests.sh [opción]"
        echo ""
        echo "Opciones disponibles:"
        echo "  all       - Ejecutar todos los tests (por defecto)"
        echo "  quick     - Tests rápidos (login + health)"
        echo "  flow      - Test de flujo completo con cookies"
        echo "  login     - Tests de login"
        echo "  compras   - Tests de compras"
        echo "  ventas    - Tests de ventas"
        echo "  verify    - Tests de verificación de credenciales"
        echo "  coverage  - Tests con coverage report"
        echo ""
        echo "Ejemplos:"
        echo "  ./run_tests.sh"
        echo "  ./run_tests.sh quick"
        echo "  ./run_tests.sh flow"
        echo "  ./run_tests.sh verify"
        exit 1
        ;;
esac

echo ""
echo "✅ Tests completados"
