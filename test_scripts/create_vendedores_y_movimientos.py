# -*- coding: utf-8 -*-
from datetime import datetime, timedelta

partner_model = env['res.partner']
user_model = env['res.users']
lead_model = env['crm.lead']
sale_model = env['sale.order']
calendar_model = env['calendar.event']

print("🚀 Iniciando la creación de vendedores, supervisor y movimientos del CRM...")

# 1. Configurar mi propio usuario como Supervisor de Ventas
supervisor_user = user_model.browse(2) # soporte@crossnexion.com (Admin)
supervisor_user.write({
    'name': 'Marcelo MPZ (Supervisor de Ventas)',
})
print(f"👤 Usuario ID 2 actualizado a: {supervisor_user.name}")

# 2. Crear Vendedores
group_salesman = env.ref('sales_team.group_sale_salesman')
group_internal = env.ref('base.group_user')

# Obtener ID del tipo de identificación
it_type = env.ref('l10n_py.it_vat', raise_if_not_found=False)
it_type_id = it_type.id if it_type else 4

user_juan = user_model.search([('login', '=', 'juan@agripar.com.py')], limit=1)
if not user_juan:
    user_juan = user_model.create({
        'name': 'Juan Villalba',
        'login': 'juan@agripar.com.py',
        'email': 'juan@agripar.com.py',
        'password': 'vendedor.123',
        'group_ids': [(6, 0, [group_salesman.id, group_internal.id])],
        'l10n_latam_identification_type_id': it_type_id,
    })
    print(f"✅ Vendedor creado: {user_juan.name}")
else:
    print(f"ℹ️ Vendedor ya existe: {user_juan.name}")

user_sofia = user_model.search([('login', '=', 'sofia@agripar.com.py')], limit=1)
if not user_sofia:
    user_sofia = user_model.create({
        'name': 'Sofía Gómez',
        'login': 'sofia@agripar.com.py',
        'email': 'sofia@agripar.com.py',
        'password': 'vendedor.123',
        'group_ids': [(6, 0, [group_salesman.id, group_internal.id])],
        'l10n_latam_identification_type_id': it_type_id,
    })
    print(f"✅ Vendedora creada: {user_sofia.name}")
else:
    print(f"ℹ️ Vendedora ya existe: {user_sofia.name}")

# 3. Configurar Equipo de Ventas
team = env['crm.team'].search([('name', '=', 'Ventas Agripar')], limit=1)
if not team:
    team = env['crm.team'].create({
        'name': 'Ventas Agripar',
        'user_id': supervisor_user.id,
    })
    print(f"✅ Equipo de Ventas '{team.name}' creado con Supervisor: {supervisor_user.name}")
else:
    team.write({'user_id': supervisor_user.id})
    print(f"ℹ️ Equipo de Ventas '{team.name}' actualizado.")

team_member_model = env['crm.team.member']
for u in [user_juan, user_sofia]:
    existing_member = team_member_model.search([('crm_team_id', '=', team.id), ('user_id', '=', u.id)], limit=1)
    if not existing_member:
        team_member_model.create({
            'crm_team_id': team.id,
            'user_id': u.id,
        })
        print(f"➕ Añadido {u.name} al equipo {team.name}")

# 4. Obtener productos y clientes para las ventas del CRM
cilindro = env['product.product'].search([('name', '=', 'Cilindro Hidráulico Rexroth Doble Efecto')], limit=1)
valvula = env['product.product'].search([('name', '=', 'Válvula Control Direccional Monoblock 80L')], limit=1)
bomba = env['product.product'].search([('name', '=', 'Bomba Hidráulica Parker PGP511')], limit=1)
servicio = env['product.product'].search([('name', '=', 'Servicio Técnico - Reparación de Sistema Hidráulico')], limit=1)

fernheim = partner_model.search([('name', '=', 'Cooperativa Fernheim')], limit=1)
chaco_central = partner_model.search([('name', '=', 'Agroganadera Chaco Central')], limit=1)
patria = partner_model.search([('name', '=', 'Estancia La Patria')], limit=1)

# Etapas CRM
prop_stage = env['crm.stage'].search([('name', '=', 'Proposition')], limit=1) or env['crm.stage'].search([], limit=1)
won_stage = env['crm.stage'].search([('name', '=', 'Won')], limit=1) or env['crm.stage'].search([], limit=1)
qual_stage = env['crm.stage'].search([('name', '=', 'Qualified')], limit=1) or env['crm.stage'].search([], limit=1)

# --- MOVIMIENTO 1: JUAN VILLALBA ---
# Oportunidad CRM
lead1_name = "Fernheim - Válvulas y Cilindros Hidráulicos"
lead1 = lead_model.search([('name', '=', lead1_name)], limit=1)
if not lead1:
    lead1 = lead_model.create({
        'name': lead1_name,
        'partner_id': fernheim.id,
        'user_id': user_juan.id,
        'team_id': team.id,
        'expected_revenue': 25000000.0,
        'stage_id': prop_stage.id,
        'type': 'opportunity',
        'probability': 80.0,
    })
    print(f"✅ Oportunidad CRM creada: {lead1.name} (Vendedor: {user_juan.name})")
    
    # Crear presupuesto asociado y APROBARLO (confirmarlo)
    so1 = sale_model.create({
        'partner_id': fernheim.id,
        'user_id': user_juan.id,
        'team_id': team.id,
        'opportunity_id': lead1.id,
        'order_line': [
            (0, 0, {
                'product_id': valvula.id,
                'product_uom_qty': 10,
                'price_unit': 2500000.0,
            })
        ]
    })
    so1.action_confirm()
    print(f"   -> Presupuesto aprobado y venta confirmada {so1.name} por {so1.amount_total} Gs")

    # Reuniones y Notas de Seguimiento
    reunion1 = calendar_model.create({
        'name': 'Reunión de Cierre - Cooperativa Fernheim',
        'start': datetime.now() - timedelta(days=1),
        'stop': datetime.now() - timedelta(days=1) + timedelta(hours=1.5),
        'user_id': user_juan.id,
        'partner_ids': [(6, 0, [user_juan.partner_id.id, fernheim.id, supervisor_user.partner_id.id])],
        'description': 'Reunión con gerente de compras para acordar volumen y descuentos de válvulas y componentes hidráulicos.',
    })
    print(f"   -> Reunión creada: {reunion1.name}")

    # Escribir notas en el chatter de la oportunidad crm
    lead1.message_post(body="""
        <b>Seguimiento de Reunión (Juan Villalba):</b><br/>
        - Se conversó con el Ing. Hein (Gerente de Compras) de Cooperativa Fernheim.<br/>
        - Solicitaron un lote de válvulas de control direccional Eaton/Monoblock.<br/>
        - Se acordó la venta de 10 válvulas con despacho para la próxima semana.<br/>
        - <b>Venta Confirmada bajo pedido aprobado.</b>
    """)
    print("   -> Nota de seguimiento agregada al chatter.")

# --- MOVIMIENTO 2: SOFIA GOMEZ (VENTA GANADA) ---
lead2_name = "Chaco Central - Equipamiento de Bombas Parker"
lead2 = lead_model.search([('name', '=', lead2_name)], limit=1)
if not lead2:
    lead2 = lead_model.create({
        'name': lead2_name,
        'partner_id': chaco_central.id,
        'user_id': user_sofia.id,
        'team_id': team.id,
        'expected_revenue': 32500000.0,
        'stage_id': won_stage.id,
        'type': 'opportunity',
        'probability': 100.0,
    })
    print(f"✅ Oportunidad CRM creada: {lead2.name} (Vendedora: {user_sofia.name})")

    # Crear presupuesto y CONFIRMARLO
    so2 = sale_model.create({
        'partner_id': chaco_central.id,
        'user_id': user_sofia.id,
        'team_id': team.id,
        'opportunity_id': lead2.id,
        'order_line': [
            (0, 0, {
                'product_id': bomba.id,
                'product_uom_qty': 5,
                'price_unit': 6500000.0,
            })
        ]
    })
    so2.action_confirm()
    print(f"   -> Presupuesto aprobado y venta confirmada {so2.name} por {so2.amount_total} Gs")

    # Registrar reunión
    reunion2 = calendar_model.create({
        'name': 'Visita Técnica e Inspección de Bomba Parker',
        'start': datetime.now() - timedelta(days=2),
        'stop': datetime.now() - timedelta(days=2) + timedelta(hours=2),
        'user_id': user_sofia.id,
        'partner_ids': [(6, 0, [user_sofia.partner_id.id, chaco_central.id])],
        'description': 'Visita en campo para la entrega técnica y firma de conformidad de la compra de las bombas de engranajes Parker.',
    })
    print(f"   -> Reunión creada: {reunion2.name}")

    lead2.message_post(body="""
        <b>Entrega Técnica (Sofía Gómez):</b><br/>
        - Se realizó la visita en la sucursal de Loma Plata de Agroganadera Chaco Central.<br/>
        - Las bombas hidráulicas fueron probadas y entregadas a satisfacción del encargado.<br/>
        - Se firmaron los documentos de entrega física y conformidad de la instalación.<br/>
        - <b>Bombas asignadas con Serie: Parker-PGP511-SER01/02. Oportunidad Ganada!</b>
    """)
    print("   -> Nota de entrega y conformidad agregada al chatter.")

# --- MOVIMIENTO 3: SOFIA GOMEZ (PRESUPUESTO EN PROCESO) ---
lead3_name = "Estancia La Patria - Cilindros y Servicio Hidráulico"
lead3 = lead_model.search([('name', '=', lead3_name)], limit=1)
if not lead3:
    lead3 = lead_model.create({
        'name': lead3_name,
        'partner_id': patria.id,
        'user_id': user_sofia.id,
        'team_id': team.id,
        'expected_revenue': 8700000.0,
        'stage_id': qual_stage.id,
        'type': 'opportunity',
        'probability': 30.0,
    })
    print(f"✅ Oportunidad CRM creada: {lead3.name} (Vendedora: {user_sofia.name})")

    # Crear presupuesto en borrador (Draft / Quoted)
    so3 = sale_model.create({
        'partner_id': patria.id,
        'user_id': user_sofia.id,
        'team_id': team.id,
        'opportunity_id': lead3.id,
        'order_line': [
            (0, 0, {
                'product_id': cilindro.id,
                'product_uom_qty': 4,
                'price_unit': 1800000.0,
            }),
            (0, 0, {
                'product_id': servicio.id,
                'product_uom_qty': 1,
                'price_unit': 1500000.0,
            })
        ]
    })
    print(f"   -> Presupuesto Borrador {so3.name} creado por {so3.amount_total} Gs")

    # Programar llamada / reunión futura
    reunion3 = calendar_model.create({
        'name': 'Seguimiento de Cotización de Cilindros y Reparación - Patria',
        'start': datetime.now() + timedelta(days=2),
        'stop': datetime.now() + timedelta(days=2) + timedelta(minutes=30),
        'user_id': user_sofia.id,
        'partner_ids': [(6, 0, [user_sofia.partner_id.id, patria.id])],
        'description': 'Llamada telefónica para dar seguimiento al presupuesto enviado por cilindros hidráulicos y servicio técnico.',
    })
    print(f"   -> Llamada de seguimiento programada: {reunion3.name}")

    lead3.message_post(body="""
        <b>Contacto Telefónico Inicial (Sofía Gómez):</b><br/>
        - El Ing. Martínez está evaluando la cotización de los cilindros hidráulicos Rexroth y el servicio de reparación.<br/>
        - Comparará los precios con otros proveedores hidráulicos.<br/>
        - Agendada llamada de seguimiento para el inicio de la próxima semana.
    """)
    print("   -> Nota inicial agregada al chatter.")

env.cr.commit()
print("🎉 ¡Carga de vendedores, equipo, supervisor y movimientos CRM completada exitosamente!")
