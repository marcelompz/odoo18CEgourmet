import sys

categories = env['product.category'].search([])
for cat in categories:
    print(f"Cat: {cat.name}")
    print(f"  Valuation: {cat.property_stock_valuation_account_id.name if cat.property_stock_valuation_account_id else 'False'}")
    print(f"  Variation: {cat.account_stock_variation_id.name if cat.account_stock_variation_id else 'False'}")
    print(f"  Journal: {cat.property_stock_journal.name if cat.property_stock_journal else 'False'}")
