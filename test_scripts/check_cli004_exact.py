import sys

partner = env['res.partner'].search([('name', '=', 'CLI004')], limit=1)
if partner:
    print(f"Partner: {partner.name}")
    print(f"Outstanding debt (orm): {partner.outstanding_debt}")
    print(f"Accounting Balance: {(partner.debit or 0.0) - (partner.credit or 0.0)}")
