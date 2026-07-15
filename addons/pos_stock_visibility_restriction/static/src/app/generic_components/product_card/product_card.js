/* @odoo-module */

import { useEffect, useState } from "@odoo/owl";
import { ProductCard } from "@point_of_sale/app/generic_components/product_card/product_card";
import { patch } from "@web/core/utils/patch";

patch(ProductCard.prototype, {
    setup() {
        super.setup(...arguments);

        this.qtyInCart = useState({ value: this.productQty || 0 });
        this.qtyAvailable = useState({ value: this.props.product.qty_available });
        this.prevCartQty = this.productQty || 0;

        useEffect(() => {
            this.updateQuantityOnCartChange();
        }, () => [this.productQty]);
    },
    updateQuantityOnCartChange() {
        const cartQtyDifference = this.productQty - this.prevCartQty;

        this.qtyInCart.value = this.productQty || 0;

        if (cartQtyDifference > 0) {
            this.qtyAvailable.value -= cartQtyDifference;
        } else if (cartQtyDifference < 0) {
            this.qtyAvailable.value -= cartQtyDifference;
        }

        this.prevCartQty = this.productQty || 0;
    }

});





