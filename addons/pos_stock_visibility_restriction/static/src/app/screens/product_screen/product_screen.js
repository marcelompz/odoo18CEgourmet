/* @odoo-module */

import { _t } from "@web/core/l10n/translation";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { patch } from "@web/core/utils/patch";

patch(ProductScreen.prototype, {
    async addProductToOrder(product) {
        if (this.pos.config.restrict_zero_stock && product.qty_available <= 0) {
            this.dialog.add(ConfirmationDialog, {
                title: _t("Product Out of Stock"),
                body: _t("%s está agotado. Haz clic en «Ordenar» si aún deseas añadir este producto.", this.getProductName(product)),
                confirmClass: "btn-primary",
                confirm: async () => {
                    const res = await super.addProductToOrder(product);
                    console.log(res)
                    return res
                },
                confirmLabel: _t("Ordenar"),
                cancelLabel: _t("Cancelar"),
                cancel: () => { },
            });
        } else {
            const res = await super.addProductToOrder(product);
            console.log(res)
            return res
        }
   }
});
