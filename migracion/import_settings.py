#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Import/Update system settings, outgoing email servers, warehouses, journals, 
product categories accounting settings, and analytic accounts from JSON.
"""

import sys
import json
import os

sys.path.append('/usr/lib/python3/dist-packages')
os.environ.setdefault('ODOO_RC', '/etc/odoo/odoo.conf')

import odoo
import odoo.modules.registry
from odoo import api, SUPERUSER_ID

def import_settings():
    db_name = os.environ.get('DB_NAME', 'prod')
    print("=" * 60)
    print(f"Importing System Settings on database: {db_name}")
    print("=" * 60)
    
    settings_path = '/mnt/migracion/settings.json'
    if not os.path.exists(settings_path):
        print("ℹ settings.json not found, skipping system settings update.")
        return
        
    with open(settings_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
        
    registry = odoo.modules.registry.Registry(db_name)
    
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        
        # 1. Outgoing Mail Server (SMTP)
        smtp_data = config.get('smtp', {})
        if smtp_data:
            print("Configuring Outgoing SMTP Email Server...")
            server_vals = {
                'name': smtp_data.get('name', 'SMTP Server'),
                'smtp_host': smtp_data.get('host'),
                'smtp_port': int(smtp_data.get('port', 587)),
                'smtp_encryption': smtp_data.get('encryption', 'starttls'),
                'smtp_user': smtp_data.get('username'),
                'smtp_pass': smtp_data.get('password'),
            }
            existing_smtp = env['ir.mail_server'].search([('name', '=', server_vals['name'])], limit=1)
            if existing_smtp:
                existing_smtp.write(server_vals)
                print(f"  ✓ Updated SMTP Server: {server_vals['name']}")
            else:
                env['ir.mail_server'].create(server_vals)
                print(f"  ✓ Created SMTP Server: {server_vals['name']}")
                
        # 2. Warehouses (Depósitos)
        warehouses_list = config.get('warehouses', [])
        if warehouses_list:
            print("Configuring Warehouses (Depósitos)...")
            for wh_data in warehouses_list:
                code = wh_data.get('code')
                name = wh_data.get('name')
                if not code or not name:
                    continue
                wh = env['stock.warehouse'].search([('code', '=', code)], limit=1)
                wh_vals = {
                    'name': name,
                    'code': code,
                }
                if wh:
                    wh.write(wh_vals)
                    print(f"  ✓ Updated Warehouse: {name} ({code})")
                else:
                    env['stock.warehouse'].create(wh_vals)
                    print(f"  ✓ Created Warehouse: {name} ({code})")
                    
        # 3. Product Categories (Costo y Valoración de Inventario)
        prod_cat_list = config.get('product_categories_config', [])
        if prod_cat_list:
            print("Configuring Product Categories Costing and Inventory Valuation...")
            for cat_data in prod_cat_list:
                cat_name = cat_data.get('name')
                if not cat_name:
                    continue
                cat = env['product.category'].search([('name', '=', cat_name)], limit=1)
                if not cat:
                    cat = env['product.category'].create({'name': cat_name})
                    print(f"  Created Product Category: {cat_name}")
                
                cat_vals = {
                    'property_cost_method': cat_data.get('property_cost_method', 'average'),
                    'property_valuation': cat_data.get('property_valuation', 'real_time'),
                }
                
                # Fetch accounts by code
                val_code = cat_data.get('stock_valuation_account')
                in_code = cat_data.get('stock_input_account')
                out_code = cat_data.get('stock_output_account')
                
                if val_code:
                    acc = env['account.account'].search([('code', '=', val_code)], limit=1)
                    if acc:
                        cat_vals['property_stock_valuation_account_id'] = acc.id
                        print(f"    Set Valuation Account: {acc.name} ({val_code})")
                if in_code:
                    acc = env['account.account'].search([('code', '=', in_code)], limit=1)
                    if acc:
                        cat_vals['property_stock_account_input_categ_id'] = acc.id
                        print(f"    Set Stock Input Account: {acc.name} ({in_code})")
                if out_code:
                    acc = env['account.account'].search([('code', '=', out_code)], limit=1)
                    if acc:
                        cat_vals['property_stock_account_output_categ_id'] = acc.id
                        print(f"    Set Stock Output Account: {acc.name} ({out_code})")
                        
                cat.write(cat_vals)
                print(f"  ✓ Category configured: {cat_name} (AVCO, Real-Time)")

        # 4. Accounting Settings (Redondeo de IVA y Plazos de Pago)
        acc_data = config.get('accounting', {})
        if acc_data:
            print("Configuring Accounting Rounding & Payment Terms...")
            # Tax Rounding Method
            company = env['res.company'].browse(1)
            rounding = acc_data.get('tax_calculation_rounding_method', 'round_per_line')
            company.write({'tax_calculation_rounding_method': rounding})
            print(f"  ✓ Company Tax Rounding set to: {rounding}")
            
            # Rename Immediate Payment Term to Contado
            rename_to = acc_data.get('payment_immediate_rename_to')
            if rename_to:
                term = env.ref('account.account_payment_term_immediate', raise_if_not_found=False)
                if not term:
                    term = env['account.payment.term'].search([('name', '=ilike', 'inmediato')], limit=1)
                if term:
                    term.write({'name': rename_to})
                    print(f"  ✓ Payment Term Immediate renamed to: {rename_to}")

        # 5. Journals (Diarios Contables por Sucursal/Localidad)
        journals_list = config.get('journals', [])
        if journals_list:
            print("Configuring Account Journals (Diarios contables)...")
            for jr_data in journals_list:
                code = jr_data.get('code')
                name = jr_data.get('name')
                jr_type = jr_data.get('type')
                if not code or not name or not jr_type:
                    continue
                jr = env['account.journal'].search([('code', '=', code)], limit=1)
                jr_vals = {
                    'name': name,
                    'code': code,
                    'type': jr_type,
                }
                if jr:
                    jr.write(jr_vals)
                    print(f"  ✓ Updated Journal: {name} ({code})")
                else:
                    env['account.journal'].create(jr_vals)
                    print(f"  ✓ Created Journal: {name} ({code})")

        # 6. Analytic Accounts (Cuentas Analíticas por Sucursal)
        analytic_list = config.get('analytic_accounts', [])
        if analytic_list:
            print("Configuring Analytic Accounts...")
            # Find or create a default analytic plan
            plan = env['account.analytic.plan'].search([], limit=1)
            if not plan:
                plan = env['account.analytic.plan'].create({'name': 'Default Plan'})
                print(f"  Created default Analytic Plan: {plan.name}")
                
            for ana_data in analytic_list:
                code = ana_data.get('code')
                name = ana_data.get('name')
                if not code or not name:
                    continue
                ana = env['account.analytic.account'].search([('code', '=', code)], limit=1)
                ana_vals = {
                    'name': name,
                    'code': code,
                    'plan_id': plan.id,
                }
                if ana:
                    ana.write(ana_vals)
                    print(f"  ✓ Updated Analytic Account: {name} ({code})")
                else:
                    env['account.analytic.account'].create(ana_vals)
                    print(f"  ✓ Created Analytic Account: {name} ({code})")

        cr.commit()
        print("✓ System Settings configuration finished successfully!")

if __name__ == '__main__':
    import_settings()
