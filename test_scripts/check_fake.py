orders = env['pos.order'].search([('name', 'in', ['000029', '000031'])])
moves = env['account.move'].search([('name', 'in', ['POSS/2026/06/0001', 'POSS/2026/06/0002'])])
print(f"Orders: {len(orders)} | Moves: {len(moves)}")
