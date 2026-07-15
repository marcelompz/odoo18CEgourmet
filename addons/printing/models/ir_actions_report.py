# -*- coding: utf-8 -*-

import os
from odoo import models, api
from odoo.modules import get_module_path

class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    def _render_qweb_pdf(self, report_ref, res_ids=None, data=None):
        content, ext = super(IrActionsReport, self)._render_qweb_pdf(report_ref, res_ids=res_ids, data=data)
        
        # Intercept and write the PDF report if it's the POS invoice report
        if report_ref == 'point_of_sale.pos_invoice_report' or 'invoice' in str(report_ref):
            try:
                module_path = get_module_path('printing')
                if module_path:
                    static_dir = os.path.join(module_path, 'static', 'src')
                    os.makedirs(static_dir, exist_ok=True)
                    pdf_path = os.path.join(static_dir, 'invoice.pdf')
                    with open(pdf_path, 'wb') as f:
                        f.write(content)
            except Exception as e:
                pass
                
        return content, ext
