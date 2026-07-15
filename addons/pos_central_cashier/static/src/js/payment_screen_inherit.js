/** @odoo-module */

import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";

patch(PaymentScreen.prototype, {
    async validateOrder(isForceValidate) {
        const order = this.currentOrder || this.pos.get_order();
        
        // If this is a pending payment order loaded at the cashier,
        // mark it for proper handling during sync
        if (order && order.is_pending_payment && order.source_order_id) {
            order._is_completing_pending_order = true;
        }
        
        // Prevent counter POS from directly paying orders marked as pending
        if (order && order.is_pending_payment && !order.source_order_id) {
            // This order was marked as pending at this counter - should not be paid here
            if (this.pos.config.is_counter_pos && !this.pos.config.is_central_cashier) {
                this.dialog.add(AlertDialog, {
                    title: _t("Order Pending Payment"),
                    body: _t("This order is pending payment. It must be paid at the central cashier."),
                });
                return;
            }
        }
        
        return super.validateOrder(...arguments);
    }
});
