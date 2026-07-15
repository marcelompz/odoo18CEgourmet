/** @odoo-module **/

import { QtyAtDatePopover, QtyAtDateWidget } from "@sale_stock/widgets/qty_at_date_widget";
import { useService } from '@web/core/utils/hooks';
import { onMounted, useState } from "@odoo/owl";

/**
 * ExtendedQtyAtDatePopover
 * Extiende el popover de cantidad de Odoo para mostrar información de stock por almacén
 * Integrado en sale_line_stock_improved para Odoo 18
 * 
 * ENFOQUE: Modifica el contenido del popover inyectando HTML dinámicamente
 * sin necesidad de heredar templates XML (más robusto)
 */
export class ExtendedQtyAtDatePopover extends QtyAtDatePopover {
    setup() {
        super.setup();
        this.orm = useService("orm");

        // Estado para gestionar la información de stock por almacén
        this.warehouseStockState = useState({
            stockByWarehouse: [],
            loading: false,
            error: null
        });

        // Cargar información al montar el componente
        onMounted(async () => {
            await this._loadAndInjectWarehouseStock();
        });
    }

    /**
     * Carga la información de stock por almacén e inyecta en el DOM
     */
    async _loadAndInjectWarehouseStock() {
        try {
            this.warehouseStockState.loading = true;
            this.warehouseStockState.error = null;

            // Obtener datos de stock
            const stockData = await this._fetchStockByWarehouse();
            this.warehouseStockState.stockByWarehouse = stockData;

            // Inyectar HTML en el popover
            setTimeout(() => this._injectWarehouseStockHTML(stockData), 100);

        } catch (error) {
            console.error('Error cargando información de stock por almacén:', error);
            this.warehouseStockState.error = 'Error al cargar información de stock';
        } finally {
            this.warehouseStockState.loading = false;
        }
    }

    /**
     * Inyecta el HTML de stock por almacén en el popover existente
     */
    _injectWarehouseStockHTML(stockData) {
        // Buscar el contenedor del popover
        const popoverContent = document.querySelector('.o_popover .p-2');
        if (!popoverContent) return;

        // Verificar si ya se inyectó
        if (popoverContent.querySelector('.warehouse-stock-section')) return;

        // No inyectar si no hay datos
        if (!stockData || stockData.length === 0) return;

        // Agrupar por compañía para mejor visualización
        const stockByCompany = {};
        stockData.forEach(wh => {
            const companyName = wh.company_name || 'Sin Compañía';
            if (!stockByCompany[companyName]) {
                stockByCompany[companyName] = [];
            }
            stockByCompany[companyName].push(wh);
        });

        // Crear HTML de la tabla con agrupación por compañía
        const warehouseHTML = `
            <hr class="my-2"/>
            <div class="warehouse-stock-section">
                <h6 class="mb-2">
                    <i class="fa fa-warehouse"></i> Stock por Almacén y Sucursal
                </h6>
                <div style="max-height: 350px; overflow-y: auto;">
                    ${Object.entries(stockByCompany).map(([companyName, warehouses]) => `
                        ${Object.keys(stockByCompany).length > 1 ? `
                            <div class="company-header bg-light px-2 py-1 mb-1" style="position: sticky; top: 0; z-index: 2;">
                                <small class="text-primary">
                                    <i class="fa fa-building"></i> <strong>${companyName}</strong>
                                </small>
                            </div>
                        ` : ''}
                        <table class="table table-sm table-hover mb-2">
                            <thead class="table-light" style="position: sticky; top: ${Object.keys(stockByCompany).length > 1 ? '25px' : '0'}; z-index: 1; background-color: #f8f9fa;">
                                <tr>
                                    <th style="font-size: 0.875rem;">Almacén</th>
                                    <th class="text-end" style="font-size: 0.875rem;">Total</th>
                                    <th class="text-end" style="font-size: 0.875rem;">Disponible</th>
                                    <th class="text-end" style="font-size: 0.875rem;">Reservado</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${warehouses.map(wh => {
            const hasStock = wh.total_quantity > 0;
            const rowClass = hasStock ? '' : 'table-secondary';
            const quantityColor = hasStock ? 'text-primary' : 'text-muted';
            const availableColor = hasStock ? 'text-success' : 'text-muted';
            const reservedColor = (hasStock && wh.total_reserved > 0) ? 'text-warning' : 'text-muted';

            return `
                                    <tr class="${rowClass}">
                                        <td>
                                            <strong>${wh.warehouse_name}</strong>
                                            ${!hasStock ? '<span class="badge bg-secondary ms-1" style="font-size: 0.65rem;">Sin Stock</span>' : ''}
                                            <br/>
                                            <small class="text-muted">
                                                ${wh.warehouse_code || ''}
                                                ${Object.keys(stockByCompany).length === 1 && wh.company_name ?
                    `<span class="badge bg-info text-dark" style="font-size: 0.7rem; margin-left: 4px;">
                                                        <i class="fa fa-building"></i> ${wh.company_name}
                                                    </span>`
                    : ''}
                                            </small>
                                        </td>
                                        <td class="text-end">
                                            <b class="${quantityColor}">${wh.total_quantity.toFixed(2)}</b><br/>
                                            <small class="text-muted">${wh.product_uom_name}</small>
                                        </td>
                                        <td class="text-end ${availableColor}">
                                            <b>${wh.total_available.toFixed(2)}</b><br/>
                                            <small class="text-muted">${wh.product_uom_name}</small>
                                        </td>
                                        <td class="text-end ${reservedColor}">
                                            <b>${wh.total_reserved.toFixed(2)}</b><br/>
                                            <small class="text-muted">${wh.product_uom_name}</small>
                                        </td>
                                    </tr>
                                `}).join('')}
                            </tbody>
                        </table>
                    `).join('')}
                </div>
            </div>
        `;

        // Insertar al final del contenido del popover
        popoverContent.insertAdjacentHTML('beforeend', warehouseHTML);

        // Ajustar el ancho del popover para acomodar la tabla
        const popover = popoverContent.closest('.o_popover');
        if (popover) {
            popover.style.minWidth = '500px';
            popover.style.maxWidth = '600px';
        }
    }

    /**
     * Obtiene el stock del producto agrupado por almacén
     * @returns {Promise<Array>} Lista de stock por almacén
     */
    async _fetchStockByWarehouse() {
        if (!this.props.record.data.product_id || !this.props.record.data.product_id[0]) {
            return [];
        }

        const product_id = this.props.record.data.product_id[0];

        try {
            const result = await this.orm.call(
                "stock.quant",
                "get_product_stock_by_warehouse",
                [product_id]
            );
            return result || [];
        } catch (error) {
            console.error('Error fetching warehouse stock:', error);
            return [];
        }
    }
}

// Reemplazar el componente Popover en QtyAtDateWidget
QtyAtDateWidget.components = { Popover: ExtendedQtyAtDatePopover };
