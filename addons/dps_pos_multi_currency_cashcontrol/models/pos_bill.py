from odoo import fields, models,api
from odoo.osv.expression import AND

class PosConfig(models.Model):
    _inherit = "pos.bill"

    company_id = fields.Many2one(
        'res.company', 
        string="Company", 
        required=True, 
        default=lambda self: self.env.company
    )
    currency_id = fields.Many2one(
        'res.currency',
        string="Other Currency",
        domain="[('id', '!=', company_currency_id)]"
    )
    company_currency_id = fields.Many2one(
        'res.currency',
        string="Company Currency",
        related="company_id.currency_id",
        store=True,
        readonly=True
    )

    @api.model
    def _load_pos_data_fields(self, config_id):
        res = super()._load_pos_data_fields(config_id)
        res += ["currency_id", "company_currency_id"]
        return res
 