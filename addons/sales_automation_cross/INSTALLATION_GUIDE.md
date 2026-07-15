# Guía de Instalación y Uso: Sales Automation Cross

Este documento detalla cómo instalar y utilizar el módulo `sales_automation_cross`, que proporciona una acción de servidor para automatizar el flujo completo de una orden de venta y pedidos de POS: confirmación, creación y validación de factura, registro de pago y validación de la salida de mercancía.

## Estructura del Módulo

El módulo `sales_automation_cross` tiene la siguiente estructura de archivos:

```text
sales_automation_cross/
├── __init__.py
├── __manifest__.py
├── INSTALLATION_GUIDE.md
├── data/
│   └── server_action.xml
├── models/
│   ├── __init__.py
│   ├── pos_order_automation.py
│   └── sale_order_automation.py
├── security/
│   └── ir.model.access.csv
└── views/
    ├── pos_order_views.xml
    └── sale_order_views.xml
```

## Requisitos

- Odoo 18 o superior.
- Módulos `sale_management`, `account`, `stock` y `point_of_sale` instalados.

## Instalación

1.  **Copia el Módulo**: Copia la carpeta `sales_automation_cross` completa en el directorio `addons` de tu instalación de Odoo.
2.  **Actualiza la Lista de Aplicaciones**:
    - Ve a **Ajustes** y activa el **Modo Desarrollador**.
    - Ve al menú **Aplicaciones**.
    - Haz clic en **Actualizar lista de aplicaciones**.
3.  **Instala el Módulo**:
    - Busca "Sales Automation Cross" en la lista de aplicaciones.
    - Haz clic en **Instalar**.

## Uso

### Ventas (Sale Order)
1.  Ve al módulo **Ventas** -> **Órdenes** -> **Órdenes de Venta**.
2.  Selecciona una o varias órdenes de venta en la vista de lista (deben estar en estado "Presupuesto" o "Presupuesto enviado").
3.  Haz clic en el botón de **Acción** (icono de engranaje o menú desplegable).
4.  Selecciona **Confirmar, Facturar, Pagar y Entregar**.
5.  Odoo procesará las órdenes automáticamente (Confirmación -> Facturación -> Pago -> Salida de Mercancía).

### Punto de Venta (POS Order)
1.  Ve al módulo **Punto de Venta** -> **Pedidos** -> **Pedidos**.
2.  Selecciona uno o varios pedidos en la vista de lista.
3.  Haz clic en el botón de **Acción**.
4.  Selecciona **Confirmar, Facturar, Pagar y Entregar (POS)**.
5.  Odoo procesará los pedidos (Facturación y entrega).

### Importación de Histórico (POS)
1.  Ve al módulo **Punto de Venta** -> **Pedidos** -> **Pedidos**.
2.  Haz clic en el botón de **Acción** -> **Importar Histórico (Excel/CSV)**.
3.  Sube un archivo con las columnas: `Fecha`, `Cliente`, `Producto`, `Cantidad`, `Precio`.
4.  Selecciona una sesión de POS abierta.
5.  Haz clic en **Importar**.

## Consideraciones Importantes

*   **Diario de Pago**: Para Ventas, el código intenta encontrar un diario de tipo 'Banco' o 'Efectivo'.
*   **Permisos**: Asegúrate de que el usuario tenga los permisos adecuados para facturar y validar stock.
*   **Manejo de Errores**: El código incluye manejo básico de errores. Si ocurre un problema, se mostrará un mensaje descriptivo.
