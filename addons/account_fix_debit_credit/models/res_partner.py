# -*- coding: utf-8 -*-
from odoo import models
from odoo.sql_db import SQL


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def _credit_debit_get(self):
        """
        Override of Odoo core _credit_debit_get to handle NULL values from SUM().
        
        During migration, account.move.line records may have NULL amount_residual,
        causing SUM() to return NULL. The core code does `partner.debit = -val`
        which fails with TypeError when val is None.
        
        This fix treats NULL as 0.0 before negation.
        """
        if not self.ids:
            self.debit = False
            self.credit = False
            return

        query = self.env['account.move.line']._where_calc([
            ('parent_state', '=', 'posted'),
            ('company_id', 'child_of', self.env.company.root_id.id)
        ])
        self.env['account.move.line'].flush_model(
            ['account_id', 'amount_residual', 'company_id', 'parent_state', 'partner_id', 'reconciled']
        )
        self.env['account.account'].flush_model(['account_type'])
        sql = SQL("""
            SELECT account_move_line.partner_id, a.account_type, SUM(account_move_line.amount_residual)
            FROM %s
            LEFT JOIN account_account a ON (account_move_line.account_id=a.id)
            WHERE a.account_type IN ('asset_receivable','liability_payable')
            AND account_move_line.partner_id IN %s
            AND account_move_line.reconciled IS NOT TRUE
            AND %s
            GROUP BY account_move_line.partner_id, a.account_type
            """,
            query.from_clause,
            tuple(self.ids),
            query.where_clause or SQL("TRUE"),
        )
        treated = self.browse()
        for pid, account_type, val in self.env.execute_query(sql):
            partner = self.browse(pid)
            # FIX: Treat NULL as 0.0 to avoid TypeError on unary minus
            val = val or 0.0
            if account_type == 'asset_receivable':
                partner.credit = val
                if partner not in treated:
                    partner.debit = False
                    treated |= partner
            elif account_type == 'liability_payable':
                partner.debit = -val
                if partner not in treated:
                    partner.credit = False
                    treated |= partner
        remaining = (self - treated)
        remaining.debit = False
        remaining.credit = False
