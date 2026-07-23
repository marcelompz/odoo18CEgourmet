import sys

companies = env['res.company'].search([])
for c in companies:
    print(f"Compania: {c.name} (ID: {c.id})")
    
    # Try finding an account for this company explicitly
    acc = env['account.account'].sudo().search([('account_type', '=', 'asset_receivable'), ('company_ids', 'in', c.id)], limit=1)
    if acc:
        print(f"  - Cuenta Encontrada: {acc.name}")
        c.account_default_pos_receivable_account_id = acc
        
    # Omitimos actualizar los payment methods porque causa error si hay sesiones abiertas
    pass

env.cr.commit()
print("FINALIZADO")
