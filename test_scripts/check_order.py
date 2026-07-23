import sys

order = env['pos.order'].search([('name', '=', '000014')])
if order:
    print(f"Order: {order.name}")
    print(f"Amount Total: {order.amount_total}")
    for line in order.lines:
        print(f"  Line: {line.product_id.name} - Price: {line.price_unit} - Qty: {line.qty} - Subtotal: {line.price_subtotal_incl}")
    for pay in order.payment_ids:
        print(f"  Payment: {pay.amount} ({pay.payment_method_id.name} - {pay.payment_method_id.type})")
else:
    print("Order 14 not found")

