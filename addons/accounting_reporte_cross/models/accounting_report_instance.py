from odoo import models, fields, api, _
from odoo.tools.safe_eval import safe_eval
import re

class AccountingReportResultCross(models.TransientModel):
    _name = 'accounting.report.result.cross'
    _description = 'Resultado de Ejecución de Reporte'

    report_id = fields.Many2one('accounting.report.cross', string='Definición de Reporte')
    date_from = fields.Date(string='Desde Fecha')
    date_to = fields.Date(string='Hasta Fecha')
    line_ids = fields.One2many('accounting.report.result.line.cross', 'result_id', string='Líneas')

    def action_print_pdf(self):
        return self.env.ref('accounting_reporte_cross.action_report_financial_cross').report_action(self)

class AccountingReportResultLineCross(models.TransientModel):
    _name = 'accounting.report.result.line.cross'
    _description = 'Línea de Resultado de Reporte'
    _order = 'sequence'

    result_id = fields.Many2one('accounting.report.result.cross', string='Resultado', ondelete='cascade')
    report_line_id = fields.Many2one('accounting.report.line.cross', string='Definición Origen')
    name = fields.Char(string='Nombre de Línea')
    code = fields.Char(string='Código')
    balance = fields.Float(string='Saldo', digits=(16, 2))
    level = fields.Integer(string='Nivel', default=0)
    sequence = fields.Integer(string='Secuencia', default=10)
    parent_id = fields.Many2one('accounting.report.result.line.cross', string='Línea Resultado Padre', ondelete='cascade')
    child_ids = fields.One2many('accounting.report.result.line.cross', 'parent_id', string='Líneas Hijas')
    
    is_title = fields.Boolean(string='Es Título', default=False)
    is_total = fields.Boolean(string='Es Total', default=False)
    tag_names = fields.Char(string='Etiquetas Regulatorias')
    display_name_indented = fields.Char(compute='_compute_display_name_indented')

    @api.depends('name', 'level')
    def _compute_display_name_indented(self):
        for record in self:
            prefix = '    ' * record.level
            record.display_name_indented = f"{prefix}{record.name}"

    def _get_line_domain(self, line):
        """Recursively get the domain for a report line or its children/components."""
        if line.type == 'formula':
            # Collect domains of all codes mentioned in the formula
            codes = re.findall(r'#(\w+)', line.formula or '')
            component_lines = self.env['accounting.report.line.cross'].search([
                ('report_id', '=', line.report_id.id),
                ('code', 'in', codes)
            ])
            domain = ['|'] * (max(0, len(component_lines) - 1))
            for comp in component_lines:
                domain += self._get_line_domain(comp)
            return domain or [('id', '=', 0)]

        if line.type == 'view':
            # Collect domains of all children
            child_lines = self.env['accounting.report.line.cross'].search([
                ('parent_id', '=', line.id)
            ])
            domain = ['|'] * (max(0, len(child_lines) - 1))
            for child in child_lines:
                domain += self._get_line_domain(child)
            return domain or [('id', '=', 0)]

        # Base case: actual filters
        line_domain = []
        if line.type in ['accounts', 'accounts_tags']:
            account_subdomain = []
            if line.account_ids:
                account_subdomain.append(('account_id', 'in', line.account_ids.ids))
            if line.account_type:
                account_subdomain.append(('account_id.account_type', '=', line.account_type))
            
            if account_subdomain:
                # Use AND for multiple account filters (precision)
                line_domain += account_subdomain
            elif not line.tag_ids and line.type == 'accounts':
                return [('id', '=', 0)]

        if line.type in ['tags', 'accounts_tags']:
            if line.tag_ids:
                line_domain.append(('regulatory_tag_ids', 'in', line.tag_ids.ids))
        
        return line_domain or [('id', '=', 0)]

    def action_drill_down(self):
        self.ensure_one()
        if not self.report_line_id:
            return
            
        line = self.report_line_id
        base_domain = [
            ('date', '>=', self.result_id.date_from),
            ('date', '<=', self.result_id.date_to),
            ('move_id.state', '=', 'posted'),
            ('display_type', 'not in', ('line_section', 'line_note')),
            ('company_id', '=', self.env.company.id),
        ]
        
        line_domain = self._get_line_domain(line)
        final_domain = base_domain + line_domain

        return {
            'name': _('Apuntes Contables: %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'account.move.line',
            'view_mode': 'list,form',
            'domain': final_domain,
            'context': {'search_default_group_by_account': 1},
        }

    def action_export_xlsx(self):
        return self.result_id.action_export_xlsx()

    def action_print_pdf(self):
        return self.env.ref('accounting_reporte_cross.action_report_financial_cross').report_action(self.result_id)
