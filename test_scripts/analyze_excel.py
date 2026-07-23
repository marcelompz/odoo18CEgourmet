import pandas as pd

file_path = '/opt/odoo/odoo8083/migracion/migracion_productos_materiaprima.xlsx'

xl = pd.ExcelFile(file_path)
print("Sheet names:", xl.sheet_names)

for sheet in xl.sheet_names:
    print(f"\n--- Sheet: {sheet} ---")
    df = xl.parse(sheet, nrows=5)
    print("Columns:", list(df.columns))
    print("First 2 rows:")
    print(df.head(2).to_dict(orient='records'))
