#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Import products from materia_prima_fixed.csv directly via Odoo ORM.
This bypasses the frontend validation that incorrectly treats numeric IDs as names.
"""

import sys
import csv
import os

sys.path.append('/usr/lib/python3/dist-packages')
os.environ.setdefault('ODOO_RC', '/etc/odoo/odoo.conf')

import odoo
import odoo.modules.registry
from odoo import api, SUPERUSER_ID

def import_products():
    """Import products from CSV file."""
    
    print("=" * 60)
    print("Importing products from materia_prima_fixed.csv")
    print("=" * 60)
    
    # Initialize Odoo registry
    registry = odoo.modules.registry.Registry('prod')
    
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        
        # UoM mapping (ID -> verify exists)
        uom_ids = {1, 12, 15}
        for uom_id in uom_ids:
            uom = env['uom.uom'].browse(uom_id)
            if not uom.exists():
                print(f"ERROR: UoM ID {uom_id} not found!")
                return False
            print(f"✓ UoM ID {uom_id}: {uom.name}")
        
        # Read CSV
        csv_file = '/mnt/migracion/materia_prima_fixed.csv'
        if not os.path.exists(csv_file):
            print(f"ERROR: File not found: {csv_file}")
            return False
        
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter=';')
            rows = list(reader)
        
        print(f"\nProcessing {len(rows)} rows...")
        
        products_created = 0
        products_updated = 0
        errors = []
        
        for row_idx, row in enumerate(rows, start=2):  # Row 1 is header
            try:
                # Parse values
                default_code = row.get('Referencia interna', '').strip()
                name = row.get('Nombre', '').strip()
                
                if not default_code or not name:
                    errors.append(f"Row {row_idx}: Missing default_code or name")
                    continue
                
                # Parse numeric values
                try:
                    standard_price = float(row.get('Costo', '0') or '0')
                except ValueError:
                    standard_price = 0.0
                
                try:
                    list_price = float(row.get('Precio de venta', '0') or '0')
                except ValueError:
                    list_price = 0.0
                
                # Parse boolean values
                is_storable = row.get('Rastrear inventario', '').upper() == 'VERDADERO'
                available_in_pos = row.get('Disponible en PdV', '').upper() == 'VERDADERO'
                
                # Get UoM ID
                uom_value = row.get('Unidades', '').strip()
                try:
                    uom_id = int(uom_value)
                except ValueError:
                    # Try mapping
                    uom_mapping = {'g': 15, 'ml': 12, 'unidades': 1, 'unidad': 1}
                    uom_id = uom_mapping.get(uom_value.lower(), 1)
                
                # Verify UoM exists
                uom = env['uom.uom'].browse(uom_id)
                if not uom.exists():
                    errors.append(f"Row {row_idx}: UoM ID {uom_id} not found")
                    continue
                
                # Get or create category
                categ_name = row.get('Categoria del producto', 'MATERIA PRIMA').strip()
                categ = env['product.category'].search([('name', '=ilike', categ_name)], limit=1)
                if not categ:
                    categ = env['product.category'].create({'name': categ_name})
                
                # Prepare values
                product_vals = {
                    'default_code': default_code,
                    'name': name,
                    'standard_price': standard_price,
                    'list_price': list_price,
                    'categ_id': categ.id,
                    'type': 'consu',
                    'is_storable': is_storable,
                    'uom_id': uom_id,
                    'uom_po_id': uom_id,
                    'available_in_pos': available_in_pos,
                }
                
                # Check if product exists
                existing = env['product.template'].search([('default_code', '=', default_code)], limit=1)
                
                if existing:
                    existing.write(product_vals)
                    products_updated += 1
                    if products_updated <= 5:
                        print(f"  Updated: {default_code}")
                else:
                    env['product.template'].create(product_vals)
                    products_created += 1
                    if products_created <= 5:
                        print(f"  Created: {default_code}")
                
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
        success = import_products()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
