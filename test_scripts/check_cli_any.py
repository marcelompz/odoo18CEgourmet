import sys

partner = env['res.partner'].search([('name', 'ilike', 'CLI')], limit=5)
for p in partner:
    print(f"Partner: {p.name}")
    orders = env['pos.order'].search([('partner_id', '=', p.id)], order='id desc', limit=5)

    for o in orders:
        print(f"Order: {o.name} - State: {o.state} - Total: {o.amount_total}")
        for line in o.lines:
            print(f"  Line: {line.product_id.name} - Price: {line.price_unit} - Subtotal: {line.price_subtotal_incl}")
        for pay in o.payment_ids:
            print(f"  Payment: {pay.amount} ({pay.payment_method_id.name} - {pay.payment_method_id.type}) - change: {pay.is_change}")
