from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import date

class UnrealizedExchangeWizard(models.TransientModel):
    _name = 'unrealized.exchange.wizard'
    _description = 'Wizard de Ganancias y Pérdidas no Realizadas'

    date = fields.Date(string='Fecha de Corte', default=fields.Date.context_today, required=True)
    company_id = fields.Many2one('res.company', string='Compañía', default=lambda self: self.env.company, required=True)
    currency_id = fields.Many2one('res.currency', string='Filtrar por Divisa', domain="[('id', '!=', company_currency_id)]")
    company_currency_id = fields.Many2one('res.currency', related='company_id.currency_id')
    transaction_type = fields.Selection([
        ('all', 'Todos'),
        ('receivable', 'Facturas de Cliente'),
        ('payable', 'Facturas de Proveedor'),
        ('bank', 'Movimientos Bancarios'),
    ], string='Tipo de Transacción', default='all', required=True)

    def action_generate_report(self):
        self.ensure_one()
        # Clean previous report lines for this wizard
        self.env['unrealized.exchange.report.line'].search([('wizard_id', '=', self.id)]).unlink()

        domain = [
            ('company_id', '=', self.company_id.id),
            ('date', '<=', self.date),
            ('amount_currency', '!=', 0),
            ('currency_id', '!=', False),
            ('currency_id', '!=', self.company_id.currency_id.id),
            ('parent_state', '=', 'posted'),
        ]

        if self.currency_id:
            domain.append(('currency_id', '=', self.currency_id.id))

        account_types = []
        if self.transaction_type == 'all':
            account_types = ['asset_receivable', 'liability_payable', 'asset_cash']
        elif self.transaction_type == 'receivable':
            account_types = ['asset_receivable']
        elif self.transaction_type == 'payable':
            account_types = ['liability_payable']
        elif self.transaction_type == 'bank':
            account_types = ['asset_cash']

        domain.append(('account_type', 'in', account_types))

        # We need residual amounts for receivables/payables that are open at the given date.
        # However, to be precise at an arbitrary date, we should rebuild the residual from partials,
        # but for simplicity, if date is today, we can use amount_residual_currency.
        # A robust way is to aggregate move_lines and partial_reconciles up to `self.date`.
        
        lines_vals = []
        
        if 'asset_receivable' in account_types or 'liability_payable' in account_types:
            # Recompute residual based on date
            self.env.cr.execute('''
                SELECT
                    aml.id,
                    aml.date,
                    aml.account_type,
                    aml.currency_id,
                    aml.amount_currency as original_amount_currency,
                    aml.balance as original_balance,
                    (
                        SELECT COALESCE(SUM(amount_currency), 0)
                        FROM account_partial_reconcile apr
                        WHERE apr.debit_move_id = aml.id AND apr.max_date <= %s
                    ) + (
                        SELECT COALESCE(SUM(amount_currency), 0)
                        FROM account_partial_reconcile apr
                        WHERE apr.credit_move_id = aml.id AND apr.max_date <= %s
                    ) as reconciled_currency,
                    aml.move_name,
                    aml.name
                FROM account_move_line aml
                JOIN account_move am ON am.id = aml.move_id
                WHERE aml.company_id = %s
                  AND aml.date <= %s
                  AND aml.amount_currency != 0
                  AND aml.currency_id IS NOT NULL
                  AND aml.currency_id != %s
                  AND am.state = 'posted'
                  AND aml.account_type IN ('asset_receivable', 'liability_payable')
            ''', (self.date, self.date, self.company_id.id, self.date, self.company_id.currency_id.id))
            
            for row in self.env.cr.dictfetchall():
                reconciled = row['reconciled_currency']
                residual_currency = row['original_amount_currency'] - reconciled if row['original_amount_currency'] > 0 else row['original_amount_currency'] + reconciled
                
                # Filter out those fully reconciled at that date
                if self.company_id.currency_id.compare_amounts(residual_currency, 0) == 0:
                    continue
                
                if self.currency_id and row['currency_id'] != self.currency_id.id:
                    continue

                move_line = self.env['account.move.line'].browse(row['id'])
                currency = self.env['res.currency'].browse(row['currency_id'])
                
                # Get rates
                current_rate_val = currency._get_rates(self.company_id, self.date).get(currency.id)
                # Odoo rates are typically Company_Curr / Foreign_Curr, or the reverse.
                # Let's use currency._convert to be safe
                amount_company_current = currency._convert(
                    residual_currency, self.company_id.currency_id, self.company_id, self.date
                )
                
                # original company amount for this residual fraction
                # We can calculate proportional original company currency
                if row['original_amount_currency']:
                    amount_company_original = (residual_currency / row['original_amount_currency']) * row['original_balance']
                else:
                    amount_company_original = 0.0

                # Gain/Loss concept:
                # Receivables (Asset): Current - Original (if positive, gain. if negative, loss)
                # Payables (Liability): Original - Current (if positive, gain. if negative, loss - but balance is negative)
                # To be standard, we can just use the difference in company currency balance.
                # Asset (Positive balance normally). So new balance - old balance = gain.
                # Liability (Negative balance normally).
                
                # Let's just track differences. In Odoo, Debit is positive, Credit is negative.
                # Receivables have Positive balance (Debit). If current rate means it's worth MORE company currency, amount_company_current is MORE positive.
                # Unrealized = Current - Original. If positive, it's a gain.
                unrealized = amount_company_current - amount_company_original
                
                original_rate_display = abs(row['original_balance'] / row['original_amount_currency']) if row['original_amount_currency'] else 0.0
                current_rate_display = abs(amount_company_current / residual_currency) if residual_currency else 0.0

                lines_vals.append((0, 0, {
                    'move_line_id': row['id'],
                    'date': row['date'],
                    'transaction_type': 'receivable' if row['account_type'] == 'asset_receivable' else 'payable',
                    'currency_id': row['currency_id'],
                    'amount_currency': residual_currency,
                    'original_rate': original_rate_display,
                    'amount_company_original': amount_company_original,
                    'current_rate': current_rate_display,
                    'amount_company_current': amount_company_current,
                    'unrealized_gain_loss': unrealized,
                }))

        if 'asset_cash' in account_types:
            # Bank accounts. For banks we don't look at reconciliation, we look at the total balance of the account up to the date.
            # Group by account_id and currency_id
            self.env.cr.execute('''
                SELECT
                    aml.account_id,
                    aml.currency_id,
                    SUM(aml.amount_currency) as total_amount_currency,
                    SUM(aml.balance) as total_balance
                FROM account_move_line aml
                JOIN account_move am ON am.id = aml.move_id
                WHERE aml.company_id = %s
                  AND aml.date <= %s
                  AND aml.currency_id IS NOT NULL
                  AND aml.currency_id != %s
                  AND am.state = 'posted'
                  AND aml.account_type = 'asset_cash'
                GROUP BY aml.account_id, aml.currency_id
            ''', (self.company_id.id, self.date, self.company_id.currency_id.id))

            for row in self.env.cr.dictfetchall():
                if self.company_id.currency_id.compare_amounts(row['total_amount_currency'], 0) == 0:
                    continue
                if self.currency_id and row['currency_id'] != self.currency_id.id:
                    continue

                currency = self.env['res.currency'].browse(row['currency_id'])
                amount_company_current = currency._convert(
                    row['total_amount_currency'], self.company_id.currency_id, self.company_id, self.date
                )
                
                amount_company_original = row['total_balance']
                unrealized = amount_company_current - amount_company_original
                
                original_rate_display = abs(row['total_balance'] / row['total_amount_currency']) if row['total_amount_currency'] else 0.0
                current_rate_display = abs(amount_company_current / row['total_amount_currency']) if row['total_amount_currency'] else 0.0

                # We don't link to a specific line for bank balances, just the account. We can create an empty line just as representative
                # Or we can link the first line. We'll leave move_line empty and add an account field if needed.
                lines_vals.append((0, 0, {
                    'date': self.date,
                    'transaction_type': 'bank',
                    'currency_id': row['currency_id'],
                    'amount_currency': row['total_amount_currency'],
                    'original_rate': original_rate_display,
                    'amount_company_original': amount_company_original,
                    'current_rate': current_rate_display,
                    'amount_company_current': amount_company_current,
                    'unrealized_gain_loss': unrealized,
                }))

        self.write({'report_line_ids': lines_vals})

        return {
            'name': _('Ganancias/Pérdidas no Realizadas'),
            'type': 'ir.actions.act_window',
            'res_model': 'unrealized.exchange.report.line',
            'view_mode': 'list,pivot,graph',
            'domain': [('wizard_id', '=', self.id)],
            'target': 'current',
        }

    report_line_ids = fields.One2many('unrealized.exchange.report.line', 'wizard_id', string='Líneas del Reporte')


class UnrealizedExchangeReportLine(models.TransientModel):
    _name = 'unrealized.exchange.report.line'
    _description = 'Línea de Reporte de Ganancia/Pérdida'

    wizard_id = fields.Many2one('unrealized.exchange.wizard', ondelete='cascade')
    move_line_id = fields.Many2one('account.move.line', string='Movimiento/Factura')
    date = fields.Date(string='Fecha Transacción/Corte')
    transaction_type = fields.Selection([
        ('receivable', 'Factura de Cliente'),
        ('payable', 'Factura de Proveedor'),
        ('bank', 'Saldo Bancario'),
    ], string='Tipo de Transacción')
    currency_id = fields.Many2one('res.currency', string='Divisa')
    amount_currency = fields.Monetary(string='Monto Moneda Extranjera', currency_field='currency_id')
    original_rate = fields.Float(string='Tasa Original', digits=(12, 6))
    amount_company_original = fields.Monetary(string='Monto Moneda Funcional (Original)', currency_field='company_currency_id')
    current_rate = fields.Float(string='Tasa a Fecha Corte', digits=(12, 6))
    amount_company_current = fields.Monetary(string='Monto Moneda Funcional (Actual)', currency_field='company_currency_id')
    unrealized_gain_loss = fields.Monetary(string='Ganancia/Pérdida no Realizada', currency_field='company_currency_id')
    
    company_currency_id = fields.Many2one('res.currency', related='wizard_id.company_currency_id')
