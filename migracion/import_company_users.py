#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Import/Update Company details and Users with security groups dynamically from JSON files.
"""

import sys
import json
import os

sys.path.append('/usr/lib/python3/dist-packages')
os.environ.setdefault('ODOO_RC', '/etc/odoo/odoo.conf')

import odoo
import odoo.modules.registry
from odoo import api, SUPERUSER_ID

def import_company_and_users():
    db_name = os.environ.get('DB_NAME', 'prod')
    print("=" * 60)
    print(f"Importing Company and Users on database: {db_name}")
    print("=" * 60)
    
    registry = odoo.modules.registry.Registry(db_name)
    
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        
        # 1. Update Company
        company_path = '/mnt/migracion/company.json'
        if os.path.exists(company_path):
            print("Loading company details from company.json...")
            with open(company_path, 'r', encoding='utf-8') as f:
                co_data = json.load(f)
            
            company = env['res.company'].browse(1)
            if company.exists():
                vals = {
                    'name': co_data.get('name', company.name),
                    'phone': co_data.get('phone', company.phone),
                    'email': co_data.get('email', company.email),
                    'website': co_data.get('website', company.website),
                    'vat': co_data.get('vat', company.vat),
                    'street': co_data.get('street', company.street),
                    'city': co_data.get('city', company.city),
                }
                country_code = co_data.get('country_code')
                country = None
                if country_code:
                    country = env['res.country'].search([('code', '=', country_code.upper())], limit=1)
                    if country:
                        vals['country_id'] = country.id
                
                state_name = co_data.get('state')
                if state_name and country:
                    states = env['res.country.state'].search([('country_id', '=', country.id)])
                    import unicodedata
                    def clean_str(s):
                        return "".join(c for c in unicodedata.normalize('NFD', s.lower()) if unicodedata.category(c) != 'Mn')
                    
                    cleaned_target = clean_str(state_name)
                    state = None
                    for s in states:
                        if clean_str(s.name) == cleaned_target or clean_str(s.code) == cleaned_target:
                            state = s
                            break
                    if state:
                        vals['state_id'] = state.id
                        print(f"  ✓ State found and mapped: {state.name} ({state.code})")
                    else:
                        print(f"  ⚠️ State '{state_name}' not found for country {country.name}")

                company.write(vals)
                print(f"✓ Company details updated: {company.name}")
        else:
            print("ℹ company.json not found, skipping company details update.")

        # 2. Load Users
        users_path = '/mnt/migracion/users.json'
        if os.path.exists(users_path):
            print("Loading users from users.json...")
            with open(users_path, 'r', encoding='utf-8') as f:
                users_list = json.load(f)
            
            for user_data in users_list:
                login = user_data.get('login')
                name = user_data.get('name')
                password = user_data.get('password')
                groups_xml_ids = user_data.get('groups', [])
                
                if not login or not name:
                    continue
                
                # Find group IDs from XML IDs
                group_ids = []
                for group_xml_id in groups_xml_ids:
                    group = env.ref(group_xml_id, raise_if_not_found=False)
                    if group:
                        group_ids.append(group.id)
                    else:
                        print(f"  ⚠️ Group not found: {group_xml_id}")
                
                user = env['res.users'].search([('login', '=', login)], limit=1)
                user_vals = {
                    'name': name,
                    'login': login,
                }
                
                # Assign groups if specified
                if group_ids:
                    user_vals['groups_id'] = [(6, 0, group_ids)]
                
                if password:
                    user_vals['password'] = password
                
                if user:
                    user.write(user_vals)
                    print(f"✓ User updated: {name} ({login})")
                else:
                    user = env['res.users'].create(user_vals)
                    print(f"✓ User created: {name} ({login})")
        else:
            print("ℹ users.json not found, skipping users creation.")
            
        cr.commit()
        print("✓ Company and Users setup finished successfully!")

if __name__ == '__main__':
    import_company_and_users()
