from odoo import api, fields, models, _
import logging

_logger = logging.getLogger(__name__)

class AccountFinancialReport(models.Model):
    _name = 'account.financial.report.ce'
    _description = 'Estructura de Reporte Financiero'

    name = fields.Char(string='Nombre del Reporte', required=True, translate=True)
    type = fields.Selection([
        ('balance', 'Balance General'),
        ('pnl', 'Estado de Resultados'),
        ('cashflow', 'Flujo de Efectivo'),
        ('other', 'Otro')
    ], string='Tipo', required=True, default='other')
    line_ids = fields.One2many('account.financial.report.line.ce', 'report_id', string='Líneas del Reporte')
    company_id = fields.Many2one('res.company', string='Compañía', default=lambda self: self.env.company)


class AccountFinancialReportLine(models.Model):
    _name = 'account.financial.report.line.ce'
    _description = 'Estructura de Línea de Reporte Financiero'
    _order = 'sequence'

    name = fields.Char(string='Nombre de la Línea', required=True, translate=True)
    sequence = fields.Integer(string='Secuencia', default=10)
    report_id = fields.Many2one('account.financial.report.ce', string='Reporte', ondelete='cascade')
    parent_id = fields.Many2one('account.financial.report.line.ce', string='Padre', ondelete='cascade')
    child_ids = fields.One2many('account.financial.report.line.ce', 'parent_id', string='Hijos')
    
    formula = fields.Char(string='Fórmula de Cálculo', help='Fórmula para calcular el valor total (ej. A + B - C)')
    code = fields.Char(string='Código', help='Código usado en fórmulas')

    domain = fields.Char(string='Dominio de Cuentas', help='Por ejemplo: [("account_type", "=", "asset_current")]')
    account_type_ids = fields.Many2many('account.account', string='Tipos de Cuentas')
    
    sign = fields.Selection([('1', 'Normal'), ('-1', 'Invertir Signo')], string='Signo', default='1', required=True)
    level = fields.Integer(string='Nivel', default=1)
    is_title = fields.Boolean(string='Es Título', default=False)
