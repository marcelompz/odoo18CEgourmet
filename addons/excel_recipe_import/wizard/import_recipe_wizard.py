# -*- coding: utf-8 -*-
import base64
import io
import odoo
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

try:
    import pandas as pd
except ImportError:
    pd = None

class ExcelRecipeImportWizard(models.TransientModel):
    _name = 'excel.recipe.import.wizard'
    _description = 'Excel Recipe Import Wizard'

    import_file = fields.Binary('Archivo Excel', required=False)
    import_filename = fields.Char('Nombre del Archivo')
    import_type = fields.Selection([
        ('products', 'Productos'),
        ('mrp_bom', 'BoM de Fabricación'),
        ('pos_bom', 'BoM POS'),
        ('all', 'Todo'),
    ], string='Tipo de Importación', default='all', required=True)

    def action_download_template(self):
        """Descargar la plantilla de importación"""
        """Descargar la plantilla de importación"""
        template_path = 'excel_recipe_import/data/plantilla_importacion.xlsx'
        try:
            with odoo.tools.file_open(template_path, 'rb') as file:
                file_content = file.read()
        except FileNotFoundError:
            # Provide alternative absolute path in case file_open fails
            try:
                import os
                path = os.path.join(os.path.dirname(__file__), '../data/plantilla_importacion.xlsx')
                with open(path, 'rb') as f:
                    file_content = f.read()
            except Exception as e:
                raise UserError(_("No se pudo encontrar el archivo de plantilla."))

        attachment_id = self.env['ir.attachment'].create({
            'name': 'plantilla_importacion.xlsx',
            'type': 'binary',
            'datas': base64.b64encode(file_content),
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'public': True
        })

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment_id.id,
            'target': 'new',
        }

    def action_back_to_launcher(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'mass.import.suite',
            'view_mode': 'form',
            'target': 'current',
        }

    def action_export_missing_pos_bom(self):
        """Exporta productos POS BoM que no tienen lista de materiales configurada"""
        if not pd:
            raise UserError(_("La librería 'pandas' no está instalada."))

        # Buscar productos que deberían tener receta POS BoM
        products = self.env['product.product'].search([('product_tmpl_id.is_pos_bom', '=', True)])
        
        # Buscar cuáles de esos productos ya tienen receta
        boms = self.env['pos.product.bom'].search([('product_id', 'in', products.ids)])
        products_with_bom = boms.mapped('product_id')
        
        # Filtrar los que faltan
        missing_products = products - products_with_bom

        if not missing_products:
            raise UserError(_("¡Genial! Todos los productos marcados como 'POS BoM' ya tienen su receta configurada."))

        data = []
        for p in missing_products:
            data.append({
                'Recipe': p.name,
                'Component': '',
                'Quantity': ''
            })

        df = pd.DataFrame(data)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='POS BoM (Comidas)', index=False)
            
        file_content = output.getvalue()
        
        attachment_id = self.env['ir.attachment'].create({
            'name': 'recetas_faltantes_pos_bom.xlsx',
            'type': 'binary',
            'datas': base64.b64encode(file_content),
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'public': True
        })

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment_id.id,
            'target': 'new',
        }

    def _get_or_create_uom(self, uom_name):
        uom_name = str(uom_name).strip()
        if not uom_name or uom_name.lower() in ['nan', 'none']:
            uom_name = 'Unidades'
        
        # Simple mappings
        mapping = {
            'mililitro': 'ml',
            'gramo': 'g',
            'unidades': 'Units',
            'kilo': 'kg',
            'litro': 'L'
        }
        search_name = mapping.get(uom_name.lower(), uom_name)
        
        uom = self.env['uom.uom'].search([('name', '=ilike', search_name)], limit=1)
        if not uom:
            uom = self.env.ref('uom.product_uom_unit', raise_if_not_found=False)
        return uom

    def _get_or_create_product(self, name, category_name=None, available_in_pos=False, cost=0.0, uom_name='Unidades'):
        if not name or str(name).lower() == 'nan':
            return False
            
        name = str(name).strip()
        product = self.env['product.product'].search([('name', '=', name)], limit=1)
        
        if not product:
            uom = self._get_or_create_uom(uom_name)
            vals = {
                'name': name,
                'detailed_type': 'product', # Almacenable
                'standard_price': cost,
                'uom_id': uom.id if uom else False,
                'available_in_pos': available_in_pos,
            }
            if 'uom_po_id' in self.env['product.product']._fields:
                vals['uom_po_id'] = uom.id if uom else False
            if category_name:
                category = self.env['product.category'].search([('name', '=', category_name)], limit=1)
                if not category:
                    category = self.env['product.category'].create({'name': category_name})
                vals['categ_id'] = category.id
            
            product = self.env['product.product'].create(vals)
            
            if available_in_pos:
                product.product_tmpl_id.is_pos_bom = True
                
        return product

    def action_validate(self):
        if not self.import_file:
            raise UserError(_("Por favor, suba un archivo Excel para validar."))

        if not pd:
            raise UserError(_("La librería 'pandas' no está instalada."))

        file_content = base64.b64decode(self.import_file)
        try:
            xl = pd.ExcelFile(io.BytesIO(file_content))
        except Exception as e:
            raise UserError(_("Formato de archivo inválido. Por favor, suba un archivo Excel (.xlsx). Error: %s") % str(e))

        required_sheets = ['Products', 'MRP BoM (Subproducts)', 'POS BoM (Comidas)']
        missing = [s for s in required_sheets if s not in xl.sheet_names]

        if missing:
            raise UserError(_("Faltan las siguientes hojas en el archivo: %s") % ', '.join(missing))

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Archivo Válido'),
                'message': _("El archivo Excel contiene todas las hojas requeridas: %s") % ', '.join(xl.sheet_names),
                'sticky': False,
                'type': 'success',
            }
        }

    def action_import(self):
        if not self.import_file:
            raise UserError(_("Por favor, suba un archivo Excel para importar."))

        if not pd:
            raise UserError(_("La librería 'pandas' no está instalada."))

        file_content = base64.b64decode(self.import_file)
        try:
            xl = pd.ExcelFile(io.BytesIO(file_content))
        except Exception as e:
            raise UserError(_("Formato de archivo inválido. Por favor, suba un archivo Excel (.xlsx). Error: %s") % str(e))

        # 1. Productos
        if 'Products' in xl.sheet_names:
            df_products = xl.parse('Products')
            for index, row in df_products.iterrows():
                name = row.get('Name')
                if not name or str(name).lower() == 'nan':
                    continue
                cat = row.get('Category')
                available = row.get('Available in POS', False)
                if str(available).lower() in ['true', '1', '1.0', 'yes']:
                    available = True
                else:
                    available = False
                cost = row.get('Cost', 0.0)
                if pd.isna(cost):
                    cost = 0.0
                uom = row.get('UoM', 'Unidades')
                self._get_or_create_product(name, cat, available, cost, uom)

        # 2. MRP BoM (Subproducts)
        if 'MRP BoM (Subproducts)' in xl.sheet_names:
            df_mrp = xl.parse('MRP BoM (Subproducts)')
            for recipe_name, group in df_mrp.groupby('Recipe'):
                if str(recipe_name).lower() == 'nan':
                    continue
                recipe_product = self._get_or_create_product(recipe_name, category_name='Subproducto')
                
                if not recipe_product:
                    continue
                    
                bom = self.env['mrp.bom'].search([('product_tmpl_id', '=', recipe_product.product_tmpl_id.id)], limit=1)
                if not bom:
                    bom = self.env['mrp.bom'].create({
                        'product_tmpl_id': recipe_product.product_tmpl_id.id,
                        'product_qty': 1.0,
                        'type': 'normal',
                    })
                else:
                    bom.bom_line_ids.unlink() # Limpiar existentes
                
                for _, row in group.iterrows():
                    comp_name = row.get('Component')
                    if str(comp_name).lower() == 'nan':
                        continue
                    comp_product = self._get_or_create_product(comp_name, category_name='Materia Prima')
                    if comp_product:
                        qty = row.get('Quantity', 1.0)
                        if pd.isna(qty):
                            qty = 1.0
                        self.env['mrp.bom.line'].create({
                            'bom_id': bom.id,
                            'product_id': comp_product.id,
                            'product_qty': float(qty)
                        })

        # 3. POS BoM (Comidas)
        if 'POS BoM (Comidas)' in xl.sheet_names:
            df_pos = xl.parse('POS BoM (Comidas)')
            for recipe_name, group in df_pos.groupby('Recipe'):
                if str(recipe_name).lower() == 'nan':
                    continue
                recipe_product = self._get_or_create_product(recipe_name, category_name='Productos Manufacturados', available_in_pos=True)
                
                if not recipe_product:
                    continue
                
                # Asegurar que esté marcado como POS BoM
                recipe_product.product_tmpl_id.is_pos_bom = True
                
                bom = self.env['pos.product.bom'].search([('product_id', '=', recipe_product.id)], limit=1)
                if not bom:
                    bom = self.env['pos.product.bom'].create({
                        'product_id': recipe_product.id,
                        'product_qty': 1.0,
                        'product_uom_id': recipe_product.uom_id.id,
                    })
                else:
                    bom.product_bom_line_ids.unlink() # Limpiar existentes
                    
                for _, row in group.iterrows():
                    comp_name = row.get('Component')
                    if str(comp_name).lower() == 'nan':
                        continue
                    comp_product = self._get_or_create_product(comp_name)
                    if comp_product:
                        qty = row.get('Quantity', 1.0)
                        if pd.isna(qty):
                            qty = 1.0
                        self.env['pos.product.bom.line'].create({
                            'pos_bom_id': bom.id,
                            'product_id': comp_product.id,
                            'product_qty': float(qty),
                            'product_uom_id': comp_product.uom_id.id,
                        })

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Importación Exitosa'),
                'message': _('Se han importado los productos y recetas correctamente.'),
                'sticky': False,
                'type': 'success',
            }
        }
