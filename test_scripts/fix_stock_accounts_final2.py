import sys

companies = env['res.company'].search([])

for company in companies:
    print(f"\n=== CONFIGURANDO COMPAÑÍA: {company.name} (ID: {company.id}) ===")
    
    # In Odoo 19, account.account uses company_ids
    valuation_account = env['account.account'].with_company(company).search([('company_ids', 'in', company.id), ('account_type', '=', 'asset_inventory')], limit=1)
    if not valuation_account:
        valuation_account = env['account.account'].with_company(company).search([('company_ids', 'in', company.id), ('account_type', 'in', ['asset_current', 'asset_fixed'])], limit=1)

    variation_account = env['account.account'].with_company(company).search([('company_ids', 'in', company.id), ('account_type', '=', 'expense_direct_cost')], limit=1)
    if not variation_account:
        variation_account = env['account.account'].with_company(company).search([('company_ids', 'in', company.id), ('account_type', '=', 'expense')], limit=1)

    journal = env['account.journal'].with_company(company).search([('company_id', '=', company.id), ('type', '=', 'general')], limit=1)

    if not valuation_account or not variation_account or not journal:
        print(f"Saltando compañía {company.name} porque faltan cuentas o diarios.")
        continue

    categories = env['product.category'].with_company(company).search([])
    for cat in categories:
        if hasattr(cat, 'property_stock_valuation_account_id') and not cat.property_stock_valuation_account_id:
            cat.property_stock_valuation_account_id = valuation_account
            print(f"  [{cat.name}] property_stock_valuation_account_id = {valuation_account.name}")
            
        if hasattr(cat, 'account_stock_variation_id') and not cat.account_stock_variation_id:
            cat.account_stock_variation_id = variation_account
            print(f"  [{cat.name}] account_stock_variation_id = {variation_account.name}")

        if hasattr(cat, 'property_stock_journal') and not cat.property_stock_journal:
            cat.property_stock_journal = journal
            print(f"  [{cat.name}] property_stock_journal = {journal.name}")

env.cr.commit()
print("Terminado.")
