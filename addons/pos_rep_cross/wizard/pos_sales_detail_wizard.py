from odoo import models, fields, api, _

class PosSalesReportWizard(models.TransientModel):
    _name = 'pos.sales.report.wizard'
    _description = 'POS Sales Report Wizard'

    date_from = fields.Datetime(string='Fecha Desde', required=True, default=fields.Datetime.now)
    date_to = fields.Datetime(string='Fecha Hasta', required=True, default=fields.Datetime.now)
    pos_config_ids = fields.Many2many('pos.config', string='Puntos de Venta')
    session_ids = fields.Many2many('pos.session', string='Sesiones')
    user_ids = fields.Many2many('res.users', string='Cajeros')
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('cancel', 'Cancelado'),
        ('paid', 'Pagado'),
        ('done', 'Publicado'),
        ('invoiced', 'Facturado'),
    ], string='Estado de Orden')

    csv_file = fields.Binary(string='Archivo CSV', readonly=True)
    csv_filename = fields.Char(string='Archivo CSV', readonly=True)
    excel_file = fields.Binary(string='Archivo Excel', readonly=True)
    excel_filename = fields.Char(string='Archivo Excel', readonly=True)

    def action_generate_report_pdf(self):
        self.ensure_one()
        report = self.env.ref('pos_rep_cross.action_report_pdf')
        return {
            'type': 'ir.actions.report',
            'report_name': report.report_name,
            'report_type': report.report_type,
            'report_file': report.report_file,
            'context': dict(self._context, active_id=self.id, active_ids=self.ids),
            'display_name': report.name,
        }

    def action_generate_report_xlsx(self):
        import io
        import base64
        import xlsxwriter
        self.ensure_one()
        
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('Detalle de Ventas')
        
        # Formats
        header_format = workbook.add_format({
            'bold': True, 'bg_color': '#BDD7EE', 'font_color': 'black', 'border': 1, 'align': 'center'
        })
        date_format = workbook.add_format({'num_format': 'dd/mm/yyyy hh:mm', 'border': 1})
        money_format = workbook.add_format({'num_format': '#,##0.00', 'border': 1})
        text_format = workbook.add_format({'border': 1})
        total_format = workbook.add_format({'bold': True, 'bg_color': '#D9E1F2', 'border': 1, 'num_format': '#,##0.00'})
        
        # Columns
        headers = ['Fecha', 'Orden', 'Referencia POS', 'Cliente', 'Cajero', 'Categoría', 'Ref. Interna', 'Código Barra', 'Producto', 'Lote/Serie', 'Cantidad', 'Unidad', 'Precio Unit.', 'Subtotal', 'Costo Total', 'Margen', 'Margen (%)']
        for col, header in enumerate(headers):
            sheet.write(0, col, header, header_format)
            
        sheet.set_column('A:A', 18) # Fecha
        sheet.set_column('B:C', 20) # Orden, Ref
        sheet.set_column('D:E', 15) # Cliente, Cajero
        sheet.set_column('F:H', 15) # Categoría, Ref Int, Código Barra
        sheet.set_column('I:I', 25) # Producto
        sheet.set_column('J:Q', 12) # Otros
        
        row = 1
        total_qty = 0
        total_subtotal = 0
        total_cost = 0
        total_margin = 0
        
        report_data = self._get_report_data()
        for order in report_data:
            for line in order['lines']:
                margin = line['price_total'] - line['cost_total']
                margin_percent = (margin / line['price_total'] if line['price_total'] != 0 else 0)
                
                sheet.write_datetime(row, 0, order['date'].replace(tzinfo=None) if order['date'] else "", date_format)
                sheet.write(row, 1, order['name'], text_format)
                sheet.write(row, 2, order['pos_ref'], text_format)
                sheet.write(row, 3, order['partner'], text_format)
                sheet.write(row, 4, order['user'], text_format)
                sheet.write(row, 5, line['category'], text_format)
                sheet.write(row, 6, line['default_code'], text_format)
                sheet.write(row, 7, line['barcode'], text_format)
                sheet.write(row, 8, line['product'], text_format)
                sheet.write(row, 9, line['lots'], text_format)
                sheet.write(row, 10, line['qty'], money_format)
                sheet.write(row, 11, line['uom'], text_format)
                sheet.write(row, 12, line['price_unit'], money_format)
                sheet.write(row, 13, line['price_total'], money_format)
                sheet.write(row, 14, line['cost_total'], money_format)
                sheet.write(row, 15, margin, money_format)
                sheet.write(row, 16, margin_percent, workbook.add_format({'num_format': '0.00%', 'border': 1}))
                
                total_qty += line['qty']
                total_subtotal += line['price_total']
                total_cost += line['cost_total']
                total_margin += margin
                row += 1
                
        # Total Row
        sheet.write(row, 9, 'TOTALES:', workbook.add_format({'bold': True, 'border': 1}))
        sheet.write(row, 10, total_qty, total_format)
        sheet.write(row, 13, total_subtotal, total_format)
        sheet.write(row, 14, total_cost, total_format)
        sheet.write(row, 15, total_margin, total_format)
        
        total_margin_percent = (total_margin / total_subtotal if total_subtotal != 0 else 0)
        sheet.write(row, 16, total_margin_percent, workbook.add_format({'bold': True, 'bg_color': '#D9E1F2', 'border': 1, 'num_format': '0.00%'}))
        
        workbook.close()
        self.excel_file = base64.b64encode(output.getvalue())
        self.excel_filename = f"reporte_ventas_profesional_{fields.Date.today()}.xlsx"
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'pos.sales.report.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_generate_report_csv(self):
        import csv
        import io
        import base64
        self.ensure_one()
        
        output = io.StringIO()
        writer = csv.writer(output, delimiter=';', quotechar='\"', quoting=csv.QUOTE_MINIMAL)
        
        # Headers
        writer.writerow(['Fecha', 'Orden', 'Referencia POS', 'Cliente', 'Cajero', 'Categoría', 'Ref. Interna', 'Código Barra', 'Producto', 'Lote/Serie', 'Cantidad', 'Unidad', 'Precio Unit.', 'Subtotal', 'Costo Total', 'Margen', 'Margen (%)'])
        
        report_data = self._get_report_data()
        for order in report_data:
            for line in order['lines']:
                # Calculate margin
                margin = line['price_total'] - line['cost_total']
                margin_percent = (margin / line['price_total'] * 100) if line['price_total'] != 0 else 0
                
                writer.writerow([
                    order['date'],
                    order['name'],
                    order['pos_ref'],
                    order['partner'],
                    order['user'],
                    line['category'],
                    line['default_code'],
                    line['barcode'],
                    line['product'],
                    line['lots'],
                    line['qty'],
                    line['uom'],
                    line['price_unit'],
                    line['price_total'],
                    round(line['cost_total'], 2),
                    round(margin, 2),
                    f"{round(margin_percent, 2)} %"
                ])
                
        self.csv_file = base64.b64encode(output.getvalue().encode('utf-8'))
        self.csv_filename = f"reporte_ventas_rentabilidad_{fields.Date.today()}.csv"
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'pos.sales.report.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def _get_orders_domain(self):
        domain = [
            ('date_order', '>=', self.date_from),
            ('date_order', '<=', self.date_to)
        ]
        if self.pos_config_ids:
            domain.append(('config_id', 'in', self.pos_config_ids.ids))
        if self.session_ids:
            domain.append(('session_id', 'in', self.session_ids.ids))
        if self.user_ids:
            domain.append(('user_id', 'in', self.user_ids.ids))
        if self.state:
            domain.append(('state', '=', self.state))
        return domain

    def _get_report_data(self):
        domain = self._get_orders_domain()
        orders = self.env['pos.order'].search(domain, order='date_order asc, name asc')
        
        report_data = []
        for order in orders:
            order_info = {
                'name': order.name,
                'session': order.session_id.name,
                'date': order.date_order,
                'config': order.config_id.name,
                'pos_ref': order.pos_reference,
                'partner': order.partner_id.name if order.partner_id else _('Consumidor Final'),
                'user': order.user_id.name,
                'state': dict(order._fields['state'].selection).get(order.state, order.state),
                'amount_total': order.amount_total,
                'lines': [],
                'payments': [],
            }
            
            for line in order.lines:
                cost_unit = line.product_id.standard_price
                cost_total = cost_unit * line.qty
                lots = ", ".join(line.pack_lot_ids.mapped('lot_name')) if line.pack_lot_ids else ""
                order_info['lines'].append({
                    'category': line.product_id.categ_id.name or '',
                    'default_code': line.product_id.default_code or '',
                    'barcode': line.product_id.barcode or '',
                    'product': line.product_id.name,
                    'lots': lots,
                    'qty': line.qty,
                    'uom': line.product_uom_id.name,
                    'price_unit': line.price_unit,
                    'cost_unit': cost_unit,
                    'cost_total': cost_total,
                    'discount': line.discount,
                    'taxes': ", ".join(line.tax_ids_after_fiscal_position.mapped('name')),
                    'price_subtotal': line.price_subtotal,
                    'price_total': line.price_subtotal_incl,
                })
            
            for payment in order.payment_ids:
                order_info['payments'].append({
                    'date': payment.payment_date,
                    'method': payment.payment_method_id.name,
                    'amount': payment.amount,
                })
                
            report_data.append(order_info)
            
        return report_data
