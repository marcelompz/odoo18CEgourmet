orders = env['pos.order'].search([('name', 'in', ['000029', '000031'])])
for o in orders:
    o.action_pos_order_cancel()
    o.unlink()
moves = env['account.move'].search([('name', 'in', ['POSS/2026/06/0001', 'POSS/2026/06/0002'])])
for m in moves:
    m.button_draft()
    m.unlink()
env.cr.commit()
print("Fake orders and moves deleted!")
