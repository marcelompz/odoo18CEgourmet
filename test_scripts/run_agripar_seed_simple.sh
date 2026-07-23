#!/bin/bash
# Script simplificado para ejecutar el seed de Agripar
# Asume que Odoo ya está corriendo y la DB está inicializada

DB_NAME="ferreteria"
ODOO_CONTAINER="odoo_web_8084"
SEED_SCRIPT="/opt/odoo/odoo8084/test_scripts/seed_agripar_demo.py"

echo " Ejecutando seed de Agripar demo..."
echo ""
echo "Database: $DB_NAME"
echo "Container: $ODOO_CONTAINER"
echo ""

# Verificar que Odoo esté disponible
if ! docker exec $ODOO_CONTAINER python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8069')" 2>/dev/null; then
    echo "⏳ Esperando que Odoo esté disponible..."
    sleep 5
    if ! docker exec $ODOO_CONTAINER python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8069')" 2>/dev/null; then
        echo "❌ Odoo no está disponible"
        exit 1
    fi
fi

echo "✅ Odoo está disponible"
echo ""

# Verificar que la DB tenga tablas
echo "🔍 Verificando tablas de Odoo en la DB..."
TABLE_CHECK=$(docker exec db_odoo_5436 psql -U odoo -d $DB_NAME -c "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'res_partner');" 2>/dev/null | grep -o "t\|f" | head -1)

if [ "$TABLE_CHECK" != "t" ]; then
    echo "❌ La DB no tiene tablas de Odoo"
    echo ""
    echo "⚠️  Necesitas inicializar la base de datos primero:"
    echo "   1. Abre http://localhost:8084 en tu navegador"
    echo "   2. Crea la base de datos '$DB_NAME'"
    echo "   3. Configura el usuario admin"
    echo "   4. Espera a que termine la instalación"
    echo "   5. Ejecuta este script nuevamente"
    exit 1
fi

echo "✅ DB tiene tablas de Odoo"
echo ""

# Verificar módulos requeridos
echo "🔍 Verificando módulos requeridos..."

# Función para verificar si un módulo está instalado
check_module_installed() {
    local module_name=$1
    local module_state=$(docker exec db_odoo_5436 psql -U odoo -d $DB_NAME -t -c "SELECT state FROM ir_module_module WHERE name='$module_name';" 2>/dev/null | tr -d ' ')
    
    if [ "$module_state" = "installed" ]; then
        echo "✅ Módulo $module_name: INSTALADO"
        return 0
    else
        echo "⚠️  Módulo $module_name: NO INSTALADO (estado: ${module_state:-no encontrado})"
        return 1
    fi
}

# Verificar módulos críticos
MODULES_OK=true

echo ""
echo "Módulos críticos:"
check_module_installed "base" || MODULES_OK=false
check_module_installed "web" || MODULES_OK=false

echo ""
echo "Módulos de negocio:"
check_module_installed "crm" || MODULES_OK=false
check_module_installed "sale_management" || MODULES_OK=false
check_module_installed "stock" || MODULES_OK=false
check_module_installed "purchase" || MODULES_OK=false

echo ""
echo "Recursos Humanos:"
check_module_installed "hr" || MODULES_OK=false

echo ""
echo "Localización Paraguay:"
if ! check_module_installed "l10n_py"; then
    echo ""
    echo "🔄 Instalando localización paraguaya (l10n_py)..."
    
    # Instalar módulo l10n_py usando odoo shell
    docker exec -i $ODOO_CONTAINER odoo shell -d $DB_NAME --limit-time-real 9999999 << 'INSTALL_EOF'
try:
    module_obj = env['ir.module.module']
    l10n_py_module = module_obj.search([('name', '=', 'l10n_py')])
    
    if l10n_py_module and l10n_py_module.state != 'installed':
        print(f"📦 Instalando l10n_py... (estado actual: {l10n_py_module.state})")
        l10n_py_module.button_immediate_install()
        env.cr.commit()
        print("✅ l10n_py instalado exitosamente")
    elif not l10n_py_module:
        print("⚠️  Módulo l10n_py no encontrado en el sistema")
    else:
        print("ℹ️  l10n_py ya está instalado")
except Exception as e:
    print(f"❌ Error al instalar l10n_py: {e}")
INSTALL_EOF
    
    echo ""
fi

echo ""

if [ "$MODULES_OK" = false ]; then
    echo ""
    echo "🔄 Instalando módulos de negocio faltantes..."
    
    # Instalar módulos usando odoo shell
    docker exec -i $ODOO_CONTAINER odoo shell -d $DB_NAME --limit-time-real 9999999 << 'INSTALL_EOF'
try:
    module_obj = env['ir.module.module']
    
    # Lista de módulos a instalar
    modules_to_install = ['crm', 'sale_management', 'stock', 'purchase', 'hr']
    
    for module_name in modules_to_install:
        module = module_obj.search([('name', '=', module_name)])
        if module and module.state != 'installed':
            print(f"📦 Instalando {module_name}... (estado: {module.state})")
            module.button_immediate_install()
            env.cr.commit()
            print(f"✅ {module_name} instalado")
        elif not module:
            print(f"⚠️  Módulo {module_name} no encontrado")
        else:
            print(f"ℹ️  {module_name} ya está instalado")
    
    print("\n✅ Módulos de negocio instalados")
except Exception as e:
    print(f"❌ Error al instalar módulos: {e}")
    import traceback
    traceback.print_exc()
INSTALL_EOF
    
    echo ""
    echo "⏳ Esperando 10 segundos para que Odoo procese la instalación..."
    sleep 10
    
    # Verificar nuevamente
    MODULES_OK=true
    echo ""
    echo "🔍 Verificando módulos nuevamente..."
    check_module_installed "crm" || MODULES_OK=false
    check_module_installed "sale_management" || MODULES_OK=false
    check_module_installed "stock" || MODULES_OK=false
    check_module_installed "purchase" || MODULES_OK=false
    
    if [ "$MODULES_OK" = false ]; then
        echo ""
        echo "❌ No se pudieron instalar todos los módulos"
        echo "   Accede a http://localhost:8084 e instálalos manualmente desde Apps"
        exit 1
    fi
fi

echo "✅ Todos los módulos requeridos están instalados"
echo ""

# Ejecutar el seed
echo "📝 Ejecutando seed script..."
echo "----------------------------------------"

docker exec -i $ODOO_CONTAINER odoo shell -d $DB_NAME --limit-time-real 9999999 < $SEED_SCRIPT

EXIT_CODE=$?

echo "----------------------------------------"
echo ""

if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ ¡Seed completado exitosamente!"
    echo ""
    echo "🎯 Datos creados:"
    echo "   ✓ Cliente: Agripar - Estancia El Ombú"
    echo "   ✓ Proveedor: Parker Hannifin Paraguay S.A."
    echo "   ✓ 4 productos hidráulicos"
    echo "   ✓ Stock con trazabilidad (lotes/series)"
    echo "   ✓ Oportunidad CRM"
    echo "   ✓ Pedido de venta confirmado"
    echo "   ✓ Solicitud de compra"
    echo ""
    echo "🌐 Accede a la demo:"
    echo "   URL: http://localhost:8084"
    echo "   App: CRM o Ventas"
else
    echo "❌ Error al ejecutar el seed (código: $EXIT_CODE)"
    echo ""
    echo "Posibles causas:"
    echo "   • La DB no está completamente inicializada"
    echo "   • Faltan módulos instalados (CRM, Ventas, Inventario)"
    echo "   • Error en el script seed"
    echo ""
    echo "Revisa los logs arriba para más detalles"
fi

exit $EXIT_CODE
