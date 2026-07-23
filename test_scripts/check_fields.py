import sys
cat = env['product.category'].search([], limit=1)
fields = cat._fields.keys()
for f in fields:
    if 'stock' in f or 'account' in f or 'valuation' in f:
        print(f"Field: {f}")
