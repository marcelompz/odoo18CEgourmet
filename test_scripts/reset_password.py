#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Reset password for user soporte@crossnexion.com"""

import sys
import os
sys.path.insert(0, '/usr/lib/python3/dist-packages')
os.environ.setdefault('ODOO_RC', '/etc/odoo/odoo.conf')

import odoo
from odoo import api, SUPERUSER_ID

def reset_password():
    odoo.modules.registry.Registry.new('dimora')
    registry = odoo.registry('dimora')
    
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        
        # Find user
        user = env['res.users'].search([('login', '=', 'soporte@crossnexion.com')], limit=1)
        
        if not user:
            print("ERROR: User not found")
            return False
        
        print(f"Found user: {user.login}")
        print(f"Active: {user.active}")
        print(f"Company: {user.company_id.name if user.company_id else 'None'}")
        
        # Reset password using Odoo's method (properly hashes it)
        new_password = 'soporte2026'
        user.write({'password': new_password})
        
        print(f"Password reset to: {new_password}")
        print("Please try logging in now")
        
        cr.commit()
        return True

if __name__ == '__main__':
    try:
        reset_password()
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
