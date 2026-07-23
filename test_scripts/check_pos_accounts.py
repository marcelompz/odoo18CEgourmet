import sys

sessions = env['pos.session'].search([('state', '!=', 'closed')])
for session in sessions:
    print("-------------------------")
    print(f"Sesion: {session.name} - ID: {session.id}")
    for order in session.order_ids:
        for line in order.lines:
            product = line.product_id
            account = product.property_account_income_id or product.categ_id.property_account_income_categ_id
            if not account:
                # Odoo's default fallback logic for POS might use something else, but let's see if product/categ has it
                account_id = None
            else:
                account_id = account.name
            print(f"Order: {order.name} | Product: {product.name} (ID: {product.id}) | Qty: {line.qty} | Account: {account_id if account_id else 'MISSING!!!'}")
