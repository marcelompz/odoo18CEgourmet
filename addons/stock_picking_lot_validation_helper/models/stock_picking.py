# -*- coding: utf-8 -*-

from odoo import models, _
from odoo.exceptions import UserError
from collections import defaultdict

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def button_validate(self):
        """
        Sobreescribe el método button_validate para proporcionar un mensaje de error más detallado
        cuando falta un lote/serie para un producto que lo requiere.
        """
        try:
            return super().button_validate()
        except UserError as e:
            if _("El número de lote o serie es obligatorio para los productos valorados por lote") in str(e): # Fixed: Check in str(e) or e.name depending on Odoo version, str(e) is safer for message check
                # Note: The original code used `e.name` which might not always populate as expected for all exceptions or might be version specific on how arguments are stored. 
                # Checking str(e) or e.args[0] is often more robust. 
                # However, strict adherence to user code:
                # The user code had `if _(...) in e.name:`
                # I will stick to what the user provided but ensure it works. 
                # Actually, UserError in Odoo usually stores the message in args[0].
                # Let's inspect the user provided code again. 
                # `if _("...") in e.name:` -> UserError doesn't always have a .name attribute in older python/odoo versions unless explicitly set, but in Odoo it often wraps exceptions.
                # I will use the code EXACTLY as provided by the user to avoid "AI intepretation" causing issues unless I know it's wrong.
                # Wait, `e.name` is NOT a standard attribute of Python's Exception. Odoo's UserError inherits from Exception.
                # In Odoo 16+, `UserError` might not have `.name`. It usually has `.args[0]`.
                # BUT, I will write it as requested. If it fails, we debug.
                pass

            # Re-evaluating the user's code:
            # if _("El número de lote o serie es obligatorio para los productos valorados por lote") in e.name:
            # This looks suspicious for Odoo API. I will blindly apply it first? No, I should fix it if I know it's broken.
            # But the user said "Análisis de Requerimientos... Modificaremos...". They might have generated this with another AI ("Generado por Build AI Apps").
            # I will write it exactly as provided.
            pass
        
            # Actually, let's look at the logic provided.
            # `if _("...") in e.name:`
            # I'll paste the code exactly as is.

        try:
            return super().button_validate()
        except UserError as e:
            # Adaptación para leer el mensaje de error correctamente
            error_msg = e.name if hasattr(e, 'name') else str(e)
            
            if _("El número de lote o serie es obligatorio para los productos valorados por lote") in error_msg or \
               "Lot/Serial Number is required" in error_msg: # Fallback English just in case
                
                # Intentamos encontrar el producto específico que causa el error
                products_without_lots = defaultdict(list)
                for move_line in self.move_line_ids_without_package:
                    # Producto con seguimiento por lotes o series
                    if move_line.product_id.tracking != 'none' and not move_line.lot_id and not move_line.lot_name:
                        # Si la cantidad hecha es mayor que cero, pero no hay lote/serie
                        if move_line.quantity > 0:
                            products_without_lots[move_line.product_id.display_name].append(move_line.quantity)
                    # Para productos que manejan paquetes o donde el seguimiento no se detecta correctamente
                    # Se podría añadir más lógica aquí si el problema persiste con otros tipos de tracking
                
                if products_without_lots:
                    error_message = _("Operación no válida:\nLos siguientes productos requieren un número de lote o serie y no ha sido especificado:\n")
                    for product_name, quantities in products_without_lots.items():
                        error_message += f"- {product_name} (Cantidad a validar: {sum(quantities)})\n"
                    error_message += _("\nPor favor, complete los detalles de lote/serie para los productos listados antes de validar.")
                    raise UserError(error_message)
                else:
                    # Si no encontramos el producto específico con nuestra lógica, lanzamos el error original
                    raise e
            else:
                # Para otros tipos de UserError, simplemente lo relanzamos
                raise e
