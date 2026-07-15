/** @odoo-module **/

import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { Component, useState, onMounted } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class StockInfoWidget extends Component {
    setup() {
        super.setup();
        this.orm = useService("orm");
        this.state = useState({
            stockData: null,
            loading: false,
            error: null,
            expanded: false
        });

        onMounted(() => {
            this.loadStockInfo();
        });
    }

    async loadStockInfo() {
        if (!this.props.record.data.product_id || !this.props.record.data.product_id[0]) {
            return;
        }

        this.state.loading = true;
        this.state.error = null;

        try {
            const productId = this.props.record.data.product_id[0];
            const stockData = await this.orm.call(
                "stock.quant",
                "get_product_stock_by_warehouse",
                [productId]
            );

            this.state.stockData = stockData;
        } catch (error) {
            console.error("Error loading stock info:", error);
            this.state.error = "Error al cargar información de stock";
        } finally {
            this.state.loading = false;
        }
    }

    toggleExpanded() {
        this.state.expanded = !this.state.expanded;
    }

    getStockStatusClass(available, reserved) {
        if (available <= 0) return "text-danger";
        if (reserved > available * 0.8) return "text-warning";
        if (available < 10) return "text-info";
        return "text-success";
    }

    formatQuantity(quantity) {
        return parseFloat(quantity).toFixed(2);
    }
}

StockInfoWidget.template = "sale_line_stock_improved.StockInfoWidget";
StockInfoWidget.props = {
    ...standardFieldProps,
};

registry.category("fields").add("stock_info_widget", {
    component: StockInfoWidget,
}); 