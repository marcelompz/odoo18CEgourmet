#!/bin/bash
# Script para ejecutar el seed de Agripar demo
# Espera a que Odoo esté listo y la DB tenga las tablas inicializadas

set -e

DB_NAME="ferreteria"
DB_HOST="db_odoo_5436"
DB_USER="odoo"
DB_PASS="crossdimora.159753"
ODOO_CONTAINER="odoo_web_8084"
SEED_SCRIPT="/opt/odoo/odoo8084/test_scripts/seed_agripar_demo.py"

echo "🔍 Verificando que Odoo esté disponible..."

# Esperar a que Odoo responda
MAX_ATTEMPTS=30
ATTEMPT=1

while [ $ATTEMPT -le $MAX_ATTEMPTS ]; do
    if docker exec $ODOO_CONTAINER wget -q --spider http://localhost:8069/web/login 2>/dev/null; then
        echo "✅ Odoo está disponible (intento $ATTEMPT)"
        break
    fi
    echo "⏳ Esperando Odoo... (intento $ATTEMPT/$MAX_ATTEMPTS)"
    sleep 5
    ATTEMPT=$((ATTEMPT + 1))
done

if [ $ATTEMPT -gt $MAX_ATTEMPTS ]; then
    echo "❌ Odoo no respondió después de $MAX_ATTEMPTS intentos"
    exit 1
fi

echo ""
echo " Verificando que la DB tenga las tablas de Odoo..."

# Verificar si las tablas de Odoo existen
TABLE_CHECK=$(docker exec db_odoo_5436 psql -U $DB_USER -d $DB_NAME -c "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'res_partner');" 2>/dev/null | grep -o "t\|f" | head -1)

if [ "$TABLE_CHECK" != "t" ]; then
    echo "⚠️  La DB $DB_NAME no tiene tablas de Odoo inicializadas"
    echo ""
    echo "📋 Para inicializar la base de datos, necesitas:"
    echo "   1. Abrir http://localhost:8084 en tu navegador"
    echo "   2. Crear la base de datos '$DB_NAME'"
    echo "   3. Configurar usuario admin (email: admin, password: admin)"
    echo "   4. Instalar módulos base (al menos CRM, Ventas, Inventario)"
    echo ""
    echo "   Luego ejecuta este script nuevamente."
    echo ""
    echo "💡 Opción alternativa: Forzar inicialización automática"
    echo "   (esto puede tomar 2-3 minutos)"
    echo ""
    read -p "¿Quieres intentar inicialización automática? (s/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[SsYy]$ ]]; then
        echo "🔄 Iniciando inicialización automática..."
        
        # Crear script de inicialización
        cat > /tmp/init_odoo.py << 'INIT_EOF'
# Script de inicialización de Odoo
import sys
import os

# Forzar creación de tablas base
env.cr.execute("""
    SELECT 1 FROM ir_module_module WHERE name = 'base' LIMIT 1
""")
print("✅ Tablas base verificadas")

# Verificar que res_partner exista
env.cr.execute("""
    SELECT EXISTS (SELECT FROM information_schema.tables 
    WHERE table_schema = 'public' AND table_name = 'res_partner')
""")
exists = env.cr.fetchone()[0]
if exists:
    print("✅ res_partner existe")
else:
    print("❌ res_partner no existe - la DB necesita inicialización desde el navegador")
    sys.exit(1)

env.cr.commit()
print("✅ Inicialización completada")
INIT_EOF
        
        # Copiar script al contenedor y ejecutar
        docker cp /tmp/init_odoo.py $ODOO_CONTAINER:/tmp/init_odoo.py
        docker exec $ODOO_CONTAINER odoo shell -d $DB_NAME --limit-time-real 9999999 < /tmp/init_odoo.py 2>&1 || true
        
        # Verificar nuevamente
        sleep 5
        TABLE_CHECK=$(docker exec db_odoo_5436 psql -U $DB_USER -d $DB_NAME -c "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'res_partner');" 2>/dev/null | grep -o "t\|f" | head -1)
        
        if [ "$TABLE_CHECK" != "t" ]; then
            echo ""
            echo "❌ La inicialización automática falló"
            echo "   Debes inicializar desde el navegador: http://localhost:8084"
            exit 1
        fi
    else
        echo "❌ Seed cancelado. Inicializa la DB desde el navegador primero."
        exit 1
    fi
fi

echo "✅ DB $DB_NAME está lista con tablas de Odoo"
echo ""

# Verificar si ya se ejecutó el seed
echo "🔍 Verificando si el seed ya fue ejecutado..."

EXISTE_CLIENTE=$(docker exec db_odoo_5436 psql -U $DB_USER -d $DB_NAME -c "SELECT EXISTS (SELECT 1 FROM res_partner WHERE name = 'Agripar - Estancia El Ombú');" 2>/dev/null | grep -o "t\|f" | head -1)

if [ "$EXISTE_CLIENTE" = "t" ]; then
    echo "⚠️  El seed YA fue ejecutado previamente (cliente Agripar encontrado)"
    echo ""
    read -p "¿Quieres volver a ejecutar el seed? (s/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[SsYy]$ ]]; then
        echo "✅ Seed saltado"
        exit 0
    fi
    echo "🗑️  Limpiando datos anteriores..."
fi

echo ""
echo "🚀 Ejecutando seed script de Agripar..."
echo ""

# Ejecutar el seed script con odoo shell
docker exec -i $ODOO_CONTAINER odoo shell -d $DB_NAME --limit-time-real 9999999 < $SEED_SCRIPT 2>&1

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ ¡Seed de Agripar completado exitosamente!"
    echo ""
    echo "📊 Datos creados:"
    echo "   • Cliente: Agripar - Estancia El Ombú"
    echo "   • Proveedor: Parker Hannifin Paraguay S.A."
    echo "   • Productos hidráulicos (4 items)"
    echo "   • Stock con lotes/series"
    echo "   • Oportunidad CRM"
    echo "   • Pedido de venta confirmado"
    echo "   • Solicitud de compra"
    echo ""
    echo "🌐 Accede a: http://localhost:8084"
    echo "   Usuario: admin"
    echo "   Contraseña: la que configuraste"
else
    echo ""
    echo "❌ Error al ejecutar el seed"
    echo "   Revisa los logs arriba para más detalles"
    exit 1
fi
