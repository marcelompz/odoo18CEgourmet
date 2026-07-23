import sys

partner = env['res.partner'].search([('name', 'ilike', 'CLI')], limit=5)
for p in partner:
    pos_orders = env['pos.order'].search([
        ('partner_id', '=', p.id),
        ('state', 'in', ['paid', 'done', 'draft']),
        ('session_id.state', '!=', 'closed')
    ])
    
    if not pos_orders:
        continue
        
    print(f"Partner: {p.name}")
    print(f"Outstanding debt (orm): {p.outstanding_debt}")

    pos_debt_delta = 0.0
    for order in pos_orders:
        real_paid = sum(order.payment_ids.filtered(
            lambda pay: pay.payment_method_id.type in ['cash', 'bank']
        ).mapped('amount'))
        
        settlement_amount = sum(order.lines.filtered(
            lambda l: l.product_id.name == 'Abono de Cuenta'
        ).mapped('price_subtotal_incl'))
        
        real_amount_total = order.amount_total - settlement_amount
        delta = real_amount_total - real_paid
        print(f"Order {order.name}: total={order.amount_total}, settle={settlement_amount}, real_total={real_amount_total}, paid={real_paid} => delta={delta}")
        pos_debt_delta += delta

    print(f"pos_debt_delta: {pos_debt_delta}")
    accounting_balance = (p.debit or 0.0) - (p.credit or 0.0)
    print(f"accounting_balance: {accounting_balance}")
    print(f"total_due: {accounting_balance + pos_debt_delta}")
    print("-----------------------------------")
