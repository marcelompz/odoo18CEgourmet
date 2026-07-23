import sys

partner = env['res.partner'].search([('name', 'ilike', 'Marcelo Pesallaccia')], limit=1)
if partner:
    print(f"Partner: {partner.name}")
    print(f"Debit: {partner.debit}")
    print(f"Credit: {partner.credit}")
    
    pos_orders = env['pos.order'].search([
        ('partner_id', '=', partner.id),
        ('state', 'in', ['paid', 'done', 'draft']),
        ('session_id.state', '!=', 'closed')
    ])
    
    pos_debt_delta = 0.0
    for order in pos_orders:
        if order.account_move and order.account_move.state == 'posted':
            print(f"  Order {order.name} SKIPPED")
            continue
        # Use amount_total - real_paid where real_paid includes change!
        # wait, if order.amount_total = 0, and they pay 165000, and change is -165000.
        # the net paid is 0!
        real_paid_no_change = sum(order.payment_ids.filtered(lambda p: not p.is_change and p.payment_method_id.type in ['cash', 'bank']).mapped('amount'))
        real_paid_all = sum(order.payment_ids.filtered(lambda p: p.payment_method_id.type in ['cash', 'bank']).mapped('amount'))
        
        delta_old = order.amount_total - real_paid_no_change
        delta_new = order.amount_total - real_paid_all
        
        print(f"  Order {order.name}: total={order.amount_total}, paid_no_change={real_paid_no_change}, paid_all={real_paid_all}")
        print(f"      delta_old={delta_old}, delta_new={delta_new}")
        
    print(f"Odoo outstanding_debt: {partner.outstanding_debt}")

