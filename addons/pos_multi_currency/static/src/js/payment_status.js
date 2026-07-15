/** @odoo-module */

import { PaymentScreenStatus } from "@point_of_sale/app/screens/payment_screen/payment_status/payment_status";
import { patch } from "@web/core/utils/patch";

patch(PaymentScreenStatus.prototype, {
    get changeText() {
        const change = this.props.order.get_change();
        
        // Use configured threshold instead of hard-coded 100
        const config = this.env.services?.pos?.config;
        const threshold = config?.min_change_threshold || 0;

        if (threshold > 0 && change < threshold && change >= 0) {
            return this.env.utils.formatCurrency(0);
        }

        return this.env.utils.formatCurrency(change);
    }
});
