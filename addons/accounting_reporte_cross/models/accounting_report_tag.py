from odoo import models, fields

class AccountingReportTagCross(models.Model):
    _name = 'accounting.report.tag.cross'
    _description = 'Etiqueta Contable Regulatoria'

    name = fields.Char(string='Nombre de la Etiqueta', required=True)
    code = fields.Char(string='Código de la Etiqueta', required=True)
    active = fields.Boolean(default=True, string='Activo')

    _sql_constraints = [
        ('code_unique', 'unique(code)', 'The tag code must be unique!')
    ]
