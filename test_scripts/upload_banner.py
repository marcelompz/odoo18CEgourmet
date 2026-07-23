import base64

banner_path = "/mnt/extra-addons-customize/hero-banner.png"

try:
    with open(banner_path, "rb") as f:
        banner_data = base64.b64encode(f.read())
        
    attachment = env['ir.attachment'].create({
        'name': 'Agripar Hero Banner',
        'datas': banner_data,
        'public': True,
        'type': 'binary',
        'mimetype': 'image/png',
    })
    print(f"✅ Banner subido como Adjunto con ID: {attachment.id}")
    
    # También subiremos el logo como adjunto independiente
    logo_path = "/mnt/extra-addons-customize/agripar.png"
    with open(logo_path, "rb") as f:
        logo_data = base64.b64encode(f.read())
    logo_attach = env['ir.attachment'].create({
        'name': 'Agripar Logo PNG',
        'datas': logo_data,
        'public': True,
        'type': 'binary',
        'mimetype': 'image/png',
    })
    print(f"✅ Logo subido como Adjunto con ID: {logo_attach.id}")
    
    env.cr.commit()
    print("Transacción de subida de medios completada.")
except Exception as e:
    print(f"❌ Error al subir medios: {e}")
