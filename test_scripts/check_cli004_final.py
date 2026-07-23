import sys

partner = env['res.partner'].search([('name', 'ilike', 'CLI004')], limit=1)
print(f"Partner: {partner.name} - Outstanding Debt: {partner.outstanding_debt}")
