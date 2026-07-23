import base64

# Ruta del logo copiado en el contenedor
logo_path = "/mnt/extra-addons-customize/agripar.png"

try:
    with open(logo_path, "rb") as f:
        logo_data = base64.b64encode(f.read())
    print("Logo leido exitosamente.")
except Exception as e:
    print(f"Error al leer el archivo de logo: {e}")
    logo_data = False

# Actualizar Compañía (ID 1)
company = env.company
company.write({
    'name': 'Agripar S.A.',
    'website': 'https://www.agripar.com.py/',
    'email': 'contacto@agripar.com.py',
    'phone': '+595 21 123456',
    'logo': logo_data,
})
print(f"Compañía actualizada a: {company.name}")

# Actualizar el contacto (res.partner) de la compañía
company.partner_id.write({
    'name': 'Agripar S.A.',
    'website': 'https://www.agripar.com.py/',
    'email': 'contacto@agripar.com.py',
    'phone': '+595 21 123456',
    'image_1920': logo_data,
})
print("Contacto de la compañía actualizado.")

# Actualizar el Registro del Sitio Web (ID 1)
website = env['website'].browse(1)
if website:
    website.write({
        'name': 'Agripar S.A.',
    })
    print(f"Registro de Sitio Web actualizado a: {website.name}")

env.cr.commit()
print("Transacción guardada exitosamente en la base de datos.")
