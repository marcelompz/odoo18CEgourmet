from odoo import models, fields

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    regulatory_tag_ids = fields.Many2many(
        'accounting.report.tag.cross',
        'account_move_line_regulatory_tag_rel',
        'move_line_id',
        'tag_id',
        string='Etiquetas Regulatorias'
    )
    
    invoice_number = fields.Char(related='move_id.name', string='Número', readonly=True, store=True)
