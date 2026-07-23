import sys

journals = env['account.journal'].search([('type', 'in', ['bank', 'cash'])])
for j in journals:
    print(f"Journal: {j.name}")
    print(f"  Default Account: {j.default_account_id.name if j.default_account_id else 'MISSING'}")
    
    # check outstanding accounts in payment methods
    in_methods = j.inbound_payment_method_line_ids
    for m in in_methods:
        print(f"  Inbound Method: {m.name} | Account: {m.payment_account_id.name if m.payment_account_id else 'MISSING (uses default or company)'}")

    out_methods = j.outbound_payment_method_line_ids
    for m in out_methods:
        print(f"  Outbound Method: {m.name} | Account: {m.payment_account_id.name if m.payment_account_id else 'MISSING (uses default or company)'}")
