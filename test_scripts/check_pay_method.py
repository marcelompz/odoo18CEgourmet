import sys

pm = env['pos.payment.method'].search([('name', 'ilike', 'Cuenta de cliente')], limit=1)
if pm:
    print(f"Payment Method: {pm.name}")
    print(f"Type: {pm.type}")
    print(f"Split Transactions: {pm.split_transactions}")
    print(f"Receivable Account: {pm.receivable_account_id.name if pm.receivable_account_id else 'None'}")
    print(f"Outstanding Account: {pm.outstanding_account_id.name if pm.outstanding_account_id else 'None'}")
    print(f"Journal: {pm.journal_id.name if pm.journal_id else 'None'}")
else:
    print("Not found")
