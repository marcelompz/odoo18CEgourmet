import sys

products = env['product.product'].search([('name', 'in', ['EJEMPLO 2', 'RECETA_EJEMPLO'])])
print("=== CHECKING STOCK VALUATION ACCOUNTS ===")
for p in products:
    cat = p.categ_id
    print(f"Product: {p.name} | Type: {p.type} | Category: {cat.name}")
    print(f"  Valuation: {cat.property_valuation}")
    
    input_acc = cat.property_stock_account_input_categ_id
    output_acc = cat.property_stock_account_output_categ_id
    valuation_acc = cat.property_stock_valuation_account_id
    
    print(f"  Input Account: {input_acc.name if input_acc else 'MISSING'}")
    print(f"  Output Account: {output_acc.name if output_acc else 'MISSING'}")
    print(f"  Valuation Account: {valuation_acc.name if valuation_acc else 'MISSING'}")

    # Also check if product has explicit accounts
    p_input = p.property_stock_account_input
    p_output = p.property_stock_account_output
    print(f"  Product Explicit Input: {p_input.name if p_input else 'NO'}")
    print(f"  Product Explicit Output: {p_output.name if p_output else 'NO'}")
