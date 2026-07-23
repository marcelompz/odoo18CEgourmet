import sys
from odoo.addons.point_of_sale.models.pos_session import PosSession

original_method = PosSession._get_pos_session_order_line_accounts

def patched_method(self, order_lines):
    try:
        return original_method(self, order_lines)
    except Exception as e:
        print("\n!!! ERROR IN _get_pos_session_order_line_accounts !!!")
        for line in order_lines:
            product = line.product_id
            print(f"Checking Line: Order {line.order_id.name} | Product {product.name}")
            try:
                if line.qty > 0:
                    account = product.with_company(self.company_id)._get_product_accounts()['income']
                else:
                    account = product.with_company(self.company_id)._get_product_accounts()['expense']
                if not account:
                    print(f"   -> FAILED: NO ACCOUNT FOUND FOR PRODUCT {product.name}")
            except Exception as e2:
                print(f"   -> EXCEPTION CHECKING ACCOUNT: {e2}")
        raise e

PosSession._get_pos_session_order_line_accounts = patched_method

session = env['pos.session'].search([('state', '!=', 'closed')], limit=1)
if not session:
    print("No open sessions found.")
    sys.exit(0)

try:
    session.action_pos_session_closing_control()
except Exception as e:
    print(f"Failed as expected: {e}")
