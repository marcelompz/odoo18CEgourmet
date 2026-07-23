import sys

partner = env['res.partner'].search([('name', 'ilike', 'Marcelo Pesallaccia')], limit=1)
orders = env['pos.order'].search([('partner_id', '=', partner.id)], order='id desc', limit=5)

for o in orders:
    print(f"Order: {o.name} (ID: {o.id}) - State: {o.state} - Total: {o.amount_total}")
    for line in o.lines:
        print(f"  Line: {line.product_id.name} - Price: {line.price_unit} - Subtotal: {line.price_subtotal_incl}")
    for p in o.payment_ids:
        print(f"  Payment: {p.amount} ({p.payment_method_id.name}) - is_change: {p.is_change}")
