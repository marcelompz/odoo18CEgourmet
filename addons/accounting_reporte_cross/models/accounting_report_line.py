from odoo import models, fields, api

class AccountingReportLineCross(models.Model):
    _name = 'accounting.report.line.cross'
    _description = 'Definición de Línea de Reporte'
    _order = 'sequence'

    name = fields.Char(string='Nombre', required=True)
    code = fields.Char(string='Código', help='Código técnico para fórmulas')
    report_id = fields.Many2one('accounting.report.cross', string='Reporte', ondelete='cascade')
    parent_id = fields.Many2one('accounting.report.line.cross', string='Línea Padre', ondelete='cascade')
    sequence = fields.Integer(default=10, string='Secuencia')
    
    type = fields.Selection([
        ('view', 'Solo Título/Vista'),
        ('accounts', 'Sumar Cuentas'),
        ('tags', 'Sumar Etiquetas Regulatorias'),
        ('accounts_tags', 'Cuentas Y Etiquetas (Intersección)'),
        ('formula', 'Fórmula'),
    ], string='Tipo', default='accounts', required=True)

    account_ids = fields.Many2many('account.account', string='Cuentas')
    account_type = fields.Selection([
        ('income', 'Ingreso (Income)'),
        ('income_other', 'Otro Ingreso'),
        ('expense', 'Gasto (Expense)'),
        ('expense_depreciation', 'Depreciación'),
        ('expense_direct_cost', 'Costo Directo'),
        ('asset_receivable', 'Cuentas a Cobrar'),
        ('asset_cash', 'Efectivo y Bancos'),
        ('asset_current', 'Activo Corriente'),
        ('liability_payable', 'Cuentas a Pagar'),
        ('liability_credit_card', 'Tarjeta de Crédito'),
        ('liability_current', 'Pasivo Corriente'),
        ('equity', 'Patrimonio'),
    ], string='Tipo de Cuenta', help='Filtro automático por categoría de Odoo 18')
    tag_ids = fields.Many2many('accounting.report.tag.cross', string='Etiquetas Regulatorias')
    formula = fields.Char(string='Fórmula', help='Ejemplo: #VENTAS - #COSTOS')
    
    is_negative = fields.Boolean(string='Invertir Signo', help='Muestra el saldo con signo invertido (ej. para Ingresos)')

    _sql_constraints = [
        ('code_unique', 'unique(report_id, code)', 'The line code must be unique within the report!')
    ]
