import sys

partner = env['res.partner'].search([('name', 'ilike', 'Marcelo Pesallaccia')], limit=1)
if partner:
    pos_orders = env['pos.order'].search([
        ('partner_id', '=', partner.id),
        ('state', 'in', ['paid', 'done', 'draft']),
        ('session_id.state', '!=', 'closed')
    ])
    
    pos_debt_delta = 0.0
    for order in pos_orders:
        if order.account_move and order.account_move.state == 'posted':
            continue
        
        real_paid = sum(order.payment_ids.filtered(
            lambda p: p.payment_method_id.type in ['cash', 'bank']
        ).mapped('amount'))
        
        settlement_amount = sum(order.lines.filtered(
            lambda l: l.product_id.name == 'Abono de Cuenta'
        ).mapped('price_subtotal_incl'))
        
        real_amount_total = order.amount_total - settlement_amount
        delta = real_amount_total - real_paid
        pos_debt_delta += delta
        print(f"Order {order.name}: amount={order.amount_total}, settle={settlement_amount}, paid={real_paid} -> delta={delta}")
    
    total_due = ((partner.debit or 0.0) - (partner.credit or 0.0)) + pos_debt_delta
    print(f"Total Due (correct): {total_due}")
    print(f"Outstanding Debt: {-total_due}")
