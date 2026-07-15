import base64
import csv
import io
from odoo import api, fields, models

class ExportPOReceiptWizard(models.TransientModel):
    _name = 'export.po.receipt.wizard'
    _description = 'Export Purchase Receipts Data'

    file_data = fields.Binary('Archivo Exportado', readonly=True)
    file_name = fields.Char('Nombre de Archivo', readonly=True)

    def action_export(self):
        po_ids = self.env.context.get('active_ids', [])
        purchases = self.env['purchase.order'].browse(po_ids)
        
        output = io.StringIO()
        writer = csv.writer(output, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        
        # Header
        writer.writerow([
            'Pedido de Compra',
            'Proveedor',
            'Recepción',
            'Producto',
            'Referencia Interna',
            'Código de Barras',
            'Lote/Nro. Serie',
            'Fecha de Caducidad',
            'Cantidad Recibida',
            'Precio de Compra',
        ])
        
        for po in purchases:
            for picking in po.picking_ids:
                if picking.state == 'cancel':
                    continue
                for line in picking.move_line_ids:
                    product = line.product_id
                    lot = line.lot_id
                    
                    purchase_price = 0.0
                    if line.move_id and getattr(line.move_id, 'purchase_line_id', False):
                        purchase_price = line.move_id.purchase_line_id.price_unit
                    elif line.move_id and line.move_id.price_unit:
                        purchase_price = line.move_id.price_unit
                    else:
                        purchase_price = product.standard_price

                    expiration_date = ''
                    if lot:
                        if hasattr(lot, 'expiration_date') and lot.expiration_date:
                            expiration_date = str(lot.expiration_date)
                        elif hasattr(lot, 'use_date') and lot.use_date:
                            expiration_date = str(lot.use_date)

                    lot_name = lot.name if lot else (line.lot_name or '')
                    qty = getattr(line, 'quantity', getattr(line, 'qty_done', 0.0))

                    writer.writerow([
                        po.name or '',
                        po.partner_id.name or '',
                        picking.name or '',
                        product.name or '',
                        product.default_code or '',
                        product.barcode or '',
                        lot_name,
                        expiration_date,
                        str(qty),
                        str(purchase_price),
                    ])
        
        output.seek(0)
        file_data = base64.b64encode(output.read().encode('utf-8'))
        
        self.write({
            'file_data': file_data,
            'file_name': 'recepciones_compras_exportadas.csv'
        })
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'export.po.receipt.wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }
