import sys

orders = env['pos.order'].search([], order='id desc', limit=10)
for o in orders:
    print(f"Order: {o.name} - Partner: {o.partner_id.name if o.partner_id else 'None'} - Total: {o.amount_total}")
    for line in o.lines:
        print(f"  Line: {line.product_id.name} - Price: {line.price_unit} - Subtotal: {line.price_subtotal_incl}")
    for pay in o.payment_ids:
        print(f"  Payment: {pay.amount} ({pay.payment_method_id.name} - {pay.payment_method_id.type}) - change: {pay.is_change}")
