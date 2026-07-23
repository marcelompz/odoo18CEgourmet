import sys

session = env['pos.session'].search([('state', '=', 'closed')], order='id desc', limit=1)
if session and session.move_id:
    print(f"Session {session.name} - Move: {session.move_id.name}")
    for line in session.move_id.line_ids:
        print(f"  Line Account: {line.account_id.name} - Partner: {line.partner_id.name} - Debit: {line.debit} - Credit: {line.credit}")
else:
    print("No move found for last closed session.")
