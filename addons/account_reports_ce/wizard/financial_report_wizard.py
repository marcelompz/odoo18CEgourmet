from odoo import api, fields, models, _
import logging

_logger = logging.getLogger(__name__)

class FinancialReportWizard(models.TransientModel):
    _name = 'financial.report.wizard.ce'
    _description = 'Wizard de Reporte Financiero'

    report_id = fields.Many2one('account.financial.report.ce', string='Reporte', required=True)
    date_from = fields.Date(string='Fecha Desde')
    date_to = fields.Date(string='Fecha Hasta', default=fields.Date.context_today, required=True)
    company_id = fields.Many2one('res.company', string='Compañía', default=lambda self: self.env.company, required=True)
    target_move = fields.Selection([
        ('posted', 'Solo Asentados'),
        ('all', 'Todos los Asientos')
    ], string='Movimientos Objetivo', default='posted')
    
    # Podrían añadirse opciones para comparativa (previous period)
    
    def action_generate_report(self):
        self.ensure_one()
        # Aquí generaríamos el diccionario con los datos o pasaríamos la acción client_action
        
        # Como Odoo 18 no tiene reportes financieros dinámicos listos en CE, 
        # pasaremos estos datos a un Action Client o a un wizard de visualización de HTML.
        
        action = {
            'type': 'ir.actions.client',
            'name': self.report_id.name,
            'tag': 'account_reports_ce_action',
            'context': {
                'report_id': self.report_id.id,
                'date_from': self.date_from,
                'date_to': self.date_to,
                'target_move': self.target_move,
                'company_id': self.company_id.id,
                'report_type': self.report_id.type,
            },
        }
        return action
