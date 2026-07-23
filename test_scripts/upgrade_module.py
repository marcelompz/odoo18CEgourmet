env['ir.module.module'].search([('name', '=', 'pos_customer_balance_ce')]).button_immediate_upgrade()
env.cr.commit()
print("Module upgraded successfully via shell!")
