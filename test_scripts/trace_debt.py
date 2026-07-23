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
            print(f"  Order {order.name} SKIPPED (already in accounting)")
            continue
        real_paid = sum(order.payment_ids.filtered(
            lambda p: not p.is_change and p.payment_method_id.type in ['cash', 'bank']
        ).mapped('amount'))
        delta = order.amount_total - real_paid
        pos_debt_delta += delta
        print(f"  Order {order.name}: total={order.amount_total}, real_paid={real_paid}, delta={delta}")
    
    print(f"pos_debt_delta: {pos_debt_delta}")
    print(f"accounting_balance: {(partner.debit or 0.0) - (partner.credit or 0.0)}")
    total_due = ((partner.debit or 0.0) - (partner.credit or 0.0)) + pos_debt_delta
    print(f"total_due: {total_due}")
