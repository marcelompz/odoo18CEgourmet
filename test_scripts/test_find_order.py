order = env['pos.order'].search([('pos_reference', 'ilike', '%261-1-000024%')], limit=1)
if order:
    print(f"Order: {order.name} | Partner: {order.partner_id.name}")
    move = env['account.move'].search([('ref', 'ilike', f'%{order.name}%')], limit=1)
    if move:
        print(f"Compensating Move: {move.name} | State: {move.state}")
    else:
        print(f"NO COMPENSATING MOVE FOR {order.name}!")
else:
    print("Order not found by pos_reference")
