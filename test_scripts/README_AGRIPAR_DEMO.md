# 🚜 Demo Agripar - Odoo 19.0

## 📋 Descripción

Este demo configura una base de datos de ejemplo para **AGRIPAR S.A.** (distribuidora de repuestos hidráulicos) con:

- ✅ Clientes y proveedores
- ✅ Productos hidráulicos con trazabilidad (lotes/series)
- ✅ Stock inicial
- ✅ Oportunidad CRM
- ✅ Pedido de venta confirmado
- ✅ Solicitud de compra

---

## 🚀 Pasos para Inicializar

### **Paso 1: Asegurar que Odoo esté corriendo**

```bash
cd /opt/odoo/odoo8084
docker compose up -d
```

Verifica que esté disponible:
```bash
docker ps | grep odoo_web_8084
```

---

### **Paso 2: Inicializar la base de datos desde el navegador**

1. **Abre tu navegador** en: `http://localhost:8084`

2. **Verás la pantalla de creación de base de datos** de Odoo

3. **Completa el formulario:**
   - **Nombre de la base de datos:** `ferreteria`
   - **Email:** `admin`
   - **Contraseña:** `admin` (o la que prefieras)
   - **Idioma:** Español
   - **País:** Paraguay

4. **Haz clic en "Crear base de datos"**

5. **Espera a que Odoo inicialice** (2-3 minutos)
   - Verás una pantalla de carga
   - Se crearán todas las tablas
   - Se instalarán módulos base

6. **Cuando termine**, verás el dashboard de Odoo

---

### **Paso 3: Ejecutar el script seed**

Una vez que la DB esté inicializada, ejecuta:

```bash
cd /opt/odoo/odoo8084/test_scripts
./run_agripar_seed_simple.sh
```

O desde la raíz:
```bash
/opt/odoo/odoo8084/test_scripts/run_agripar_seed_simple.sh
```

---

## 📊 ¿Qué datos se crearán?

### **Clientes y Proveedores**
| Tipo | Nombre | RUC |
|------|--------|-----|
| Cliente | Agripar - Estancia El Ombú | 80001122-3 |
| Proveedor | Parker Hannifin Paraguay S.A. | 80003344-5 |

### **Productos Hidráulicos**
| Producto | Tipo | Precio Venta | Costo | Trazabilidad |
|----------|------|--------------|-------|--------------|
| Cilindro Hidráulico Rexroth Doble Efecto | Storable | ₲ 1.800.000 | ₲ 1.100.000 | Lote |
| Válvula Control Direccional Monoblock 80L | Storable | ₲ 2.500.000 | ₲ 1.500.000 | Lote |
| Bomba Hidráulica Parker PGP511 | Storable | ₲ 6.500.000 | ₲ 4.000.000 | Serie |
| Servicio Técnico - Reparación | Servicio | ₲ 1.500.000 | ₲ 500.000 | N/A |

### **Stock Inicial**
| Producto | Cantidad | Lote/Serie |
|----------|----------|------------|
| Cilindro Hidráulico | 50 un. | LOTE-CILINDRO-2026-01 |
| Válvula Control | 30 un. | LOTE-VALVULA-2026-03 |
| Bomba Parker | 1 un. | BOMBA-PGP511-SER01 |
| Bomba Parker | 1 un. | BOMBA-PGP511-SER02 |

### **Ventas y Compras**
| Documento | Tipo | Estado | Total Aprox. |
|-----------|------|--------|--------------|
| Pedido de Venta | SO/2026/... | Confirmado | ₲ 7.600.000 |
| Solicitud de Compra | PO/2026/... | Borrador | ₲ 15.000.000 |

### **CRM**
| Oportunidad | Etapa | Probabilidad | Revenue Esperado |
|-------------|-------|--------------|------------------|
| Agripar Demo - Reparación de Maquinaria | Proposición | 70% | ₲ 7.600.000 |

---

## 🔍 Verificar datos cargados

Después de ejecutar el seed, puedes verificar:

### **Desde el navegador:**

1. **Clientes:** `http://localhost:8084/web#model=res.partner&view_type=list`
   - Buscar "Agripar - Estancia El Ombú"

2. **Productos:** `http://localhost:8084/web#model=product.product&view_type=list`
   - Buscar "Cilindro Hidráulico"

3. **Pedidos de venta:** `http://localhost:8084/web#model=sale.order&view_type=list`
   - Ver último pedido confirmado

4. **CRM:** `http://localhost:8084/web#model=crm.lead&view_type=list`
   - Ver oportunidad "Agripar Demo"

### **Desde la terminal:**

```bash
# Verificar cliente
docker exec db_odoo_5436 psql -U odoo -d ferreteria -c \
  "SELECT name, vat, email FROM res_partner WHERE name LIKE '%Agripar%';"

# Verificar productos
docker exec db_odoo_5436 psql -U odoo -d ferreteria -c \
  "SELECT name, list_price, standard_price FROM product_product WHERE name LIKE '%Hidráulico%';"

# Verificar stock
docker exec db_odoo_5436 psql -U odoo -d ferreteria -c \
  "SELECT pp.name, sq.quantity, sl.name as lote
   FROM stock_quant sq
   JOIN product_product pp ON sq.product_id = pp.id
   LEFT JOIN stock_lot sl ON sq.lot_id = sl.id
   WHERE pp.name LIKE '%Hidráulico%';"
```

---

## 🛠️ Solución de Problemas

### **Error: "La DB no tiene tablas de Odoo"**

**Causa:** La base de datos no fue inicializada desde el navegador.

**Solución:**
1. Abre `http://localhost:8084`
2. Crea la base de datos `ferreteria`
3. Espera a que termine la instalación
4. Ejecuta el script nuevamente

---

### **Error: "relation does not exist"**

**Causa:** Faltan módulos instalados.

**Solución:**
1. En Odoo, ve a **Apps**
2. Instala al menos:
   - **CRM**
   - **Ventas**
   - **Inventario**
3. Ejecuta el script nuevamente

---

### **Error: "Connection refused"**

**Causa:** Odoo no está corriendo.

**Solución:**
```bash
cd /opt/odoo/odoo8084
docker compose up -d
docker logs -f odoo_web_8084
```

---

### **Error: "Permission denied"**

**Causa:** El script no tiene permisos de ejecución.

**Solución:**
```bash
chmod +x /opt/odoo/odoo8084/test_scripts/run_agripar_seed_simple.sh
```

---

## 🧹 Limpiar y reiniciar

Si necesitas empezar desde cero:

```bash
cd /opt/odoo/odoo8084

# Detener contenedores y eliminar volúmenes
docker compose down -v

# Eliminar datos en disco (si existen)
sudo rm -rf db-data/* web-data/*

# Levantar nuevamente
docker compose up -d

# Esperar 30 segundos y luego inicializar desde el navegador
sleep 30
# Abre http://localhost:8084 en tu navegador
```

---

## 📞 Soporte

Si encuentras problemas:

1. Revisa los logs de Odoo:
   ```bash
   docker logs odoo_web_8084 --tail 100
   ```

2. Verifica el estado de la DB:
   ```bash
   docker exec db_odoo_5436 psql -U odoo -d ferreteria -c "\dt"
   ```

3. Consulta la documentación oficial de Odoo 19.0

---

## 📝 Archivos del Proyecto

| Archivo | Propósito |
|---------|-----------|
| `seed_agripar_demo.py` | Script principal con los datos a cargar |
| `run_agripar_seed_simple.sh` | Wrapper bash para ejecutar el seed |
| `run_agripar_seed.sh` | Versión completa con verificaciones |
| `README_AGRIPAR_DEMO.md` | Este documento |

---

**Última actualización:** 26 de junio, 2026  
**Odoo versión:** 19.0  
**Demo para:** AGRIPAR S.A.
