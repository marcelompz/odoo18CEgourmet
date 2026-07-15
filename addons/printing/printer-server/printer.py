import base64
import subprocess
import uuid
import os
import urllib.request


def send_print_job(printer, options):
    base64string = options.get('base64')
    filename = options.get('filename')
    full_path = '/opt/odoo/addons/printing/static/src/'
    if base64string:
        base64data = str.encode(base64string)
        uid = uuid.uuid4()
        filename = f'{uid}.png'
        full_path = full_path + filename
        with open(full_path, 'wb') as f:
            f.write(base64.decodebytes(base64data))
    elif filename:
        urllib.request.urlretrieve(filename, '/opt/odoo/addons/printing/static/src/invoice.pdf')
        filename = 'invoice.pdf'
        full_path = full_path + filename
    else:
        return
    subprocess.run(['lp', '-d', printer, full_path])
    os.remove(full_path)
