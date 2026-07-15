# -*- coding: utf-8 -*-
"""
Created on 2025-06-02 07:53:47

@author: drojo
"""
# python
import base64
import io
import logging
from io import BytesIO

try:
    import pandas as pd
except ImportError:
    logging.getLogger(__name__).warning("La biblioteca 'pandas' no está instalada. Instálela para usar la función de importación de Excel.")
    pd = None

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter

# odoo
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class PurchaseOrderImportWizard(models.TransientModel):
    _name = 'purchase.order.import.wizard'
    _description = 'Wizard to import purchase order lines from Excel'

    purchase_order_id = fields.Many2one(
        'purchase.order', string='Orden de Compra', required=True, ondelete='cascade')
    excel_file = fields.Binary(
        string='Archivo Excel')
    file_name = fields.Char(
        string='Nombre del Archivo')

    def action_import_lines(self):
        self.ensure_one()

        if not pd:
            raise UserError(_("La librería 'pandas' no está instalada en el servidor. Por favor, contacte a su administrador."))

        if not self.excel_file:
            raise UserError(_("Por favor, suba un archivo Excel."))

        try:
            # Decodificar el archivo base64
            file_content = base64.b64decode(self.excel_file)
            # Leer el archivo Excel usando pandas
            df = pd.read_excel(io.BytesIO(file_content))
        except Exception as e:
            raise UserError(_("Error al leer el archivo Excel. Asegúrese de que es un archivo Excel válido. Detalle: %s") % e)

        required_columns = [
            'REFERENCIA INTERNA',
            'PRODUCTO', 
            'CANTIDAD',
            'PRECIO UNITARIO',
        ]

        if not all(col in df.columns for col in required_columns):
            missing_cols = [col for col in required_columns if col not in df.columns]
            raise UserError(_("El archivo Excel debe contener las siguientes columnas: %s. Faltan: %s") % (", ".join(required_columns), ", ".join(missing_cols)))

        ProductProduct = self.env['product.product']
        PurchaseOrderLine = self.env['purchase.order.line']
        productos_no_encontrados = []

        for index, row in df.iterrows():
            ref_interna = self.clean_ref(row['REFERENCIA INTERNA']) if pd.notna(row['REFERENCIA INTERNA']) else False
            nombre_producto = str(row['PRODUCTO']).strip() if pd.notna(row['PRODUCTO']) else False
            cantidad = float(row['CANTIDAD']) if pd.notna(row['CANTIDAD']) else 0.0
            precio_unitario = float(row['PRECIO UNITARIO']) if pd.notna(row['PRECIO UNITARIO']) else 0.0

            # Referencia interna & Nombre del producto
            if not ref_interna:
                raise UserError(f'Fila {index + 2}: Debe proporcionar al menos una Referencia Interna.')

            product = False
            if ref_interna:
                product = ProductProduct.search([('default_code', '=', ref_interna)], limit=1)

            if not product:
                productos_no_encontrados.append(f"Fila {index + 2}: {nombre_producto or ref_interna}")
                continue  # Saltamos esta fila

            existing_line = self.purchase_order_id.order_line.filtered(lambda l: l.product_id == product)
            if existing_line:
                existing_line.write({
                    'product_qty': existing_line.product_qty + cantidad,
                    'price_unit': precio_unitario,
                })
            else:
                line_vals = {
                    'order_id': self.purchase_order_id.id,
                    'product_id': product.id,
                    'name': product.name,
                    'product_qty': cantidad,
                    'price_unit': precio_unitario,
                    'product_uom': product.uom_po_id.id,
                    'date_planned': fields.Date.today(),
                }
                PurchaseOrderLine.create(line_vals)

        if productos_no_encontrados:
            raise UserError(_(
                "Los siguientes productos no se encontraron:\n%s"
            ) % "\n".join(productos_no_encontrados))

        return {'type': 'ir.actions.act_window_close'}

    def action_download_template(self):
        """
        Método para descargar una plantilla de Excel para la importación de órdenes de compra.
        """
        # Crear un DataFrame vacío con las columnas requeridas
        with BytesIO() as output:
            workbook = xlsxwriter.Workbook(output, {'in_memory': True})
            worksheet = workbook.add_worksheet()

            # Define formatos
            header_column = workbook.add_format({'font_name': 'Arial', 'bold': True, 'font_size': 8, 'align': 'center', 'border': 1, 'valign': 'vcenter'})
            data_cells = workbook.add_format({'font_name': 'Arial', 'font_size': 8, 'align': 'left', 'border': 1})

            # Definimos la anchura de las columnas
            worksheet.set_column('A:O', 20)

            # Creamos el encabezado de las columnas
            worksheet.write(0, 0, 'REFERENCIA INTERNA',header_column)
            worksheet.write(0, 1, 'PRODUCTO', header_column)
            worksheet.write(0, 2, 'CANTIDAD',header_column)
            worksheet.write(0, 3, 'PRECIO UNITARIO',header_column)
            
            # Cerramos y preparamos la descarga
            workbook.close()
            output.seek(0)

            xlsx_data = output.read()

        # Asignamos el nombre al reporte
        report_name = _('ImportarProductosEnCompras.xlsx')

        # Devolver el archivo en base64 para la descarga
        attachment = self.env['ir.attachment'].create({
            'name': report_name,
            'type': 'binary',
            'datas': base64.b64encode(xlsx_data),
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        })

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'new',
        }

    def clean_ref(self, value):
        if pd.isna(value):
            return False

        # Si es float entero → quitar .0
        if isinstance(value, float) and value.is_integer():
            return str(int(value))

        # Si es float pero con decimales → remover ceros
        if isinstance(value, float):
            return str(value).rstrip('0').rstrip('.')

        return str(value).strip()
