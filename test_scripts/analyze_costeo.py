import pandas as pd

file_path = '/opt/odoo/odoo8083/migracion/migracion_productos_materiaprima.xlsx'
xl = pd.ExcelFile(file_path)

print("--- COSTEO COMIDAS ---")
df_com = xl.parse("COSTEO COMIDAS", nrows=20)
print(df_com)

