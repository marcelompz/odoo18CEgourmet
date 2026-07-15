/** @odoo-module */

import { PosOrder } from "@point_of_sale/app/models/pos_order";
import { patch } from "@web/core/utils/patch";

patch(PosOrder.prototype, {
    export_for_printing(...args) {
        const result = super.export_for_printing(...args);
        result.is_pending_payment = this.is_pending_payment || false;
        result.precuenta_ref = this.precuenta_ref || "";
        result.source_order_id = this.source_order_id?.id || false;
        return result;
    },
});
