import sys

sessions = env['pos.session'].search([('state', '!=', 'closed')])
for s in sessions:
    print(f"Session: {s.name} - State: {s.state}")
