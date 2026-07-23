import sys

partners = env['res.partner'].search([])
for p in partners:
    if p.outstanding_debt != 0:
        print(f"Partner: {p.name} - Debt: {p.outstanding_debt}")
