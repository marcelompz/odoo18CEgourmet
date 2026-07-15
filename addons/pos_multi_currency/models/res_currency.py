from odoo import models, api


class ResCurrency(models.Model):
    _inherit = 'res.currency'

    # DPS module (dps_pos_multi_currency_cashcontrol) already loads ALL currencies
    # with domain [('id', '!=', False)], which is exactly what we need.
    # Our selective loading was redundant and potentially problematic.
    # Removed _load_pos_data_domain override to avoid conflicts.
