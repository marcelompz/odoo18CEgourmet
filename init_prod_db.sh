#!/bin/bash
# Script de inicialización de base de datos Odoo para Provecchio
set -e

echo "============================================================"
echo "Inicialización de Odoo Provecchio - Base de datos PROD"
echo "============================================================"

DB_NAME="${DB_NAME:-prod}"
DB_HOST="${DB_HOST:-db}"
DB_PORT="${DB_PORT:-5432}"
DB_USER="${DB_USER:-odoo}"
DB_PASSWD="${DB_PASSWD:-crossdimora.159753}"
ADMIN_EMAIL="${ADMIN_EMAIL:-soporte@crossnexion.com}"
ADMIN_PASSWORD="${ADMIN_PASSWORD:-Cross1983_}"

export PGPASSWORD="$DB_PASSWD"

# Verificar módulos l10n_py (montados en el contenedor)
echo "=== Verificando módulos l10n_py ==="
L10N_PY_DIR="/mnt/extra-addons-l10py"

if [ -d "$L10N_PY_DIR/l10n_py" ]; then
    echo "✓ Módulos l10n_py disponibles"
    ls -la "$L10N_PY_DIR"
else
    echo "✗ ERROR: Módulos l10n_py no disponibles en $L10N_PY_DIR"
    exit 1
fi
echo ""

# Esperar a que PostgreSQL esté disponible
echo "Esperando PostgreSQL..."
until psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -c '\q' 2>/dev/null; do
  echo "  Esperando..."
  sleep 2
done
echo "✓ PostgreSQL disponible"

# Crear DB si no existe
echo "Creando base de datos '$DB_NAME'..."
if psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -t -c "SELECT 1 FROM pg_database WHERE datname='$DB_NAME'" | grep -q 1; then
  echo "✓ Base de datos '$DB_NAME' ya existe"
else
  psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -c "CREATE DATABASE \"$DB_NAME\" OWNER \"$DB_USER\";"
  echo "✓ Base de datos '$DB_NAME' creada"
fi

# Verificar si Odoo ya está inicializado (si existe la tabla res_users)
if psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT 1 FROM pg_tables WHERE tablename='res_users'" 2>/dev/null | grep -q 1; then
  echo "✓ Odoo ya está inicializado en '$DB_NAME'. Omitiendo configuración."
  exit 0
fi

# Leer los módulos desde modules.conf
MODULES_LIST=""
MODULES_FILE="/modules.conf"

if [ -f "$MODULES_FILE" ]; then
  echo "✓ Cargando lista de módulos desde $MODULES_FILE"
  MODULES_LIST=$(grep -v '^#' "$MODULES_FILE" | grep -v '^[[:space:]]*$' | tr '\n' ',' | sed 's/,$//')
else
  echo "⚠️ Archivo $MODULES_FILE no encontrado. Usando lista por defecto."
  MODULES_LIST="base,web,mail,mrp,point_of_sale,pos_restaurant,stock,purchase,sale,product_mass_import,pos_product_bom,excel_recipe_import,ica_web_responsive"
fi

echo "Módulos a instalar: $MODULES_LIST"

# Inicializar Odoo
echo "Inicializando Odoo en '$DB_NAME'..."
odoo \
     -d "$DB_NAME" \
     --init "$MODULES_LIST" \
     --stop-after-init \
     --without-demo=all \
     --db_host "$DB_HOST" \
     --db_port "$DB_PORT" \
     --db_user "$DB_USER" \
     --db_password "$DB_PASSWD" \
     --addons-path=/mnt/extra-addons-customize,/mnt/extra-addons-l10py,/usr/lib/python3/dist-packages/odoo/addons \
     2>&1 | tail -30

echo "✓ Odoo inicializado"

# Actualizar usuario admin
echo "Actualizando usuario admin..."
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" <<EOF
UPDATE res_users SET login='$ADMIN_EMAIL' WHERE login='admin';
EOF
echo "  ✓ Email actualizado a: $ADMIN_EMAIL"

# Establecer password usando ORM de Odoo
echo "Estableciendo password..."
python3 << PYEOF
import sys
sys.path.insert(0, '/usr/lib/python3/dist-packages')
import odoo
import odoo.tools
import odoo.modules.registry
from odoo import api, SUPERUSER_ID

odoo.tools.config.parse_config([
    '--db_host', '$DB_HOST',
    '--db_port', '$DB_PORT',
    '--db_user', '$DB_USER',
    '--db_password', '$DB_PASSWD',
])

try:
    registry = odoo.modules.registry.Registry('$DB_NAME')
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        user = env['res.users'].search([('login', '=', '$ADMIN_EMAIL')], limit=1)
        if user:
            user.sudo().write({'password': '$ADMIN_PASSWORD'})
            print('  ✓ Password establecido')
        else:
            print('  ✗ Usuario no encontrado')

        # Cargar logo de la empresa si existe en /mnt/migracion/
        import glob
        import base64
        logo_files = glob.glob('/mnt/migracion/*logo*.[pP][nN][gG]') + \
                     glob.glob('/mnt/migracion/*logo*.[jJ][pP][gG]') + \
                     glob.glob('/mnt/migracion/*logo*.[jJ][pP][eE][gG]')
        if logo_files:
            logo_path = logo_files[0]
            with open(logo_path, 'rb') as f:
                logo_data = base64.b64encode(f.read())
            company = env['res.company'].browse(1)
            if company.exists():
                company.write({'logo': logo_data})
                print(f'  ✓ Logo de empresa cargado con éxito desde {logo_path}')
        cr.commit()
except Exception as e:
    print('  ✗ Error:', e)
PYEOF

# Configurar Paraguay
echo "Configurando Paraguay..."
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c \
  "UPDATE res_company SET country_id=(SELECT id FROM res_country WHERE name='Paraguay' LIMIT 1) WHERE id=1;" 2>/dev/null || true

psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c \
  "UPDATE res_company SET currency_id=(SELECT id FROM res_currency WHERE name='PYG' LIMIT 1) WHERE id=1;" 2>/dev/null || true

echo "✓ Paraguay configurado"

# Instalar módulos l10n_py
echo "Instalando módulos de localización Paraguay..."
echo "  (tu-ruc-python-client ya instalado por docker-compose)"

# Instalar solo l10n_py base (los otros se pueden instalar desde la UI)
echo "  Instalando l10n_py..."
odoo \
     -d "$DB_NAME" \
     --init l10n_py \
     --stop-after-init \
     --without-demo=all \
     --db_host "$DB_HOST" \
     --db_port "$DB_PORT" \
     --db_user "$DB_USER" \
     --db_password "$DB_PASSWD" \
     --addons-path=/mnt/extra-addons-customize,/mnt/extra-addons-l10py,/usr/lib/python3/dist-packages/odoo/addons \
     2>&1 | tail -20

echo ""
echo "✓ Módulos de localización Paraguay instalados"
echo "  NOTA: electronic_invoice_cross y pos_einvoice_cross se pueden instalar desde la UI"

echo ""
echo "=== Importando Datos Maestros (Materias Primas, Comidas, Recetas) ==="
python3 /mnt/migracion/import_products_direct.py
python3 /mnt/migracion/import_comidas_direct.py
python3 /mnt/migracion/import_recipes_direct.py
echo "✓ Datos maestros importados"
echo ""
echo "============================================================"
echo "✓ Inicialización completada"
echo "============================================================"
echo ""
echo "Acceso:"
echo "  URL: http://localhost:8069/web/login"
echo "  Email: $ADMIN_EMAIL"
echo "  Password: $ADMIN_PASSWORD"
echo "  Database: $DB_NAME"
echo ""
