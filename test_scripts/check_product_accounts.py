import sys

products = env['product.product'].search([('name', 'in', ['EJEMPLO 2', 'RECETA_EJEMPLO', 'Abono de Cuenta'])])
for p in products:
    accounts = p.with_company(env.company)._get_product_accounts()
    print(f"Product: {p.name}")
    print(f"  Income: {accounts.get('income').name if accounts.get('income') else 'False'}")
    print(f"  Expense: {accounts.get('expense').name if accounts.get('expense') else 'False'}")
    print(f"  Stock Valuation: {accounts.get('stock_valuation').name if accounts.get('stock_valuation') else 'False'}")
    print(f"  Stock Input: {accounts.get('stock_input').name if accounts.get('stock_input') else 'False'}")
    print(f"  Stock Output: {accounts.get('stock_output').name if accounts.get('stock_output') else 'False'}")
    
