import sys

print("=== CHECKING OPEN SESSIONS ===")
sessions = env['pos.session'].search([('state', '!=', 'closed')])

for session in sessions:
    print(f"\n--- Sesion: {session.name} ---")
    for order in session.order_ids:
        for line in order.lines:
            product = line.product_id
            
            income_acc = product.property_account_income_id or product.categ_id.property_account_income_categ_id
            expense_acc = product.property_account_expense_id or product.categ_id.property_account_expense_categ_id
            
            print(f"[{order.name}] Producto: '{product.name}' (ID: {product.id})")
            print(f"    - Ingresos: {income_acc.name if income_acc else 'MISSING'}")
            print(f"    - Gastos:   {expense_acc.name if expense_acc else 'MISSING'}")
            
    print(f"\n--- Pagos de la Sesion ---")
    for payment in session.order_ids.mapped('payment_ids'):
        method = payment.payment_method_id
        # In Odoo 16/17/18/19 POS payment methods have outstanding accounts
        receivable = method.receivable_account_id
        outstanding = method.outstanding_account_id
        print(f"Pago: {payment.amount} | Metodo: {method.name}")
        print(f"    - Receivable: {receivable.name if receivable else 'MISSING (Usa el de la compania)'}")
        print(f"    - Outstanding: {outstanding.name if outstanding else 'MISSING (Usa el de la compania)'}")

print("\n=== CHECKING COMPANY DEFAULT ACCOUNTS ===")
company = env.company
print(f"Company: {company.name}")
print(f"Default POS Receivable Account: {company.account_default_pos_receivable_account_id.name if hasattr(company, 'account_default_pos_receivable_account_id') and company.account_default_pos_receivable_account_id else 'MISSING'}")
print(f"Company default Outstanding Receipts: {company.account_journal_payment_debit_account_id.name if hasattr(company, 'account_journal_payment_debit_account_id') and company.account_journal_payment_debit_account_id else 'MISSING'}")

