import sys

valuation_account = env['account.account'].search([('account_type', '=', 'asset_inventory')], limit=1)
if not valuation_account:
    valuation_account = env['account.account'].search([('account_type', 'in', ['asset_current', 'asset_fixed'])], limit=1)

variation_account = env['account.account'].search([('account_type', '=', 'expense_direct_cost')], limit=1)
if not variation_account:
    variation_account = env['account.account'].search([('account_type', '=', 'expense')], limit=1)

categories = env['product.category'].search([])
for cat in categories:
    print(f"Configurando categoria: {cat.name}")
    if hasattr(cat, 'property_stock_valuation_account_id') and not cat.property_stock_valuation_account_id:
        cat.property_stock_valuation_account_id = valuation_account
        print(f"  -> property_stock_valuation_account_id = {valuation_account.name}")
        
    if hasattr(cat, 'account_stock_variation_id') and not cat.account_stock_variation_id:
        cat.account_stock_variation_id = variation_account
        print(f"  -> account_stock_variation_id = {variation_account.name}")

    if hasattr(cat, 'property_stock_journal') and not cat.property_stock_journal:
        journal = env['account.journal'].search([('type', '=', 'general')], limit=1)
        cat.property_stock_journal = journal
        print(f"  -> property_stock_journal = {journal.name}")

env.cr.commit()
print("Terminado.")
