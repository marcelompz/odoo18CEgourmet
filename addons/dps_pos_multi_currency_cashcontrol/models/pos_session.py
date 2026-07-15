from odoo import fields, models,api
from odoo.osv.expression import AND
from odoo.exceptions import AccessError
import json
import logging

_logger = logging.getLogger(__name__)


class PosSession(models.Model):
    _inherit = "pos.session"

    currency_rates_display = fields.Char(
        string="Tasas de Cambio", compute="_compute_currency_rates_display", store=True)
    oc_opening_bal_ids = fields.One2many("other.currency.opening.balance", "session_id", string="Other Currencies Opening Balance")
    oc_opening_cash_details = fields.Text("Other Currency Opening Details")

    @api.model
    def _load_pos_data_fields(self, config_id):
        res = super()._load_pos_data_fields(config_id)
        res += ["currency_rates_display", "oc_opening_bal_ids", "oc_opening_cash_details"]
        return res

    @api.model
    def _load_pos_data_models(self, config_id):
        res = super()._load_pos_data_models(config_id)
        res.append("other.currency.opening.balance")
        return res

    def _prepare_account_bank_statement_line_vals(self, session, sign, amount, reason, extras):
        res = super()._prepare_account_bank_statement_line_vals(session, sign, amount, reason, extras)
        if extras.get('oc_name',False):
            currency = self.env['res.currency'].sudo().search([
                ('name', '=', extras.get('oc_name',False))])
            if currency:
                res.update({
                    'foreign_currency_id': currency.id,
                })
        return res

    @api.depends('start_at', 'config_id')
    def _compute_currency_rates_display(self):
        for session in self:
            date = session.start_at.date() if session.start_at else fields.Date.context_today(session)
            company = session.company_id
            company_currency = company.currency_id
            bills_config = self.env['pos.bill'].search([('company_id', '=', company.id)])
            currencies_to_show = bills_config.mapped('currency_id')
            currencies_to_show = list(set(currencies_to_show) - {company_currency})

            rates_list = []

            for currency in currencies_to_show:
                rate_value = currency._convert(
                    1.0, 
                    company_currency, 
                    company, 
                    date
                )

                if rate_value >= 100:
                    formatted_rate = "{:,.0f}".format(rate_value).replace(",", ".")

                else:
                    formatted_rate = "{:,.2f}".format(rate_value).replace(",", "X").replace(".", ",").replace("X", ".")

                rates_list.append(f"{currency.name}: {formatted_rate}")

            if rates_list:
                session.currency_rates_display = " | ".join(rates_list)

            else:
                session.currency_rates_display = ""

    @api.model
    def _check_installation(self, module_name):
        return self.env['ir.module.module'].sudo().search([('name', '=', module_name), ('state', '=', 'installed')], limit=1)

    def set_other_currency_opening_bal(self,oc_details):
        if oc_details:
            self.oc_opening_cash_details = oc_details
            vals = []
            for k,v in oc_details.items():
                key = k.replace('Total','').strip()
                if key:
                    if self._check_installation('currency_multirate_cross'):
                        currency = self.env['res.currency'].sudo().search([
                        ('name','=',key),('rate_type','=','sale')])
                    
                    else:
                        currency = self.env['res.currency'].sudo().search([
                            ('name','=',key)])
        
                    if currency:
                        vals.append({
                            'session_id' : self.id,
                            'currency_id' : currency.id,
                            'opening_total' : float(v),
                        })
            self.env['other.currency.opening.balance'].create(vals)

    def set_opening_usd_vef_cash(self,usd_cash,fc_cash):
        self.usd_opening_cash = usd_cash
        self.fc_opening_cash = fc_cash

    def get_closing_control_data(self):
        if not self.env.user.has_group('point_of_sale.group_pos_user'):
            raise AccessError(_("You don't have the access rights to get the point of sale closing control data."))
        self.ensure_one()
        orders = self._get_closed_orders()
        payments = orders.payment_ids.filtered(lambda p: p.payment_method_id.type != "pay_later")
        cash_payment_method_ids = self.payment_method_ids.filtered(lambda pm: pm.type == 'cash')
        default_cash_payment_method_id = cash_payment_method_ids[0] if cash_payment_method_ids else None
        default_cash_payments = payments.filtered(lambda p: p.payment_method_id == default_cash_payment_method_id) if default_cash_payment_method_id else []
        total_default_cash_payment_amount = sum(default_cash_payments.mapped('amount')) if default_cash_payment_method_id else 0
        non_cash_payment_method_ids = self.payment_method_ids - default_cash_payment_method_id if default_cash_payment_method_id else self.payment_method_ids
        non_cash_payments_grouped_by_method_id = {pm: orders.payment_ids.filtered(lambda p: p.payment_method_id == pm) for pm in non_cash_payment_method_ids}

        cash_in_count = 0
        cash_out_count = 0
        cash_in_out_list = []
        for cash_move in self.sudo().statement_line_ids.sorted('create_date'):
            if cash_move.amount > 0:
                cash_in_count += 1
                name = f'Cash in {cash_in_count}'
            else:
                cash_out_count += 1
                name = f'Cash out {cash_out_count}'
            cash_in_out_list.append({
                'name': cash_move.payment_ref if cash_move.payment_ref else name,
                'amount': cash_move.amount,
                'other_curr' : cash_move.foreign_currency_id.name if cash_move.foreign_currency_id else '',
                'other_curr_amt' : cash_move.amount_currency,
                'other_curr_symbol' : cash_move.foreign_currency_id.symbol if cash_move.foreign_currency_id else '',
            })
        oc_details = []
        for oc in self.oc_opening_bal_ids:
            oc_details.append([
                oc.name,
                oc.currency_id.rate,
                oc.opening_total,
                oc.symbol])
        print('111111111111111111111111111111111111')

        other_cash_total = 0
        if default_cash_payment_method_id:
            other_cash_payment_method_ids = cash_payment_method_ids - default_cash_payment_method_id
            other_cash_payments = payments.filtered(
                lambda p: p.payment_method_id in other_cash_payment_method_ids
            )
            other_cash_total = sum(other_cash_payments.mapped('amount'))
        _logger.info(
            "POS session %s: other-cash payments total=%s",
            self.id,
            other_cash_total,
        )
        
        return {
            'orders_details': {
                'quantity': len(orders),
                'amount': sum(orders.mapped('amount_total'))
            },
            'opening_notes': self.opening_notes,
            'default_cash_details': {
                'name': default_cash_payment_method_id.name,
                'amount': self.cash_register_balance_start
                          + total_default_cash_payment_amount
                          + sum(self.sudo().statement_line_ids.mapped('amount'))
                          + other_cash_total,
                'opening': self.cash_register_balance_start,
                'payment_amount': total_default_cash_payment_amount,
                'moves': cash_in_out_list,
                'id': default_cash_payment_method_id.id
            } if default_cash_payment_method_id else {},
            'non_cash_payment_methods': [{
                'name': pm.name,
                'amount': sum(non_cash_payments_grouped_by_method_id[pm].mapped('amount')),
                'number': len(non_cash_payments_grouped_by_method_id[pm]),
                'id': pm.id,
                'type': pm.type,
            } for pm in non_cash_payment_method_ids],
            'is_manager': self.env.user.has_group("point_of_sale.group_pos_manager"),
            'amount_authorized_diff': self.config_id.amount_authorized_diff if self.config_id.set_maximum_difference else None,
            'oc_details' : oc_details
        }
