from odoo import models, api


class AccountJournal(models.Model):
    _name = 'account.journal'
    _inherit = ['account.journal', 'pos.load.mixin']

    @api.model
    def _load_pos_data_domain(self, data):
        payment_method_ids = data['pos.payment.method']['data']
        journal_ids = [pm['journal_id'] for pm in payment_method_ids if pm.get('journal_id')]
        return [('id', 'in', journal_ids)]

    @api.model
    def _load_pos_data_fields(self, config_id):
        return ['id', 'name', 'type', 'currency_id']
