#!/bin/bash
# Script para ejecutar tests en Docker
# Uso: ./run_tests_docker.sh [test_file] [test_name]

set -e

# Colores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🐳 Running tests in Docker...${NC}"

# Argumentos opcionales
TEST_FILE=${1:-"tests/test_f29_service_e2e.py"}
TEST_NAME=${2:-""}

# Construir comando pytest
if [ -z "$TEST_NAME" ]; then
    PYTEST_CMD="pytest ${TEST_FILE} -v -s"
else
    PYTEST_CMD="pytest ${TEST_FILE}::${TEST_NAME} -v -s"
fi

echo -e "${YELLOW}Test command: ${PYTEST_CMD}${NC}"
echo ""

# Ejecutar en Docker Compose
docker compose exec backend-v2 /bin/bash -c "source .venv/bin/activate && ${PYTEST_CMD}"

echo ""
echo -e "${GREEN}✅ Tests completed!${NC}"
