import csv

picking_name = "ALMAC/IN/00060"
picking = env['stock.picking'].search([('name', '=', picking_name)])
if not picking:
    print("Receipt " + picking_name + " not found")
else:
    data = []
    # Header
    data.append([
        'Producto',
        'Referencia',
        'Código de Barra',
        'Lote',
        'Fecha de Caducidad',
        'Cantidad',
        'Precio de Compra'
    ])
    for line in picking.move_line_ids:
        product_name = line.product_id.name
        default_code = line.product_id.default_code or ''
        barcode = line.product_id.barcode or ''
        lot_name = line.lot_id.name if line.lot_id else (line.lot_name or '')
        expiration_date = ''
        if line.lot_id:
            # Check if expiration_date exists
            if hasattr(line.lot_id, 'expiration_date') and line.lot_id.expiration_date:
                expiration_date = str(line.lot_id.expiration_date)
            elif hasattr(line.lot_id, 'use_date') and line.lot_id.use_date:
                expiration_date = str(line.lot_id.use_date)
            # In Odoo 18 sometimes they use 'lot_id.expiration_date'
        
        # In Odoo 18, qty_done might be 'qty_done' or 'quantity'
        qty = getattr(line, 'quantity', getattr(line, 'qty_done', 0.0))
        
        # Precio de compra (costo en el movimiento o costo del producto)
        purchase_price = 0.0
        if line.move_id and line.move_id.price_unit:
            purchase_price = line.move_id.price_unit
        else:
            purchase_price = line.product_id.standard_price

        data.append([
            product_name,
            default_code,
            barcode,
            lot_name,
            expiration_date,
            str(qty),
            str(purchase_price)
        ])
    
    csv_path = '/tmp/exported_ALMAC_IN_00060.csv'
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(data)
    
    print("Exported data to: " + csv_path)

env.cr.commit()
