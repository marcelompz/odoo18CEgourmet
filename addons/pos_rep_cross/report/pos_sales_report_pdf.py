from odoo import models, api

class PosSalesReportPdf(models.AbstractModel):
    _name = 'report.pos_rep_cross.report_pdf_template'
    _description = 'POS Sales Report PDF Helper'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['pos.sales.report.wizard'].browse(docids)
        return {
            'doc_ids': docids,
            'doc_model': 'pos.sales.report.wizard',
            'docs': docs,
            'data': data,
        }
