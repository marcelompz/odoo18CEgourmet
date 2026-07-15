# -*- coding: utf-8 -*-
"""
Created on 2026-02-20 09:23:05

@author: drojo
"""
# python
import logging
import base64
from io import BytesIO

try:
    import xlsxwriter
except ImportError:
    xlsxwriter = None

# odoo
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class DetailedPurchasesReportWizard(models.TransientModel):
    _name = 'detailed.purchases.report.wizard'
    _description = 'Wizard de Reporte Detallado de Compras'

    date_from = fields.Date(
        string='Desde', 
        required=True, 
        default=lambda self: fields.Date.start_of(fields.Date.context_today(self), 'month')
    )
    date_to = fields.Date(
        string='Hasta', 
        required=True, 
        default=lambda self: fields.Date.end_of(fields.Date.context_today(self), 'month')
    )

    def action_generate_xlsx_report(self):
        if not xlsxwriter:
            raise UserError(_("La librería 'xlsxwriter' no está instalada."))

        # 1. Construimos el dominio para 'purchase.order.line'
        domain = [
            ('order_id.state', 'in', ['draft', 'sent', 'purchase', 'done', 'to approve']),
            ('order_id.date_order', '>=', self.date_from),
            ('order_id.date_order', '<=', self.date_to),
            ('display_type', '=', False),
        ]
        
        # 2. Buscamos y ordenamos las líneas de compra
        purchase_lines_unordered = self.env['purchase.order.line'].search(domain)
        purchase_lines = purchase_lines_unordered.sorted(key=lambda line: (
            line.order_id.date_order,
            line.order_id.name
        ))
        
        # 3. Mapeo de estados traducidos
        state_map = dict(self.env['purchase.order'].fields_get(['state'])['state']['selection'])

        with BytesIO() as output:
            workbook = xlsxwriter.Workbook(output, {'in_memory': True})
            worksheet = workbook.add_worksheet('Detalle de Compras')
            
            # Formatos
            header_format = workbook.add_format({'bold': True, 'bg_color': '#1f4e78', 'font_color': 'white', 'align': 'center', 'border': 1})
            date_format = workbook.add_format({'num_format': 'dd/mm/yyyy', 'border': 1})
            money_format = workbook.add_format({'num_format': '#,##0.00', 'border': 1})
            text_format = workbook.add_format({'border': 1})

            # 4. Definimos las cabeceras (Incluimos Referencia y Barcode)
            headers = [
                'Fecha', 
                'Orden de Compra', 
                'Estado',
                'Proveedor', 
                'Referencia Interna',
                'Código de Barras',
                'Producto', 
                'Descripción', 
                'Cantidad', 
                'Precio Unitario', 
                'SubTotal (Sin Imp)', 
                'Impuestos',
                'Moneda'
            ]
            
            for col, header in enumerate(headers):
                worksheet.write(0, col, header, header_format)
                worksheet.set_column(col, col, 18)

            # 5. Escribimos los datos
            row = 1
            for line in purchase_lines:
                order = line.order_id
                product = line.product_id
                
                estado_label = state_map.get(order.state, order.state)

                worksheet.write(row, 0, order.date_order, date_format)
                worksheet.write(row, 1, order.name or '', text_format)
                worksheet.write(row, 2, estado_label, text_format)
                worksheet.write(row, 3, order.partner_id.name or '', text_format)
                worksheet.write(row, 4, product.default_code or '', text_format)
                worksheet.write(row, 5, product.barcode or '', text_format)
                worksheet.write(row, 6, product.name or '', text_format)
                worksheet.write(row, 7, line.name or '', text_format)
                worksheet.write(row, 8, line.product_qty, text_format)
                worksheet.write(row, 9, line.price_unit, money_format)
                worksheet.write(row, 10, line.price_subtotal, money_format)
                worksheet.write(row, 11, ', '.join(line.taxes_id.mapped('name')), text_format)
                worksheet.write(row, 12, order.currency_id.name or '', text_format)
                
                row += 1

            workbook.close()
            xlsx_data = output.getvalue()

        report_name = f"Reporte_Detallado_Compras_{self.date_from}_{self.date_to}.xlsx"
        
        attachment = self.env['ir.attachment'].create({
            'name': report_name,
            'type': 'binary',
            'datas': base64.b64encode(xlsx_data),
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }
