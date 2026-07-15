/** @odoo-module */

import { PosStore } from "@point_of_sale/app/store/pos_store";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";

patch(PosStore.prototype, {
    /**
     * Mark current order as pending payment (Counter POS workflow)
     */
    async markOrderPending() {
        const order = this.get_order();

        // Check if order has lines
        if (!order || order.lines.length === 0) {
            this.dialog.add(AlertDialog, {
                title: _t("Empty Order"),
                body: _t("Cannot mark an empty order as pending."),
            });
            return;
        }

        // Sync the order to server first to get an ID
        try {
            await this.syncAllOrders({ orders: [order] });
        } catch (error) {
            this.dialog.add(AlertDialog, {
                title: _t("Sync Error"),
                body: _t("Failed to sync order. Please check your connection and try again."),
            });
            return;
        }

        if (!order.id) {
            this.dialog.add(AlertDialog, {
                title: _t("Error"),
                body: _t("Order ID not available. Please try again."),
            });
            return;
        }

        // Mark the order as pending in the backend
        try {
            const orderData = await this.data.call("pos.order", "mark_order_pending", [order.id]);

            if (orderData && orderData.precuenta_ref) {
                // Update order fields in the frontend model
                await this.data.write("pos.order", [order.id], {
                    is_pending_payment: true,
                    precuenta_ref: orderData.precuenta_ref,
                });
                order.is_pending_payment = true;
                order.precuenta_ref = orderData.precuenta_ref;

                // Print the ticket directly (pending orders shouldn't go to "Payment Successful" screen)
                order.nb_print = 0;
                await this.printReceipt();

                // Create a new empty order for next customer
                this.add_new_order();
            }
        } catch (error) {
            this.dialog.add(AlertDialog, {
                title: _t("Error"),
                body: _t("Failed to mark order as pending: ") + error.message,
            });
        }
    },

    /**
     * Open pending orders dialog (Central Cashier workflow)
     */
    openPendingOrdersDialog() {
        this.showScreen("PendingOrdersDialog");
    },
});
