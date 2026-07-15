from odoo import models, fields, api, _
from odoo.tools.safe_eval import safe_eval
import re

class AccountingReportWizard(models.TransientModel):
    _name = 'accounting.report.wizard'
    _description = 'Asistente de Reporte Contable'

    report_id = fields.Many2one('accounting.report.cross', string='Reporte', required=True)
    date_from = fields.Date(string='Desde Fecha', required=True, default=fields.Date.context_today)
    date_to = fields.Date(string='Hasta Fecha', required=True, default=fields.Date.context_today)
    
    # Filter by tags for the whole report (auxiliary)
    tag_ids = fields.Many2many('accounting.report.tag.cross', string='Filtrar por Etiquetas Regulatorias')

    def action_generate_report(self):
        self.ensure_one()
        
        # 1. Create Result Container
        result = self.env['accounting.report.result.cross'].create({
            'report_id': self.report_id.id,
            'date_from': self.date_from,
            'date_to': self.date_to,
        })
        
        # 2. Get all definition lines ordered
        def_lines = self.env['accounting.report.line.cross'].search([
            ('report_id', '=', self.report_id.id)
        ], order='sequence')
        
        # Map to track definitions vs results
        parent_map = {}
        # Balance map for formulas {code: balance}
        balance_map = {}
        
        # 3. Compute balances
        for def_line in def_lines:
            balance = 0.0
            
            if def_line.type in ['accounts', 'tags', 'accounts_tags']:
                # Determine domain for the line
                domain = [
                    ('date', '>=', self.date_from),
                    ('date', '<=', self.date_to),
                    ('move_id.state', '=', 'posted'),
                    ('company_id', '=', self.env.company.id),
                    ('display_type', 'not in', ('line_section', 'line_note')),
                ]
                
                # Apply wizard tag filters if any (global filter)
                if self.tag_ids:
                    domain.append(('regulatory_tag_ids', 'in', self.tag_ids.ids))
                
                # Apply line specific filters
                if def_line.type in ['accounts', 'accounts_tags']:
                    line_account_domain = []
                    if def_line.account_ids:
                        line_account_domain.append(('account_id', 'in', def_line.account_ids.ids))
                    if def_line.account_type:
                        line_account_domain.append(('account_id.account_type', '=', def_line.account_type))
                    
                    if line_account_domain:
                        # If both are set, it acts as an AND for precision.
                        # If only one is set, it works as expected.
                        domain += line_account_domain
                    elif not def_line.tag_ids and def_line.type == 'accounts': # If type is accounts but no accounts or tags are selected
                        # No accounts or account type specified, and no tags for a pure 'accounts' type line
                        # This line would result in 0 balance, so we can skip further processing for it.
                        # If it's 'accounts_tags' and only accounts are missing, tags might still apply.
                        pass # Let the domain be empty for accounts, which will result in 0 balance
                
                if def_line.type in ['tags', 'accounts_tags']:
                    if def_line.tag_ids:
                        domain.append(('regulatory_tag_ids', 'in', def_line.tag_ids.ids))
                
                # Sum balances grouped by account for details
                aml_data = self.env['account.move.line'].read_group(
                    domain, ['balance:sum'], ['account_id']
                )
                balance = sum(d['balance'] for d in aml_data)
                
            elif def_line.type == 'formula':
                # Replace #CODE with values from balance_map
                formula = def_line.formula or "0"
                # Find all #CODE occurrences
                codes = re.findall(r'#(\w+)', formula)
                eval_formula = formula
                for code in codes:
                    val = balance_map.get(code, 0.0)
                    eval_formula = eval_formula.replace(f'#{code}', str(val))
                
                try:
                    balance = safe_eval(eval_formula)
                except Exception:
                    balance = 0.0
            
            # Flip sign if configured
            final_balance = balance * (-1 if def_line.is_negative else 1)
            
            # Update balance map for future formulas
            if def_line.code:
                balance_map[def_line.code] = balance # Use raw balance for multi-formula consistency if needed, but usually we use final_balance?
                # Actually, standard suggests we store the raw balance for formulas if others depend on it, 
                # but flip sign is usually for "Revenue" display. 
                # Let's use raw balance in map to avoid sign confusion in formulas.
                
            # Create Result Line
            level = self._get_line_level(def_line)
            # Create category result line
            line_res = self.env['accounting.report.result.line.cross'].create({
                'result_id': result.id,
                'report_line_id': def_line.id,
                'name': def_line.name,
                'code': def_line.code,
                'balance': final_balance, # Use final_balance for the category line
                'level': level,
                'sequence': def_line.sequence,
                'parent_id': parent_map.get(def_line.parent_id.id) if def_line.parent_id else None,
                'is_title': True,
                'is_total': def_line.type == 'formula',
                'tag_names': ", ".join(def_line.tag_ids.mapped('name')),
            })
            parent_map[def_line.id] = line_res.id

            # Create account-level detail lines if applicable
            if def_line.type in ['accounts', 'accounts_tags'] and aml_data:
                for data in aml_data:
                    account = self.env['account.account'].browse(data['account_id'][0])
                    self.env['accounting.report.result.line.cross'].create({
                        'result_id': result.id,
                        'name': f"{account.code} {account.name}",
                        'balance': data['balance'] * (-1 if def_line.is_negative else 1),
                        'level': level + 1,
                        'sequence': def_line.sequence + 1,
                        'parent_id': line_res.id,
                        'is_title': False,
                    })
            
        # 4. Return view action (Form view for Dashboard look)
        return {
            'name': _('Reporte: %s') % self.report_id.name,
            'type': 'ir.actions.act_window',
            'res_model': 'accounting.report.result.cross',
            'view_mode': 'form',
            'res_id': result.id,
            'target': 'current',
        }

    def _get_line_level(self, line):
        level = 0
        curr = line
        while curr.parent_id:
            level += 1
            curr = curr.parent_id
        return level
