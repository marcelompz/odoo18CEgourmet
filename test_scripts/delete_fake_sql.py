# Find the orders
orders = env['pos.order'].search([('name', 'in', ['000029', '000031'])])
print(f"Found orders: {orders.ids}")

if orders:
    order_ids = tuple(orders.ids)
    
    # 1. Delete pos.payment
    env.cr.execute("DELETE FROM pos_payment WHERE pos_order_id IN %s", (order_ids,))
    print("Deleted payments")
    
    # 2. Delete pos.order.line
    env.cr.execute("DELETE FROM pos_order_line WHERE order_id IN %s", (order_ids,))
    print("Deleted lines")
    
    # 3. Delete pos.order
    env.cr.execute("DELETE FROM pos_order WHERE id IN %s", (order_ids,))
    print("Deleted orders")
    
    env.cr.commit()
    print("Fake POS Orders deleted from DB!")
