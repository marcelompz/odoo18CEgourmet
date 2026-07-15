/** @odoo-module */

import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { patch } from "@web/core/utils/patch";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { _t } from "@web/core/l10n/translation";

patch(PaymentScreen.prototype, {
    async validateOrder(isForceValidate) {
        const currentOrder = this.currentOrder;
        
        if (!currentOrder) {
            return super.validateOrder(...arguments);
        }

        const orderLines = currentOrder.get_orderlines();
        let zeroCostProducts = [];

        for (const line of orderLines) {
            const product = line.get_product();

            if (product && product.standard_price !== undefined) {
                // Validación: Costo <= 0 y NO es un servicio
                if (product.standard_price <= 0 && product.type !== 'service') {
                    zeroCostProducts.push(product.display_name);
                }
            }
        }

        if (zeroCostProducts.length > 0) {
            this.env.services.dialog.add(AlertDialog, {
                title: _t("⚠️ Error de Costos"),
                body: _t(
                    `No se puede procesar la venta. Los siguientes productos tienen COSTO 0:\n\n` +
                    zeroCostProducts.join("\n") +
                    `\n\nPor favor, contacte a compras.`
                ),
            });
            return;
        }

        return super.validateOrder(...arguments);
    }
});
