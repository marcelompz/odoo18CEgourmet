import pandas as pd

file_path = '/opt/odoo/odoo8083/migracion/migracion_productos_materiaprima.xlsx'
xl = pd.ExcelFile(file_path)

print("--- SUBPRODUCTO ---")
df_sub = xl.parse("SUBPRODUCTO", nrows=20)
print(df_sub)

print("\n--- FÓRMULAS DE COSTEO ---")
df_form = xl.parse("FÓRMULAS DE COSTEO", nrows=20)
print(df_form.iloc[:, :10])
