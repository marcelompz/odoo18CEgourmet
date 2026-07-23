# -*- coding: utf-8 -*-
from datetime import datetime

partner_model = env['res.partner']
product_model = env['product.product']
lead_model = env['crm.lead']
sale_model = env['sale.order']
purchase_model = env['purchase.order']
employee_model = env['hr.employee']
user_model = env['res.users']
group_model = env['res.groups']

# Eliminar productos antiguos de demo agrícola
old_product_names = [
    "Semilla de Soja Certificada Agri-Max (50 kg)",
    "Fertilizante NPK Granulado Yara (50 kg)",
    "Tractor Agrícola John Deere 5090E",
    "Servicio Técnico - Análisis de Suelos"
]
for name in old_product_names:
    p = product_model.search([('name', '=', name)])
    if p:
        try:
            p.unlink()
            print(f"🗑️ Producto agrícola eliminado: {name}")
        except Exception as e:
            print(f"⚠️ No se pudo eliminar producto {name}: {e}")

# Eliminar proveedor agrícola
env['res.partner'].search([('name', '=', 'Yara Paraguay S.A.')]).unlink()

print("🌱 Iniciando la creación de datos de demo de repuestos hidráulicos para Agripar...")

# ============================================================
# 0. CREAR EMPLEADOS Y USUARIOS VENDEDORES
# ============================================================
print("\n👥 Creando empleados y usuarios vendedores...")

# Buscar grupos de permisos de Ventas
sale_user_group = group_model.search([('name', '=', 'User')], limit=1)
if not sale_user_group:
    # Si no encuentra, buscar el grupo base de ventas
    sale_user_group = group_model.search([('name', 'ilike', 'ventas')], limit=1)

# Si no hay grupo, usar None (los usuarios se crearán sin permisos especiales)
if not sale_user_group:
    print("⚠️  No se encontró grupo de ventas, se creará sin permisos específicos")

# Crear vendedores
vendedores_data = [
    {
        'name': 'Carlos Benítez',
        'email': 'carlos.benitez@agripar.com.py',
        'login': 'carlos',
        'password': 'agripar123',
        'phone': '0981 234567',
        'job_title': 'Vendedor Senior - Línea Hidráulica',
    },
    {
        'name': 'María González',
        'email': 'maria.gonzalez@agripar.com.py',
        'login': 'maria',
        'password': 'agripar123',
        'phone': '0982 345678',
        'job_title': 'Vendedora - Línea Automotriz',
    },
    {
        'name': 'Jorge Martínez',
        'email': 'jorge.martinez@agripar.com.py',
        'login': 'jorge',
        'password': 'agripar123',
        'phone': '0983 456789',
        'job_title': 'Vendedor - Línea Agrícola',
    },
]

for vendedor_data in vendedores_data:
    # Crear partner primero
    partner = partner_model.search([('email', '=', vendedor_data['email'])], limit=1)
    if not partner:
        partner = partner_model.create({
            'name': vendedor_data['name'],
            'email': vendedor_data['email'],
            'phone': vendedor_data['phone'],
            'is_company': False,
        })
    
    # Crear empleado
    employee = employee_model.search([('name', '=', vendedor_data['name'])], limit=1)
    if not employee:
        employee = employee_model.create({
            'name': vendedor_data['name'],
            'work_phone': vendedor_data['phone'],
            'work_email': vendedor_data['email'],
            'job_id': False,
            'department_id': False,
            'parent_id': False,
            'coach_id': False,
        })
        print(f"✅ Empleado creado: {vendedor_data['name']} - {vendedor_data['job_title']}")
    else:
        print(f"ℹ️ Empleado ya existe: {vendedor_data['name']}")
    
    # Crear usuario de Odoo
    user = user_model.search([('login', '=', vendedor_data['login'])], limit=1)
    if not user:
        user = user_model.create({
            'name': vendedor_data['name'],
            'login': vendedor_data['login'],
            'email': vendedor_data['email'],
            'password': vendedor_data['password'],
            'partner_id': partner.id,
            'employee_ids': [(6, 0, [employee.id])],
        })
        print(f"✅ Usuario creado: {vendedor_data['login']} (password: {vendedor_data['password']})")
        print(f"   📧 Email: {vendedor_data['email']}")
        print(f"   👤 Empleado: {employee.name}")
    else:
        print(f"ℹ️ Usuario ya existe: {vendedor_data['login']}")

print("\n👥 Empleados y usuarios creados exitosamente")

# ============================================================
# 1. CREAR CONTACTOS (CLIENTE Y PROVEEDOR)
# ============================================================
cust = partner_model.search([('name', '=', 'Agripar - Estancia El Ombú')], limit=1)
if not cust:
    cust = partner_model.create({
        'name': 'Agripar - Estancia El Ombú',
        'vat': '80001122-3',
        'email': 'contacto@estancia-el-ombu.com',
        'phone': '0981 123456',
        'is_company': True,
        'street': 'Ruta 2, Km 120',
        'city': 'Coronel Oviedo',
        'l10n_latam_identification_type_id': 4,
    })
    print(f"✅ Cliente creado: {cust.name}")
else:
    print(f"ℹ️ Cliente ya existe: {cust.name}")

vend = partner_model.search([('name', '=', 'Parker Hannifin Paraguay S.A.')], limit=1)
if not vend:
    vend = partner_model.create({
        'name': 'Parker Hannifin Paraguay S.A.',
        'vat': '80003344-5',
        'email': 'ventas@parker.com.py',
        'phone': '021 555666',
        'is_company': True,
        'street': 'Av. Aviadores del Chaco 2050',
        'city': 'Asunción',
        'l10n_latam_identification_type_id': 4,
    })
    print(f"✅ Proveedor hidráulico creado: {vend.name}")
else:
    print(f"ℹ️ Proveedor hidráulico ya existe: {vend.name}")

# 2. Buscar Impuesto IVA 10%
tax_10 = env['account.tax'].search([('company_id', '=', env.company.id), ('type_tax_use', '=', 'sale'), ('amount', '=', 10.0)], limit=1)
tax_ids = [(6, 0, [tax_10.id])] if tax_10 else []

# 3. Crear Productos Hidráulicos
cilindro_name = "Cilindro Hidráulico Rexroth Doble Efecto"
valvula_name = "Válvula Control Direccional Monoblock 80L"
bomba_name = "Bomba Hidráulica Parker PGP511"
servicio_name = "Servicio Técnico - Reparación de Sistema Hidráulico"

def get_or_create_product(name, detailed_type, list_price, standard_price, tracking, is_storable=False):
    prod = product_model.search([('name', '=', name)], limit=1)
    if not prod:
        prod = product_model.create({
            'name': name,
            'type': detailed_type,
            'list_price': list_price,
            'standard_price': standard_price,
            'tracking': tracking,
            'taxes_id': tax_ids,
            'is_storable': is_storable,
        })
        print(f"✅ Producto hidráulico creado: {name}")
    else:
        print(f"ℹ️ Producto ya existe: {name}")
    return prod

cilindro = get_or_create_product(cilindro_name, "consu", 1800000.0, 1100000.0, "lot", is_storable=True)
valvula = get_or_create_product(valvula_name, "consu", 2500000.0, 1500000.0, "lot", is_storable=True)
bomba = get_or_create_product(bomba_name, "consu", 6500000.0, 4000000.0, "serial", is_storable=True)
servicio = get_or_create_product(servicio_name, "service", 1500000.0, 500000.0, "none", is_storable=False)

# 4. Obtener ubicación interna de stock
stock_loc = env['stock.location'].search([('usage', '=', 'internal'), ('name', '=', 'Stock')], limit=1)
if not stock_loc:
    stock_loc = env['stock.location'].search([('usage', '=', 'internal')], limit=1)

# 5. Agregar Stock Inicial con Trazabilidad (Lotes y Números de Serie)
def add_stock_lot(product, qty, lot_name=None):
    lot = False
    if lot_name and product.tracking in ('lot', 'serial'):
        lot = env['stock.lot'].search([('name', '=', lot_name), ('product_id', '=', product.id)], limit=1)
        if not lot:
            lot = env['stock.lot'].create({
                'name': lot_name,
                'product_id': product.id,
                'company_id': env.company.id,
            })
            
    domain = [('product_id', '=', product.id), ('location_id', '=', stock_loc.id)]
    if lot:
        domain.append(('lot_id', '=', lot.id))
    existing_quant = env['stock.quant'].search(domain, limit=1)
    if existing_quant and existing_quant.quantity > 0:
        print(f"ℹ️ Ya existe stock para {product.name} (Lote: {lot_name}): {existing_quant.quantity}")
        return
        
    quant_vals = {
        'product_id': product.id,
        'location_id': stock_loc.id,
        'inventory_quantity': qty,
    }
    if lot:
        quant_vals['lot_id'] = lot.id
        
    quant = env['stock.quant'].with_context(inventory_mode=True).create(quant_vals)
    quant.action_apply_inventory()
    print(f"✅ Agregado stock: {qty} un. de {product.name} (Lote/Serie: {lot_name})")

add_stock_lot(cilindro, 50, "LOTE-CILINDRO-2026-01")
add_stock_lot(valvula, 30, "LOTE-VALVULA-2026-03")
add_stock_lot(bomba, 1, "BOMBA-PGP511-SER01")
add_stock_lot(bomba, 1, "BOMBA-PGP511-SER02")

# 6. Crear CRM Opportunity
print("\n💼 Creando oportunidades CRM...")

# Buscar usuario Carlos para asignar la oportunidad
carlos_user = user_model.search([('login', '=', 'carlos')], limit=1)

# Obtener etapa del CRM
prop_stage = env['crm.stage'].search([('name', '=', 'Proposition')], limit=1)
if not prop_stage:
    prop_stage = env['crm.stage'].search([], limit=1)

lead_name = "Agripar Demo - Reparación de Maquinaria e Hidráulica"
lead = lead_model.search([('name', '=', lead_name)], limit=1)
if not lead:
    lead = lead_model.create({
        'name': lead_name,
        'partner_id': cust.id,
        'expected_revenue': 7600000.0,
        'stage_id': prop_stage.id,
        'type': 'opportunity',
        'probability': 70.0,
        'user_id': carlos_user.id if carlos_user else False,  # Asignar a Carlos
    })
    print(f"✅ Oportunidad CRM creada: {lead.name}")
    if carlos_user:
        print(f"   👤 Asignada a: {carlos_user.name}")
else:
    print(f"ℹ️ Oportunidad CRM ya existe: {lead.name}")

# Crear oportunidades adicionales para otros vendedores
oportunidades_adicionales = [
    {
        'name': 'Mantenimiento Sistema Hidráulico - Pulverizadora',
        'revenue': 4500000.0,
        'probability': 50.0,
        'vendedor': 'maria',
    },
    {
        'name': 'Venta de Repuestos - Cosechadora John Deere',
        'revenue': 8200000.0,
        'probability': 60.0,
        'vendedor': 'jorge',
    },
]

for opp_data in oportunidades_adicionales:
    vendedor_user = user_model.search([('login', '=', opp_data['vendedor'])], limit=1)
    opp_name = f"{opp_data['name']} - {cust.name}"
    
    existing_opp = lead_model.search([('name', '=', opp_name)], limit=1)
    if not existing_opp:
        opp = lead_model.create({
            'name': opp_name,
            'partner_id': cust.id,
            'expected_revenue': opp_data['revenue'],
            'stage_id': prop_stage.id,
            'type': 'opportunity',
            'probability': opp_data['probability'],
            'user_id': vendedor_user.id if vendedor_user else False,
        })
        print(f"✅ Oportunidad creada: {opp_name}")
        if vendedor_user:
            print(f"   👤 Asignada a: {vendedor_user.name}")
    else:
        print(f"ℹ️ Oportunidad ya existe: {opp_name}")

# 7. Crear y Confirmar Pedido de Venta (Sales Order)
existing_so = sale_model.search([('partner_id', '=', cust.id)], limit=1)
if not existing_so:
    so_vals = {
        'partner_id': cust.id,
        'order_line': [
            (0, 0, {
                'product_id': cilindro.id,
                'product_uom_qty': 2,
                'price_unit': 1800000.0,
            }),
            (0, 0, {
                'product_id': valvula.id,
                'product_uom_qty': 1,
                'price_unit': 2500000.0,
            }),
            (0, 0, {
                'product_id': servicio.id,
                'product_uom_qty': 1,
                'price_unit': 1500000.0,
            }),
        ]
    }
    so = sale_model.create(so_vals)
    print(f"✅ Pedido de Venta {so.name} creado en estado Borrador")
    
    # Confirmar pedido
    so.action_confirm()
    print(f"🚀 Pedido de Venta {so.name} CONFIRMADO. Esto generó automáticamente una orden de entrega (picking) en el Almacén.")
    
    # Generar factura borrador para mostrar contabilidad integrada
    invoice_ids = so._create_invoices()
    if invoice_ids:
        print(f"💼 Factura de Cliente borrador creada: {invoice_ids.name or 'Factura Borrador'}")
else:
    print(f"ℹ️ Pedido de Venta ya existe para este cliente: {existing_so.name}")

# 8. Crear un Pedido de Compra (Request for Quotation)
existing_po = purchase_model.search([('partner_id', '=', vend.id)], limit=1)
if not existing_po:
    po_vals = {
        'partner_id': vend.id,
        'order_line': [
            (0, 0, {
                'product_id': valvula.id,
                'product_qty': 10,
                'price_unit': 1500000.0,
                'date_planned': datetime.today(),
            }),
        ]
    }
    po = purchase_model.create(po_vals)
    print(f"✅ Solicitud de Presupuesto de Compra {po.name} creada para el proveedor {vend.name}")
else:
    print(f"ℹ️ Pedido de Compra ya existe para este proveedor: {existing_po.name}")

env.cr.commit()

# ============================================================
# RESUMEN FINAL
# ============================================================
print("\n" + "="*70)
print("📊 RESUMEN DE LA DEMO AGRIPAR")
print("="*70)

print("\n👥 EMPLEADOS Y USUARIOS:")
print("-" * 50)
usuarios_creados = [
    {'login': 'carlos', 'nombre': 'Carlos Benítez', 'rol': 'Vendedor Senior - Hidráulica'},
    {'login': 'maria', 'nombre': 'María González', 'rol': 'Vendedora - Automotriz'},
    {'login': 'jorge', 'nombre': 'Jorge Martínez', 'rol': 'Vendedor - Agrícola'},
]
for u in usuarios_creados:
    print(f"   • {u['nombre']} ({u['login']})")
    print(f"     Email: {u['login']}@agripar.com.py")
    print(f"     Rol: {u['rol']}")
    print(f"     Password: agripar123")
    print()

print("\n💼 OPORTUNIDADES CRM:")
print("-" * 50)
oportunidades = lead_model.search([('type', '=', 'opportunity')], limit=10)
for opp in oportunidades:
    vendedor_name = opp.user_id.name if opp.user_id else "Sin asignar"
    print(f"   • {opp.name}")
    print(f"     Cliente: {opp.partner_id.name}")
    print(f"     Vendedor: {vendedor_name}")
    print(f"     Etapa: {opp.stage_id.name}")
    print(f"     Revenue: ₲ {opp.expected_revenue:,.0f}")
    print(f"     Probabilidad: {opp.probability}%")
    print()

print("\n📦 DOCUMENTOS COMERCIALES:")
print("-" * 50)
ventas = sale_model.search([], order='id desc', limit=5)
for so in ventas:
    print(f"   • {so.name} - {so.partner_id.name}")
    print(f"     Estado: {so.state}")
    print(f"     Total: ₲ {so.amount_total:,.0f}")
    print()

compras = purchase_model.search([], order='id desc', limit=5)
for po in compras:
    print(f"   • {po.name} - {po.partner_id.name}")
    print(f"     Estado: {po.state}")
    print()

print("\n🎯 ACCESOS AL SISTEMA:")
print("-" * 50)
print("   URL: http://localhost:8084")
print()
print("   Admin:")
print("     Login: admin")
print("     Password: admin")
print()
print("   Vendedores:")
print("     Login: carlos / maria / jorge")
print("     Password: agripar123")
print()

print("="*70)
print("🎉 ¡Datos de demo para Agripar creados exitosamente!")
print("="*70)
