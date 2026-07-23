orders = env['pos.order'].search([('name', 'in', ['000037', '000039'])])
for o in orders:
    print(f"Order: {o.name} | Amount Total: {o.amount_total}")
    for l in o.lines:
        print(f"  Line: {l.product_id.name} | subtotal: {l.price_subtotal_incl}")
