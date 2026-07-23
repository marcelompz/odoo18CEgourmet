import sys
from odoo.addons.point_of_sale.models.pos_session import PosSession

original = PosSession._create_stock_valuation_lines

def patched(self, data):
    with open('/tmp/debug_keys_out.txt', 'w') as f:
        f.write("=== STOCK VALUATION KEYS ===\n")
        for k in data.get('stock_valuation', {}).keys():
            f.write(f"  VAL: {k}\n")
        for k in data.get('stock_return', {}).keys():
            f.write(f"  RET: {k}\n")
    return original(self, data)

PosSession._create_stock_valuation_lines = patched

session = env['pos.session'].search([('state', '!=', 'closed')], limit=1)
if session:
    try:
        session.action_pos_session_closing_control()
    except Exception as e:
        pass
