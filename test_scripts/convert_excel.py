import pandas as pd
import numpy as np

def clean_excel(input_path, output_path):
    xl = pd.ExcelFile(input_path)
    
    # 1. MATERIAPRIMA
    df_mp = xl.parse("MATERIAPRIMA")
    # Filter out empty rows
    df_mp = df_mp[df_mp['Nombre'].notna()]
    
    products = []
    # Add MATERIAPRIMA products
    for _, row in df_mp.iterrows():
        products.append({
            'Name': str(row['Nombre']).strip(),
            'Type': 'Product',
            'Category': 'Materia Prima',
            'Available in POS': False,
            'Cost': row['Precio'] if pd.notna(row['Precio']) else 0.0,
            'UoM': str(row['Unidad de medida']).strip() if pd.notna(row['Unidad de medida']) else 'Unidades'
        })
        
    # 2. COMIDAS
    df_comidas = xl.parse("COMIDAS")
    df_comidas = df_comidas[df_comidas['Nombre'].notna()]
    for _, row in df_comidas.iterrows():
        products.append({
            'Name': str(row['Nombre']).strip(),
            'Type': 'Product',
            'Category': 'Comidas',
            'Available in POS': True,
            'Cost': 0.0,
            'UoM': 'Unidades'
        })

    # 3. SUBPRODUCTOS (BoM)
    df_sub = xl.parse("SUBPRODUCTO")
    boms_mrp = []
    current_recipe = None
    
    for i, row in df_sub.iterrows():
        # Recipe header usually has 'RINDE'
        col0 = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ''
        col1 = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ''
        col3 = str(row.iloc[3]).strip() if pd.notna(row.iloc[3]) else ''
        
        if 'RINDE' in str(row.values).upper():
            if pd.notna(row.iloc[1]) and row.iloc[1] != 'Descripción' and row.iloc[1] != 'HARINA 3 CEROS':
                current_recipe = str(row.iloc[1]).strip()
            elif pd.notna(df_sub.columns[1]) and 'PAN' in df_sub.columns[1].upper() and current_recipe is None:
                current_recipe = df_sub.columns[1].strip()
            continue
            
        if col0 == 'Cant.' or col1 == 'Descripción':
            continue
            
        if 'COSTO TOTAL' in col1.upper() or 'SUB TOTAL' in col1.upper():
            current_recipe = None
            continue
            
        # It's an ingredient row
        if current_recipe and col1 and col0:
            try:
                qty = float(col0)
                if qty > 0 and col1 != '.' and col1 != '0':
                    boms_mrp.append({
                        'Recipe': current_recipe,
                        'Component': col1,
                        'Quantity': qty
                    })
            except ValueError:
                pass
                
    # Add subproducts to products list
    subproduct_names = set(b['Recipe'] for b in boms_mrp)
    for sp in subproduct_names:
        products.append({
            'Name': sp,
            'Type': 'Product',
            'Category': 'Subproducto',
            'Available in POS': False,
            'Cost': 0.0,
            'UoM': 'Unidades'
        })
        
    # 4. COMIDAS (POS BoM)
    df_costeo = xl.parse("COSTEO COMIDAS")
    boms_pos = []
    current_recipe = None
    
    for i, row in df_costeo.iterrows():
        col0 = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ''
        col1 = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ''
        
        if col0.startswith('N') and len(col0) < 5:
            current_recipe = col1
            continue
            
        if col0 == 'Cant.' or col1 == 'Descripción':
            continue
            
        if 'COSTO TOTAL' in col1.upper() or 'SUB TOTAL' in col1.upper() or 'COSTO DE PLATO' in col1.upper() or 'TOTAL' in col1.upper() or '%' in col1:
            if not pd.notna(row.iloc[0]):
                current_recipe = None
            continue
            
        if current_recipe and col1 and col0:
            try:
                qty = float(col0)
                if qty > 0 and col1 != '.' and col1 != '0' and col1 != 'nan':
                    boms_pos.append({
                        'Recipe': current_recipe,
                        'Component': col1,
                        'Quantity': qty
                    })
            except ValueError:
                pass
                
    # Save to new Excel
    with pd.ExcelWriter(output_path) as writer:
        pd.DataFrame(products).drop_duplicates(subset=['Name']).to_excel(writer, sheet_name='Products', index=False)
        pd.DataFrame(boms_mrp).to_excel(writer, sheet_name='MRP BoM (Subproducts)', index=False)
        pd.DataFrame(boms_pos).to_excel(writer, sheet_name='POS BoM (Comidas)', index=False)

if __name__ == '__main__':
    input_file = '/opt/odoo/odoo8083/migracion/migracion_productos_materiaprima.xlsx'
    output_file = '/opt/odoo/odoo8083/migracion/plantilla_importacion.xlsx'
    clean_excel(input_file, output_file)
    print("Done generating plantilla_importacion.xlsx")
