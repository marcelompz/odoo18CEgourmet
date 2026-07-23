# -*- coding: utf-8 -*-
"""
Script de prueba para el módulo product_mass_import
Genera un Excel con 100 productos de prueba y verifica la importación

NOTA: Las categorías se crearán automáticamente durante la importación.
"""

import openpyxl
from datetime import datetime

# Crear Excel de prueba
wb = openpyxl.Workbook()
ws = wb.active
ws.title = 'Productos Test'

# Headers
headers = [
    'Referencia Interna',
    'Nombre del Producto',
    'Descripción para PdV',
    'Código de Barras',
    'Disponible en PdV',
    'Categoría de Producto',
    'Categoría de PdV',
    'Precio de Venta',
    'Precio de Costo',
    'Cantidad a la Mano',
    'Tipo de Producto',
    'Trazabilidad'
]
ws.append(headers)

# Generar 100 productos de prueba
categorias = ['Electrónica', 'Herramientas', 'Hogar', 'Deportes']
pos_categorias = ['Electrónica', 'Herramientas', 'Hogar', 'Deportes']
tipos = ['Almacenable', 'Servicio', 'Combo']
trazabilidades = ['Ninguno', 'Por Lote', 'Por Número de Serie']

for i in range(1, 101):
    row = [
        f'TEST-{i:04d}',  # Referencia Interna
        f'Producto de Prueba {i}',  # Nombre
        f'Descripción para PdV del producto {i}',  # Descripción PdV
        f'7701234567{i:04d}',  # Barcode
        'VERDADERO' if i % 2 == 0 else 'FALSO',  # Disponible en PdV
        categorias[i % len(categorias)],  # Categoría
        pos_categorias[i % len(pos_categorias)],  # Categoría PdV
        10000 * i,  # Precio Venta
        7500 * i,  # Precio Costo
        i * 10 if i % 3 == 0 else 0,  # Cantidad (solo cada 3ro tiene stock)
        'Almacenable',  # Tipo
        'Ninguno'  # Trazabilidad
    ]
    ws.append(row)

# Guardar archivo
filename = f'/tmp/test_import_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
wb.save(filename)

print(f'✅ Excel generado: {filename}')
print(f'   - 100 productos de prueba')
print(f'   - Categorías que se crearán automáticamente: {", ".join(categorias)}')
print(f'   - Categorías PdV que se crearán: {", ".join(pos_categorias)}')
print(f'   - Precios desde $10,000 hasta $1,000,000')
print(f'   - 33 productos con stock inicial')
print()
print('📝 NOTA: Las categorías se crearán automáticamente durante la importación.')
