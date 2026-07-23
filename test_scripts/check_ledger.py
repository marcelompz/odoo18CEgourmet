import sys

partner = env['res.partner'].search([('name', 'ilike', 'CLI004')], limit=1)
print(f"Partner: {partner.name} - Debit: {partner.debit} - Credit: {partner.credit}")
print(f"Accounting Balance: {(partner.debit or 0) - (partner.credit or 0)}")

orders = env['pos.order'].search([('partner_id', '=', partner.id)])
for o in orders:
    print(f"Order: {o.name} - Session State: {o.session_id.state}")
    if o.account_move:
        print(f"  Account Move: {o.account_move.name} - State: {o.account_move.state}")
        for line in o.account_move.line_ids:
            if line.partner_id.id == partner.id:
                print(f"    Line Partner Match! Account: {line.account_id.name} - Debit: {line.debit} - Credit: {line.credit}")
    else:
        print("  No Account Move yet.")
