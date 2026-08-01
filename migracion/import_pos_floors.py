#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Import/Update POS Restaurant Floors and Tables dynamically from pos_floors.json.
"""
import sys
import json
import os

sys.path.append('/usr/lib/python3/dist-packages')
os.environ.setdefault('ODOO_RC', '/etc/odoo/odoo.conf')

import odoo
import odoo.modules.registry
from odoo import api, SUPERUSER_ID

def import_pos_floors():
    db_host = os.environ.get('DB_HOST', 'db_odoo_8085')
    db_port = '5432' if os.environ.get('DB_PORT') in ['5436', None] else os.environ.get('DB_PORT', '5432')
    db_user = os.environ.get('DB_USER', 'odoo')
    db_password = os.environ.get('DB_PASSWD', 'odoo')
    db_name = os.environ.get('DB_NAME', 'prod')
    addons_path = os.environ.get('ADDONS_PATH', '/mnt/extra-addons-customize,/mnt/extra-addons-l10py,/usr/lib/python3/dist-packages/odoo/addons')
    valid_addons = [p for p in addons_path.split(',') if os.path.exists(p)]

    odoo.tools.config.parse_config([
        '--db_host', db_host,
        '--db_port', db_port,
        '--db_user', db_user,
        '--db_password', db_password,
        '--addons-path', ','.join(valid_addons),
    ])

    floors_path = '/mnt/migracion/pos_floors.json'
    if not os.path.exists(floors_path):
        floors_path = './migracion/pos_floors.json'

    if not os.path.exists(floors_path):
        print("ℹ pos_floors.json not found, skipping floors & tables setup.")
        return

    print("=" * 60)
    print(f"Importing POS Floors & Tables on database: {db_name}")
    print("=" * 60)

    registry = odoo.modules.registry.Registry(db_name)

    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})

        if 'restaurant.floor' not in env:
            print("⚠️ Module pos_restaurant is not installed in database. Skipping.")
            return

        with open(floors_path, 'r', encoding='utf-8') as f:
            floors_data = json.load(f)

        Floor = env['restaurant.floor']
        Table = env['restaurant.table']

        pos_configs = env['pos.config'].search([])

        for f_data in floors_data:
            floor_name = f_data.get('name')
            if not floor_name:
                continue

            floor_vals = {
                'name': floor_name,
                'sequence': f_data.get('sequence', 1),
            }
            if f_data.get('background_color'):
                floor_vals['background_color'] = f_data.get('background_color')

            floor = Floor.search([('name', '=', floor_name)], limit=1)
            if floor:
                floor.write(floor_vals)
                print(f"✓ Floor updated: {floor_name}")
            else:
                floor = Floor.create(floor_vals)
                print(f"✓ Floor created: {floor_name}")

            # Assign floor to all POS configurations if present
            for pos in pos_configs:
                if hasattr(pos, 'floor_ids') and floor.id not in pos.floor_ids.ids:
                    pos.write({'floor_ids': [(4, floor.id)]})

            # Import Tables for this Floor
            tables_data = f_data.get('tables', [])
            for t_data in tables_data:
                table_name = t_data.get('name')
                if not table_name:
                    continue

                table_vals = {
                    'name': table_name,
                    'floor_id': floor.id,
                    'seats': t_data.get('seats', 2),
                    'shape': t_data.get('shape', 'square'),
                    'position_h': t_data.get('position_h', 10),
                    'position_v': t_data.get('position_v', 10),
                    'width': t_data.get('width', 100),
                    'height': t_data.get('height', 100),
                    'active': t_data.get('active', True),
                }

                table = Table.search([('name', '=', table_name), ('floor_id', '=', floor.id)], limit=1)
                if table:
                    table.write(table_vals)
                    print(f"  └─ Table updated: {table_name} (seats: {table.seats})")
                else:
                    Table.create(table_vals)
                    print(f"  └─ Table created: {table_name} (seats: {t_data.get('seats', 2)})")

        cr.commit()
        print("✓ POS Floors & Tables import completed successfully!")

if __name__ == '__main__':
    import_pos_floors()
