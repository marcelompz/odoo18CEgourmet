import sys

# Buscar la primera cuenta de tipo stock valuation o simplemente usar alguna de activos
valuation_account = env['account.account'].search([('account_type', '=', 'asset_inventory')], limit=1)
if not valuation_account:
    valuation_account = env['account.account'].search([('account_type', 'in', ['asset_current', 'asset_fixed'])], limit=1)

output_account = env['account.account'].search([('account_type', '=', 'expense_direct_cost')], limit=1)
if not output_account:
    output_account = env['account.account'].search([('account_type', '=', 'expense')], limit=1)

input_account = env['account.account'].search([('account_type', '=', 'liability_payable')], limit=1)
if not input_account:
    input_account = env['account.account'].search([('account_type', '=', 'liability_current')], limit=1)

print(f"Valuation: {valuation_account.name if valuation_account else 'NO'}")
print(f"Output: {output_account.name if output_account else 'NO'}")
print(f"Input: {input_account.name if input_account else 'NO'}")

categories = env['product.category'].search([])
for cat in categories:
    try:
        # Intentar setear las cuentas de stock si no las tiene
        if hasattr(cat, 'property_stock_valuation_account_id') and not cat.property_stock_valuation_account_id:
            cat.property_stock_valuation_account_id = valuation_account
            print(f"✅ Valuation set for {cat.name}")
        
        if hasattr(cat, 'property_stock_account_output_categ_id') and not cat.property_stock_account_output_categ_id:
            cat.property_stock_account_output_categ_id = output_account
            print(f"✅ Output set for {cat.name}")
            
        if hasattr(cat, 'property_stock_account_input_categ_id') and not cat.property_stock_account_input_categ_id:
            cat.property_stock_account_input_categ_id = input_account
            print(f"✅ Input set for {cat.name}")
    except Exception as e:
        print(f"Error on cat {cat.name}: {e}")

env.cr.commit()
print("Terminado.")
