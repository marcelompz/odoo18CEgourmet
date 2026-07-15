from odoo import api, models

class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.model
    def _load_pos_data_fields(self, config_id):
        res = super(ProductProduct, self)._load_pos_data_fields(config_id=config_id)

        res += ['qty_available']
        return res