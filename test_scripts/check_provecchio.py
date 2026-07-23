import sys

partner = env['res.partner'].search([('name', 'ilike', 'Provecchio')], limit=1)
if not partner:
    print("Partner not found")
    sys.exit()

print(f"Partner: {partner.name}")
print(f"Outstanding debt (orm): {partner.outstanding_debt}")

pos_orders = env['pos.order'].search([
    ('partner_id', '=', partner.id),
    ('state', 'in', ['paid', 'done', 'draft']),
    ('session_id.state', '!=', 'closed')
])

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
    for p in order.payment_ids:
        print(f"  Payment: {p.amount} ({p.payment_method_id.name} - {p.payment_method_id.type})")
    pos_debt_delta += delta

print(f"pos_debt_delta: {pos_debt_delta}")
accounting_balance = (partner.debit or 0.0) - (partner.credit or 0.0)
print(f"accounting_balance: {accounting_balance} (debit: {partner.debit}, credit: {partner.credit})")
print(f"total_due: {accounting_balance + pos_debt_delta}")
