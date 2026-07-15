from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class PosConfig(models.Model):
    _inherit = 'pos.config'

    cash_currency_ids = fields.Many2many(
        'res.currency',
        compute='_compute_cash_currency_ids',
        string='Cash Payment Currencies',
        help='Currencies used by cash payment methods in this POS'
    )

    @api.depends('payment_method_ids', 'payment_method_ids.journal_id', 'company_id')
    def _compute_cash_currency_ids(self):
        """
        Compute unique currencies from all cash-type payment methods.
        If a journal has no currency, use company currency.
        """
        for config in self:
            currencies = self.env['res.currency']

            cash_payment_methods = config.payment_method_ids.filtered(
                lambda pm: pm.journal_id and pm.journal_id.type == 'cash'
            )

            # Collect unique currencies
            for pm in cash_payment_methods:
                currency = pm.journal_id.currency_id or config.company_id.currency_id
                if currency and currency not in currencies:
                    currencies |= currency

            config.cash_currency_ids = currencies

    # Multi-Currency Display Configuration
    min_change_threshold = fields.Float(
        string='Minimum Change Threshold',
        default=100.0,
        help='Change amounts below this value will be rounded to zero in the UI. Set to 0 to disable.'
    )
    
    excluded_currency_ids = fields.Many2many(
        'res.currency',
        'pos_config_excluded_currency_rel',
        'config_id',
        'currency_id',
        string='Excluded Currencies from Display',
        help='Currencies to exclude from exchange rate display on payment screen (e.g., base currency like PYG)'
    )

    @api.model
    def _load_pos_data_fields(self, config_id):
        """Ensure POS receives standard config fields plus multi-currency configuration."""
        fields = super()._load_pos_data_fields(config_id)
        if not fields:
            # Base implementation returns an empty list, which means "all fields".
            # Rebuild that behaviour so we don't miss expected keys like use_pricelist.
            fields = list(self.fields_get().keys())
        
        # Add all multi-currency related fields
        for field in ['cash_currency_ids', 'min_change_threshold', 'excluded_currency_ids']:
            if field not in fields:
                fields.append(field)
        
        return fields

    @api.constrains('pricelist_id', 'use_pricelist', 'available_pricelist_ids', 'journal_id', 'invoice_journal_id', 'payment_method_ids')
    def _check_currencies(self):
        for config in self:
            if config.use_pricelist and config.pricelist_id and config.pricelist_id not in config.available_pricelist_ids:
                raise ValidationError(_("The default pricelist must be included in the available pricelists."))

            """
            # Check if the config's payment methods are compatible with its currency
            for pm in config.payment_method_ids:
                if pm.journal_id and pm.journal_id.currency_id and pm.journal_id.currency_id != config.currency_id:
                    raise ValidationError(_("All payment methods must be in the same currency as the Sales Journal or the company currency if that is not set."))
            """

            if config.use_pricelist and any(config.available_pricelist_ids.mapped(lambda pricelist: pricelist.currency_id != config.currency_id)):
                raise ValidationError(_("All available pricelists must be in the same currency as the company or"
                                        " as the Sales Journal set on this point of sale if you use"
                                        " the Accounting application."))
            if config.invoice_journal_id.currency_id and config.invoice_journal_id.currency_id != config.currency_id:
                raise ValidationError(_("The invoice journal must be in the same currency as the Sales Journal or the company currency if that is not set."))
