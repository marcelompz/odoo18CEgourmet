partner = env['res.partner'].search([('name', 'ilike', 'Marcelo Pesallaccia')], limit=1)
# Simulate the exact ORM read done by the UI
result = partner.with_context(company_id=env.company.id).read(['outstanding_debt'])
print(f"ORM Read Result: {result}")
