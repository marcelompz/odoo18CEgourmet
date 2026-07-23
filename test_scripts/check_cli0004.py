import sys

partner = env['res.partner'].search([('name', 'ilike', 'CLI0004')], limit=1)
if not partner:
    print("Partner CLI0004 not found")
    sys.exit()

print(f"Partner: {partner.name}")
orders = env['pos.order'].search([('partner_id', '=', partner.id)], order='id desc', limit=5)

for o in orders:
    print(f"Order: {o.name} - State: {o.state} - Total: {o.amount_total}")
    for line in o.lines:
        print(f"  Line: {line.product_id.name} - Price: {line.price_unit} - Subtotal: {line.price_subtotal_incl}")
    for p in o.payment_ids:
        print(f"  Payment: {p.amount} ({p.payment_method_id.name} - {p.payment_method_id.type}) - change: {p.is_change}")
