#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Export POS Restaurant Floors and Tables to migracion/pos_floors.json
"""
import sys
import json
import os

sys.path.append('/usr/lib/python3/dist-packages')
os.environ.setdefault('ODOO_RC', '/etc/odoo/odoo.conf')

import odoo
import odoo.modules.registry
from odoo import api, SUPERUSER_ID

def export_pos_floors():
    db_host = os.environ.get('DB_HOST', 'db_odoo_8085')
    db_port = '5432' if os.environ.get('DB_PORT') in ['5436', None] else os.environ.get('DB_PORT', '5432')
    db_user = os.environ.get('DB_USER', 'odoo')
    db_password = os.environ.get('DB_PASSWD', 'cross.159753')
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

    print("=" * 60)
    print(f"Exporting POS Floors & Tables from database: {db_name}")
    print("=" * 60)

    registry = odoo.modules.registry.Registry(db_name)

    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})

        if 'restaurant.floor' not in env:
            print("⚠️ Module pos_restaurant is not installed. Nothing to export.")
            return

        floors = env['restaurant.floor'].search([])
        floors_data = []

        for floor in floors:
            f_item = {
                'name': floor.name,
                'sequence': floor.sequence,
                'background_color': floor.background_color or False,
                'tables': []
            }

            tables = env['restaurant.table'].search([('floor_id', '=', floor.id)])
            for table in tables:
                t_item = {
                    'name': table.name,
                    'seats': table.seats,
                    'shape': table.shape,
                    'position_h': table.position_h,
                    'position_v': table.position_v,
                    'width': table.width,
                    'height': table.height,
                    'active': table.active,
                }
                f_item['tables'].append(t_item)

            floors_data.append(f_item)

        output_path = '/mnt/migracion/pos_floors.json'
        if not os.path.exists('/mnt/migracion'):
            output_path = './migracion/pos_floors.json'

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(floors_data, f, indent=4, ensure_ascii=False)

        print(f"✓ Exported {len(floors_data)} floors and their tables to {output_path}")

if __name__ == '__main__':
    export_pos_floors()
