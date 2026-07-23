import sys

income_account = env['account.account'].search([('account_type', '=', 'income')], limit=1)
expense_account = env['account.account'].search([('account_type', '=', 'expense')], limit=1)

if not income_account:
    print("❌ No se encontró cuenta de ingresos en la BD")
if not expense_account:
    print("❌ No se encontró cuenta de gastos en la BD")

if income_account and expense_account:
    categories = env['product.category'].search([])
    for cat in categories:
        if not cat.property_account_income_categ_id:
            cat.property_account_income_categ_id = income_account
            print(f"✅ Cuenta de ingresos asignada a categoría '{cat.name}'")
        if not cat.property_account_expense_categ_id:
            cat.property_account_expense_categ_id = expense_account
            print(f"✅ Cuenta de gastos asignada a categoría '{cat.name}'")

    products = env['product.product'].search([])
    for prod in products:
        if not prod.property_account_income_id and not prod.categ_id.property_account_income_categ_id:
            prod.property_account_income_id = income_account
            print(f"✅ Cuenta de ingresos asignada a producto '{prod.name}'")
        if not prod.property_account_expense_id and not prod.categ_id.property_account_expense_categ_id:
            prod.property_account_expense_id = expense_account
            print(f"✅ Cuenta de gastos asignada a producto '{prod.name}'")

env.cr.commit()
print("Operación completada.")
