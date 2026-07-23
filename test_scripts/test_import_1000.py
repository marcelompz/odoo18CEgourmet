# -*- coding: utf-8 -*-
"""
Script de prueba para el módulo product_mass_import
Genera un Excel con 1000 productos de prueba para stress testing
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

# Generar 1000 productos de prueba
categorias = ['Electrónica', 'Herramientas', 'Hogar', 'Deportes', 'Jardín', 'Automotor', 'Oficina', 'Mascotas']
pos_categorias = ['Electrónica', 'Herramientas', 'Hogar', 'Deportes', 'Jardín', 'Automotor', 'Oficina', 'Mascotas']

print('📊 Generando 1000 productos de prueba...')

for i in range(1, 1001):
    row = [
        f'TEST-{i:05d}',  # Referencia Interna
        f'Producto de Prueba {i}',  # Nombre
        f'Descripción para PdV del producto {i}',  # Descripción PdV
        f'7701234567{i:05d}',  # Barcode (12 dígitos)
        'VERDADERO' if i % 2 == 0 else 'FALSO',  # Disponible en PdV
        categorias[i % len(categorias)],  # Categoría
        pos_categorias[i % len(pos_categorias)],  # Categoría PdV
        10000 * (i % 100 + 1),  # Precio Venta (evita números muy grandes)
        7500 * (i % 100 + 1),  # Precio Costo
        i * 10 if i % 3 == 0 else 0,  # Cantidad (solo cada 3ro tiene stock)
        'Almacenable',  # Tipo
        'Ninguno'  # Trazabilidad
    ]
    ws.append(row)

# Ajustar ancho de columnas
ws.column_dimensions['A'].width = 15  # Referencia
ws.column_dimensions['B'].width = 25  # Nombre
ws.column_dimensions['C'].width = 30  # Descripción
ws.column_dimensions['D'].width = 18  # Barcode
ws.column_dimensions['E'].width = 18  # Disponible PdV
ws.column_dimensions['F'].width = 20  # Categoría
ws.column_dimensions['G'].width = 20  # Categoría PdV
ws.column_dimensions['H'].width = 15  # Precio Venta
ws.column_dimensions['I'].width = 15  # Precio Costo
ws.column_dimensions['J'].width = 15  # Cantidad
ws.column_dimensions['K'].width = 15  # Tipo
ws.column_dimensions['L'].width = 15  # Trazabilidad

# Guardar archivo
filename = f'/tmp/test_import_1000_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
wb.save(filename)

# Calcular estadísticas
productos_con_stock = sum(1 for i in range(1, 1001) if i % 3 == 0)

print(f'✅ Excel generado: {filename}')
print(f'   - 1000 productos de prueba')
print(f'   - {len(categorias)} categorías que se crearán automáticamente')
print(f'   - {productos_con_stock} productos con stock inicial')
print(f'   - Precios desde $10,000 hasta $1,000,000')
print()
print('📝 NOTA: Las categorías se crearán automáticamente durante la importación.')
print('   Si ya existen categorías similares, se reutilizarán (fuzzy match).')
print()
print('🚀 Para probar rendimiento:')
print('   1. Subir este archivo en Odoo')
print('   2. Click en "Cargar Archivo" → Debería validar en ~2-3 segundos')
print('   3. Click en "Confirmar Importación" → Debería crear en ~5-10 segundos')
