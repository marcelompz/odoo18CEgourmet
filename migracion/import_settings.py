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
    db_host = os.environ.get('DB_HOST', 'db_odoo_5436')
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
        
        # 0. Currency (PYG)
        try:
            pyg = env['res.currency'].with_context(active_test=False).search([('name', '=', 'PYG')], limit=1)
            if pyg and not pyg.active:
                pyg.write({'active': True})
                print("  ✓ Activated PYG currency (Guaraní) in the system.")
            
            company = env['res.company'].browse(1)
            if company.exists():
                if company.currency_id and not company.currency_id.active:
                    company.currency_id.write({'active': True})
                    print(f"  ✓ Activated company currency: {company.currency_id.name}")
            cr.commit()
        except Exception as e:
            cr.rollback()
            print(f"  ⚠️ Currency configuration warning: {e}")
        
        # 1. Outgoing Mail Server (SMTP)
        try:
            smtp_data = config.get('smtp', {})
            if smtp_data and 'ir.mail_server' in env:
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
            cr.commit()
        except Exception as e:
            cr.rollback()
            print(f"  ⚠️ SMTP Server configuration warning: {e}")
                
        # 2. Warehouses (Depósitos)
        try:
            if 'stock.warehouse' in env:
                # Archive or rename sample/demo warehouses (Coronel Bogado, SUC1, etc.)
                demo_whs = env['stock.warehouse'].search([('code', 'in', ['SUC1', 'SUC2', 'BOG'])])
                for dwh in demo_whs:
                    if dwh.code != 'WHC':
                        try:
                            dwh.write({'active': False})
                            print(f"  ✓ Archived sample warehouse: {dwh.name} ({dwh.code})")
                        except Exception:
                            pass

                warehouses_list = config.get('warehouses', [{'name': 'Depósito Central', 'code': 'WHC'}])
                for wh_data in warehouses_list:
                    code = wh_data.get('code')
                    name = wh_data.get('name')
                    if not code or not name:
                        continue
                    wh = env['stock.warehouse'].search([('code', '=', code)], limit=1)
                    wh_vals = {
                        'name': name,
                        'code': code,
                        'active': True,
                    }
                    if wh:
                        wh.write(wh_vals)
                        print(f"  ✓ Updated Warehouse: {name} ({code})")
                    else:
                        env['stock.warehouse'].create(wh_vals)
                        print(f"  ✓ Created Warehouse: {name} ({code})")
            cr.commit()
        except Exception as e:
            cr.rollback()
            print(f"  ⚠️ Warehouse configuration warning: {e}")
                    
        # 3. Product Categories (Costo y Valoración de Inventario)
        try:
            prod_cat_list = config.get('product_categories_config', [])
            if prod_cat_list and 'product.category' in env:
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
                    cat.write(cat_vals)
                    print(f"  ✓ Category configured: {cat_name}")
            cr.commit()
        except Exception as e:
            cr.rollback()
            print(f"  ⚠️ Product categories configuration warning: {e}")

        # 4. Accounting Settings (Redondeo de IVA y Plazos de Pago)
        try:
            acc_data = config.get('accounting', {})
            if acc_data:
                print("Configuring Accounting Rounding & Payment Terms...")
                company = env['res.company'].browse(1)
                rounding = acc_data.get('tax_calculation_rounding_method', 'round_per_line')
                if company.exists():
                    company.write({'tax_calculation_rounding_method': rounding})
                    print(f"  ✓ Company Tax Rounding set to: {rounding}")
                
                rename_to = acc_data.get('payment_immediate_rename_to')
                if rename_to and 'account.payment.term' in env:
                    term = env.ref('account.account_payment_term_immediate', raise_if_not_found=False)
                    if not term:
                        term = env['account.payment.term'].search([('name', '=ilike', 'inmediato')], limit=1)
                    if term:
                        term.write({'name': rename_to})
                        print(f"  ✓ Payment Term Immediate renamed to: {rename_to}")
            cr.commit()
        except Exception as e:
            cr.rollback()
            print(f"  ⚠️ Accounting settings warning: {e}")

        # 5. Journals (Diarios Contables)
        try:
            if 'account.journal' in env:
                print("Configuring Account Journals (Diarios contables)...")
                cash_j = env['account.journal'].search([('type', '=', 'cash'), ('company_id', '=', 1)], limit=1)
                if cash_j:
                    cash_j.write({'name': 'Efectivo'})
                    print(f"  ✓ Updated Cash Journal: {cash_j.name} ({cash_j.code})")

                bank_j = env['account.journal'].search([('type', '=', 'bank'), ('company_id', '=', 1)], limit=1)
                if bank_j:
                    bank_j.write({'name': 'Banco'})
                    print(f"  ✓ Updated Bank Journal: {bank_j.name} ({bank_j.code})")
            cr.commit()
        except Exception as e:
            cr.rollback()
            print(f"  ⚠️ Journals configuration warning: {e}")

        # 6. Analytic Accounts
        try:
            if 'account.analytic.account' in env:
                sample_analytics = env['account.analytic.account'].search([('code', 'in', ['SUC1-ANA', 'SUC1'])])
                for sa in sample_analytics:
                    try:
                        sa.write({'active': False})
                        print(f"  ✓ Archived sample Analytic Account: {sa.name}")
                    except Exception:
                        pass
            cr.commit()
        except Exception as e:
            cr.rollback()
            print(f"  ⚠️ Analytic accounts configuration warning: {e}")

        # 7. POS Config (Puntos de Venta)
        try:
            if 'pos.config' in env and 'account.journal' in env and 'pos.payment.method' in env:
                print("Configuring Point of Sale (POS)...")
                to_remove = config.get('pos_configs_to_remove', ["Bakery", "Clothes Shop", "Furniture Shop"])
                for demo_name in to_remove:
                    demo_pos = env['pos.config'].search([('name', '=ilike', demo_name)], limit=1)
                    if demo_pos and demo_pos.name != 'Ferretería':
                        try:
                            has_session = False
                            if 'pos.session' in env:
                                has_session = bool(env['pos.session'].search([('config_id', '=', demo_pos.id), ('state', '!=', 'closed')], limit=1))
                            if not has_session:
                                demo_pos.write({'active': False})
                                print(f"  ✓ Archived demo POS Config: {demo_pos.name}")
                        except Exception:
                            pass

                cash_journal = env['account.journal'].search([('type', '=', 'cash'), ('company_id', '=', 1)], limit=1)
                cash_method = env['pos.payment.method'].search([('journal_id', '=', cash_journal.id)], limit=1) if cash_journal else None
                if cash_journal and not cash_method:
                    cash_method = env['pos.payment.method'].create({
                        'name': 'Efectivo',
                        'journal_id': cash_journal.id,
                    })
                    print(f"  ✓ Created POS Payment Method: {cash_method.name}")

                bank_journal = env['account.journal'].search([('type', '=', 'bank'), ('company_id', '=', 1)], limit=1)
                bank_method = env['pos.payment.method'].search([('journal_id', '=', bank_journal.id)], limit=1) if bank_journal else None
                if bank_journal and not bank_method:
                    bank_method = env['pos.payment.method'].create({
                        'name': 'Banco/Tarjeta',
                        'journal_id': bank_journal.id,
                    })
                    print(f"  ✓ Created POS Payment Method: {bank_method.name}")

                invoice_journal = env['account.journal'].search([
                    ('type', '=', 'sale'),
                    ('company_id', '=', 1)
                ], limit=1)

                payment_methods = []
                if cash_method:
                    payment_methods.append(cash_method.id)
                if bank_method:
                    payment_methods.append(bank_method.id)

                pos_list = config.get('pos_configs', [{'name': 'Ferretería', 'is_restaurant': False}])
                for pos_data in pos_list:
                    pos_name = pos_data.get('name', 'Ferretería')
                    pos_config = env['pos.config'].search([('name', '=', pos_name)], limit=1)
                    if not pos_config:
                        unnamed_pos = env['pos.config'].with_context(active_test=False).search([('name', 'in', ['Caja Principal', 'Shop', 'Main'])], limit=1)
                        if unnamed_pos:
                            pos_config = unnamed_pos
                            pos_config.write({'name': pos_name, 'active': True})
                            print(f"  ✓ Renamed default POS Config to: {pos_name}")

                    has_active_session = False
                    if pos_config and 'pos.session' in env:
                        active_sessions = env['pos.session'].search([
                            ('config_id', '=', pos_config.id),
                            ('state', '!=', 'closed')
                        ])
                        if active_sessions:
                            has_active_session = True
                            print(f"  ℹ POS {pos_name} has active sessions. Skipping configuration updates to avoid Odoo locks.")

                    if not has_active_session:
                        pos_vals = {
                            'name': pos_name,
                            'active': True,
                        }
                        if hasattr(env['pos.config'], 'module_pos_restaurant'):
                            pos_vals['module_pos_restaurant'] = pos_data.get('is_restaurant', False)
                        if invoice_journal:
                            pos_vals['invoice_journal_id'] = invoice_journal.id
                        if payment_methods:
                            pos_vals['payment_method_ids'] = [(6, 0, payment_methods)]

                        if pos_config:
                            pos_config.write(pos_vals)
                            print(f"  ✓ Updated POS Config: {pos_config.name}")
                        else:
                            pos_config = env['pos.config'].create(pos_vals)
                            print(f"  ✓ Created POS Config: {pos_config.name}")
            cr.commit()
        except Exception as e:
            cr.rollback()
            print(f"  ⚠️ POS configuration warning: {e}")

        # 8. Configure Language (Español América Latina)
        try:
            lang_code = 'es_419'
            lang = env['res.lang'].with_context(active_test=False).search([('code', '=', lang_code)], limit=1)
            if lang:
                if not lang.active:
                    lang.write({'active': True})
                    print(f"  ✓ Activated language record {lang_code}")
                print("Installing/loading language translations: Spanish (Latin America) / Español (América Latina)...")
                try:
                    lang_installer = env['base.language.install'].create({
                        'lang_ids': [(6, 0, [lang.id])],
                        'overwrite': True,
                    })
                    lang_installer.lang_install()
                    print("  ✓ Language es_419 installed/loaded successfully.")
                except Exception as e:
                    print(f"  Warning: Could not install language es_419: {e}")
            else:
                print(f"  Warning: Language record {lang_code} not found in res.lang")
                    
            print("Setting default language es_419 for existing users and partners...")
            env['res.users'].search([]).write({'lang': lang_code})
            env['res.partner'].search([]).write({'lang': lang_code})
            print("  ✓ Updated existing users and partners language to es_419.")

            if 'ir.default' in env:
                env['ir.default'].set('res.partner', 'lang', lang_code)
                env['ir.default'].set('res.users', 'lang', lang_code)
                print("  ✓ Default language set for future contacts/users.")
            cr.commit()
        except Exception as e:
            cr.rollback()
            print(f"  ⚠️ Language configuration warning: {e}")

        cr.commit()
        print("✓ System Settings configuration finished successfully!")

if __name__ == '__main__':
    import_settings()
