import sys

with open('/tmp/check_session_moves_out.txt', 'w') as f:
    session = env['pos.session'].search([('state', '!=', 'closed')], limit=1)
    if not session:
        f.write("No open sessions found.\n")
        sys.exit(0)

    all_picking_ids = session.order_ids.filtered(lambda p: not p.is_invoiced and not p.shipping_date).picking_ids.ids + session.picking_ids.filtered(lambda p: not p.pos_order_id).ids
    stock_moves = env['stock.move'].sudo().search([
        ('picking_id', 'in', all_picking_ids),
        ('product_id.is_storable', '=', True),
        ('product_id.valuation', '=', 'real_time'),
    ])

    for move in stock_moves:
        p = move.product_id
        accounts = p._get_product_accounts()
        f.write(f"Move: {move.id} | Product: {p.name}\n")
        f.write(f"  Expense: {accounts.get('expense').name if accounts.get('expense') else 'False'}\n")
        f.write(f"  Stock Valuation: {accounts.get('stock_valuation').name if accounts.get('stock_valuation') else 'False'}\n")
