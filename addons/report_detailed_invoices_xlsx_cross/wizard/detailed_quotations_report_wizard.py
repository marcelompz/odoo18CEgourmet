# -*- coding: utf-8 -*-
"""
Created on 2025-10-07 17:32:48

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


class DetailedQuotationsReportWizard(models.TransientModel):
    _name = 'detailed.quotations.report.wizard'
    _description = 'Wizard de Reporte Detallado de Cotizaciones'

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

        # 2. Construimos el dominio para 'sale.order.line'
        domain = [
            ('order_id.state', 'in', ['draft', 'sent', 'sale', 'done']),
            ('order_id.date_order', '>=', self.date_from),
            ('order_id.date_order', '<=', self.date_to),
            ('display_type', '=', False),
        ]
        
        # 3. Buscamos y ordenamos las líneas de cotización
        quotation_lines_unordered = self.env['sale.order.line'].search(domain)
        quotation_lines = quotation_lines_unordered.sorted(key=lambda line: (
            line.order_id.date_order,
            line.order_id.name
        ))
        
        # Obtenemos las etiquetas traducidas de los estados una sola vez ---
        state_map = dict(self.env['sale.order'].fields_get(['state'])['state']['selection'])

        with BytesIO() as output:
            workbook = xlsxwriter.Workbook(output, {'in_memory': True})
            worksheet = workbook.add_worksheet('Detalle de Cotizaciones')
            
            header_format = workbook.add_format({'bold': True, 'bg_color': '#A9A9A9', 'align': 'center'})
            date_format = workbook.add_format({'num_format': 'dd/mm/yyyy'})
            money_format = workbook.add_format({'num_format': '#,##0.00'})

            # 4. Definimos las cabeceras (Agregamos 'Estado' en la posición 2)
            headers = [
                'Fecha', 
                'Número de Cotización', 
                'Estado',
                'Cliente', 
                'Comercial', 
                'Producto', 
                'Descripción', 
                'Cantidad', 
                'Precio Unitario', 
                'SubTotal', 
                'Impuestos',
                'Moneda',
                'Descuento (%)'
            ]
            for col, header in enumerate(headers):
                worksheet.write(0, col, header, header_format)
                worksheet.set_column(col, col, 20)

            # 5. Escribimos los datos de las líneas de cotización
            row = 1
            for line in quotation_lines:
                order = line.order_id
                
                # Obtenemos el nombre legible del estado (ej: "Orden de Venta")
                estado_label = state_map.get(order.state, order.state)

                worksheet.write(row, 0, order.date_order, date_format)
                worksheet.write(row, 1, order.name or '')
                worksheet.write(row, 2, estado_label)
                worksheet.write(row, 3, order.partner_id.display_name or '')
                worksheet.write(row, 4, order.user_id.name or '')
                worksheet.write(row, 5, line.product_id.name or '')
                worksheet.write(row, 6, line.name or '')
                worksheet.write(row, 7, line.product_uom_qty)
                worksheet.write(row, 8, line.price_unit, money_format)
                worksheet.write(row, 9, line.price_total, money_format)
                worksheet.write(row, 10, ', '.join(line.tax_id.mapped('name')))
                worksheet.write(row, 11, line.order_id.currency_id.name or '')
                worksheet.write(row, 12, line.discount)
                row += 1

            workbook.close()
            xlsx_data = output.getvalue()

        report_name = f"Reporte_Detallado_Cotizaciones_{self.date_from}_{self.date_to}.xlsx"
        
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
