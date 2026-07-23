import sys

company = env['res.company'].search([('name', 'ilike', 'Provecchio')], limit=1)
if not company:
    print("Company not found")
    sys.exit(0)

print(f"Company: {company.name}")
product = env['product.product'].with_company(company).search([('name', 'ilike', 'Abono de Cuenta')], limit=1)
if not product:
    print("Product 'Abono de Cuenta' not found")
    sys.exit(0)

print(f"Product: {product.name} (ID: {product.id})")
print(f"  Income Account (Product): {product.property_account_income_id.name if product.property_account_income_id else 'False'}")
print(f"  Expense Account (Product): {product.property_account_expense_id.name if product.property_account_expense_id else 'False'}")

cat = product.categ_id
if cat:
    print(f"Category: {cat.name} (ID: {cat.id})")
    print(f"  Income Account (Category): {cat.property_account_income_categ_id.name if cat.property_account_income_categ_id else 'False'}")
    print(f"  Expense Account (Category): {cat.property_account_expense_categ_id.name if cat.property_account_expense_categ_id else 'False'}")
else:
    print("No category assigned")

