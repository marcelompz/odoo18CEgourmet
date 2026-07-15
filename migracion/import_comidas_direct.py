#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Import products from comida.csv directly via Odoo ORM.
"""

import sys
import csv
import os

sys.path.append('/usr/lib/python3/dist-packages')
os.environ.setdefault('ODOO_RC', '/etc/odoo/odoo.conf')

import odoo
import odoo.modules.registry
from odoo import api, SUPERUSER_ID

def import_comidas():
    print("=" * 60)
    print("Importing products from comida.csv")
    print("=" * 60)
    
    # Initialize Odoo registry
    registry = odoo.modules.registry.Registry('prod')
    
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        
        # UoM mapping (ID -> verify exists)
        uom_id = 1 # Units
        uom = env['uom.uom'].browse(uom_id)
        if not uom.exists():
            print(f"ERROR: UoM ID {uom_id} not found!")
            return False
        
        # Read CSV
        csv_file = '/mnt/migracion/comida.csv'
        if not os.path.exists(csv_file):
            print(f"ERROR: File not found: {csv_file}")
            return False
        
        products_created = 0
        products_updated = 0
        errors = []
        
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter=';')
            rows = list(reader)
            
        print(f"Processing {len(rows)} rows...")
        
        for row_idx, row in enumerate(rows, start=2):
            default_code = row.get('Referencia interna', '').strip()
            name = row.get('Nombre', '').strip()
            
            if not name:
                continue
                
            try:
                # Available in POS
                available_in_pos = row.get('Disponible en PDV', '').strip().upper() == 'VERDADERO'
                
                # Track inventory
                is_storable = row.get('Rastrear inventario', '').strip().upper() == 'VERDADERO'
                
                # POS BoM
                is_pos_bom = row.get('is_pos_bom', '').strip().upper() == 'VERDADERO'
                
                # Sales Price
                list_price_str = row.get('Precio de venta', '0').strip().replace(',', '.')
                list_price = float(list_price_str) if list_price_str else 0.0
                
                # Get category
                categ_name = row.get('Categoria del producto', '').strip() or 'All'
                categ = env['product.category'].search([('name', '=', categ_name)], limit=1)
                if not categ:
                    categ = env['product.category'].create({'name': categ_name})
                
                # Prepare values
                product_vals = {
                    'default_code': default_code,
                    'name': name,
                    'list_price': list_price,
                    'categ_id': categ.id,
                    'type': 'consu',
                    'is_storable': is_storable,
                    'is_pos_bom': is_pos_bom,
                    'uom_id': uom_id,
                    'uom_po_id': uom_id,
                    'available_in_pos': available_in_pos,
                }
                
                # Check if product exists
                existing = env['product.template'].search([('default_code', '=', default_code)], limit=1)
                if not existing and default_code:
                    existing = env['product.template'].search([('name', '=', name)], limit=1)
                
                if existing:
                    existing.write(product_vals)
                    products_updated += 1
                    if products_updated <= 5:
                        print(f"  Updated: {name} (code: {default_code})")
                else:
                    env['product.template'].create(product_vals)
                    products_created += 1
                    if products_created <= 5:
                        print(f"  Created: {name} (code: {default_code})")
                
            except Exception as e:
                errors.append(f"Row {row_idx}: {str(e)}")
        
        # Commit transaction
        cr.commit()
        
        # Print summary
        print("\n" + "=" * 60)
        print("IMPORT SUMMARY")
        print("=" * 60)
        print(f"Total rows processed: {len(rows)}")
        print(f"Products created: {products_created}")
        print(f"Products updated: {products_updated}")
        
        if errors:
            print(f"\nErrors ({len(errors)}):")
            for error in errors[:10]:
                print(f"  - {error}")
            if len(errors) > 10:
                print(f"  ... and {len(errors) - 10} more")
        else:
            print("\n✓ Import completed successfully!")
            
        return len(errors) == 0

if __name__ == '__main__':
    try:
        success = import_comidas()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
