company = env['res.company'].search([('name', '=', 'Provecchio')])
partner = env['res.partner'].search([('name', 'ilike', 'Marcelo Pesallaccia')], limit=1)
partner_c = partner.with_company(company)

print(f"Partner: {partner_c.name}")
print(f"Company: {company.name}")
print(f"Receivable Account: {partner_c.property_account_receivable_id.name}")
print(f"Debit: {partner_c.debit}")
print(f"Credit: {partner_c.credit}")

# Find all unreconciled move lines for this account
lines = env['account.move.line'].search([
    ('partner_id', '=', partner.id),
    ('account_id', '=', partner_c.property_account_receivable_id.id),
    ('reconciled', '=', False)
])
print(f"Unreconciled lines for {partner.name}:")
for l in lines:
    print(f"  {l.move_id.name} | Debit: {l.debit} | Credit: {l.credit}")
