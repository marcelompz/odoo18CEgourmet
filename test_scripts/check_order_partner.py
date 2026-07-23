import sys

o = env['pos.order'].search([('name', '=', '000001')], limit=1)
if o and o.partner_id:
    partner = o.partner_id
    print(f"Partner: {partner.name} - Debit: {partner.debit} - Credit: {partner.credit}")
    
    orders = env['pos.order'].search([('partner_id', '=', partner.id)])
    for o in orders:
        print(f"Order: {o.name} - Session State: {o.session_id.state}")
        if o.account_move:
            print(f"  Account Move: {o.account_move.name} - State: {o.account_move.state}")
        else:
            print("  No Account Move yet.")
