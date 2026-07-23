pm = env['pos.payment.method'].search([])
for p in pm:
    print(f"PM: {p.name} - Type: {getattr(p, 'type', 'NO TYPE')} - Is Cash: {getattr(p, 'is_cash_count', False)}")
