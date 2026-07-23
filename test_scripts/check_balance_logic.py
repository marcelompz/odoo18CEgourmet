import sys

pm_methods = env['pos.payment.method'].search([])
for pm in pm_methods:
    print(f"ID: {pm.id} - Name: {pm.name} - Type: {pm.type}")

partner = env['res.partner'].search([('name', 'ilike', 'Marcelo Pesallaccia')], limit=1)
if partner:
    print(f"\nPartner: {partner.name}")
    print(f"Debit: {partner.debit}")
    print(f"Credit: {partner.credit}")
    print(f"Outstanding Debt: {partner.outstanding_debt}")

    pos_orders = env['pos.order'].search([('partner_id', '=', partner.id)])
    print(f"All POS Orders for {partner.name}:")
    for o in pos_orders:
        print(f"  Order: {o.name} - State: {o.state} - Total: {o.amount_total}")
        for p in o.payment_ids:
            print(f"    Payment: {p.amount} ({p.payment_method_id.name} - {p.payment_method_id.type})")
