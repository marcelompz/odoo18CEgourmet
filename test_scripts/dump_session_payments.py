import sys

# Get the most recently opened POS session
session = env['pos.session'].search([], order='id desc', limit=1)
if session:
    print(f"Session: {session.name} - State: {session.state}")
    print(f"Cash Register Balance Start: {session.cash_register_balance_start}")
    
    payments = env['pos.payment'].search([('session_id', '=', session.id)])
    total_cash = 0
    print("Payments in this session:")
    for p in payments:
        print(f"  Order {p.pos_order_id.name} - Method: {p.payment_method_id.name} - Amount: {p.amount} - Change: {p.is_change}")
        if p.payment_method_id.type == 'cash':
            total_cash += p.amount
            
    print(f"Total Cash Payments: {total_cash}")
else:
    print("No session found.")
