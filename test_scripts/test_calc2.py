partner = env['res.partner'].search([('name', 'ilike', 'Marcelo Pesallaccia')], limit=1)
partner_c = partner.with_company(env.company)

print(f"\nManual Calculation with Company Context:")
accounting_balance = (partner_c.debit or 0.0) - (partner_c.credit or 0.0)
print(f"Debit: {partner_c.debit} | Credit: {partner_c.credit} | Accounting Balance: {accounting_balance}")

pos_orders = env['pos.order'].search([
    ('partner_id', '=', partner.id),
    ('state', 'in', ['paid', 'done', 'draft']),
    ('session_id.state', '!=', 'closed')
])

pos_debt_delta = 0.0
for order in pos_orders:
    if order.account_move and order.account_move.state == 'posted':
        print(f"  Order {order.name} skipped (account move posted)")
        continue
    
    compensating_move = env['account.move'].search([
        ('ref', 'ilike', f'%{order.name}%'),
        ('state', '=', 'posted')
    ], limit=1)
    if compensating_move:
        print(f"  Order {order.name} skipped (compensating move {compensating_move.name} posted)")
        continue

    real_paid = sum(order.payment_ids.filtered(lambda p: p.payment_method_id.type in ['cash', 'bank']).mapped('amount'))
    settlement_amount = sum(order.lines.filtered(lambda l: l.product_id.name == 'Abono de Cuenta').mapped('price_subtotal_incl'))
    real_amount_total = order.amount_total - settlement_amount
    delta = (real_amount_total - real_paid)
    pos_debt_delta += delta
    print(f"  Order {order.name} | Total: {order.amount_total} | Settlemnt: {settlement_amount} | RealPaid: {real_paid} | Delta: {delta}")

print(f"POS Debt Delta: {pos_debt_delta}")
total_due = accounting_balance + pos_debt_delta
print(f"Total Due: {total_due} | Outstanding: {-total_due}")
