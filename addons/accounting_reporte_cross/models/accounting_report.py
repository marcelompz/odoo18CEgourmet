from odoo import models, fields

class AccountingReportCross(models.Model):
    _name = 'accounting.report.cross'
    _description = 'Definición de Reporte Financiero'

    name = fields.Char(string='Nombre del Reporte', required=True)
    line_ids = fields.One2many('accounting.report.line.cross', 'report_id', string='Líneas del Reporte')
    active = fields.Boolean(default=True, string='Activo')
