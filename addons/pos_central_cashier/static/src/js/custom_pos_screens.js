/** @odoo-module */

import { Component, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { _t } from "@web/core/l10n/translation";

export class PendingOrdersDialog extends Component {
    static template = "pos_central_cashier.PendingOrdersDialog";
    static props = {
        close: { type: Function, optional: true },
    };

    setup() {
        super.setup();
        this.pos = usePos();
        this.orm = useService("orm");
        this.state = useState({
            searchQuery: "",
            orders: [],
            loading: false,
            error: null,
        });
        this.searchOrders();
    }

    async searchOrders() {
        try {
            const orders = await this.orm.call("pos.order", "search_pending_orders_for_pos", [], {
                query: this.state.searchQuery,
            });
            this.state.orders = orders;
            this.state.error = null;
        } catch (error) {
            this.state.error = _t("Error searching orders: ") + error.message;
            this.state.orders = [];
        }
    }

    async onSearchInput(ev) {
        this.state.searchQuery = ev.target.value;
        await this.searchOrders();
    }

    async loadOrder(order_id) {
        if (this.state.loading) return;
        this.state.loading = true;
        this.state.error = null;

        try {
            const orderData = await this.orm.call("pos.order", "export_pending_order_payload", [order_id]);

            // If current order has items, create a new order
            const currentOrder = this.pos.get_order();
            if (currentOrder && currentOrder.lines.length > 0) {
                this.pos.add_new_order();
            }

            const newOrder = this.pos.get_order();
            
            // Set partner if available
            if (orderData.partner_id) {
                const partner = this.pos.models["res.partner"].get(orderData.partner_id, false);
                if (partner) {
                    newOrder.set_partner(partner);
                }
            }

            // Mark order as pending with source reference
            newOrder.is_pending_payment = true;
            newOrder.precuenta_ref = orderData.precuenta_ref;
            newOrder.source_order_id = orderData.id;

            // Add all product lines from the original order
            for (const line of orderData.lines) {
                const product = this.pos.models["product.product"].get(line.product_id, false);
                if (product) {
                    await this.pos.addLineToCurrentOrder(
                        {
                            product_id: product,
                            qty: line.qty,
                            price_unit: line.price_unit,
                            discount: line.discount,
                            note: line.note,
                        },
                        { merge: false }
                    );
                }
            }

            // Navigate to payment screen to complete payment
            this.pos.showScreen("PaymentScreen");
            if (this.props.close) {
                this.props.close();
            }
        } catch (error) {
            this.state.error = _t("Error loading order: ") + error.message;
        } finally {
            this.state.loading = false;
        }
    }
}

import { registry } from "@web/core/registry";
registry.category("pos_screens").add("PendingOrdersDialog", PendingOrdersDialog);
