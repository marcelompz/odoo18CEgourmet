from odoo import models, fields, api, _
import io
import base64

try:
    import xlsxwriter
except ImportError:
    xlsxwriter = None

class AccountingReportResultCross(models.TransientModel):
    _inherit = 'accounting.report.result.cross'

    def action_export_xlsx(self):
        self.ensure_one()
        if not xlsxwriter:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Error'),
                    'message': _('La librería xlsxwriter no está instalada.'),
                    'type': 'danger',
                }
            }

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('Reporte Financiero')

        # Styles
        title_fmt = workbook.add_format({'bold': True, 'font_size': 14, 'align': 'center'})
        header_fmt = workbook.add_format({'bold': True, 'bg_color': '#E9ECEF', 'border': 1})
        category_fmt = workbook.add_format({'bold': True})
        total_fmt = workbook.add_format({'bold': True, 'bg_color': '#F8F9FA', 'top': 1})
        num_fmt = workbook.add_format({'num_format': '#,##0.00'})
        num_total_fmt = workbook.add_format({'num_format': '#,##0.00', 'bold': True, 'bg_color': '#F8F9FA', 'top': 1})

        # Header
        sheet.merge_range('A1:B1', self.report_id.name, title_fmt)
        sheet.merge_range('A2:B2', f"Desde: {self.date_from} Hasta: {self.date_to}", workbook.add_format({'align': 'center'}))
        
        sheet.write(4, 0, 'Descripción', header_fmt)
        sheet.write(4, 1, 'Saldo', header_fmt)
        sheet.set_column(0, 0, 50)
        sheet.set_column(1, 1, 15)

        row = 5
        for line in self.line_ids:
            fmt = category_fmt if line.is_title else None
            n_fmt = num_fmt
            
            if line.is_total:
                fmt = total_fmt
                n_fmt = num_total_fmt
            
            indent = "    " * line.level
            sheet.write(row, 0, f"{indent}{line.name}", fmt)
            sheet.write(row, 1, line.balance, n_fmt)
            row += 1

        workbook.close()
        output.seek(0)
        
        file_data = base64.b64encode(output.read())
        attachment = self.env['ir.attachment'].create({
            'name': f"{self.report_id.name}.xlsx",
            'type': 'binary',
            'datas': file_data,
            'store_fname': f"{self.report_id.name}.xlsx",
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'new',
        }
