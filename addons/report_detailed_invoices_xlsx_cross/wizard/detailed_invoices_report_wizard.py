# -*- coding: utf-8 -*-
"""
Created on 2025-10-07 16:34:09

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


class DetailedInvoicesReportWizard(models.TransientModel):
    _name = 'detailed.invoices.report.wizard'
    _description = 'Wizard de Reporte Detallado de Facturas'

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
            raise UserError(_("La librería 'xlsxwriter' no está instalada. Por favor, instálela con: pip install xlsxwriter"))

        # 1. Construir el dominio para buscar en las líneas de factura
        domain = [
            ('move_id.state', '=', 'posted'),
            ('move_id.move_type', 'in', ['out_invoice', 'out_refund']),
            ('move_id.invoice_date', '>=', self.date_from),
            ('move_id.invoice_date', '<=', self.date_to),
            ('account_id.account_type', '=', 'income'),
        ]
        
        # 2. Buscar las líneas y ordenarlas
        invoice_lines_unordered = self.env['account.move.line'].search(domain)

        invoice_lines = invoice_lines_unordered.sorted(key=lambda line: (
            line.move_id.invoice_date,
            line.move_id.name,
            line.sequence
        ))
        
        # 3. Generar el archivo Excel en memoria
        with BytesIO() as output:
            workbook = xlsxwriter.Workbook(output, {'in_memory': True})
            worksheet = workbook.add_worksheet('Detalle de Facturas')
            
            # Formatos
            header_format = workbook.add_format({'bold': True, 'bg_color': '#A9A9A9', 'align': 'center', 'valign': 'vcenter'})
            date_format = workbook.add_format({'num_format': 'dd/mm/yyyy'})
            money_format = workbook.add_format({'num_format': '#,##0.00'})

            # Escribir cabeceras
            headers = [
                'Empresa (Cliente)', 'Comercial', 'Dirección de Entrega', 'Timbrado Electrónico', 'Fecha de Factura',
                'Comprobante Fiscal', 'Timbrado', 'Número', 'Condiciones de Pago', 'Diario',
                'Estado del DE', 'Producto', 'Cantidad', 'Precio Unitario', 'Precio Costo', 'SubTotal', 'Impuestos',
                'Origen', 'Banco Destinatario'
            ]
            for col, header in enumerate(headers):
                worksheet.write(0, col, header, header_format)
                worksheet.set_column(col, col, 20) # Ancho por defecto

            # Escribir datos
            row = 1
            for line in invoice_lines:
                move = line.move_id # Acceso fácil a la factura padre
                worksheet.write(row, 0, move.partner_id.display_name or '')
                worksheet.write(row, 1, move.invoice_user_id.name or '')
                worksheet.write(row, 2, move.partner_shipping_id.display_name or '')
                worksheet.write(row, 3, move.authorization_id.stamped or '')
                worksheet.write(row, 4, move.invoice_date, date_format)
                worksheet.write(row, 5, move.fiscal_document or '')
                worksheet.write(row, 6, move.authorization_id.name or '')
                worksheet.write(row, 7, move.invoice_number or move.name or '')
                worksheet.write(row, 8, move.invoice_payment_term_id.name or '')
                worksheet.write(row, 9, move.journal_id.name or '')
                worksheet.write(row, 10, move.de_status or '')
                worksheet.write(row, 11, line.product_id.display_name or line.name)
                worksheet.write(row, 12, line.quantity)
                worksheet.write(row, 13, line.price_unit, money_format)
                worksheet.write(row, 14, line.product_id.standard_price if line.product_id else 0.0, money_format)
                worksheet.write(row, 15, line.price_total, money_format)
                worksheet.write(row, 16, ', '.join(line.tax_ids.mapped('name')))
                worksheet.write(row, 17, move.invoice_origin or '')
                worksheet.write(row, 18, move.partner_bank_id.acc_number or '')
                row += 1

            workbook.close()
            xlsx_data = output.getvalue()

        # 4. Devolver para descarga
        report_name = f"Reporte_Detallado_Facturas_{self.date_from}_{self.date_to}.xlsx"
        
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
