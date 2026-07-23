# -*- coding: utf-8 -*-

partner_model = env['res.partner']

# Buscar los tipos de identificación de la localización LATAM
ruc_type = env['l10n_latam.identification.type'].search([('name', '=', 'R.U.C.')], limit=1).id
ci_type = env['l10n_latam.identification.type'].search([('name', '=', 'C.I.')], limit=1).id
innominado_type = env['l10n_latam.identification.type'].search([('name', '=', 'Innominado')], limit=1).id

customers_data = [
    {
        'name': 'Clientes Varios',
        'vat': '44444401-7',
        'l10n_latam_identification_type_id': innominado_type,
        'email': 'clientesvarios@agripar.com.py',
        'phone': '',
        'is_company': False,
        'street': 'Sin Dirección',
        'city': 'Asunción',
    },
    {
        'name': 'Estancia La Patria',
        'vat': '80012399-1',
        'l10n_latam_identification_type_id': ruc_type,
        'email': 'administracion@lapatria.com.py',
        'phone': '0981 999111',
        'is_company': True,
        'street': 'Ruta Transchaco, Km 450',
        'city': 'Mariscal Estigarribia',
    },
    {
        'name': 'Agroganadera Chaco Central',
        'vat': '80098765-4',
        'l10n_latam_identification_type_id': ruc_type,
        'email': 'info@chacocentral.com.py',
        'phone': '0983 222333',
        'is_company': True,
        'street': 'Calle Principal',
        'city': 'Filadelfia',
    },
    {
        'name': 'Cooperativa Fernheim',
        'vat': '80002244-1',
        'l10n_latam_identification_type_id': ruc_type,
        'email': 'fernheim@fernheim.com.py',
        'phone': '0491 432100',
        'is_company': True,
        'street': 'Av. Hindenburg',
        'city': 'Filadelfia',
    },
    {
        'name': 'Estancia Santa María',
        'vat': '80033445-9',
        'l10n_latam_identification_type_id': ruc_type,
        'email': 'santamaria@santamaria.com.py',
        'phone': '0971 444555',
        'is_company': True,
        'street': 'Ruta 7, Km 180',
        'city': 'Caaguazú',
    },
    {
        'name': 'Agropecuaria San Isidro',
        'vat': '80055667-2',
        'l10n_latam_identification_type_id': ruc_type,
        'email': 'contacto@sanisidro.com.py',
        'phone': '0985 777888',
        'is_company': True,
        'street': 'Av. de los Colonos',
        'city': 'Bella Vista',
    },
    {
        'name': 'Ing. Carlos Bogado (Asesor Agrícola)',
        'vat': '1234567-8',
        'l10n_latam_identification_type_id': ci_type,
        'email': 'carlos.bogado@gmail.com',
        'phone': '0961 888999',
        'is_company': False,
        'street': 'Calle 14 de Mayo',
        'city': 'Santa Rita',
    }
]

print("👤 Creando/Actualizando lista de clientes varios y agrícolas...")

for c_data in customers_data:
    existing = partner_model.search([('name', '=', c_data['name'])], limit=1)
    if not existing:
        partner = partner_model.create(c_data)
        print(f"✅ Cliente creado: {partner.name} (RUC/Doc: {partner.vat})")
    else:
        existing.write(c_data)
        print(f"ℹ️ Cliente actualizado: {existing.name} (RUC/Doc: {existing.vat})")

env.cr.commit()
print("🎉 ¡Carga de clientes completada exitosamente!")
