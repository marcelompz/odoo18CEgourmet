orders = env['pos.order'].search([('name', 'in', ['000029', '000031'])])
orders.write({'partner_id': False})

moves = env['account.move'].search([('name', 'in', ['POSS/2026/06/0001', 'POSS/2026/06/0002'])])
for m in moves:
    m.button_draft()
    m.write({'partner_id': False})
    for l in m.line_ids:
        l.write({'partner_id': False})
    m.action_post()
env.cr.commit()
print("Removed partner from fake data!")
