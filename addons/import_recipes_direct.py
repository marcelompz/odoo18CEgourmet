import sys
import base64
import os

sys.path.append('/usr/lib/python3/dist-packages')
os.environ.setdefault('ODOO_RC', '/etc/odoo/odoo.conf')

import odoo
import odoo.modules.registry
from odoo import api, SUPERUSER_ID

def import_recipes():
    print("=" * 60)
    print("Importing recipes from recetas_finales_generado.xlsx")
    print("=" * 60)
    
    # Initialize Odoo registry
    registry = odoo.modules.registry.Registry('prod')
    
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        
        # Read Excel file
        excel_path = '/mnt/extra-addons-customize/plantilla_importacion.xlsx'
        if not os.path.exists(excel_path):
            print(f"ERROR: File not found: {excel_path}")
            return False
            
        with open(excel_path, 'rb') as f:
            file_data = f.read()
            
        # Create wizard record
        wizard = env['excel.recipe.import.wizard'].create({
            'import_file': base64.b64encode(file_data),
            'import_filename': 'recetas_finales_generado.xlsx',
            'import_type': 'both',
        })
        
        # Run import
        try:
            wizard.action_import()
            print("✓ Recipe import completed successfully!")
            cr.commit()
            return True
        except Exception as e:
            print(f"✗ ERROR running wizard: {e}")
            import traceback
            traceback.print_exc()
            cr.rollback()
            return False

if __name__ == '__main__':
    success = import_recipes()
    sys.exit(0 if success else 1)
