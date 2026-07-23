company = env['res.company'].search([('name', '=', 'Provecchio')])
partner = env['res.partner'].search([('name', 'ilike', 'Marcelo Pesallaccia')], limit=1)
partner_c = partner.with_company(company)

lines = env['account.move.line'].search([
    ('partner_id', '=', partner.id),
    ('account_id', '=', partner_c.property_account_receivable_id.id),
    ('reconciled', '=', False)
])
accounting_balance = sum(lines.mapped('debit')) - sum(lines.mapped('credit'))

print(f"Manual Accounting Balance: {accounting_balance}")
