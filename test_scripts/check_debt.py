import sys

partner = env['res.partner'].search([('name', 'ilike', 'Marcelo Pesallaccia')], limit=1)
if partner:
    print(f"Partner: {partner.name}")
    print(f"Outstanding Debt: {partner.outstanding_debt}")
    print(f"Debit: {partner.debit}")
    print(f"Credit: {partner.credit}")
    print(f"Total Due: {partner.total_due if hasattr(partner, 'total_due') else 'N/A'}")
    
    pos_orders = env['pos.order'].search([
        ('partner_id', '=', partner.id),
        ('state', 'in', ['paid', 'done', 'draft']),
        ('session_id.state', '!=', 'closed')
    ])
    print(f"POS Orders in current session: {len(pos_orders)}")
    for o in pos_orders:
        print(f"  Order: {o.name} - Total: {o.amount_total}")
        for p in o.payment_ids:
            print(f"    Payment: {p.amount} ({p.payment_method_id.name})")
else:
    print("Partner not found")
