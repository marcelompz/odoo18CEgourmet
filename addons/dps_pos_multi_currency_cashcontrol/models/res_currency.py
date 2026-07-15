from odoo import models, api


class ResCurrency(models.Model):
    _inherit = 'res.currency'

    @api.model
    def _load_pos_data_domain(self, data):
        """overridden to load all currencies"""
        return [('id', '!=', False)]