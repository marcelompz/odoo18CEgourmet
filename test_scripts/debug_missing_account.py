import sys
import traceback
from odoo.addons.account.models.account_move_line import AccountMoveLine

original_create = AccountMoveLine.create

def patched_create(self, vals_list):
    if isinstance(vals_list, dict):
        vals_list = [vals_list]
    for vals in vals_list:
        if not vals.get('account_id'):
            with open('/tmp/missing_account.txt', 'a') as f:
                f.write("\\n!!! MISSING ACCOUNT_ID IN VALS !!!\\n")
                f.write(f"Vals: {vals}\\n")
                f.write("TRACEBACK:\\n")
                traceback.print_stack(file=f)
    return original_create(self, vals_list)

AccountMoveLine.create = patched_create

session = env['pos.session'].search([('state', '!=', 'closed')], limit=1)
if session:
    try:
        session.action_pos_session_closing_control()
    except Exception as e:
        pass
