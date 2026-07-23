#!/usr/bin/env python3
"""
Script para convertir los nombres de UoM en el CSV a IDs numéricos.

Odoo 19 CE trata los valores numéricos como IDs de Many2one en lugar de nombres.
Este script convierte:
  - 'g' -> 15
  - 'ml' -> 12
  - 'Unidades' -> 1
"""

import csv
import sys

UOM_MAPPING = {
    'g': '15',
    'ml': '12',
    'Unidades': '1',
    'Gramos': '15',
    'Mililitros': '12',
    'Uds': '1',
    'ud': '1',
}

def fix_uom_csv(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        # Leer con separador ;
        reader = csv.DictReader(f, delimiter=';')
        fieldnames = reader.fieldnames
        
        if 'Unidades' not in fieldnames:
            print(f"Error: La columna 'Unidades' no existe en el archivo")
            print(f"Columnas disponibles: {fieldnames}")
            return False
        
        rows = list(reader)
    
    # Convertir valores
    converted = 0
    for row in rows:
        old_value = row['Unidades'].strip() if row['Unidades'] else ''
        if old_value in UOM_MAPPING:
            row['Unidades'] = UOM_MAPPING[old_value]
            converted += 1
    
    # Escribir archivo de salida
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';')
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"Procesado: {len(rows)} filas")
    print(f"Convertidas: {converted} filas")
    print(f"Archivo guardado: {output_file}")
    return True

if __name__ == '__main__':
    input_file = sys.argv[1] if len(sys.argv) > 1 else 'materia_prima.csv'
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'materia_prima_fixed.csv'
    
    if fix_uom_csv(input_file, output_file):
        print("\nAhora podés importar el archivo 'materia_prima_fixed.csv' en Odoo")
    else:
        sys.exit(1)
