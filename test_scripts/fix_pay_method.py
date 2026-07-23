import sys

pm = env['pos.payment.method'].search([('name', 'ilike', 'Cuenta de cliente')], limit=1)
if not pm:
    print("Payment Method not found")
    sys.exit()

# Find the Customer Invoices journal or create a generic POS journal
journal = env['account.journal'].search([('type', '=', 'general'), ('code', '=', 'POSS')], limit=1)
if not journal:
    journal = env['account.journal'].search([('type', '=', 'general')], limit=1)

# Find the Receivable account
receivable_account = env['account.account'].search([('account_type', '=', 'asset_receivable')], limit=1)

pm.write({
    'journal_id': journal.id if journal else False,
    'receivable_account_id': receivable_account.id if receivable_account else False,
    'outstanding_account_id': receivable_account.id if receivable_account else False,
})

print(f"Updated Payment Method {pm.name}:")
print(f"  Journal: {pm.journal_id.name}")
print(f"  Receivable Account: {pm.receivable_account_id.name}")
print(f"  Outstanding Account: {pm.outstanding_account_id.name}")
