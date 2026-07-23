#!/bin/bash

# Crear directorio de logs si no existe y configurar archivo de log con fecha/hora
LOG_DIR="./logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/deploy_$(date +'%Y%m%d_%H%M%S').log"

# Redirigir toda la salida estándar y de errores a la terminal y al archivo de log simultáneamente
exec > >(tee -i "$LOG_FILE") 2>&1

# Estilos de texto
BOLD='\033[1m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BOLD}${BLUE}============================================================${NC}"
echo -e "${BOLD}${BLUE}       DESPLIEGUE AUTOMÁTICO DE ODOO 18 CE - PROVECCHIO     ${NC}"
echo -e "${BOLD}${BLUE}============================================================${NC}"
echo -e "${GREEN} Registro de salida guardándose en: $LOG_FILE${NC}\n"

# Leer puerto y credenciales del .env
if [ -f .env ]; then
    # Cargar variables del .env
    set -a
    source .env
    set +a
else
    echo -e "${RED}Error: No se encontró el archivo .env${NC}"
    exit 1
fi

PORT=${WEB_PORT:-8085}
DB_NAME=${DB_NAME:-prod}
EMAIL=${ADMIN_EMAIL:-soporte@crossnexion.com}
PASS=${ADMIN_PASSWORD:-Cross1983_}
DB_VOLS=${DB_VOLUMES:-./db-data}
WEB_VOLS=${WEB_VOLUMES:-./web-data}

# Opción para limpiar base de datos y modo no interactivo
CLEAN_DB=false
AUTO_YES=false
for arg in "$@"; do
    case $arg in
        --clean) CLEAN_DB=true ;;
        -y|--yes) AUTO_YES=true ;;
    esac
done

if [ "$AUTO_YES" = false ]; then
    echo -e "\n${YELLOW}[!] ADVERTENCIA: Se detendrán los contenedores de Docker (db, web, init).${NC}"
    read -p "¿Desea continuar con el deploy? (s/N): " confirm
    if [[ ! "$confirm" =~ ^[sSyY]$ ]]; then
        echo -e "\n${RED}Operación cancelada por el usuario.${NC}"
        exit 0
    fi
fi

echo -e "\n${BLUE}[1/4] Deteniendo contenedores existentes...${NC}"
docker compose down

if [ "$CLEAN_DB" = false ] && [ "$AUTO_YES" = false ]; then
    echo -e "\n${YELLOW}¿Desea vaciar la base de datos y recrear el entorno desde cero? (s/N): ${NC}\c"
    read confirm_clean
    if [[ "$confirm_clean" =~ ^[sSyY]$ ]]; then
        CLEAN_DB=true
    fi
fi

if [ "$CLEAN_DB" = true ]; then
    if [ "$AUTO_YES" = false ]; then
        echo -e "\n${YELLOW}[!] ADVERTENCIA: Se eliminarán todos los volúmenes de datos de la base de datos.${NC}"
        read -p " ¿Confirma que desea vaciar la base de datos por completo? (s/N): " confirmacion
        if [[ ! "$confirmacion" =~ ^[sSyY]$ ]]; then
            echo -e "\n${RED}Operación de limpieza cancelada por el usuario.${NC}"
            exit 0
        fi
    fi
    # Usar contenedor temporal para borrar las carpetas del host que tienen permisos de root
    docker run --rm -v "${DB_VOLS}":/db -v "${WEB_VOLS}":/web alpine sh -c "rm -rf /db/* /web/*"
    echo -e "${GREEN}✓ Volúmenes de datos limpiados.${NC}"
fi

echo -e "\n${BLUE}[2/4] Iniciando contenedor de Base de Datos...${NC}"
docker compose up -d db5771

echo -e "\n${BLUE}[2.5/4] Construyendo imagen de Odoo 18 local...${NC}"
docker compose build web9049

echo -e "\n${BLUE}[3/4] Iniciando contenedor de Inicialización Automática...${NC}"
docker compose up -d init

echo -e "${YELLOW}[*] Siguiendo logs del contenedor de inicialización en tiempo real:${NC}\n"

# Seguir los logs de init_db hasta que el contenedor se detenga
docker logs -f odoo_init_db_18

# Obtener código de salida del contenedor init
if docker ps -a --format '{{.Names}}' | grep -q '^odoo_init_db_18$'; then
    EXIT_CODE=$(docker inspect odoo_init_db_18 --format='{{.State.ExitCode}}')
else
    echo -e "${RED}Error: El contenedor de inicialización no se creó.${NC}"
    exit 1
fi

if [ "$EXIT_CODE" -eq 0 ]; then
    echo -e "\n${GREEN}✓ Inicialización y carga de datos completada con éxito!${NC}"
    docker rm odoo_init_db_18 2>/dev/null || true
else
    echo -e "\n${RED}✗ Error: La inicialización falló con código de salida $EXIT_CODE.${NC}"
    exit 1
fi

echo -e "\n${BLUE}[4/4] Levantando servidor Web de Odoo...${NC}"
docker compose up -d web9049

echo -e "\n${BOLD}${GREEN}============================================================${NC}"
echo -e "${BOLD}${GREEN}  ¡Despliegue finalizado con éxito!                         ${NC}"
echo -e "${BOLD}${GREEN}  Acceso web: http://localhost:$PORT                        ${NC}"
echo -e "${BOLD}${GREEN}  Base de datos: $DB_NAME                                   ${NC}"
echo -e "${BOLD}${GREEN}  Usuario: $EMAIL                                           ${NC}"
echo -e "${BOLD}${GREEN}  Contraseña: $PASS                                         ${NC}"
echo -e "${BOLD}${GREEN}  Log guardado en: $LOG_FILE                                ${NC}"
echo -e "${BOLD}${GREEN}============================================================${NC}\n"

