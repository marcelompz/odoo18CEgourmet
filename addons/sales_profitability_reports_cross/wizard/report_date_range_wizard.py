# -*- coding: utf-8 -*-
"""
Created on 2025-08-06 12:06:45

@author: drojo
"""
# python
from datetime import datetime
import calendar
import base64
from io import BytesIO
import logging

# odoo
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_round

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter

_logger = logging.getLogger(__name__)


class ReportDateRangeWizard(models.TransientModel):
    _name = 'report.date.range.wizard'
    _description = 'Reporte de Rentabilidad de Ventas'

    date_from = fields.Date(
        string='Fecha desde', default=lambda self: self._default_date_from(), required=True)
    date_until = fields.Date(
        string='Fecha hasta', default=lambda self: self._default_date_until(), required=True)
    user_id = fields.Many2one(
        'res.users', string='Comercial (opcional)',
        help="Filtra por el comercial en Cotizaciones (Sale Order) o por el vendedor en Punto de Venta (PoS Order).")
    partner_id = fields.Many2one(
        'res.partner', string='Cliente',
        help="Filtra por el cliente en Cotizaciones (Sale Order) o por el cliente de la orden en Punto de Venta (PoS Order).")
    options = fields.Selection(
        string='Agrupar por', selection=[('summary', 'Comercial'), ('product', 'Producto'), ('partner', 'Cliente')], default='summary', required=True)
    sales_summary = fields.One2many(
        'sales.summary.line', 'wizard_id', string='Resumen por Comercial')
    product_summary = fields.One2many(
        'product.summary.line', 'wizard_id', string='Resumen por Producto')
    partner_summary = fields.One2many(
        'partner.summary.line', 'wizard_id', string='Resumen por Cliente')
    sale_report = fields.Boolean(
        string='Cotizaciones', default=True,
        help="Incluir datos de Órdenes de Venta (Sale Orders).")
    pos_report = fields.Boolean(
        string='Punto de ventas', default=False,
        help="Incluir datos de Órdenes de Punto de Venta (PoS Orders).")
    currency_id = fields.Many2one(
        'res.currency', string='Moneda del reporte', default=lambda self: self.env.company.currency_id.id, required=True)

    sales_ids = fields.Many2many('sale.order', string="Órdenes de Venta")
    pos_order_ids = fields.Many2many('pos.order', string="Órdenes de Punto de Venta")

    show_profitability = fields.Boolean(
        string='Mostrar rentabilidad?')

    @api.model
    def _default_date_from(self):
        today = datetime.today()
        return today.replace(day=1).date()

    @api.model
    def _default_date_until(self):
        today = datetime.today()
        last_day_of_month = calendar.monthrange(today.year, today.month)[1]
        return today.replace(day=last_day_of_month).date()
    
    @api.constrains('sale_report', 'pos_report')
    def _check_at_least_one_source(self):
        if not self.sale_report and not self.pos_report:
            raise UserError(_('ERROR: Debe seleccionar al menos una fuente de datos (Cotizaciones o Punto de Ventas).'))

    def open_query_result(self, for_xlsx=False):
        if self.options == 'partner' and not self.partner_id and not (self.sale_report or self.pos_report):
            raise UserError(_("Por favor, seleccione un cliente o al menos una fuente de datos (Cotizaciones o Punto de Venta) para generar este reporte agrupado por cliente."))
        elif self.options == 'partner' and not self.partner_id:
            pass

        if self.date_from > self.date_until:
            raise UserError(_('ERROR: La fecha desde debe ser menor o igual a la fecha hasta.'))

        self._clear_fields()

        start_datetime = datetime.combine(self.date_from, datetime.min.time())
        end_datetime = datetime.combine(self.date_until, datetime.max.time())
        
        sale_domain = [
            ('state', 'in', ['sale', 'done']),
            ('date_order', '>=', start_datetime),
            ('date_order', '<=', end_datetime)
        ]
        
        pos_domain = [
            ('state', 'in', ['paid', 'done', 'invoiced']),
            ('date_order', '>=', start_datetime),
            ('date_order', '<=', end_datetime)
        ]

        if self.user_id:
            sale_domain.append(('user_id', '=', self.user_id.id))
            pos_domain.append(('user_id', '=', self.user_id.id))
        
        if self.partner_id:
            sale_domain.append(('partner_id', '=', self.partner_id.id))
            pos_domain.append(('partner_id', '=', self.partner_id.id))

        sale_orders = self.env['sale.order']
        pos_orders = self.env['pos.order']

        if self.sale_report:
            sale_orders = self.env['sale.order'].search(sale_domain)
        if self.pos_report:
            pos_orders = self.env['pos.order'].search(pos_domain)

        self.sales_ids = [(6, 0, sale_orders.ids)]
        self.pos_order_ids = [(6, 0, pos_orders.ids)]

        if not sale_orders and not pos_orders:
            if not for_xlsx:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {'title': _('Sin datos para mostrar.'), 'type': 'warning'},
                }
            return

        company_currency = self.env.company.currency_id

        if self.options == 'summary':
            self._generate_summary_by_user(sale_orders, pos_orders, self.currency_id, company_currency)
        elif self.options == 'product':
            self._generate_detailed_product_summary(sale_orders, pos_orders, self.currency_id, company_currency)
        elif self.options == 'partner':
            self._generate_summary_by_partner(sale_orders, pos_orders, self.currency_id, company_currency)
        
        if not for_xlsx:
            return self.env.ref('sales_profitability_reports_cross.action_commercial_report').report_action(self)

    def _generate_detailed_product_summary(self, sale_orders, pos_orders, report_currency, company_currency):
        """
        Genera un resumen detallado de productos.
        """
        product_data = {}
        
        if sale_orders:
            for line in sale_orders.mapped('order_line').filtered(lambda l: l.product_id):
                sale_order = line.order_id
                
                converted_sales = sale_order.currency_id._convert(
                    line.price_total, report_currency, self.env.company, sale_order.date_order
                )
                converted_margin = sale_order.currency_id._convert(
                    line.margin, report_currency, self.env.company, sale_order.date_order
                )

                product_id = line.product_id.id
                if product_id not in product_data:
                    product_data[product_id] = {'qty': 0.0, 'sales': 0.0, 'margin': 0.0, 'sources': set()}
                product_data[product_id]['qty'] = float_round(product_data[product_id]['qty'] + line.product_uom_qty, precision_digits=0)
                product_data[product_id]['sales'] = float_round(product_data[product_id]['sales'] + converted_sales, precision_rounding=report_currency.rounding)
                product_data[product_id]['margin'] = float_round(product_data[product_id]['margin'] + converted_margin, precision_rounding=report_currency.rounding)
                product_data[product_id]['sources'].add('Cotizaciones')

        if pos_orders:
            for line in pos_orders.mapped('lines').filtered(lambda l: l.product_id):
                pos_order = line.order_id
                
                # 1. Ventas: Convertir price_subtotal_incl
                converted_sales = pos_order.currency_id._convert(
                    line.price_subtotal_incl, report_currency, self.env.company, pos_order.date_order
                )

                # 2. Margen: Usar el campo 'margin' almacenado en la línea y convertirlo a la moneda del reporte.
                converted_pos_line_margin = pos_order.currency_id._convert(
                    line.margin, report_currency, self.env.company, pos_order.date_order
                )
                converted_pos_line_margin = float_round(converted_pos_line_margin, precision_rounding=report_currency.rounding)

                product_id = line.product_id.id
                if product_id not in product_data:
                    product_data[product_id] = {'qty': 0.0, 'sales': 0.0, 'margin': 0.0, 'sources': set()}
                
                product_data[product_id]['qty'] = float_round(product_data[product_id]['qty'] + line.qty, precision_digits=0)
                product_data[product_id]['sales'] = float_round(product_data[product_id]['sales'] + converted_sales, precision_rounding=report_currency.rounding)
                product_data[product_id]['margin'] = float_round(product_data[product_id]['margin'] + converted_pos_line_margin, precision_rounding=report_currency.rounding)
                product_data[product_id]['sources'].add('Punto de Venta')

        product_lines = []
        for product_id, data in product_data.items():
            source_str = "Mixto"
            if len(data['sources']) == 1:
                source_str = list(data['sources'])[0]

            product_lines.append((0, 0, {
                'product_id': product_id,
                'quantity_sold': data['qty'],
                'total_sales': data['sales'],
                'total_margin': data['margin'],
                'source': source_str,
            }))
        self.product_summary = product_lines

    def _generate_summary_by_user(self, sale_orders, pos_orders, report_currency, company_currency):
        """
        Combina datos de Sale Orders y PoS Orders para agregarlos por comercial.
        """
        user_data = {}

        if sale_orders:
            for order in sale_orders:
                user_id = order.user_id.id if order.user_id else False
                if user_id not in user_data:
                    user_data[user_id] = {'sales': 0.0, 'margin': 0.0, 'sources': set()}
                
                converted_sales = order.currency_id._convert(
                    order.amount_total, report_currency, self.env.company, order.date_order
                )
                converted_margin = order.currency_id._convert(
                    order.margin, report_currency, self.env.company, order.date_order
                )
                
                user_data[user_id]['sales'] = float_round(user_data[user_id]['sales'] + converted_sales, precision_rounding=report_currency.rounding)
                user_data[user_id]['margin'] = float_round(user_data[user_id]['margin'] + converted_margin, precision_rounding=report_currency.rounding)
                user_data[user_id]['sources'].add('Cotizaciones')

        if pos_orders:
            for order in pos_orders:
                user_id = order.user_id.id if order.user_id else False
                if user_id not in user_data:
                    user_data[user_id] = {'sales': 0.0, 'margin': 0.0, 'sources': set()}
                
                converted_sales = order.currency_id._convert(
                    order.amount_total, report_currency, self.env.company, order.date_order
                )
                user_data[user_id]['sales'] = float_round(user_data[user_id]['sales'] + converted_sales, precision_rounding=report_currency.rounding)
                user_data[user_id]['sources'].add('Punto de Venta')

                total_margin_in_pos_currency = sum(order.lines.mapped('margin'))
                
                converted_pos_margin = order.currency_id._convert(
                    total_margin_in_pos_currency, report_currency, self.env.company, order.date_order
                )
                
                user_data[user_id]['margin'] = float_round(user_data[user_id]['margin'] + converted_pos_margin, precision_rounding=report_currency.rounding)

        summary_lines = []
        for user_id, data in user_data.items():
            source_str = "Mixto"
            if len(data['sources']) == 1:
                source_str = list(data['sources'])[0]

            summary_lines.append((0, 0, {
                'user_id': user_id,
                'total_sales': data['sales'],
                'total_margin': data['margin'],
                'source': source_str,
            }))
        self.sales_summary = summary_lines

    def _generate_summary_by_partner(self, sale_orders, pos_orders, report_currency, company_currency):
        """
        Genera un resumen por cliente.
        """
        partner_data = {}

        if sale_orders:
            for order in sale_orders:
                partner_id = order.partner_id.id if order.partner_id else False
                if partner_id not in partner_data:
                    partner_data[partner_id] = {'sales': 0.0, 'margin': 0.0, 'sources': set()}
                
                converted_sales = order.currency_id._convert(
                    order.amount_total, report_currency, self.env.company, order.date_order
                )
                converted_margin = order.currency_id._convert(
                    order.margin, report_currency, self.env.company, order.date_order
                )
                
                partner_data[partner_id]['sales'] = float_round(partner_data[partner_id]['sales'] + converted_sales, precision_rounding=report_currency.rounding)
                partner_data[partner_id]['margin'] = float_round(partner_data[partner_id]['margin'] + converted_margin, precision_rounding=report_currency.rounding)
                partner_data[partner_id]['sources'].add('Cotizaciones')

        if pos_orders:
            for order in pos_orders:
                partner_id = order.partner_id.id if order.partner_id else False
                if partner_id not in partner_data:
                    partner_data[partner_id] = {'sales': 0.0, 'margin': 0.0, 'sources': set()}
                
                converted_sales = order.currency_id._convert(
                    order.amount_total, report_currency, self.env.company, order.date_order
                )
                partner_data[partner_id]['sales'] = float_round(partner_data[partner_id]['sales'] + converted_sales, precision_rounding=report_currency.rounding)
                partner_data[partner_id]['sources'].add('Punto de Venta')

                total_margin_in_pos_currency = sum(order.lines.mapped('margin'))
                
                converted_pos_margin = order.currency_id._convert(
                    total_margin_in_pos_currency, report_currency, self.env.company, order.date_order
                )

                partner_data[partner_id]['margin'] = float_round(partner_data[partner_id]['margin'] + converted_pos_margin, precision_rounding=report_currency.rounding)

        partner_lines = []
        for partner_id, data in partner_data.items():
            source_str = "Mixto"
            if len(data['sources']) == 1:
                source_str = list(data['sources'])[0]

            partner_lines.append((0, 0, {
                'partner_id': partner_id,
                'total_sales': data['sales'],
                'total_margin': data['margin'],
                'source': source_str,
            }))
        self.partner_summary = partner_lines

    def _clear_fields(self):
        self.sales_ids = [(5, 0, 0)]
        self.pos_order_ids = [(5, 0, 0)]
        self.sales_summary.unlink()
        self.product_summary.unlink()
        self.partner_summary.unlink()

    def action_generate_xlsx_report(self):
        self.open_query_result(for_xlsx=True)

        if not self.sales_ids and not self.pos_order_ids:
            raise UserError(f'No hay datos para generar el reporte.')
        
        with BytesIO() as output:
            workbook = xlsxwriter.Workbook(output, {'in_memory': True})

            report_currency = self.currency_id 

            if self.options == 'summary':
                self._write_summary_sheet_to_xlsx(workbook, report_currency)
            elif self.options == 'product':
                self._write_product_sheet_to_xlsx(workbook, report_currency)
            elif self.options == 'partner':
                self._write_partner_sheet_to_xlsx(workbook, report_currency)
            
            workbook.close()
            xlsx_data = output.getvalue()

        report_type = 'Rentabilidad' if self.show_profitability else 'Ventas'
        report_name = f"Reporte {report_type} {self.options.capitalize()} {self.date_from.strftime('%d-%m-%Y')} al {self.date_until.strftime('%d-%m-%Y')}.xlsx"
        
        attachment = self.env['ir.attachment'].create({
            'name': report_name,
            'type': 'binary',
            'datas': base64.b64encode(xlsx_data),
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'res_model': self._name,
            'res_id': self.id,
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }

    def _write_summary_sheet_to_xlsx(self, workbook, report_currency):
        sheet = workbook.add_worksheet('Resumen por Comercial')
        bold = workbook.add_format({'bold': True, 'align': 'center'})
        header_format = workbook.add_format({'bold': True, 'bg_color': '#A9A9A9', 'align': 'center'})

        currency_symbol = report_currency.symbol
        currency_position = report_currency.position
        decimal_places = report_currency.decimal_places if hasattr(report_currency, 'decimal_places') else 2
        decimal_part = f".{'0' * decimal_places}" if decimal_places > 0 else ""

        if currency_position == 'before':
            xlsx_money_format_str = f'"{currency_symbol}"#,##0{decimal_part}'
        else:
            xlsx_money_format_str = f'#,##0{decimal_part}"{currency_symbol}"'

        money_format = workbook.add_format({'num_format': xlsx_money_format_str})
        money_format_bold = workbook.add_format({'num_format': xlsx_money_format_str, 'bold': True})
        percent_format = workbook.add_format({'num_format': '0.00"%"'})
        
        add_source_column = self.sale_report and self.pos_report

        col_offset = 1 if add_source_column else 0

        sheet.merge_range(0, 0, 0, (3 + col_offset) if self.show_profitability else (1 + col_offset), 'Reporte de Rentabilidad por Comercial' if self.show_profitability else 'Reporte de Ventas por Comercial', bold)
        sheet.merge_range(1, 0, 1, (3 + col_offset) if self.show_profitability else (1 + col_offset), f' Del {self.date_from.strftime('%d-%m-%Y')} al {self.date_until.strftime('%d-%m-%Y')}', bold)
        
        headers_base = ['Comercial']
        if add_source_column:
            headers_base.append('Origen')

        if self.show_profitability:
            headers_base.extend(['Total Ventas', 'Ganancia Bruta', 'Margen %'])
        else:
            headers_base.append('Total Ventas')
        
        sheet.write_row('A3', headers_base, header_format)
        
        row = 3
        for line in self.sales_summary:
            col = 0
            sheet.write(row, col, line.user_id.name or 'Sin Comercial')
            col += 1
            if add_source_column:
                sheet.write(row, col, line.source)
                col += 1
            
            sheet.write(row, col, line.total_sales, money_format)
            col += 1
            if self.show_profitability:
                sheet.write(row, col, line.total_margin, money_format)
                col += 1
                sheet.write(row, col, line.margin_percent, percent_format)
            row += 1

        sheet.set_column('A:A', 30)
        if add_source_column:
            sheet.set_column('B:B', 15)
            sheet.set_column('C:E', 18)
        else:
            sheet.set_column('B:D', 18)

    def _write_product_sheet_to_xlsx(self, workbook, report_currency):
        sheet_name = 'Resumen por Producto'
        report_title = 'Reporte de Rentabilidad por Producto' if self.show_profitability else 'Reporte de Ventas por Producto'

        sheet = workbook.add_worksheet(sheet_name)
        
        bold = workbook.add_format({'bold': True, 'align': 'center'})
        header_format = workbook.add_format({'bold': True, 'bg_color': '#A9A9A9', 'align': 'center'})
        
        currency_symbol = report_currency.symbol
        currency_position = report_currency.position
        # Usar la precisión de la moneda del reporte, si no, por defecto 2
        decimal_places = report_currency.decimal_places if hasattr(report_currency, 'decimal_places') else 2
        decimal_part = f".{'0' * decimal_places}" if decimal_places > 0 else ""

        if currency_position == 'before':
            xlsx_money_format_str = f'"{currency_symbol}"#,##0{decimal_part}'
        else:
            xlsx_money_format_str = f'#,##0{decimal_part}"{currency_symbol}"'


        money_format = workbook.add_format({'num_format': xlsx_money_format_str})
        money_format_bold = workbook.add_format({'num_format': xlsx_money_format_str, 'bold': True})
        percent_format = workbook.add_format({'num_format': '0.00"%"'})

        add_source_column = self.sale_report and self.pos_report

        col_offset = 1 if add_source_column else 0
        
        num_profit_cols = 11 + col_offset
        num_sales_cols = 5 + col_offset

        sheet.merge_range(0, 0, 0, num_profit_cols - 1 if self.show_profitability else num_sales_cols - 1, report_title, bold)
        sheet.merge_range(1, 0, 1, num_profit_cols - 1 if self.show_profitability else num_sales_cols - 1, f'Del {self.date_from.strftime("%d-%m-%Y")} al {self.date_until.strftime("%d-%m-%Y")}', bold)
        
        headers_profit_base = ['Ref.Interna', 'Producto', 'Categoria']
        headers_sales_base = ['Ref.Interna', 'Producto', 'Categoria']

        if add_source_column:
            headers_profit_base.append('Origen')
            headers_sales_base.append('Origen')

        headers_profit_base.extend(['Cantidad', 'Costo Unit.', 'Costo Total', 'Precio Unit.', 'Precio Total', 'Ganancia Bruta', '%M/S Venta', '%M/S Costo'])
        headers_sales_base.extend(['Cantidad', 'Precio Total'])
        
        headers = headers_profit_base if self.show_profitability else headers_sales_base
        sheet.write_row('A4', headers, header_format)
        
        row = 4
        for line in self.product_summary:
            col = 0
            sheet.write(row, col, line.product_id.default_code or '')
            col += 1
            sheet.write(row, col, line.product_id.name)
            col += 1
            sheet.write(row, col, line.product_id.categ_id.name if line.product_id.categ_id else '')
            col += 1
            
            if add_source_column:
                sheet.write(row, col, line.source)
                col += 1
            
            sheet.write(row, col, line.quantity_sold)
            col += 1
            
            if self.show_profitability:
                sheet.write(row, col, line.average_cost, money_format)
                col += 1
                sheet.write(row, col, line.total_cost, money_format)
                col += 1
                sheet.write(row, col, line.unit_price, money_format)
                col += 1
                sheet.write(row, col, line.total_sales, money_format)
                col += 1
                sheet.write(row, col, line.total_margin, money_format)
                col += 1
                sheet.write(row, col, line.margin_percent, percent_format)
                col += 1
                sheet.write(row, col, line.percentage_profit_cost, percent_format)
            else:
                sheet.write(row, col, line.total_sales, money_format)
                
            row += 1
        
        row += 1 
        sheet.write(row, 0, 'Total General', bold)
        
        # Ajustamos las columnas para las fórmulas SUMA
        col_qty_sold = 3 + col_offset
        col_total_cost = 5 + col_offset
        col_total_sales_index = 7 + col_offset
        col_total_margin = 8 + col_offset
        col_margin_perc = 9 + col_offset
        col_profit_cost_perc = 10 + col_offset

        if self.show_profitability:
            sheet.write_formula(row, col_qty_sold, f'=SUM({xlsxwriter.utility.xl_col_to_name(col_qty_sold)}{4+1}:{xlsxwriter.utility.xl_col_to_name(col_qty_sold)}{row-1})', money_format_bold)
            sheet.write_formula(row, col_total_cost, f'=SUM({xlsxwriter.utility.xl_col_to_name(col_total_cost)}{4+1}:{xlsxwriter.utility.xl_col_to_name(col_total_cost)}{row-1})', money_format_bold)
            sheet.write_formula(row, col_total_sales_index, f'=SUM({xlsxwriter.utility.xl_col_to_name(col_total_sales_index)}{4+1}:{xlsxwriter.utility.xl_col_to_name(col_total_sales_index)}{row-1})', money_format_bold)
            sheet.write_formula(row, col_total_margin, f'=SUM({xlsxwriter.utility.xl_col_to_name(col_total_margin)}{4+1}:{xlsxwriter.utility.xl_col_to_name(col_total_margin)}{row-1})', money_format_bold)

            total_sales_overall_formula = f'{xlsxwriter.utility.xl_col_to_name(col_total_sales_index)}{row}'
            total_margin_overall_formula = f'{xlsxwriter.utility.xl_col_to_name(col_total_margin)}{row}'
            
            # Usar float_round para la comparación en la fórmula de Excel para evitar errores de división por cero
            # debido a la representación de flotantes. Los valores de Odoo tienen una precisión de dos decimales.
            sheet.write_formula(row, col_margin_perc, f'=IF({total_sales_overall_formula}>0, {total_margin_overall_formula}/{total_sales_overall_formula}*100, 0)', percent_format)
            # Para %M/S Costo, el costo es Ventas - Margen. Aseguramos que no sea cero.
            total_cost_overall_formula = f'ROUND({total_sales_overall_formula}-{total_margin_overall_formula},{report_currency.decimal_places})'
            sheet.write_formula(row, col_profit_cost_perc, f'=IF({total_cost_overall_formula}>0, {total_margin_overall_formula}/{total_cost_overall_formula}*100, 0)', percent_format)
        else:
            sheet.write_formula(row, col_total_sales_index, f'=SUM({xlsxwriter.utility.xl_col_to_name(col_total_sales_index)}{4+1}:{xlsxwriter.utility.xl_col_to_name(col_total_sales_index)}{row-1})', money_format_bold)

        sheet.set_column('A:A', 15)
        sheet.set_column('B:B', 50)
        sheet.set_column('C:C', 15)
        if add_source_column: 
            sheet.set_column('D:D', 12)
            sheet.set_column('E:L', 15)
        else:
            sheet.set_column('D:K', 15)

    def _write_partner_sheet_to_xlsx(self, workbook, report_currency):
        sheet = workbook.add_worksheet('Resumen por Cliente')
        bold = workbook.add_format({'bold': True, 'align': 'center'})
        header_format = workbook.add_format({'bold': True, 'bg_color': '#A9A9A9', 'align': 'center'})
        
        currency_symbol = report_currency.symbol
        currency_position = report_currency.position
        decimal_places = report_currency.decimal_places if hasattr(report_currency, 'decimal_places') else 2
        decimal_part = f".{'0' * decimal_places}" if decimal_places > 0 else ""

        if currency_position == 'before':
            xlsx_money_format_str = f'"{currency_symbol}"#,##0{decimal_part}'
        else:
            xlsx_money_format_str = f'#,##0{decimal_part}"{currency_symbol}"'

        money_format = workbook.add_format({'num_format': xlsx_money_format_str})
        percent_format = workbook.add_format({'num_format': '0.00"%"'})
        
        add_source_column = self.sale_report and self.pos_report

        col_offset = 1 if add_source_column else 0

        sheet.merge_range(0, 0, 0, (3 + col_offset) if self.show_profitability else (1 + col_offset), 'Reporte de Rentabilidad por Cliente' if self.show_profitability else 'Reporte de Ventas por Cliente', bold)
        sheet.merge_range(1, 0, 1, (3 + col_offset) if self.show_profitability else (1 + col_offset), f' Del {self.date_from.strftime('%d-%m-%Y')} al {self.date_until.strftime('%d-%m-%Y')}', bold)
        
        headers_base = ['Cliente']
        if add_source_column:
            headers_base.append('Origen')

        if self.show_profitability:
            headers_base.extend(['Total Ventas', 'Ganancia Bruta', 'Margen %'])
        else:
            headers_base.append('Total Ventas')

        sheet.write_row('A3', headers_base, header_format)
        
        row = 3
        for line in self.partner_summary:
            col = 0
            sheet.write(row, col, line.partner_id.name or 'Sin Cliente')
            col += 1
            if add_source_column:
                sheet.write(row, col, line.source)
                col += 1
            
            sheet.write(row, col, line.total_sales, money_format)
            col += 1
            if self.show_profitability:
                sheet.write(row, col, line.total_margin, money_format)
                col += 1
                sheet.write(row, col, line.margin_percent, percent_format)
            row += 1

        sheet.set_column('A:A', 30)
        if add_source_column:
            sheet.set_column('B:B', 15)
            sheet.set_column('C:E', 18)
        else:
            sheet.set_column('B:D', 18)


class SalesSummaryLine(models.TransientModel):
    _name = 'sales.summary.line'
    _description = 'Línea de Resumen de Ventas por Comercial'

    wizard_id = fields.Many2one('report.date.range.wizard', string='Wizard')
    user_id = fields.Many2one('res.users', string='Comercial')
    total_sales = fields.Float(string='Total Ventas (sin IVA)', digits='Product Price')
    total_margin = fields.Float(string='Ganancia Bruta', digits='Product Price')
    margin_percent = fields.Float(string='Margen %', compute='_compute_margin_percent', digits=(16, 2))
    source = fields.Char(string='Origen', help="Indica si los datos provienen de Cotizaciones, Punto de Venta o son Mixtos.")

    @api.depends('total_sales', 'total_margin')
    def _compute_margin_percent(self):
        for line in self:
            report_currency = line.wizard_id.currency_id or self.env.company.currency_id
            # Usar float_round con precision_rounding de la moneda para la comparación
            if float_round(line.total_sales, precision_rounding=report_currency.rounding) != 0:
                line.margin_percent = (line.total_margin / line.total_sales) * 100
            else:
                line.margin_percent = 0.0

    
class ProductSummaryLine(models.TransientModel):
    _name = 'product.summary.line'
    _description = 'Línea de Resumen de Ventas por Producto'

    wizard_id = fields.Many2one('report.date.range.wizard', string='Wizard')
    product_id = fields.Many2one('product.product', string='Producto')
    quantity_sold = fields.Float(string='Cantidad Vendida', digits='Product Unit of Measure')
    total_sales = fields.Float(string='Total Ventas (sin IVA)', digits='Product Price')
    total_margin = fields.Float(string='Ganancia Bruta', digits='Product Price')
    margin_percent = fields.Float(string='%M/S Venta', compute='_compute_margin_percent', digits=(16, 2))
    percentage_profit_cost = fields.Float(string='%M/S Costo', compute='_compute_percentage_profit_cost', digits=(16, 2))
    total_cost = fields.Float(string="Costo Total", compute='_compute_total_cost', digits='Product Price')
    unit_price = fields.Float(string="Precio Unit.", compute='_compute_unit_price', digits='Product Price')
    average_cost = fields.Float(string='Costo Unit. Promedio', compute='_compute_average_cost', digits='Product Price')
    source = fields.Char(string='Origen', help="Indica si los datos provienen de Cotizaciones, Punto de Venta o son Mixtos.")

    @api.depends('quantity_sold', 'average_cost')
    def _compute_total_cost(self):
        for record in self:
            report_currency = record.wizard_id.currency_id or self.env.company.currency_id
            record.total_cost = float_round(record.average_cost * record.quantity_sold, precision_rounding=report_currency.rounding)

    @api.depends('total_sales', 'quantity_sold')
    def _compute_unit_price(self):
        for record in self:
            # Obtener la precisión de las unidades de medida.
            # Esto busca la precisión definida para "Product Unit of Measure"
            uom_precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')

            if float_round(record.quantity_sold, precision_digits=uom_precision) != 0:
                # El resultado de la división también debe redondearse a la precisión de la moneda
                report_currency = record.wizard_id.currency_id or self.env.company.currency_id
                record.unit_price = float_round(record.total_sales / record.quantity_sold, precision_rounding=report_currency.rounding)
            else:
                record.unit_price = 0.0

    @api.depends('total_sales', 'total_margin', 'quantity_sold')
    def _compute_average_cost(self):
        for line in self:
            report_currency = line.wizard_id.currency_id or self.env.company.currency_id
            total_cost_calc = float_round(line.total_sales - line.total_margin, precision_rounding=report_currency.rounding)
            
            # Obtener la precisión de las unidades de medida.
            # Esto busca la precisión definida para "Product Unit of Measure"
            uom_precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            
            if float_round(line.quantity_sold, precision_digits=uom_precision) != 0:
                line.average_cost = float_round(total_cost_calc / line.quantity_sold, precision_rounding=report_currency.rounding)
            else:
                line.average_cost = 0.0

    @api.depends('total_sales', 'total_margin')
    def _compute_margin_percent(self):
        for line in self:
            report_currency = line.wizard_id.currency_id or self.env.company.currency_id
            if float_round(line.total_sales, precision_rounding=report_currency.rounding) != 0:
                line.margin_percent = (line.total_margin / line.total_sales) * 100
            else:
                line.margin_percent = 0.0
    
    @api.depends('total_margin', 'total_sales', 'quantity_sold')
    def _compute_percentage_profit_cost(self):
        for record in self:
            report_currency = record.wizard_id.currency_id or self.env.company.currency_id
            total_cost = float_round(record.total_sales - record.total_margin, precision_rounding=report_currency.rounding)
            if total_cost != 0:
                record.percentage_profit_cost = (record.total_margin / total_cost) * 100
            else:
                record.percentage_profit_cost = 0.0


class PartnerSummaryLine(models.TransientModel):
    _name = 'partner.summary.line'
    _description = 'Línea de Resumen de Ventas por Cliente'

    wizard_id = fields.Many2one('report.date.range.wizard', string='Wizard')
    partner_id = fields.Many2one('res.partner', string='Cliente')
    total_sales = fields.Float(string='Total Ventas (sin IVA)', digits='Product Price')
    total_margin = fields.Float(string='Ganancia Bruta', digits='Product Price')
    margin_percent = fields.Float(string='Margen %', compute='_compute_margin_percent', digits=(16, 2))
    source = fields.Char(string='Origen', help="Indica si los datos provienen de Cotizaciones, Punto de Venta o son Mixtos.") # Nuevo campo

    @api.depends('total_sales', 'total_margin')
    def _compute_margin_percent(self):
        for line in self:
            report_currency = line.wizard_id.currency_id or self.env.company.currency_id
            if float_round(line.total_sales, precision_rounding=report_currency.rounding) != 0:
                line.margin_percent = (line.total_margin / line.total_sales) * 100
            else:
                line.margin_percent = 0.0
