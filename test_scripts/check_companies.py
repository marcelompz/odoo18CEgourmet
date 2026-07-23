import sys

print("=== COMPANIES ===")
for c in env['res.company'].search([]):
    print(f"Company: {c.id} - {c.name}")

session = env['pos.session'].search([('state', '!=', 'closed')], limit=1)
if session:
    print(f"\n=== POS SESSION ===")
    print(f"Session Company: {session.company_id.id} - {session.company_id.name}")

print("\n=== STOCK ACCOUNTS IN CATEGORIES FOR SESSION COMPANY ===")
for cat in env['product.category'].with_company(session.company_id).search([]):
    val = cat.property_stock_valuation_account_id
    print(f"Cat {cat.name}: Valuation={val.id if val else 'False'} ({val.name if val else ''})")
