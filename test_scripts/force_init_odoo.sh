#!/bin/bash
# Script para forzar inicialización de Odoo 19.0 con DB ferreteria

set -e

echo "🔄 Reiniciando Odoo para inicialización forzada..."

cd /opt/odoo/odoo8084

# Detener contenedor
echo "⏹️  Deteniendo Odoo..."
docker compose down

# Eliminar volúmenes de datos corruptos
echo "🧹 Limpiando volúmenes..."
docker volume rm odoo8084_odoo-web-data odoo8084_odoo-db-data 2>/dev/null || true

# Modificar temporalmente docker-compose para inicialización
echo "📝 Configurando inicialización automática..."

# Crear backup del docker-compose original
cp docker-compose.yml docker-compose.yml.backup

# Modificar entrypoint para forzar inicialización
cat > docker-compose.yml << 'EOF'
networks:
  default:
    driver: bridge
    ipam:
      config:
        - subnet: 10.201.0.0/16

services:
  web8084:
    container_name: odoo_web_8084
    image: odoo:19.0
    build: ./
    depends_on:
      - db5436
    ports:
      - "8084:8069"
    volumes:
      - odoo-web-data:/var/lib/odoo
      - ./config:/etc/odoo
      - /mnt/addons:/mnt/extra-addons
      - /opt/odoo/odoo8084/addons:/mnt/extra-addons-customize
    entrypoint: "/usr/bin/odoo -c /etc/odoo/odoo.conf --database=ferreteria --init base --without-demo=all --stop-after-init"
    environment:
      - HOST=db_odoo_5436
      - USER=odoo
      - PASSWORD=crossdimora.159753
      - TZ=America/Asuncion
      - DEBIAN_FRONTEND=noninteractive
  
  db5436:
    container_name: db_odoo_5436
    image: postgres:15
    environment:
      - POSTGRES_DB=ferreteria
      - POSTGRES_PASSWORD=crossdimora.159753
      - POSTGRES_USER=odoo
      - PGDATA=/var/lib/postgresql/data/pgdata
      - TZ=America/Asuncion
      - DEBIAN_FRONTEND=noninteractive
    ports:
      - "5436:5432"
    volumes:
      - odoo-db-data:/var/lib/postgresql/data/pgdata

volumes:
  odoo-db-data:
    driver: local
    driver_opts:
      type: none
      device: /opt/odoo/odoo8084/db-data
      o: bind
  odoo-web-data:
    driver: local
    driver_opts:
      type: none
      device: /opt/odoo/odoo8084/web-data
      o: bind
EOF

# Levantar para inicialización
echo "🚀 Iniciando inicialización de base de datos..."
docker compose up -d

# Esperar a que termine la inicialización
echo "⏳ Esperando inicialización (esto toma 1-2 minutos)..."
sleep 30

# Verificar logs
echo "📋 Verificando logs de inicialización..."
docker logs odoo_web_8084 2>&1 | grep -i -E "(initialization|modules loaded|error|exception)" | tail -30

# Verificar si se crearon las tablas
echo ""
echo "🔍 Verificando tablas en la DB..."
TABLE_COUNT=$(docker exec db_odoo_5436 psql -U odoo -d ferreteria -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" 2>/dev/null | grep -E "^[0-9]+" | head -1)

if [ "$TABLE_COUNT" -gt 50 ]; then
    echo "✅ ¡Inicialización exitosa! $TABLE_COUNT tablas creadas"
else
    echo "⚠️  Solo se crearon $TABLE_COUNT tablas, puede haber un problema"
fi

# Restaurar docker-compose original
echo ""
echo "🔄 Restaurando configuración original..."
cp docker-compose.yml.backup docker-compose.yml

# Detener contenedor de inicialización
docker compose down

# Levantar normalmente
echo "🚀 Levantando Odoo en modo normal..."
docker compose up -d

echo ""
echo "✅ ¡Proceso completado!"
echo ""
echo "🌐 Ahora puedes acceder a: http://localhost:8084"
echo "   Usuario: admin"
echo "   Contraseña: admin"
echo ""
echo "📝 Para ejecutar el seed de Agripar:"
echo "   /opt/odoo/odoo8084/test_scripts/run_agripar_seed_simple.sh"
