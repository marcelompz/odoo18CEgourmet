from odoo import models, fields, api


class PosPayment(models.Model):
    _inherit = 'pos.payment'

    amount_converted = fields.Monetary(
        string='Importe conversión',
        currency_field='payment_currency_id',
        store=True,
        readonly=False,
    )
    payment_currency_id = fields.Many2one(
        'res.currency',
        string='Moneda',
        store=True,
        readonly=False,
    )
    conversion_rate = fields.Float(
        string='Cotización',
        digits=(12, 6),
        readonly=False,
        store=True,
    )

    amount_converted_display = fields.Monetary(
        string='Importe conversión',
        compute='_compute_converted_display',
        currency_field='payment_currency_display_id',
    )
    payment_currency_display_id = fields.Many2one(
        'res.currency',
        string='Moneda',
        compute='_compute_converted_display',
    )
    conversion_rate_display = fields.Float(
        string='Cotización',
        digits=(12, 6),
        compute='_compute_converted_display',
    )

    @api.depends('payment_currency_id', 'currency_id', 'amount_converted', 'conversion_rate')
    def _compute_converted_display(self):
        for payment in self:
            if payment.payment_currency_id and payment.currency_id and payment.payment_currency_id != payment.currency_id:
                payment.amount_converted_display = payment.amount_converted
                payment.payment_currency_display_id = payment.payment_currency_id
                payment.conversion_rate_display = payment.conversion_rate
            else:
                payment.amount_converted_display = 0
                payment.payment_currency_display_id = False
                payment.conversion_rate_display = 0

    @api.model
    def _load_pos_data_fields(self, config_id):
        fields = super()._load_pos_data_fields(config_id)
        fields = list(fields) if fields else list(self.fields_get().keys())

        for extra_field in ['amount_converted', 'payment_currency_id', 'conversion_rate']:
            if extra_field not in fields:
                fields.append(extra_field)

        return fields
