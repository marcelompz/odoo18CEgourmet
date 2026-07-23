import sys

session = env['pos.session'].search([('state', '!=', 'closed')], limit=1)
if not session:
    print("No open sessions found.")
    sys.exit(0)

print(f"Checking session: {session.name}")

order_lines = session.order_ids.mapped('lines')
for line in order_lines:
    if line.qty > 0:
        # It's an income
        account = line.product_id.with_company(session.company_id)._get_product_accounts()['income']
    else:
        # It's a refund / expense
        account = line.product_id.with_company(session.company_id)._get_product_accounts()['expense']
        
    if not account:
        print(f"❌ FAIL: Line ID {line.id} | Order: {line.order_id.name} | Product: {line.product_id.name} | Qty: {line.qty} -> NO ACCOUNT")
    else:
        print(f"✅ OK: Line ID {line.id} | Order: {line.order_id.name} | Product: {line.product_id.name} | Qty: {line.qty} -> Account: {account.name}")

