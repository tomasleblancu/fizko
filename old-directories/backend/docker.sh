#!/bin/bash
# ============================================
# Docker Helper Script - Fizko Backend
# ============================================
# Script de ayuda para manejar Docker Compose con profiles
#
# Uso:
#   ./docker.sh up          # Servicios básicos (backend, workers, redis)
#   ./docker.sh up-all      # Todo (básicos + flower + ngrok)
#   ./docker.sh up-dev      # Básicos + ngrok
#   ./docker.sh up-mon      # Básicos + flower
#   ./docker.sh down        # Detener básicos
#   ./docker.sh down-all    # Detener todo
#   ./docker.sh logs        # Ver logs de todos
#   ./docker.sh logs backend # Ver logs de un servicio
#   ./docker.sh ps          # Ver estado
#   ./docker.sh ngrok-url   # Ver URL de ngrok
# ============================================

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
show_help() {
    echo -e "${BLUE}Fizko Backend - Docker Helper${NC}"
    echo ""
    echo "Comandos disponibles:"
    echo ""
    echo -e "  ${GREEN}up${NC}          - Iniciar servicios básicos (backend, workers, redis)"
    echo -e "  ${GREEN}up-all${NC}      - Iniciar TODO (básicos + flower + ngrok)"
    echo -e "  ${GREEN}up-dev${NC}      - Iniciar básicos + ngrok (para webhooks)"
    echo -e "  ${GREEN}up-mon${NC}      - Iniciar básicos + flower (monitoring)"
    echo -e "  ${GREEN}down${NC}        - Detener servicios básicos"
    echo -e "  ${GREEN}down-all${NC}    - Detener TODO incluyendo profiles"
    echo -e "  ${GREEN}restart${NC}     - Reiniciar servicios básicos"
    echo -e "  ${GREEN}logs${NC}        - Ver logs de todos los servicios"
    echo -e "  ${GREEN}logs <srv>${NC}  - Ver logs de un servicio específico"
    echo -e "  ${GREEN}ps${NC}          - Ver estado de contenedores"
    echo -e "  ${GREEN}ngrok-url${NC}   - Mostrar URL pública de ngrok"
    echo -e "  ${GREEN}rebuild${NC}     - Rebuild de imágenes"
    echo ""
    echo "Ejemplos:"
    echo "  ./docker.sh up-all           # Todo el stack"
    echo "  ./docker.sh logs backend     # Solo logs del backend"
    echo "  ./docker.sh down-all         # Detener todo"
}

ngrok_url() {
    echo -e "${YELLOW}→${NC} Obteniendo URL de ngrok..."
    URL=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null | grep -o '"public_url":"https://[^"]*' | head -1 | cut -d'"' -f4)

    if [ -z "$URL" ]; then
        echo -e "${YELLOW}⚠${NC}  ngrok no está corriendo o no responde"
        echo -e "   Iniciar con: ./docker.sh up-dev o up-all"
    else
        echo -e "${GREEN}✓${NC} URL pública: ${BLUE}$URL${NC}"
        echo ""
        echo "Webhook para Kapso:"
        echo "  ${BLUE}$URL/api/whatsapp/webhook${NC}"
        echo ""
        echo "Dashboard ngrok:"
        echo "  ${BLUE}http://localhost:4040${NC}"
    fi
}

# Main
case "$1" in
    up)
        echo -e "${GREEN}🚀 Iniciando servicios básicos...${NC}"
        docker-compose up -d
        echo -e "${GREEN}✓${NC} Servicios iniciados"
        echo ""
        echo "URLs disponibles:"
        echo "  Backend:  http://localhost:8000"
        echo "  API Docs: http://localhost:8000/docs"
        ;;

    up-all)
        echo -e "${GREEN}🚀 Iniciando TODO (básicos + flower + ngrok)...${NC}"
        docker-compose --profile monitoring --profile dev up -d
        sleep 3
        echo -e "${GREEN}✓${NC} Todos los servicios iniciados"
        echo ""
        echo "URLs disponibles:"
        echo "  Backend:  http://localhost:8000"
        echo "  Flower:   http://localhost:5555"
        echo "  ngrok UI: http://localhost:4040"
        echo ""
        ngrok_url
        ;;

    up-dev)
        echo -e "${GREEN}🚀 Iniciando básicos + ngrok...${NC}"
        docker-compose --profile dev up -d
        sleep 3
        echo -e "${GREEN}✓${NC} Servicios iniciados"
        echo ""
        ngrok_url
        ;;

    up-mon)
        echo -e "${GREEN}🚀 Iniciando básicos + flower...${NC}"
        docker-compose --profile monitoring up -d
        echo -e "${GREEN}✓${NC} Servicios iniciados"
        echo ""
        echo "URLs disponibles:"
        echo "  Backend: http://localhost:8000"
        echo "  Flower:  http://localhost:5555"
        ;;

    down)
        echo -e "${YELLOW}⏹${NC}  Deteniendo servicios básicos..."
        docker-compose down
        echo -e "${GREEN}✓${NC} Servicios detenidos"
        ;;

    down-all)
        echo -e "${YELLOW}⏹${NC}  Deteniendo TODOS los servicios..."
        docker-compose --profile monitoring --profile dev down
        echo -e "${GREEN}✓${NC} Todos los servicios detenidos"
        ;;

    restart)
        echo -e "${YELLOW}🔄${NC} Reiniciando servicios..."
        docker-compose restart
        echo -e "${GREEN}✓${NC} Servicios reiniciados"
        ;;

    logs)
        if [ -z "$2" ]; then
            docker-compose logs -f
        else
            docker-compose logs -f "$2"
        fi
        ;;

    ps)
        docker-compose ps
        ;;

    ngrok-url)
        ngrok_url
        ;;

    rebuild)
        echo -e "${YELLOW}🔨${NC} Rebuilding imágenes..."
        docker-compose build --no-cache
        echo -e "${GREEN}✓${NC} Rebuild completado"
        ;;

    help|--help|-h|"")
        show_help
        ;;

    *)
        echo -e "${YELLOW}⚠${NC}  Comando desconocido: $1"
        echo ""
        show_help
        exit 1
        ;;
esac
